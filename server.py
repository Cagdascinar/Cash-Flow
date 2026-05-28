import sqlite3, json, os, csv, io, re
from datetime import datetime, date
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "nakit.db")

GELIR_CATS = ["Maaş", "Serbest Meslek", "Kira Geliri", "Yatırım / Temettü", "Hediye / İkramiye", "Diğer Gelir"]
GIDER_CATS = ["Kira / Mortgage", "Market / Gıda", "Faturalar", "Ulaşım", "Yemek / Restoran",
               "Eğlence", "Sağlık", "Giyim", "Eğitim", "Abonelikler", "Elektronik", "Diğer Gider"]

# ── DB ────────────────────────────────────────────────────────────────────────

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db: db.close()

def init_db():
    with sqlite3.connect(DB) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            type        TEXT NOT NULL,
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            description TEXT DEFAULT '',
            date        TEXT NOT NULL,
            created_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS budgets (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE NOT NULL,
            limit_   REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_date ON transactions(date);
        """)

# ── helpers ───────────────────────────────────────────────────────────────────

def row_to_dict(row):
    return dict(row)

def today_str():
    return date.today().isoformat()

def month_range(year, month):
    from calendar import monthrange
    _, last = monthrange(year, month)
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last:02d}"

# ── API ───────────────────────────────────────────────────────────────────────

@app.route("/api/transactions", methods=["GET"])
def list_transactions():
    db   = get_db()
    year  = request.args.get("year",  date.today().year,  type=int)
    month = request.args.get("month", date.today().month, type=int)
    ftype = request.args.get("type")
    start, end = month_range(year, month)
    q = "SELECT * FROM transactions WHERE date BETWEEN ? AND ?"
    params = [start, end]
    if ftype:
        q += " AND type=?"; params.append(ftype)
    q += " ORDER BY date DESC, id DESC"
    rows = db.execute(q, params).fetchall()
    return jsonify([row_to_dict(r) for r in rows])

@app.route("/api/transactions", methods=["POST"])
def add_transaction():
    d = request.get_json(force=True)
    ttype  = d.get("type")
    amount = float(d.get("amount", 0))
    cat    = d.get("category", "")
    desc   = d.get("description", "")
    dt     = d.get("date", today_str())
    if ttype not in ("gelir", "gider") or amount <= 0 or not cat:
        return jsonify({"ok": False, "error": "Geçersiz veri"}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO transactions (type,amount,category,description,date,created_at) VALUES (?,?,?,?,?,?)",
        (ttype, amount, cat, desc, dt, datetime.now().isoformat())
    )
    db.commit()
    return jsonify({"ok": True, "id": cur.lastrowid})

@app.route("/api/transactions/<int:tid>", methods=["DELETE"])
def del_transaction(tid):
    db = get_db()
    db.execute("DELETE FROM transactions WHERE id=?", (tid,))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/summary")
def summary():
    db    = get_db()
    year  = request.args.get("year",  date.today().year,  type=int)
    month = request.args.get("month", date.today().month, type=int)
    start, end = month_range(year, month)

    rows = db.execute(
        "SELECT type, category, SUM(amount) as total FROM transactions "
        "WHERE date BETWEEN ? AND ? GROUP BY type, category",
        (start, end)
    ).fetchall()

    gelir_total = gider_total = 0.0
    gelir_cats  = {}
    gider_cats  = {}
    for r in rows:
        if r["type"] == "gelir":
            gelir_total += r["total"]
            gelir_cats[r["category"]] = round(r["total"], 2)
        else:
            gider_total += r["total"]
            gider_cats[r["category"]] = round(r["total"], 2)

    # 12-month bar chart data
    bar = []
    for m in range(1, 13):
        s, e2 = month_range(year, m)
        totals = db.execute(
            "SELECT type, SUM(amount) as t FROM transactions "
            "WHERE date BETWEEN ? AND ? GROUP BY type", (s, e2)
        ).fetchall()
        g_val = next((r["t"] for r in totals if r["type"] == "gelir"), 0)
        ex_val = next((r["t"] for r in totals if r["type"] == "gider"), 0)
        bar.append({"month": m, "gelir": round(g_val, 2), "gider": round(ex_val, 2)})

    # all-time balance
    balance_row = db.execute(
        "SELECT SUM(CASE WHEN type='gelir' THEN amount ELSE -amount END) as bal FROM transactions"
    ).fetchone()
    balance = round(balance_row["bal"] or 0, 2)

    # budgets
    budgets = {r["category"]: r["limit_"] for r in db.execute("SELECT * FROM budgets").fetchall()}

    return jsonify({
        "gelir":      round(gelir_total, 2),
        "gider":      round(gider_total, 2),
        "net":        round(gelir_total - gider_total, 2),
        "balance":    balance,
        "gelir_cats": gelir_cats,
        "gider_cats": gider_cats,
        "bar":        bar,
        "budgets":    budgets,
    })

@app.route("/api/budgets", methods=["POST"])
def set_budget():
    d = request.get_json(force=True)
    cat   = d.get("category", "")
    limit = float(d.get("limit", 0))
    if not cat or limit <= 0:
        return jsonify({"ok": False}), 400
    db = get_db()
    db.execute("INSERT INTO budgets(category,limit_) VALUES(?,?) "
               "ON CONFLICT(category) DO UPDATE SET limit_=excluded.limit_", (cat, limit))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/motivation")
def motivation():
    db    = get_db()
    today = date.today()
    year, month = today.year, today.month
    start, end  = month_range(year, month)

    # this month totals
    rows = db.execute(
        "SELECT type, SUM(amount) as t FROM transactions WHERE date BETWEEN ? AND ? GROUP BY type",
        (start, end)
    ).fetchall()
    gelir  = next((r["t"] for r in rows if r["type"] == "gelir"), 0) or 0
    gider  = next((r["t"] for r in rows if r["type"] == "gider"), 0) or 0
    net    = gelir - gider

    # days passed / remaining in month
    from calendar import monthrange
    _, days_in_month = monthrange(year, month)
    days_passed   = today.day
    days_left     = days_in_month - days_passed
    daily_spend   = gider / max(days_passed, 1)
    projected_spend = daily_spend * days_in_month

    # all-time balance
    bal_row = db.execute(
        "SELECT SUM(CASE WHEN type='gelir' THEN amount ELSE -amount END) as b FROM transactions"
    ).fetchone()
    balance = (bal_row["b"] or 0)

    # budgets
    budgets = {r["category"]: r["limit_"] for r in db.execute("SELECT * FROM budgets").fetchall()}
    budget_total = sum(budgets.values())

    # top gider category
    top_rows = db.execute(
        "SELECT category, SUM(amount) as t FROM transactions WHERE date BETWEEN ? AND ? AND type='gider' GROUP BY category ORDER BY t DESC LIMIT 1",
        (start, end)
    ).fetchall()
    top_gider_cat = top_rows[0]["category"] if top_rows else None
    top_gider_amt = top_rows[0]["t"] if top_rows else 0

    msgs = []
    score = 0  # 0-100 health score

    # ── analysis ──────────────────────────────────────────────────────────────
    if gelir == 0:
        msgs.append({"icon": "💡", "text": "Henüz bu ay gelir girmedin. Maaş veya gelirini ekle, hesaplama yapayım."})
        return jsonify({"score": 0, "label": "Veri Bekleniyor", "color": "#64748b", "msgs": msgs,
                        "projected_month": 0, "daily_avg": 0, "days_left": days_left, "net": 0})

    save_rate = net / gelir * 100 if gelir > 0 else 0

    # Save rate score
    if save_rate >= 30:
        score += 40
        msgs.append({"icon": "🔥", "text": f"Harika! Gelirinin %{save_rate:.0f}'ini biriktiriyorsun. Finansal özgürlük yolundasın."})
    elif save_rate >= 15:
        score += 25
        msgs.append({"icon": "✅", "text": f"İyi gidiyorsun — gelirinin %{save_rate:.0f}'ini tasarruf ediyorsun."})
    elif save_rate >= 0:
        score += 10
        msgs.append({"icon": "⚠️", "text": f"Bu ay gelirinin sadece %{save_rate:.0f}'ini biriktirebildin. Hedef en az %20."})
    else:
        msgs.append({"icon": "🚨", "text": f"Bu ay gelirininden {abs(net):,.0f}₺ fazla harcadın. Acil inceleme gerekiyor!"})

    # Daily burn rate projection
    if days_left > 0:
        if projected_spend < gelir * 0.85:
            score += 20
            projected_save = gelir - projected_spend
            msgs.append({"icon": "📈", "text": f"Ay sonuna {days_left} gün kaldı. Bu hızla gidersen {projected_save:,.0f}₺ biriktireceksin. Süper!"})
        elif projected_spend < gelir:
            score += 10
            msgs.append({"icon": "📊", "text": f"Günlük ortalama harcaman {daily_spend:,.0f}₺. Ay sonunda tahminen {projected_spend:,.0f}₺ harcarsin."})
        else:
            msgs.append({"icon": "⚡", "text": f"Dikkat! Bu hızda ay sonunda {projected_spend:,.0f}₺ harcamış olacaksın ama gelirin {gelir:,.0f}₺. Freni biraz bas!"})

    # Budget adherence
    if budgets:
        over_budget = []
        from calendar import monthrange as mr2
        for cat, lim in budgets.items():
            spent_row = db.execute(
                "SELECT SUM(amount) as t FROM transactions WHERE date BETWEEN ? AND ? AND type='gider' AND category=?",
                (start, end, cat)
            ).fetchone()
            spent = spent_row["t"] or 0
            if spent > lim:
                over_budget.append((cat, spent - lim))

        if not over_budget:
            score += 20
            msgs.append({"icon": "🎯", "text": "Tüm bütçe hedeflerini tutturuyorsun. Disiplin çok iyi!"})
        else:
            for cat, excess in over_budget[:2]:
                msgs.append({"icon": "🔴", "text": f"'{cat}' bütçeni {excess:,.0f}₺ aştın. Bu ayki harcamana dikkat et."})
    else:
        score += 10
        msgs.append({"icon": "💡", "text": "Bütçe hedefleri belirle — harcamalarını kontrol etmek çok kolaylaşır."})

    # Top spending category insight
    if top_gider_cat and top_gider_amt > 0 and gelir > 0:
        pct = top_gider_amt / gelir * 100
        if pct > 40:
            msgs.append({"icon": "🔍", "text": f"En büyük giderin '{top_gider_cat}' — gelirinin %{pct:.0f}'i gidiyor. Buraya odaklan."})
        else:
            score += 10
            msgs.append({"icon": "✨", "text": f"En büyük gider kalemen '{top_gider_cat}': {top_gider_amt:,.0f}₺ (%{pct:.0f}). Dengeli görünüyor."})

    # Balance milestone
    if balance >= 100000:
        score += 10
        msgs.append({"icon": "🏆", "text": f"Toplam birikimin {balance:,.0f}₺! 100K kulübüne girdin, tebrikler."})
    elif balance >= 50000:
        score += 8
        remaining = 100000 - balance
        months_to_goal = remaining / (net if net > 0 else 1)
        msgs.append({"icon": "🎯", "text": f"100K₺ hedefine {remaining:,.0f}₺ kaldı. Bu tasarruf hızıyla yaklaşık {months_to_goal:.0f} ayda ulaşırsın."})
    elif balance > 0 and net > 0:
        score += 5
        msgs.append({"icon": "🌱", "text": f"Birikimin büyüyor. Aylık {net:,.0f}₺ tasarrufla 1 yılda {net*12:,.0f}₺ yaparsın!"})

    # Compute label
    score = min(100, max(0, score))
    if score >= 75:
        label, color = "Finansal Sağlık: Mükemmel", "#22c55e"
    elif score >= 50:
        label, color = "Finansal Sağlık: İyi", "#3b82f6"
    elif score >= 25:
        label, color = "Finansal Sağlık: Orta", "#f59e0b"
    else:
        label, color = "Finansal Sağlık: Zayıf", "#ef4444"

    return jsonify({
        "score":          score,
        "label":          label,
        "color":          color,
        "msgs":           msgs,
        "projected_month": round(projected_spend, 2),
        "daily_avg":       round(daily_spend, 2),
        "days_left":       days_left,
        "net":             round(net, 2),
        "save_rate":       round(save_rate, 1),
    })

@app.route("/api/categories")
def categories():
    return jsonify({"gelir": GELIR_CATS, "gider": GIDER_CATS})

# ── CSV import ────────────────────────────────────────────────────────────────

def _parse_amount(s):
    """Parse Turkish/international number strings to float. Handles:
    1.234,56 → 1234.56  (Turkish: dot=thousands, comma=decimal)
    1,234.56 → 1234.56  (English: comma=thousands, dot=decimal)
    35000,00 → 35000.00 (Turkish decimal-only)
    35000.00 → 35000.00 (plain)
    """
    s = s.strip().replace(" ", "").replace("\xa0", "")
    s = re.sub(r"[₺$€£+]", "", s)
    neg = s.startswith("-")
    s = s.lstrip("-")
    if not s:
        return None

    dots   = s.count(".")
    commas = s.count(",")

    if dots == 0 and commas == 0:
        # plain integer
        pass
    elif dots >= 1 and commas == 0:
        # could be 35000.00 or 1.234.567 (all dots = thousands in some formats)
        if dots == 1:
            pass  # treat as decimal point
        else:
            s = s.replace(".", "")  # all dots = thousand separators
    elif dots == 0 and commas == 1:
        # 35000,00 → decimal comma
        s = s.replace(",", ".")
    elif dots == 0 and commas > 1:
        # 1,234,567 → commas = thousands
        s = s.replace(",", "")
    elif dots == 1 and commas == 1:
        if s.index(".") < s.index(","):
            # 1.234,56 → Turkish (dot=thousands, comma=decimal)
            s = s.replace(".", "").replace(",", ".")
        else:
            # 1,234.56 → English
            s = s.replace(",", "")
    elif dots > 1 and commas == 1:
        # 1.234.567,89 → Turkish
        s = s.replace(".", "").replace(",", ".")
    elif dots == 1 and commas > 1:
        # 1,234,567.89 → English
        s = s.replace(",", "")

    try:
        return abs(float(s))
    except Exception:
        return None

def _parse_date(s):
    """Try multiple date formats → YYYY-MM-DD"""
    s = s.strip()
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return None

# keyword → category mapping (lowercase)
_CAT_MAP = {
    "maaş": "Maaş", "maas": "Maaş", "salary": "Maaş", "ücret": "Maaş",
    "kira": "Kira / Mortgage", "mortgage": "Kira / Mortgage", "aidat": "Faturalar",
    "elektrik": "Faturalar", "su fatura": "Faturalar", "doğalgaz": "Faturalar", "dogalgaz": "Faturalar",
    "fatura": "Faturalar", "internet": "Abonelikler", "netflix": "Abonelikler",
    "spotify": "Abonelikler", "abonelik": "Abonelikler",
    "market": "Market / Gıda", "migros": "Market / Gıda", "a101": "Market / Gıda",
    "bim": "Market / Gıda", "carrefour": "Market / Gıda", "şok": "Market / Gıda",
    "taxi": "Ulaşım", "taksi": "Ulaşım", "uber": "Ulaşım", "metro": "Ulaşım",
    "otobüs": "Ulaşım", "akaryakıt": "Ulaşım", "benzin": "Ulaşım", "shell": "Ulaşım",
    "opet": "Ulaşım", "bp ": "Ulaşım",
    "restoran": "Yemek / Restoran", "cafe": "Yemek / Restoran", "kahve": "Yemek / Restoran",
    "yemeksepeti": "Yemek / Restoran", "getir": "Yemek / Restoran", "trendyol yemek": "Yemek / Restoran",
    "sinema": "Eğlence", "konser": "Eğlence", "bilet": "Eğlence",
    "eczane": "Sağlık", "hastane": "Sağlık", "doktor": "Sağlık", "ilaç": "Sağlık",
    "giyim": "Giyim", "zara": "Giyim", "h&m": "Giyim", "lcw": "Giyim",
    "okul": "Eğitim", "kurs": "Eğitim", "udemy": "Eğitim",
    "amazon": "Elektronik", "trendyol": "Diğer Gider", "hepsiburada": "Diğer Gider",
    "faiz": "Yatırım / Temettü", "temettü": "Yatırım / Temettü", "getirisi": "Yatırım / Temettü",
    "hediye": "Hediye / İkramiye", "ikramiye": "Hediye / İkramiye",
}

def _guess_category(desc, ttype):
    dl = desc.lower()
    for kw, cat in _CAT_MAP.items():
        if kw in dl:
            return cat
    return "Diğer Gelir" if ttype == "gelir" else "Diğer Gider"

def _detect_bank_format(header_row):
    """Return column indices: (date_col, desc_col, debit_col, credit_col, amount_col)"""
    h = [c.lower().strip() for c in header_row]

    def find(*names):
        for n in names:
            for i, c in enumerate(h):
                if n in c:
                    return i
        return None

    date_col   = find("tarih", "date", "işlem tarihi", "valör")
    desc_col   = find("açıklama", "aciklama", "işlem", "description", "detay", "karşı taraf")
    debit_col  = find("borç", "borc", "çıkış", "debit", "gider", "harcama")
    credit_col = find("alacak", "giriş", "credit", "gelir", "tahsilat")
    amount_col = find("tutar", "amount", "miktar") if (debit_col is None and credit_col is None) else None

    return date_col, desc_col, debit_col, credit_col, amount_col

@app.route("/api/import/preview", methods=["POST"])
def import_preview():
    """Parse uploaded CSV, return preview rows (not saved yet)."""
    f = request.files.get("file")
    if not f:
        return jsonify({"ok": False, "error": "Dosya yüklenmedi"}), 400

    raw = f.read().decode("utf-8-sig", errors="replace")  # handle BOM
    # try comma then semicolon
    dialect = "excel"
    if raw.count(";") > raw.count(","):
        dialect = "excel-semicolon"
        csv.register_dialect("excel-semicolon", delimiter=";")

    reader = csv.reader(io.StringIO(raw), dialect)
    rows   = [r for r in reader if any(c.strip() for c in r)]

    if len(rows) < 2:
        return jsonify({"ok": False, "error": "CSV çok kısa veya boş"}), 400

    # skip leading non-data rows (banks often have bank name / account info at top)
    header_idx = 0
    for i, row in enumerate(rows):
        if any(kw in " ".join(row).lower() for kw in ("tarih", "date", "tutar", "açıklama", "işlem")):
            header_idx = i
            break

    header = rows[header_idx]
    data_rows = rows[header_idx + 1:]

    date_col, desc_col, debit_col, credit_col, amount_col = _detect_bank_format(header)

    parsed = []
    skipped = 0
    for row in data_rows:
        if len(row) <= max(filter(lambda x: x is not None,
                                  [date_col or 0, desc_col or 0, debit_col or 0,
                                   credit_col or 0, amount_col or 0])):
            skipped += 1
            continue

        dt  = _parse_date(row[date_col]) if date_col is not None and date_col < len(row) else None
        if not dt:
            skipped += 1
            continue

        desc = row[desc_col].strip() if desc_col is not None and desc_col < len(row) else ""

        if amount_col is not None:
            # single amount column — need sign or separate gelir/gider detection
            raw_amt = row[amount_col] if amount_col < len(row) else ""
            neg = raw_amt.strip().startswith("-")
            amt = _parse_amount(raw_amt)
            if not amt:
                skipped += 1; continue
            ttype = "gider" if neg else "gelir"
        elif debit_col is not None or credit_col is not None:
            d_val = _parse_amount(row[debit_col])  if debit_col  is not None and debit_col  < len(row) else None
            c_val = _parse_amount(row[credit_col]) if credit_col is not None and credit_col < len(row) else None
            if d_val and d_val > 0:
                amt, ttype = d_val, "gider"
            elif c_val and c_val > 0:
                amt, ttype = c_val, "gelir"
            else:
                skipped += 1; continue
        else:
            skipped += 1; continue

        cat = _guess_category(desc, ttype)
        parsed.append({
            "date": dt, "description": desc, "amount": round(amt, 2),
            "type": ttype, "category": cat
        })

    return jsonify({"ok": True, "rows": parsed, "skipped": skipped, "headers": header})

@app.route("/api/import/confirm", methods=["POST"])
def import_confirm():
    """Save a list of already-previewed transactions."""
    rows = request.get_json(force=True)
    if not isinstance(rows, list):
        return jsonify({"ok": False}), 400
    db  = get_db()
    now = datetime.now().isoformat()
    count = 0
    for r in rows:
        if not r.get("skip") and r.get("amount", 0) > 0:
            db.execute(
                "INSERT INTO transactions (type,amount,category,description,date,created_at) VALUES (?,?,?,?,?,?)",
                (r["type"], r["amount"], r["category"], r.get("description",""), r["date"], now)
            )
            count += 1
    db.commit()
    return jsonify({"ok": True, "imported": count})

# ── HTML ──────────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nakit Akışım</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0f1117;--bg2:#1a1d27;--bg3:#22263a;
  --g:#22c55e;--r:#ef4444;--b:#3b82f6;--y:#f59e0b;--p:#a855f7;
  --txt:#e2e8f0;--muted:#64748b;--border:#2d3348;
  --radius:14px;--shadow:0 4px 24px rgba(0,0,0,.4);
}
body{background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}
a{color:inherit;text-decoration:none}

/* layout */
.wrap{max-width:1200px;margin:0 auto;padding:24px 16px}
header{display:flex;align-items:center;justify-content:space-between;margin-bottom:28px;flex-wrap:wrap;gap:12px}
header h1{font-size:1.5rem;font-weight:700;display:flex;align-items:center;gap:10px}
header h1 span{font-size:1.8rem}

/* cards */
.card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow)}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px}
@media(max-width:700px){.grid3{grid-template-columns:1fr}.grid2{grid-template-columns:1fr}}

/* summary cards */
.scard{border-radius:var(--radius);padding:22px 20px;position:relative;overflow:hidden}
.scard .label{font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;opacity:.6;margin-bottom:6px}
.scard .amount{font-size:1.9rem;font-weight:800;letter-spacing:-.02em}
.scard .sub{font-size:.78rem;opacity:.55;margin-top:6px}
.scard.gelir{background:linear-gradient(135deg,#166534 0%,#14532d 100%);border:1px solid #22c55e33}
.scard.gider{background:linear-gradient(135deg,#7f1d1d 0%,#6b1414 100%);border:1px solid #ef444433}
.scard.net  {background:linear-gradient(135deg,#1e3a5f 0%,#172a47 100%);border:1px solid #3b82f633}
.scard .icon{position:absolute;right:16px;top:16px;font-size:2rem;opacity:.25}

/* month nav */
.mnav{display:flex;align-items:center;gap:12px}
.mnav button{background:var(--bg3);border:1px solid var(--border);color:var(--txt);padding:6px 14px;border-radius:8px;cursor:pointer;font-size:.85rem;transition:.15s}
.mnav button:hover{background:var(--bg2);border-color:var(--b)}
.mnav .mlabel{font-weight:600;min-width:110px;text-align:center}

/* form */
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
@media(max-width:600px){.form-row{grid-template-columns:1fr}}
label{display:block;font-size:.78rem;color:var(--muted);margin-bottom:4px;font-weight:500}
input,select,textarea{width:100%;background:var(--bg3);border:1px solid var(--border);color:var(--txt);
  padding:10px 12px;border-radius:8px;font-size:.9rem;outline:none;transition:.15s}
input:focus,select:focus{border-color:var(--b)}
.btn{padding:11px 20px;border-radius:8px;border:none;font-size:.9rem;font-weight:600;cursor:pointer;transition:.2s}
.btn-g{background:var(--g);color:#fff}
.btn-r{background:var(--r);color:#fff}
.btn-b{background:var(--b);color:#fff}
.btn:hover{opacity:.85;transform:translateY(-1px)}
.tab-row{display:flex;gap:8px;margin-bottom:16px}
.tab{flex:1;padding:10px;border-radius:8px;border:2px solid transparent;font-weight:600;font-size:.88rem;cursor:pointer;transition:.2s;background:var(--bg3);color:var(--muted)}
.tab.active-g{border-color:var(--g);color:var(--g);background:#16532022}
.tab.active-r{border-color:var(--r);color:var(--r);background:#7f1d1d22}

/* transactions list */
.tx-list{display:flex;flex-direction:column;gap:8px;max-height:440px;overflow-y:auto}
.tx-list::-webkit-scrollbar{width:4px}
.tx-list::-webkit-scrollbar-track{background:transparent}
.tx-list::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px}
.tx-item{display:flex;align-items:center;gap:12px;padding:12px 14px;
  background:var(--bg3);border-radius:10px;border:1px solid var(--border);transition:.15s}
.tx-item:hover{border-color:var(--b)}
.tx-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.tx-dot.g{background:var(--g)}
.tx-dot.r{background:var(--r)}
.tx-info{flex:1;min-width:0}
.tx-cat{font-size:.8rem;color:var(--muted)}
.tx-desc{font-size:.88rem;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tx-date{font-size:.75rem;color:var(--muted)}
.tx-amt{font-weight:700;font-size:.95rem;white-space:nowrap}
.tx-del{background:none;border:none;color:var(--muted);cursor:pointer;padding:4px;border-radius:4px;font-size:1rem;transition:.15s;flex-shrink:0}
.tx-del:hover{color:var(--r)}
.empty{text-align:center;color:var(--muted);padding:40px 20px;font-size:.9rem}

/* charts */
canvas{display:block}
.chart-title{font-size:.82rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:14px}

/* progress bars (budget) */
.budget-row{margin-bottom:14px}
.budget-row .top{display:flex;justify-content:space-between;font-size:.8rem;margin-bottom:5px}
.budget-row .top .cat{color:var(--txt)}
.budget-row .top .nums{color:var(--muted)}
.prog-bg{background:var(--bg3);border-radius:4px;height:7px;overflow:hidden}
.prog-fill{height:100%;border-radius:4px;transition:width .6s cubic-bezier(.4,0,.2,1)}

/* badge */
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:.72rem;font-weight:600}
.badge-g{background:#22c55e22;color:var(--g)}
.badge-r{background:#ef444422;color:var(--r)}

/* toast */
#toast{position:fixed;bottom:24px;right:24px;background:#22263a;border:1px solid var(--b);
  color:var(--txt);padding:12px 20px;border-radius:10px;font-size:.88rem;
  transform:translateY(80px);opacity:0;transition:.3s;z-index:999}
#toast.show{transform:translateY(0);opacity:1}

.section-title{font-size:1rem;font-weight:700;margin-bottom:14px;display:flex;align-items:center;gap:8px}
.section-title::after{content:'';flex:1;height:1px;background:var(--border)}

/* balance big */
.balance-hero{text-align:center;padding:10px 0 18px}
.balance-hero .lbl{font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:6px}
.balance-hero .val{font-size:3rem;font-weight:900;letter-spacing:-.04em}
.balance-hero .val.pos{color:var(--g)}
.balance-hero .val.neg{color:var(--r)}
</style>
</head>
<body>
<div class="wrap">

<!-- HEADER -->
<header>
  <h1><span>💰</span> Nakit Akışım</h1>
  <div class="mnav">
    <button onclick="changeMonth(-1)">‹</button>
    <div class="mlabel" id="mlabel"></div>
    <button onclick="changeMonth(1)">›</button>
  </div>
</header>

<!-- BALANCE -->
<div class="balance-hero">
  <div class="lbl">Toplam Birikimim</div>
  <div class="val" id="balance-val">—</div>
</div>

<!-- SUMMARY CARDS -->
<div class="grid3">
  <div class="scard gelir">
    <div class="icon">📈</div>
    <div class="label">Bu Ay Gelir</div>
    <div class="amount" id="s-gelir">—</div>
    <div class="sub" id="s-gelir-sub"></div>
  </div>
  <div class="scard gider">
    <div class="icon">📉</div>
    <div class="label">Bu Ay Gider</div>
    <div class="amount" id="s-gider">—</div>
    <div class="sub" id="s-gider-sub"></div>
  </div>
  <div class="scard net">
    <div class="icon">⚖️</div>
    <div class="label">Net Tasarruf</div>
    <div class="amount" id="s-net">—</div>
    <div class="sub" id="s-net-sub"></div>
  </div>
</div>

<!-- MOTIVATION CARD -->
<div class="card" id="motiv-card" style="margin-bottom:20px">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:10px">
    <div class="section-title" style="margin:0;flex:1">Finansal Durum Analizi</div>
    <div id="motiv-score-badge" style="font-size:.82rem;font-weight:700;padding:5px 14px;border-radius:20px;background:#22263a;border:1px solid #2d3348">—</div>
  </div>
  <div style="margin-bottom:14px">
    <div style="background:var(--bg3);border-radius:8px;height:8px;overflow:hidden">
      <div id="motiv-bar" style="height:100%;border-radius:8px;transition:width .8s cubic-bezier(.4,0,.2,1);width:0%"></div>
    </div>
  </div>
  <div id="motiv-msgs" style="display:flex;flex-direction:column;gap:8px">
    <div class="empty">Yükleniyor…</div>
  </div>
</div>

<!-- CHARTS + FORM -->
<div class="grid2">

  <!-- BAR CHART -->
  <div class="card">
    <div class="chart-title">Aylık Gelir / Gider</div>
    <canvas id="barChart" height="200"></canvas>
  </div>

  <!-- DONUT CHART -->
  <div class="card">
    <div class="chart-title">Gider Dağılımı</div>
    <canvas id="donut" height="200"></canvas>
  </div>

</div>

<!-- ADD FORM + TRANSACTIONS -->
<div class="grid2">

  <!-- FORM -->
  <div class="card">
    <div class="section-title">İşlem Ekle</div>
    <div class="tab-row">
      <button class="tab active-g" id="tab-g" onclick="setTab('gelir')">+ Gelir</button>
      <button class="tab" id="tab-r" onclick="setTab('gider')">− Gider</button>
    </div>
    <div class="form-row">
      <div>
        <label>Tutar (₺)</label>
        <input type="number" id="f-amount" placeholder="0.00" min="0" step="0.01">
      </div>
      <div>
        <label>Tarih</label>
        <input type="date" id="f-date">
      </div>
    </div>
    <div style="margin-bottom:12px">
      <label>Kategori</label>
      <select id="f-cat"></select>
    </div>
    <div style="margin-bottom:16px">
      <label>Açıklama (opsiyonel)</label>
      <input type="text" id="f-desc" placeholder="örn. Ocak maaşı">
    </div>
    <button class="btn btn-g" id="add-btn" style="width:100%" onclick="addTx()">Ekle</button>
  </div>

  <!-- TRANSACTIONS -->
  <div class="card">
    <div class="section-title">Son İşlemler</div>
    <div class="tx-list" id="tx-list"><div class="empty">Bu ay işlem yok</div></div>
  </div>

</div>

<!-- BUDGET -->
<div class="card" id="budget-card">
  <div class="section-title">Bütçe Takibi</div>
  <div id="budget-rows"><div class="empty">Bütçe hedefi girilmemiş</div></div>
  <div style="margin-top:16px;display:flex;gap:10px;flex-wrap:wrap">
    <div style="flex:1;min-width:140px">
      <label>Kategori</label>
      <select id="b-cat"></select>
    </div>
    <div style="flex:1;min-width:100px">
      <label>Aylık Limit (₺)</label>
      <input type="number" id="b-limit" placeholder="örn. 5000">
    </div>
    <div style="display:flex;align-items:flex-end">
      <button class="btn btn-b" onclick="saveBudget()">Kaydet</button>
    </div>
  </div>
</div>

<!-- CSV IMPORT -->
<div class="card" style="margin-bottom:20px" id="csv-card">
  <div class="section-title">Banka CSV Aktar</div>
  <p style="font-size:.85rem;color:var(--muted);margin-bottom:16px;line-height:1.6">
    Banka uygulamasından <strong style="color:var(--txt)">Hesap Hareketleri → Dışa Aktar (CSV/Excel)</strong> yapıp
    dosyayı aşağıya yükle. Garanti, İş Bankası, Akbank, Yapı Kredi formatları desteklenir.
  </p>

  <!-- drop zone -->
  <div id="drop-zone" onclick="document.getElementById('csv-file').click()"
    style="border:2px dashed var(--border);border-radius:10px;padding:32px;text-align:center;cursor:pointer;transition:.2s;margin-bottom:16px">
    <div style="font-size:2rem;margin-bottom:8px">📂</div>
    <div style="font-size:.9rem;color:var(--muted)">Dosyayı buraya sürükle veya tıkla</div>
    <div style="font-size:.78rem;color:var(--muted);margin-top:4px">CSV, XLS, XLSX — maks 5 MB</div>
    <input type="file" id="csv-file" accept=".csv,.xls,.xlsx" style="display:none" onchange="csvSelected(this)">
  </div>

  <!-- preview table -->
  <div id="csv-preview" style="display:none">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:8px">
      <div id="csv-stats" style="font-size:.85rem;color:var(--muted)"></div>
      <div style="display:flex;gap:8px">
        <button class="btn" style="background:var(--bg3);border:1px solid var(--border);color:var(--muted)" onclick="csvReset()">İptal</button>
        <button class="btn btn-b" id="csv-confirm-btn" onclick="csvConfirm()">Seçilenleri İçe Aktar</button>
      </div>
    </div>
    <div style="overflow-x:auto;max-height:340px;overflow-y:auto">
      <table id="csv-table" style="width:100%;border-collapse:collapse;font-size:.82rem">
        <thead>
          <tr style="position:sticky;top:0;background:var(--bg2)">
            <th style="padding:8px 6px;text-align:left;color:var(--muted);font-weight:600;white-space:nowrap">
              <input type="checkbox" id="csv-chk-all" onchange="csvToggleAll(this.checked)" checked> Tümü
            </th>
            <th style="padding:8px 6px;text-align:left;color:var(--muted);font-weight:600">Tarih</th>
            <th style="padding:8px 6px;text-align:left;color:var(--muted);font-weight:600">Açıklama</th>
            <th style="padding:8px 6px;text-align:left;color:var(--muted);font-weight:600">Tür</th>
            <th style="padding:8px 6px;text-align:left;color:var(--muted);font-weight:600">Kategori</th>
            <th style="padding:8px 6px;text-align:right;color:var(--muted);font-weight:600">Tutar</th>
          </tr>
        </thead>
        <tbody id="csv-tbody"></tbody>
      </table>
    </div>
  </div>
</div>

</div><!-- /wrap -->

<div id="toast"></div>

<script>
var curYear  = new Date().getFullYear();
var curMonth = new Date().getMonth() + 1;
var curTab   = 'gelir';
var summaryData = {};
var MONTHS = ['','Ocak','Şubat','Mart','Nisan','Mayıs','Haziran',
              'Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'];
var COLORS = ['#3b82f6','#f59e0b','#a855f7','#ef4444','#22c55e','#06b6d4',
              '#f97316','#ec4899','#84cc16','#14b8a6','#6366f1','#e11d48'];

// ── init ──────────────────────────────────────────────────────────────────────
window.onload = function() {
  document.getElementById('f-date').value = new Date().toISOString().split('T')[0];
  updateLabel();
  loadCats(function() {
    loadAll();
  });
};

function updateLabel() {
  document.getElementById('mlabel').textContent = MONTHS[curMonth] + ' ' + curYear;
}

function changeMonth(d) {
  curMonth += d;
  if (curMonth > 12) { curMonth = 1; curYear++; }
  if (curMonth < 1)  { curMonth = 12; curYear--; }
  updateLabel();
  loadAll();
}

// ── cats ──────────────────────────────────────────────────────────────────────
var CATS = {gelir: [], gider: []};

function loadCats(cb) {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/categories');
  xhr.onload = function() {
    CATS = JSON.parse(xhr.responseText);
    fillCatSelect('f-cat', CATS[curTab]);
    fillCatSelect('b-cat', CATS.gider);
    if (cb) cb();
  };
  xhr.send();
}

function fillCatSelect(id, list) {
  var sel = document.getElementById(id);
  sel.innerHTML = '';
  list.forEach(function(c) {
    var o = document.createElement('option'); o.value = c; o.textContent = c;
    sel.appendChild(o);
  });
}

function setTab(t) {
  curTab = t;
  document.getElementById('tab-g').className = 'tab' + (t==='gelir' ? ' active-g' : '');
  document.getElementById('tab-r').className = 'tab' + (t==='gider' ? ' active-r' : '');
  document.getElementById('add-btn').className = 'btn ' + (t==='gelir' ? 'btn-g' : 'btn-r');
  fillCatSelect('f-cat', CATS[t]);
}

// ── load all ──────────────────────────────────────────────────────────────────
function loadAll() {
  loadSummary();
  loadTx();
  loadMotivation();
}

function loadSummary() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/summary?year='+curYear+'&month='+curMonth);
  xhr.onload = function() {
    summaryData = JSON.parse(xhr.responseText);
    renderSummary(summaryData);
    drawBar(summaryData.bar);
    drawDonut(summaryData.gider_cats);
    renderBudget(summaryData.gider_cats, summaryData.budgets);
  };
  xhr.send();
}

function loadTx() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/transactions?year='+curYear+'&month='+curMonth);
  xhr.onload = function() {
    renderTx(JSON.parse(xhr.responseText));
  };
  xhr.send();
}

// ── render summary ────────────────────────────────────────────────────────────
function fmt(n) {
  return '₺' + Number(n).toLocaleString('tr-TR', {minimumFractionDigits:2, maximumFractionDigits:2});
}

function renderSummary(d) {
  var balEl = document.getElementById('balance-val');
  balEl.textContent = fmt(d.balance);
  balEl.className = 'val ' + (d.balance >= 0 ? 'pos' : 'neg');

  document.getElementById('s-gelir').textContent = fmt(d.gelir);
  document.getElementById('s-gider').textContent = fmt(d.gider);
  document.getElementById('s-net').textContent   = fmt(d.net);

  var netPct = d.gelir > 0 ? Math.round(d.net / d.gelir * 100) : 0;
  document.getElementById('s-net-sub').textContent = 'Gelirin ' + netPct + '% tasarruf';

  var gTopCat = topCat(d.gelir_cats);
  var eTopCat = topCat(d.gider_cats);
  document.getElementById('s-gelir-sub').textContent = gTopCat ? 'En çok: ' + gTopCat : '';
  document.getElementById('s-gider-sub').textContent = eTopCat ? 'En çok: ' + eTopCat : '';
}

function topCat(obj) {
  var top = null, max = 0;
  Object.keys(obj).forEach(function(k) { if (obj[k] > max) { max = obj[k]; top = k; } });
  return top;
}

// ── render transactions ───────────────────────────────────────────────────────
function renderTx(list) {
  var el = document.getElementById('tx-list');
  if (!list.length) { el.innerHTML = '<div class="empty">Bu ay işlem yok</div>'; return; }
  el.innerHTML = list.map(function(t) {
    var isG = t.type === 'gelir';
    return '<div class="tx-item">' +
      '<div class="tx-dot ' + (isG?'g':'r') + '"></div>' +
      '<div class="tx-info">' +
        '<div class="tx-desc">' + (t.description || t.category) + '</div>' +
        '<div class="tx-cat">' + t.category + ' &middot; ' + t.date + '</div>' +
      '</div>' +
      '<div class="tx-amt" style="color:' + (isG?'var(--g)':'var(--r)') + '">' +
        (isG?'+':'-') + fmt(t.amount) + '</div>' +
      '<button class="tx-del" onclick="delTx(' + t.id + ')">✕</button>' +
    '</div>';
  }).join('');
}

// ── add / delete ──────────────────────────────────────────────────────────────
function addTx() {
  var amount = parseFloat(document.getElementById('f-amount').value);
  var cat    = document.getElementById('f-cat').value;
  var desc   = document.getElementById('f-desc').value;
  var dt     = document.getElementById('f-date').value;
  if (!amount || amount <= 0) { toast('Tutar giriniz'); return; }
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/transactions');
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.onload = function() {
    var r = JSON.parse(xhr.responseText);
    if (r.ok) {
      toast('İşlem eklendi ✓');
      document.getElementById('f-amount').value = '';
      document.getElementById('f-desc').value = '';
      loadAll();
    }
  };
  xhr.send(JSON.stringify({type: curTab, amount: amount, category: cat, description: desc, date: dt}));
}

function delTx(id) {
  var xhr = new XMLHttpRequest();
  xhr.open('DELETE', '/api/transactions/' + id);
  xhr.onload = function() { loadAll(); };
  xhr.send();
}

// ── budget ────────────────────────────────────────────────────────────────────
function saveBudget() {
  var cat   = document.getElementById('b-cat').value;
  var limit = parseFloat(document.getElementById('b-limit').value);
  if (!cat || !limit || limit <= 0) { toast('Kategori ve limit giriniz'); return; }
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/budgets');
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.onload = function() { document.getElementById('b-limit').value = ''; loadSummary(); toast('Bütçe kaydedildi ✓'); };
  xhr.send(JSON.stringify({category: cat, limit: limit}));
}

function renderBudget(gider_cats, budgets) {
  var el = document.getElementById('budget-rows');
  var keys = Object.keys(budgets);
  if (!keys.length) { el.innerHTML = '<div class="empty">Bütçe hedefi girilmemiş</div>'; return; }
  el.innerHTML = keys.map(function(cat) {
    var lim   = budgets[cat];
    var spent = gider_cats[cat] || 0;
    var pct   = Math.min(100, Math.round(spent / lim * 100));
    var over  = spent > lim;
    var color = over ? 'var(--r)' : pct > 75 ? 'var(--y)' : 'var(--g)';
    return '<div class="budget-row">' +
      '<div class="top"><span class="cat">' + cat + '</span>' +
      '<span class="nums">' + fmt(spent) + ' / ' + fmt(lim) +
      ' <span class="badge ' + (over?'badge-r':'badge-g') + '">' + pct + '%</span></span></div>' +
      '<div class="prog-bg"><div class="prog-fill" style="width:' + pct + '%;background:' + color + '"></div></div>' +
    '</div>';
  }).join('');
}

// ── bar chart ─────────────────────────────────────────────────────────────────
function drawBar(data) {
  var canvas = document.getElementById('barChart');
  var W = canvas.parentElement.clientWidth - 40;
  var H = 200;
  canvas.width  = W;
  canvas.height = H;
  var ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, W, H);

  var maxVal = 0;
  data.forEach(function(d) { if (d.gelir > maxVal) maxVal = d.gelir; if (d.gider > maxVal) maxVal = d.gider; });
  if (!maxVal) maxVal = 1;

  var pad  = { t:10, r:10, b:30, l:50 };
  var cw   = W - pad.l - pad.r;
  var ch   = H - pad.t - pad.b;
  var bw   = cw / 12 * 0.3;
  var gap  = cw / 12;

  // y-axis lines
  ctx.strokeStyle = '#2d3348';
  ctx.lineWidth   = 1;
  [0, .25, .5, .75, 1].forEach(function(f) {
    var y = pad.t + ch * (1 - f);
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
    ctx.fillStyle = '#64748b';
    ctx.font = '10px system-ui';
    ctx.textAlign = 'right';
    ctx.fillText(fmtK(maxVal * f), pad.l - 4, y + 3);
  });

  data.forEach(function(d, i) {
    var x = pad.l + i * gap + gap / 2;
    var gh = ch * (d.gelir / maxVal);
    var eh = ch * (d.gider / maxVal);

    // gelir bar
    ctx.fillStyle = d.gelir > 0 ? '#22c55e88' : 'transparent';
    ctx.beginPath();
    roundRect(ctx, x - bw - 2, pad.t + ch - gh, bw, gh, 3);
    ctx.fill();

    // gider bar
    ctx.fillStyle = d.gider > 0 ? '#ef444488' : 'transparent';
    ctx.beginPath();
    roundRect(ctx, x + 2, pad.t + ch - eh, bw, eh, 3);
    ctx.fill();

    // highlight current month
    if (i + 1 === curMonth && curYear === new Date().getFullYear()) {
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 1.5;
      ctx.strokeRect(x - bw - 4, pad.t, bw * 2 + 8, ch);
    }

    // month label
    ctx.fillStyle = '#64748b';
    ctx.font = '9px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText(MONTHS[i+1].slice(0,3), x, H - 8);
  });
}

function fmtK(n) {
  if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
  if (n >= 1000)    return (n/1000).toFixed(0) + 'K';
  return Math.round(n).toString();
}

function roundRect(ctx, x, y, w, h, r) {
  if (h < 0) return;
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h);
  ctx.lineTo(x, y + h);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

// ── donut chart ───────────────────────────────────────────────────────────────
function drawDonut(cats) {
  var canvas = document.getElementById('donut');
  var W = canvas.parentElement.clientWidth - 40;
  var H = 200;
  canvas.width  = W;
  canvas.height = H;
  var ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, W, H);

  var keys = Object.keys(cats).filter(function(k) { return cats[k] > 0; });
  if (!keys.length) {
    ctx.fillStyle = '#64748b';
    ctx.font = '13px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText('Bu ay gider yok', W/2, H/2);
    return;
  }

  var total = keys.reduce(function(s, k) { return s + cats[k]; }, 0);
  var cx = H / 2, cy = H / 2, R = cy - 16, r = cy * 0.48;
  var angle = -Math.PI / 2;

  keys.forEach(function(k, i) {
    var slice = cats[k] / total * 2 * Math.PI;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, R, angle, angle + slice);
    ctx.closePath();
    ctx.fillStyle = COLORS[i % COLORS.length];
    ctx.fill();
    angle += slice;
  });

  // hole
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, 2 * Math.PI);
  ctx.fillStyle = '#1a1d27';
  ctx.fill();

  // center text
  ctx.fillStyle = '#e2e8f0';
  ctx.font = 'bold 13px system-ui';
  ctx.textAlign = 'center';
  ctx.fillText(fmtK(total) + '₺', cx, cy - 4);
  ctx.fillStyle = '#64748b';
  ctx.font = '10px system-ui';
  ctx.fillText('toplam gider', cx, cy + 12);

  // legend
  var lx = H + 8, ly = 14, lh = 18;
  keys.slice(0, 8).forEach(function(k, i) {
    var pct = Math.round(cats[k] / total * 100);
    ctx.fillStyle = COLORS[i % COLORS.length];
    ctx.beginPath();
    ctx.arc(lx + 6, ly + i * lh + 6, 5, 0, 2 * Math.PI);
    ctx.fill();

    ctx.fillStyle = '#e2e8f0';
    ctx.font = '10px system-ui';
    ctx.textAlign = 'left';
    var label = k.length > 14 ? k.slice(0,14) + '…' : k;
    ctx.fillText(label, lx + 16, ly + i * lh + 10);

    ctx.fillStyle = '#64748b';
    ctx.textAlign = 'right';
    ctx.fillText(pct + '%', W, ly + i * lh + 10);
  });
}

// ── motivation ────────────────────────────────────────────────────────────────
function loadMotivation() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/motivation');
  xhr.onload = function() {
    var d = JSON.parse(xhr.responseText);
    document.getElementById('motiv-bar').style.width = d.score + '%';
    document.getElementById('motiv-bar').style.background = d.color;
    var badge = document.getElementById('motiv-score-badge');
    badge.textContent = d.label;
    badge.style.color = d.color;
    badge.style.borderColor = d.color + '44';

    var el = document.getElementById('motiv-msgs');
    if (!d.msgs || !d.msgs.length) {
      el.innerHTML = '<div class="empty">Veri girdikçe analiz burada görünür.</div>';
      return;
    }
    el.innerHTML = d.msgs.map(function(m) {
      return '<div style="display:flex;gap:10px;align-items:flex-start;padding:10px 12px;background:var(--bg3);border-radius:8px;border:1px solid var(--border)">' +
        '<span style="font-size:1.1rem;flex-shrink:0">' + m.icon + '</span>' +
        '<span style="font-size:.88rem;line-height:1.5">' + m.text + '</span>' +
      '</div>';
    }).join('');
  };
  xhr.send();
}

// ── toast ─────────────────────────────────────────────────────────────────────
function toast(msg) {
  var el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(function() { el.classList.remove('show'); }, 2500);
}

// ── CSV import ────────────────────────────────────────────────────────────────
var csvRows = [];

// drag & drop
var dz = document.getElementById('drop-zone');
dz.addEventListener('dragover', function(e){ e.preventDefault(); dz.style.borderColor='var(--b)'; });
dz.addEventListener('dragleave', function(){ dz.style.borderColor='var(--border)'; });
dz.addEventListener('drop', function(e){
  e.preventDefault(); dz.style.borderColor='var(--border)';
  var f = e.dataTransfer.files[0];
  if (f) uploadCsv(f);
});

function csvSelected(input) {
  if (input.files[0]) uploadCsv(input.files[0]);
}

function uploadCsv(file) {
  if (file.size > 5 * 1024 * 1024) { toast('Dosya çok büyük (maks 5 MB)'); return; }
  var fd = new FormData();
  fd.append('file', file);
  dz.innerHTML = '<div style="font-size:1.5rem">⏳</div><div style="color:var(--muted);font-size:.88rem;margin-top:6px">Analiz ediliyor…</div>';
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/import/preview');
  xhr.onload = function() {
    var d = JSON.parse(xhr.responseText);
    if (!d.ok) { toast('Hata: ' + d.error); csvReset(); return; }
    csvRows = d.rows;
    renderCsvPreview(d);
  };
  xhr.onerror = function() { toast('Yükleme başarısız'); csvReset(); };
  xhr.send(fd);
}

function renderCsvPreview(d) {
  document.getElementById('csv-stats').textContent =
    d.rows.length + ' işlem bulundu' + (d.skipped ? ', ' + d.skipped + ' satır atlandı' : '');
  var tbody = document.getElementById('csv-tbody');
  tbody.innerHTML = d.rows.map(function(r, i) {
    var isG = r.type === 'gelir';
    return '<tr style="border-bottom:1px solid var(--border)">' +
      '<td style="padding:7px 6px"><input type="checkbox" class="csv-chk" data-i="'+i+'" checked></td>' +
      '<td style="padding:7px 6px;white-space:nowrap">' + r.date + '</td>' +
      '<td style="padding:7px 6px;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="'+r.description+'">' + (r.description||'—') + '</td>' +
      '<td style="padding:7px 6px">' +
        '<span class="badge '+(isG?'badge-g':'badge-r')+'">'+(isG?'Gelir':'Gider')+'</span></td>' +
      '<td style="padding:7px 6px">' +
        '<select class="csv-cat-sel" data-i="'+i+'" style="background:var(--bg3);border:1px solid var(--border);color:var(--txt);padding:3px 6px;border-radius:6px;font-size:.78rem">' +
        buildCatOptions(r.type, r.category) + '</select></td>' +
      '<td style="padding:7px 6px;text-align:right;font-weight:600;color:'+(isG?'var(--g)':'var(--r)')+'">'+
        (isG?'+':'-') + fmt(r.amount) + '</td>' +
    '</tr>';
  }).join('');
  // sync category changes back to csvRows
  [].forEach.call(document.querySelectorAll('.csv-cat-sel'), function(sel) {
    sel.addEventListener('change', function() {
      csvRows[parseInt(this.dataset.i)].category = this.value;
    });
  });
  document.getElementById('csv-preview').style.display = 'block';
}

function buildCatOptions(ttype, selected) {
  var list = ttype === 'gelir' ? CATS.gelir : CATS.gider;
  return list.map(function(c) {
    return '<option value="'+c+'"'+(c===selected?' selected':'')+'>'+c+'</option>';
  }).join('');
}

function csvToggleAll(checked) {
  [].forEach.call(document.querySelectorAll('.csv-chk'), function(c){ c.checked = checked; });
}

function csvConfirm() {
  var toImport = [];
  [].forEach.call(document.querySelectorAll('.csv-chk'), function(chk) {
    if (chk.checked) {
      var i = parseInt(chk.dataset.i);
      toImport.push(csvRows[i]);
    }
  });
  if (!toImport.length) { toast('Hiç satır seçili değil'); return; }
  var btn = document.getElementById('csv-confirm-btn');
  btn.textContent = 'Kaydediliyor…'; btn.disabled = true;
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/import/confirm');
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.onload = function() {
    var d = JSON.parse(xhr.responseText);
    toast(d.imported + ' işlem içe aktarıldı ✓');
    csvReset();
    loadAll();
  };
  xhr.send(JSON.stringify(toImport));
}

function csvReset() {
  csvRows = [];
  document.getElementById('csv-preview').style.display = 'none';
  dz.innerHTML = '<div style="font-size:2rem;margin-bottom:8px">📂</div>' +
    '<div style="font-size:.9rem;color:var(--muted)">Dosyayı buraya sürükle veya tıkla</div>' +
    '<div style="font-size:.78rem;color:var(--muted);margin-top:4px">CSV, XLS, XLSX — maks 5 MB</div>' +
    '<input type="file" id="csv-file" accept=".csv,.xls,.xlsx" style="display:none" onchange="csvSelected(this)">';
  dz.style.borderColor = 'var(--border)';
  document.getElementById('csv-file') && (document.getElementById('csv-file').value = '');
}

// ── resize ────────────────────────────────────────────────────────────────────
window.addEventListener('resize', function() {
  if (summaryData.bar) { drawBar(summaryData.bar); drawDonut(summaryData.gider_cats || {}); }
});
</script>
</body>
</html>"""

@app.route("/")
def index():
    return HTML

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)

init_db()
