import sqlite3, json, os, csv, io, re
from datetime import datetime, date
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "cashflow.db")

GELIR_CATS = ["Maaş", "Serbest Meslek", "Kira Geliri", "Yatırım / Temettü", "Hediye / İkramiye", "Diğer Gelir"]
GIDER_CATS = ["Kira / Mortgage", "Market / Gıda", "Faturalar", "Ulaşım", "Yemek / Restoran",
               "Eğlence", "Sağlık", "Giyim", "Eğitim", "Abonelikler", "Elektronik", "Diğer Gider"]
ALL_CATS   = GELIR_CATS + GIDER_CATS

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

def row_to_dict(r): return dict(r)
def today_str():    return date.today().isoformat()

def month_range(year, month):
    from calendar import monthrange
    _, last = monthrange(year, month)
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last:02d}"

# ── CRUD ──────────────────────────────────────────────────────────────────────

@app.route("/api/transactions", methods=["GET"])
def list_transactions():
    db    = get_db()
    year  = request.args.get("year",  type=int)
    month = request.args.get("month", type=int)
    q     = "SELECT * FROM transactions"
    params = []
    if year and month:
        s, e = month_range(year, month)
        q += " WHERE date BETWEEN ? AND ?"; params = [s, e]
    elif year:
        q += " WHERE date LIKE ?"; params = [f"{year}-%"]
    q += " ORDER BY date DESC, id DESC"
    return jsonify([row_to_dict(r) for r in db.execute(q, params).fetchall()])

@app.route("/api/transactions", methods=["POST"])
def add_transaction():
    d = request.get_json(force=True)
    ttype = d.get("type"); amount = float(d.get("amount", 0))
    cat = d.get("category",""); desc = d.get("description",""); dt = d.get("date", today_str())
    if ttype not in ("gelir","gider") or amount <= 0 or not cat:
        return jsonify({"ok": False, "error": "Geçersiz veri"}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO transactions (type,amount,category,description,date,created_at) VALUES (?,?,?,?,?,?)",
        (ttype, amount, cat, desc, dt, datetime.now().isoformat()))
    db.commit()
    return jsonify({"ok": True, "id": cur.lastrowid})

@app.route("/api/transactions/<int:tid>", methods=["PUT"])
def update_transaction(tid):
    d = request.get_json(force=True)
    fields, params = [], []
    for col in ("type","amount","category","description","date"):
        if col in d:
            fields.append(f"{col}=?")
            params.append(float(d[col]) if col == "amount" else d[col])
    if not fields: return jsonify({"ok": False}), 400
    params.append(tid)
    get_db().execute(f"UPDATE transactions SET {','.join(fields)} WHERE id=?", params)
    get_db().commit()
    return jsonify({"ok": True})

@app.route("/api/transactions/<int:tid>", methods=["DELETE"])
def del_transaction(tid):
    get_db().execute("DELETE FROM transactions WHERE id=?", (tid,)); get_db().commit()
    return jsonify({"ok": True})

@app.route("/api/transactions/bulk-delete", methods=["POST"])
def bulk_delete():
    ids = request.get_json(force=True)
    if not isinstance(ids, list): return jsonify({"ok": False}), 400
    get_db().execute(f"DELETE FROM transactions WHERE id IN ({','.join('?'*len(ids))})", ids)
    get_db().commit()
    return jsonify({"ok": True, "deleted": len(ids)})

@app.route("/api/summary")
def summary():
    db    = get_db()
    year  = request.args.get("year",  date.today().year,  type=int)
    month = request.args.get("month", date.today().month, type=int)
    start, end = month_range(year, month)
    rows = db.execute(
        "SELECT type,category,SUM(amount) as total FROM transactions "
        "WHERE date BETWEEN ? AND ? GROUP BY type,category", (start, end)).fetchall()
    gelir_total = gider_total = 0.0
    gelir_cats  = {}; gider_cats = {}
    for r in rows:
        if r["type"]=="gelir": gelir_total+=r["total"]; gelir_cats[r["category"]]=round(r["total"],2)
        else:                   gider_total+=r["total"]; gider_cats[r["category"]]=round(r["total"],2)
    bar = []
    for m in range(1,13):
        s,e2 = month_range(year,m)
        totals = db.execute("SELECT type,SUM(amount) as t FROM transactions WHERE date BETWEEN ? AND ? GROUP BY type",(s,e2)).fetchall()
        g_val  = next((r["t"] for r in totals if r["type"]=="gelir"),0)
        ex_val = next((r["t"] for r in totals if r["type"]=="gider"),0)
        bar.append({"month":m,"gelir":round(g_val,2),"gider":round(ex_val,2)})
    bal = db.execute("SELECT SUM(CASE WHEN type='gelir' THEN amount ELSE -amount END) as b FROM transactions").fetchone()
    budgets = {r["category"]:r["limit_"] for r in db.execute("SELECT * FROM budgets").fetchall()}
    return jsonify({"gelir":round(gelir_total,2),"gider":round(gider_total,2),
                    "net":round(gelir_total-gider_total,2),"balance":round(bal["b"] or 0,2),
                    "gelir_cats":gelir_cats,"gider_cats":gider_cats,"bar":bar,"budgets":budgets})

@app.route("/api/budgets", methods=["POST"])
def set_budget():
    d = request.get_json(force=True)
    cat = d.get("category",""); limit = float(d.get("limit",0))
    if not cat or limit<=0: return jsonify({"ok":False}),400
    db = get_db()
    db.execute("INSERT INTO budgets(category,limit_) VALUES(?,?) ON CONFLICT(category) DO UPDATE SET limit_=excluded.limit_",(cat,limit))
    db.commit(); return jsonify({"ok":True})

@app.route("/api/categories")
def categories():
    return jsonify({"gelir":GELIR_CATS,"gider":GIDER_CATS,"all":ALL_CATS})

@app.route("/api/motivation")
def motivation():
    db = get_db(); today = date.today()
    year, month = today.year, today.month
    start, end  = month_range(year, month)
    rows = db.execute("SELECT type,SUM(amount) as t FROM transactions WHERE date BETWEEN ? AND ? GROUP BY type",(start,end)).fetchall()
    gelir  = next((r["t"] for r in rows if r["type"]=="gelir"),0) or 0
    gider  = next((r["t"] for r in rows if r["type"]=="gider"),0) or 0
    net    = gelir - gider
    from calendar import monthrange as mr
    _, days_in_month = mr(year,month)
    days_passed = today.day; days_left = days_in_month - days_passed
    daily_spend = gider / max(days_passed,1)
    projected   = daily_spend * days_in_month
    bal = (db.execute("SELECT SUM(CASE WHEN type='gelir' THEN amount ELSE -amount END) as b FROM transactions").fetchone()["b"] or 0)
    budgets = {r["category"]:r["limit_"] for r in db.execute("SELECT * FROM budgets").fetchall()}
    top = db.execute("SELECT category,SUM(amount) as t FROM transactions WHERE date BETWEEN ? AND ? AND type='gider' GROUP BY category ORDER BY t DESC LIMIT 1",(start,end)).fetchall()
    top_cat = top[0]["category"] if top else None; top_amt = top[0]["t"] if top else 0
    msgs=[]; score=0
    if gelir==0:
        msgs.append({"icon":"💡","text":"Henüz bu ay gelir girmedin. Maaş veya gelirini ekle, analiz yapayım."})
        return jsonify({"score":0,"label":"Veri Bekleniyor","color":"#64748b","msgs":msgs,"projected_month":0,"daily_avg":0,"days_left":days_left,"net":0,"save_rate":0})
    save_rate = net/gelir*100
    if save_rate>=30: score+=40; msgs.append({"icon":"🔥","text":f"Harika! Gelirinin %{save_rate:.0f}'ini biriktiriyorsun. Finansal özgürlük yolundasın."})
    elif save_rate>=15: score+=25; msgs.append({"icon":"✅","text":f"İyi gidiyorsun — gelirinin %{save_rate:.0f}'ini tasarruf ediyorsun."})
    elif save_rate>=0:  score+=10; msgs.append({"icon":"⚠️","text":f"Bu ay gelirinin sadece %{save_rate:.0f}'ini biriktirebildin. Hedef en az %20."})
    else: msgs.append({"icon":"🚨","text":f"Bu ay gelirininden {abs(net):,.0f}₺ fazla harcadın!"})
    if days_left>0:
        if projected < gelir*0.85: score+=20; msgs.append({"icon":"📈","text":f"Ay sonuna {days_left} gün kaldı. Bu hızla {gelir-projected:,.0f}₺ biriktireceksin!"})
        elif projected < gelir:    score+=10; msgs.append({"icon":"📊","text":f"Günlük ort. {daily_spend:,.0f}₺ harcıyorsun. Ay sonu tahmini: {projected:,.0f}₺"})
        else: msgs.append({"icon":"⚡","text":f"Dikkat! Bu hızda ay sonunda {projected:,.0f}₺ harcarsin, gelirine göre fazla!"})
    if budgets:
        over=[]
        for cat,lim in budgets.items():
            sp=(db.execute("SELECT SUM(amount) as t FROM transactions WHERE date BETWEEN ? AND ? AND type='gider' AND category=?",(start,end,cat)).fetchone()["t"] or 0)
            if sp>lim: over.append((cat,sp-lim))
        if not over: score+=20; msgs.append({"icon":"🎯","text":"Tüm bütçe hedeflerini tutturuyorsun. Süper disiplin!"})
        else:
            for cat,exc in over[:2]: msgs.append({"icon":"🔴","text":f"'{cat}' bütçeni {exc:,.0f}₺ aştın."})
    else: score+=10; msgs.append({"icon":"💡","text":"Bütçe hedefleri belirle — harcamaların otomatik takip edilsin."})
    if top_cat and top_amt>0 and gelir>0:
        pct=top_amt/gelir*100
        if pct>40: msgs.append({"icon":"🔍","text":f"En büyük giderin '{top_cat}' — gelirinin %{pct:.0f}'i gidiyor."})
        else: score+=10; msgs.append({"icon":"✨","text":f"En büyük gider: '{top_cat}' {top_amt:,.0f}₺ (%{pct:.0f}). Dengeli görünüyor."})
    if bal>=100000: score+=10; msgs.append({"icon":"🏆","text":f"Toplam birikimin {bal:,.0f}₺! 100K kulübüne girdin."})
    elif bal>=50000:
        score+=8; left=100000-bal; mos=left/(net if net>0 else 1)
        msgs.append({"icon":"🎯","text":f"100K₺ hedefine {left:,.0f}₺ kaldı. Bu hızla ~{mos:.0f} ayda ulaşırsın."})
    elif bal>0 and net>0: score+=5; msgs.append({"icon":"🌱","text":f"Aylık {net:,.0f}₺ tasarrufla 1 yılda {net*12:,.0f}₺ yaparsın!"})
    score=min(100,max(0,score))
    if score>=75:   label,color="Finansal Sağlık: Mükemmel","#22c55e"
    elif score>=50: label,color="Finansal Sağlık: İyi","#3b82f6"
    elif score>=25: label,color="Finansal Sağlık: Orta","#f59e0b"
    else:           label,color="Finansal Sağlık: Zayıf","#ef4444"
    return jsonify({"score":score,"label":label,"color":color,"msgs":msgs,
                    "projected_month":round(projected,2),"daily_avg":round(daily_spend,2),
                    "days_left":days_left,"net":round(net,2),"save_rate":round(save_rate,1)})

# ── CSV import ────────────────────────────────────────────────────────────────

def _parse_amount(s):
    s = s.strip().replace(" ","").replace("\xa0","")
    s = re.sub(r"[₺$€£+]","",s)
    s = s.lstrip("-")
    if not s: return None
    dots=s.count("."); commas=s.count(",")
    if   dots==0 and commas==0: pass
    elif dots>=1 and commas==0:
        if dots==1: pass
        else: s=s.replace(".","")
    elif dots==0 and commas==1: s=s.replace(",",".")
    elif dots==0 and commas>1:  s=s.replace(",","")
    elif dots==1 and commas==1:
        if s.index(".")<s.index(","): s=s.replace(".","").replace(",",".")
        else: s=s.replace(",","")
    elif dots>1 and commas==1:  s=s.replace(".","").replace(",",".")
    elif dots==1 and commas>1:  s=s.replace(",","")
    try: return abs(float(s))
    except: return None

def _parse_date(s):
    s=s.strip()
    for fmt in ("%d.%m.%Y","%d/%m/%Y","%Y-%m-%d","%d-%m-%Y","%d.%m.%y","%m/%d/%Y"):
        try: return datetime.strptime(s,fmt).strftime("%Y-%m-%d")
        except: pass
    return None

_CAT_MAP = {
    "maaş":"Maaş","maas":"Maaş","salary":"Maaş","ücret":"Maaş",
    "kira":"Kira / Mortgage","mortgage":"Kira / Mortgage","aidat":"Faturalar",
    "elektrik":"Faturalar","doğalgaz":"Faturalar","dogalgaz":"Faturalar","fatura":"Faturalar",
    "internet":"Abonelikler","netflix":"Abonelikler","spotify":"Abonelikler","abonelik":"Abonelikler",
    "market":"Market / Gıda","migros":"Market / Gıda","a101":"Market / Gıda",
    "bim":"Market / Gıda","carrefour":"Market / Gıda","şok":"Market / Gıda",
    "taxi":"Ulaşım","taksi":"Ulaşım","uber":"Ulaşım","metro":"Ulaşım",
    "otobüs":"Ulaşım","akaryakıt":"Ulaşım","benzin":"Ulaşım","shell":"Ulaşım","opet":"Ulaşım",
    "restoran":"Yemek / Restoran","cafe":"Yemek / Restoran","kahve":"Yemek / Restoran",
    "yemeksepeti":"Yemek / Restoran","getir yemek":"Yemek / Restoran",
    "sinema":"Eğlence","konser":"Eğlence","bilet":"Eğlence",
    "eczane":"Sağlık","hastane":"Sağlık","doktor":"Sağlık","ilaç":"Sağlık",
    "giyim":"Giyim","zara":"Giyim","h&m":"Giyim","lcw":"Giyim",
    "okul":"Eğitim","kurs":"Eğitim","udemy":"Eğitim",
    "faiz":"Yatırım / Temettü","temettü":"Yatırım / Temettü",
    "hediye":"Hediye / İkramiye","ikramiye":"Hediye / İkramiye",
}

def _guess_cat(desc, ttype):
    dl=desc.lower()
    for kw,cat in _CAT_MAP.items():
        if kw in dl: return cat
    return "Diğer Gelir" if ttype=="gelir" else "Diğer Gider"

def _detect_cols(header):
    h=[c.lower().strip() for c in header]
    def find(*names):
        for n in names:
            for i,c in enumerate(h):
                if n in c: return i
        return None
    return (find("tarih","date","işlem tarihi","valör"),
            find("açıklama","aciklama","işlem","description","detay","karşı taraf"),
            find("borç","borc","çıkış","debit"),
            find("alacak","giriş","credit"),
            find("tutar","amount","miktar") if find("borç","borc") is None and find("alacak") is None else None)

@app.route("/api/import/preview", methods=["POST"])
def import_preview():
    f = request.files.get("file")
    if not f: return jsonify({"ok":False,"error":"Dosya yüklenmedi"}),400
    raw = f.read().decode("utf-8-sig",errors="replace")
    dialect = "excel"
    if raw.count(";")>raw.count(","):
        csv.register_dialect("excel-semicolon",delimiter=";"); dialect="excel-semicolon"
    reader = csv.reader(io.StringIO(raw),dialect)
    rows   = [r for r in reader if any(c.strip() for c in r)]
    if len(rows)<2: return jsonify({"ok":False,"error":"CSV çok kısa"}),400
    header_idx=0
    for i,row in enumerate(rows):
        if any(kw in " ".join(row).lower() for kw in ("tarih","date","tutar","açıklama","işlem")):
            header_idx=i; break
    header=rows[header_idx]; data_rows=rows[header_idx+1:]
    dc,desc_c,deb_c,cred_c,amt_c = _detect_cols(header)
    parsed=[]; skipped=0
    for row in data_rows:
        if not any(c.strip() for c in row): continue
        dt = _parse_date(row[dc]) if dc is not None and dc<len(row) else None
        if not dt: skipped+=1; continue
        desc = row[desc_c].strip() if desc_c is not None and desc_c<len(row) else ""
        if amt_c is not None:
            raw_a=row[amt_c] if amt_c<len(row) else ""
            neg=raw_a.strip().startswith("-"); amt=_parse_amount(raw_a)
            if not amt: skipped+=1; continue
            ttype="gider" if neg else "gelir"
        elif deb_c is not None or cred_c is not None:
            dv=_parse_amount(row[deb_c])  if deb_c  is not None and deb_c <len(row) else None
            cv=_parse_amount(row[cred_c]) if cred_c is not None and cred_c<len(row) else None
            if dv and dv>0:   amt,ttype=dv,"gider"
            elif cv and cv>0: amt,ttype=cv,"gelir"
            else: skipped+=1; continue
        else: skipped+=1; continue
        parsed.append({"date":dt,"description":desc,"amount":round(amt,2),"type":ttype,"category":_guess_cat(desc,ttype)})
    return jsonify({"ok":True,"rows":parsed,"skipped":skipped,"headers":header})

@app.route("/api/import/confirm", methods=["POST"])
def import_confirm():
    rows=request.get_json(force=True)
    if not isinstance(rows,list): return jsonify({"ok":False}),400
    db=get_db(); now=datetime.now().isoformat(); count=0
    for r in rows:
        if not r.get("skip") and r.get("amount",0)>0:
            db.execute("INSERT INTO transactions (type,amount,category,description,date,created_at) VALUES (?,?,?,?,?,?)",
                       (r["type"],r["amount"],r["category"],r.get("description",""),r["date"],now))
            count+=1
    db.commit(); return jsonify({"ok":True,"imported":count})

# ── HTML ──────────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cash Flow</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0a0c12;--bg2:#111318;--bg3:#1a1d26;--bg4:#21253a;
  --g:#22c55e;--r:#ef4444;--b:#6366f1;--b2:#818cf8;--y:#f59e0b;--p:#a855f7;--c:#06b6d4;
  --txt:#e2e8f0;--txt2:#94a3b8;--border:#1e2233;--border2:#2a2f45;
  --radius:12px;--shadow:0 8px 32px rgba(0,0,0,.5);
  --font:'Inter',system-ui,sans-serif;
}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
body{background:var(--bg);color:var(--txt);font-family:var(--font);min-height:100vh;overflow-x:hidden}

/* ── LAYOUT ── */
.shell{display:flex;min-height:100vh}
nav{width:220px;background:var(--bg2);border-right:1px solid var(--border);
    display:flex;flex-direction:column;flex-shrink:0;position:fixed;top:0;left:0;height:100vh;z-index:100}
.main{margin-left:220px;flex:1;display:flex;flex-direction:column;min-height:100vh}
@media(max-width:768px){
  nav{width:100%;height:56px;flex-direction:row;border-right:none;border-bottom:1px solid var(--border);
      position:fixed;bottom:0;top:auto;z-index:200}
  .main{margin-left:0;margin-bottom:56px}
  .nav-logo{display:none}
}

/* ── NAV ── */
.nav-logo{padding:24px 20px 16px;border-bottom:1px solid var(--border);margin-bottom:8px}
.nav-logo .brand{font-size:1.1rem;font-weight:800;letter-spacing:-.02em;display:flex;align-items:center;gap:8px}
.nav-logo .brand .dot{width:8px;height:8px;border-radius:50%;background:var(--b2)}
.nav-logo .sub{font-size:.72rem;color:var(--txt2);margin-top:2px;padding-left:16px}
.nav-links{flex:1;padding:4px 8px;display:flex;flex-direction:column;gap:2px}
.nl{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:9px;
    cursor:pointer;color:var(--txt2);font-size:.88rem;font-weight:500;transition:.15s;user-select:none}
.nl:hover{background:var(--bg3);color:var(--txt)}
.nl.active{background:linear-gradient(135deg,#6366f122,#818cf811);color:var(--b2);
  border:1px solid #6366f133}
.nl .ico{font-size:1.1rem;width:22px;text-align:center}
@media(max-width:768px){
  .nav-links{flex-direction:row;padding:0;gap:0;justify-content:space-around;align-items:center;height:100%}
  .nl{flex-direction:column;gap:2px;font-size:.65rem;padding:4px 12px}
  .nl .ico{font-size:1.2rem}
}
.nav-bottom{padding:16px;border-top:1px solid var(--border);font-size:.72rem;color:var(--txt2);line-height:1.6}
@media(max-width:768px){.nav-bottom{display:none}}

/* ── PAGE ── */
.page{display:none;padding:28px 28px;max-width:1280px}
.page.active{display:block}
@media(max-width:600px){.page{padding:16px}}
.page-title{font-size:1.4rem;font-weight:800;margin-bottom:4px;letter-spacing:-.02em}
.page-sub{font-size:.82rem;color:var(--txt2);margin-bottom:24px}

/* ── CARDS ── */
.card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:20px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px}
@media(max-width:900px){.grid4{grid-template-columns:repeat(2,1fr)}.grid2{grid-template-columns:1fr}}
@media(max-width:500px){.grid4{grid-template-columns:1fr}.grid3{grid-template-columns:1fr}}

/* ── STAT CARDS ── */
.stat{border-radius:var(--radius);padding:18px 20px;position:relative;overflow:hidden;border:1px solid transparent}
.stat .lbl{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--txt2);margin-bottom:8px;display:flex;align-items:center;gap:6px}
.stat .val{font-size:1.8rem;font-weight:800;letter-spacing:-.03em;line-height:1}
.stat .sub{font-size:.75rem;color:var(--txt2);margin-top:6px}
.stat .glow{position:absolute;width:60px;height:60px;border-radius:50%;filter:blur(25px);opacity:.35;right:-5px;top:-5px}
.stat-bal{background:linear-gradient(135deg,#1e2845,#161c33);border-color:#6366f133}
.stat-bal .glow{background:var(--b)}
.stat-g{background:linear-gradient(135deg,#0d2118,#0a1a12);border-color:#22c55e22}
.stat-g .glow{background:var(--g)}
.stat-r{background:linear-gradient(135deg,#1f0e0e,#180a0a);border-color:#ef444422}
.stat-r .glow{background:var(--r)}
.stat-n{background:linear-gradient(135deg,#14182a,#0f1220);border-color:#6366f122}
.stat-n .glow{background:var(--p)}

/* ── MONTH NAV ── */
.mnav{display:flex;align-items:center;gap:10px}
.mnav button{background:var(--bg3);border:1px solid var(--border2);color:var(--txt);
  padding:6px 14px;border-radius:8px;cursor:pointer;font-size:.82rem;font-weight:500;transition:.15s}
.mnav button:hover{border-color:var(--b2);color:var(--b2)}
.mnav .ml{font-weight:700;min-width:110px;text-align:center;font-size:.9rem}
.top-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;flex-wrap:wrap;gap:10px}

/* ── MOTIVATION ── */
.motiv-card{margin-bottom:20px}
.motiv-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:8px}
.health-badge{font-size:.78rem;font-weight:700;padding:5px 14px;border-radius:20px;border:1px solid}
.motiv-bar-bg{background:var(--bg3);border-radius:6px;height:6px;overflow:hidden;margin-bottom:14px}
.motiv-bar-fill{height:100%;border-radius:6px;transition:width .9s cubic-bezier(.4,0,.2,1)}
.motiv-msgs{display:flex;flex-direction:column;gap:7px}
.motiv-msg{display:flex;gap:10px;align-items:flex-start;padding:10px 12px;
  background:var(--bg3);border-radius:8px;border:1px solid var(--border);font-size:.84rem;line-height:1.5}
.motiv-msg .ico{flex-shrink:0;font-size:1rem}

/* ── CHARTS ── */
canvas{display:block;width:100%!important}
.chart-wrap{position:relative}
.chart-lbl{font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--txt2);margin-bottom:12px}

/* ── LEDGER TABLE ── */
.ledger-toolbar{display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap}
.search-box{flex:1;min-width:160px;background:var(--bg3);border:1px solid var(--border2);
  color:var(--txt);padding:9px 14px;border-radius:9px;font-size:.85rem;outline:none}
.search-box:focus{border-color:var(--b2)}
.filter-sel{background:var(--bg3);border:1px solid var(--border2);color:var(--txt2);
  padding:9px 12px;border-radius:9px;font-size:.82rem;outline:none;cursor:pointer}
.filter-sel:focus{border-color:var(--b2)}
.btn{padding:9px 18px;border-radius:9px;border:none;font-size:.82rem;font-weight:600;cursor:pointer;transition:.2s;display:inline-flex;align-items:center;gap:6px}
.btn:hover{opacity:.85;transform:translateY(-1px)}
.btn-primary{background:var(--b);color:#fff}
.btn-danger{background:var(--r);color:#fff}
.btn-ghost{background:var(--bg3);border:1px solid var(--border2);color:var(--txt2)}
.btn-ghost:hover{border-color:var(--b2);color:var(--b2)}
.btn-green{background:var(--g);color:#fff}

.ledger-wrap{overflow-x:auto;border:1px solid var(--border);border-radius:var(--radius)}
table{width:100%;border-collapse:collapse;font-size:.83rem}
thead tr{background:var(--bg3);position:sticky;top:0;z-index:10}
th{padding:11px 12px;text-align:left;font-size:.72rem;font-weight:600;text-transform:uppercase;
   letter-spacing:.06em;color:var(--txt2);border-bottom:1px solid var(--border);white-space:nowrap;user-select:none}
th.sortable{cursor:pointer}
th.sortable:hover{color:var(--b2)}
th .sort-ico{margin-left:4px;opacity:.4}
td{padding:0;border-bottom:1px solid var(--border);vertical-align:middle}
td .cell{padding:10px 12px;display:flex;align-items:center;gap:6px;min-height:42px}
tbody tr:hover{background:#ffffff05}
tbody tr.selected{background:#6366f10d}
tbody tr:last-child td{border-bottom:none}

/* inline edit */
.cell-edit{padding:0!important}
.cell-edit input,.cell-edit select{
  width:100%;padding:10px 12px;background:transparent;border:none;
  color:var(--txt);font-size:.83rem;outline:none;font-family:inherit}
.cell-editing{background:#6366f108!important;outline:2px solid var(--b2);outline-offset:-1px;border-radius:0}

/* badges */
.badge{display:inline-block;padding:3px 9px;border-radius:20px;font-size:.7rem;font-weight:600;white-space:nowrap}
.badge-g{background:#22c55e18;color:var(--g);border:1px solid #22c55e33}
.badge-r{background:#ef444418;color:var(--r);border:1px solid #ef444433}
.badge-cat{background:var(--bg4);color:var(--txt2);border:1px solid var(--border2)}

.del-row{background:none;border:none;color:var(--txt2);cursor:pointer;padding:6px;
  border-radius:6px;opacity:.4;transition:.15s;font-size:.9rem}
.del-row:hover{color:var(--r);opacity:1;background:#ef444418}

/* add row button */
.add-row-btn{display:flex;align-items:center;gap:8px;padding:10px 16px;
  color:var(--txt2);font-size:.82rem;cursor:pointer;border-top:1px solid var(--border);
  background:var(--bg2);transition:.15s}
.add-row-btn:hover{color:var(--b2);background:var(--bg3)}

.empty-state{text-align:center;padding:48px;color:var(--txt2);font-size:.88rem}
.empty-state .icon{font-size:2.5rem;margin-bottom:10px;opacity:.4}

/* ── FORMS (add page) ── */
label{display:block;font-size:.75rem;color:var(--txt2);margin-bottom:4px;font-weight:500}
.f-input{width:100%;background:var(--bg3);border:1px solid var(--border2);color:var(--txt);
  padding:10px 14px;border-radius:9px;font-size:.88rem;outline:none;transition:.15s;font-family:inherit}
.f-input:focus{border-color:var(--b2)}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
@media(max-width:500px){.form-row{grid-template-columns:1fr}}
.type-tabs{display:flex;gap:8px;margin-bottom:16px}
.type-tab{flex:1;padding:10px;border-radius:9px;border:2px solid var(--border2);
  font-weight:600;font-size:.85rem;cursor:pointer;transition:.2s;background:var(--bg3);color:var(--txt2)}
.type-tab.tg{border-color:var(--g);color:var(--g);background:#22c55e12}
.type-tab.tr{border-color:var(--r);color:var(--r);background:#ef444412}

/* ── CSV DROP ZONE ── */
.drop-zone{border:2px dashed var(--border2);border-radius:12px;padding:36px;text-align:center;
  cursor:pointer;transition:.2s;margin-bottom:16px;background:var(--bg3)}
.drop-zone:hover,.drop-zone.drag{border-color:var(--b2);background:#6366f108}
.drop-zone .dz-icon{font-size:2.4rem;margin-bottom:10px}
.drop-zone .dz-title{font-size:.9rem;font-weight:600;margin-bottom:4px}
.drop-zone .dz-sub{font-size:.77rem;color:var(--txt2)}

/* preview table */
.prev-table-wrap{overflow:auto;max-height:350px;border:1px solid var(--border);border-radius:var(--radius)}
.prev-table{width:100%;border-collapse:collapse;font-size:.8rem}
.prev-table th{padding:8px 10px;background:var(--bg3);font-size:.7rem;font-weight:600;
  text-transform:uppercase;letter-spacing:.05em;color:var(--txt2);border-bottom:1px solid var(--border);
  position:sticky;top:0}
.prev-table td{padding:7px 10px;border-bottom:1px solid var(--border)}
.prev-table tr:hover td{background:#ffffff04}
.prev-table select{background:var(--bg4);border:1px solid var(--border2);color:var(--txt);
  padding:3px 6px;border-radius:6px;font-size:.76rem}

/* ── BUDGET ── */
.budget-row{margin-bottom:14px}
.budget-row .btop{display:flex;justify-content:space-between;font-size:.8rem;margin-bottom:5px}
.prog-bg{background:var(--bg3);border-radius:4px;height:6px;overflow:hidden}
.prog-fill{height:100%;border-radius:4px;transition:width .7s cubic-bezier(.4,0,.2,1)}

/* ── TOAST ── */
#toast{position:fixed;bottom:72px;right:20px;background:var(--bg3);border:1px solid var(--b);
  color:var(--txt);padding:12px 20px;border-radius:10px;font-size:.85rem;
  transform:translateY(20px);opacity:0;transition:.25s;z-index:999;pointer-events:none;box-shadow:var(--shadow)}
#toast.show{transform:translateY(0);opacity:1}
@media(min-width:769px){#toast{bottom:24px}}

/* ── SCROLLBAR ── */
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:4px}

.divider{height:1px;background:var(--border);margin:20px 0}
.section-title{font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--txt2);margin-bottom:14px}
</style>
</head>
<body>
<div class="shell">

<!-- ── SIDEBAR NAV ── -->
<nav>
  <div class="nav-logo">
    <div class="brand"><div class="dot"></div>Cash Flow</div>
    <div class="sub">Nakit Akışı Takibi</div>
  </div>
  <div class="nav-links">
    <div class="nl active" data-page="dashboard" onclick="goPage('dashboard',this)">
      <span class="ico">📊</span>Dashboard
    </div>
    <div class="nl" data-page="ledger" onclick="goPage('ledger',this)">
      <span class="ico">📋</span>Tablo
    </div>
    <div class="nl" data-page="add" onclick="goPage('add',this)">
      <span class="ico">➕</span>Ekle
    </div>
    <div class="nl" data-page="import" onclick="goPage('import',this)">
      <span class="ico">📂</span>İçe Aktar
    </div>
    <div class="nl" data-page="budget" onclick="goPage('budget',this)">
      <span class="ico">🎯</span>Bütçe
    </div>
  </div>
  <div class="nav-bottom">Tüm veriler cihazınızda saklanır.</div>
</nav>

<!-- ── MAIN ── -->
<div class="main">

<!-- DASHBOARD -->
<div class="page active" id="page-dashboard">
  <div class="top-row">
    <div>
      <div class="page-title">Dashboard</div>
      <div class="page-sub" id="db-sub">Aylık özet</div>
    </div>
    <div class="mnav">
      <button onclick="changeMonth(-1)">‹</button>
      <div class="ml" id="mlabel"></div>
      <button onclick="changeMonth(1)">›</button>
    </div>
  </div>

  <div class="grid4">
    <div class="stat stat-bal">
      <div class="glow"></div>
      <div class="lbl">💼 Toplam Birikim</div>
      <div class="val" id="s-bal">—</div>
      <div class="sub">tüm zamanlar</div>
    </div>
    <div class="stat stat-g">
      <div class="glow"></div>
      <div class="lbl">📈 Bu Ay Gelir</div>
      <div class="val" id="s-gelir">—</div>
      <div class="sub" id="s-gelir-sub"></div>
    </div>
    <div class="stat stat-r">
      <div class="glow"></div>
      <div class="lbl">📉 Bu Ay Gider</div>
      <div class="val" id="s-gider">—</div>
      <div class="sub" id="s-gider-sub"></div>
    </div>
    <div class="stat stat-n">
      <div class="glow"></div>
      <div class="lbl">⚖️ Net Tasarruf</div>
      <div class="val" id="s-net">—</div>
      <div class="sub" id="s-net-sub"></div>
    </div>
  </div>

  <!-- motivation -->
  <div class="card motiv-card">
    <div class="motiv-header">
      <div class="section-title" style="margin:0">Finansal Durum Analizi</div>
      <div id="health-badge" class="health-badge" style="color:var(--txt2);border-color:var(--border2)">—</div>
    </div>
    <div class="motiv-bar-bg"><div id="motiv-fill" class="motiv-bar-fill" style="width:0%"></div></div>
    <div id="motiv-msgs" class="motiv-msgs"><div style="color:var(--txt2);font-size:.83rem">Yükleniyor…</div></div>
  </div>

  <div class="grid2">
    <div class="card"><div class="chart-lbl">Aylık Gelir / Gider</div><div class="chart-wrap"><canvas id="barChart" height="190"></canvas></div></div>
    <div class="card"><div class="chart-lbl">Gider Dağılımı</div><div class="chart-wrap"><canvas id="donut" height="190"></canvas></div></div>
  </div>
</div>

<!-- LEDGER -->
<div class="page" id="page-ledger">
  <div class="top-row">
    <div>
      <div class="page-title">Tablo Görünümü</div>
      <div class="page-sub">Hücreye tıkla → düzenle &nbsp;·&nbsp; Tab ile ileri &nbsp;·&nbsp; Enter ile kaydet</div>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <button class="btn btn-ghost" id="del-sel-btn" onclick="bulkDelete()" style="display:none">🗑 Seçilenleri Sil</button>
      <button class="btn btn-primary" onclick="goPage('add',document.querySelector('[data-page=add]'))">+ Yeni Satır</button>
    </div>
  </div>

  <div class="ledger-toolbar">
    <input class="search-box" id="ledger-search" placeholder="🔍  Ara…" oninput="filterLedger()">
    <select class="filter-sel" id="f-type" onchange="filterLedger()">
      <option value="">Tümü</option>
      <option value="gelir">Gelir</option>
      <option value="gider">Gider</option>
    </select>
    <select class="filter-sel" id="f-cat" onchange="filterLedger()"><option value="">Tüm Kategoriler</option></select>
    <select class="filter-sel" id="f-year" onchange="filterLedger()"></select>
    <button class="btn btn-ghost" onclick="exportCsv()">⬇ CSV</button>
  </div>

  <div class="ledger-wrap">
    <table id="ledger-table">
      <thead>
        <tr>
          <th style="width:36px"><input type="checkbox" id="chk-all" onchange="toggleAllChk(this.checked)"></th>
          <th class="sortable" onclick="sortBy('date')">Tarih <span class="sort-ico" id="sort-date">↕</span></th>
          <th>Tür</th>
          <th class="sortable" onclick="sortBy('category')">Kategori <span class="sort-ico" id="sort-category">↕</span></th>
          <th>Açıklama</th>
          <th class="sortable" onclick="sortBy('amount')" style="text-align:right">Tutar <span class="sort-ico" id="sort-amount">↕</span></th>
          <th style="width:36px"></th>
        </tr>
      </thead>
      <tbody id="ledger-body"></tbody>
    </table>
    <div class="add-row-btn" onclick="goPage('add',document.querySelector('[data-page=add]'))">
      <span style="font-size:1rem;color:var(--b2)">+</span> Yeni işlem ekle
    </div>
  </div>
  <div id="ledger-count" style="font-size:.78rem;color:var(--txt2);margin-top:10px;text-align:right"></div>
</div>

<!-- ADD -->
<div class="page" id="page-add">
  <div class="page-title">İşlem Ekle</div>
  <div class="page-sub">Manuel olarak gelir veya gider gir</div>

  <div class="card" style="max-width:520px">
    <div class="type-tabs">
      <button class="type-tab tg" id="tab-g" onclick="setTab('gelir')">📈  Gelir</button>
      <button class="type-tab" id="tab-r" onclick="setTab('gider')">📉  Gider</button>
    </div>
    <div class="form-row">
      <div><label>Tutar (₺)</label><input class="f-input" type="number" id="f-amount" placeholder="0.00" min="0" step="0.01"></div>
      <div><label>Tarih</label><input class="f-input" type="date" id="f-date"></div>
    </div>
    <div style="margin-bottom:12px"><label>Kategori</label><select class="f-input" id="f-cat"></select></div>
    <div style="margin-bottom:20px"><label>Açıklama</label><input class="f-input" type="text" id="f-desc" placeholder="örn. Ocak maaşı"></div>
    <button class="btn btn-green" id="add-btn" style="width:100%;padding:13px" onclick="addTx()">Kaydet</button>
  </div>
</div>

<!-- IMPORT -->
<div class="page" id="page-import">
  <div class="page-title">Banka Verisi İçe Aktar</div>
  <div class="page-sub">Banka uygulaması → Hesap Hareketleri → CSV/Excel olarak dışa aktar → buraya yükle</div>

  <div class="card" style="max-width:700px;margin-bottom:16px">
    <div class="drop-zone" id="drop-zone" onclick="document.getElementById('csv-file').click()">
      <div class="dz-icon">📂</div>
      <div class="dz-title">Dosyayı sürükle veya tıkla</div>
      <div class="dz-sub">CSV · XLS · XLSX &nbsp;—&nbsp; Garanti, İş Bankası, Akbank, YKB desteklenir</div>
      <input type="file" id="csv-file" accept=".csv,.xls,.xlsx" style="display:none" onchange="csvSelected(this)">
    </div>

    <div id="csv-preview" style="display:none">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:8px">
        <div id="csv-stats" style="font-size:.83rem;color:var(--txt2)"></div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-ghost" onclick="csvReset()">İptal</button>
          <button class="btn btn-primary" id="csv-ok-btn" onclick="csvConfirm()">İçe Aktar</button>
        </div>
      </div>
      <div class="prev-table-wrap">
        <table class="prev-table">
          <thead><tr>
            <th><input type="checkbox" id="prev-chk-all" checked onchange="prevToggleAll(this.checked)"></th>
            <th>Tarih</th><th>Açıklama</th><th>Tür</th><th>Kategori</th><th style="text-align:right">Tutar</th>
          </tr></thead>
          <tbody id="prev-body"></tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="card" style="max-width:700px">
    <div class="section-title">Desteklenen Formatlar</div>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;font-size:.82rem">
      <div style="background:var(--bg3);padding:12px 14px;border-radius:9px;border:1px solid var(--border2)">
        <div style="font-weight:600;margin-bottom:4px">🏦 Garanti BBVA</div>
        <div style="color:var(--txt2)">Noktalı virgüllü, Borç/Alacak sütunlu</div>
      </div>
      <div style="background:var(--bg3);padding:12px 14px;border-radius:9px;border:1px solid var(--border2)">
        <div style="font-weight:600;margin-bottom:4px">🏦 İş Bankası</div>
        <div style="color:var(--txt2)">Tekli Tutar sütunu, eksi = gider</div>
      </div>
      <div style="background:var(--bg3);padding:12px 14px;border-radius:9px;border:1px solid var(--border2)">
        <div style="font-weight:600;margin-bottom:4px">🏦 Akbank</div>
        <div style="color:var(--txt2)">Virgülle veya noktalı virgüllü</div>
      </div>
      <div style="background:var(--bg3);padding:12px 14px;border-radius:9px;border:1px solid var(--border2)">
        <div style="font-weight:600;margin-bottom:4px">🏦 Yapı Kredi</div>
        <div style="color:var(--txt2)">İşlem Tarihi, Açıklama, Tutar</div>
      </div>
    </div>
  </div>
</div>

<!-- BUDGET -->
<div class="page" id="page-budget">
  <div class="page-title">Bütçe Hedefleri</div>
  <div class="page-sub">Kategorilere aylık harcama limiti koy — otomatik takip edilir</div>

  <div class="grid2">
    <div class="card">
      <div class="section-title">Hedef Ekle / Güncelle</div>
      <div style="margin-bottom:12px"><label>Kategori</label><select class="f-input" id="b-cat"></select></div>
      <div style="margin-bottom:16px"><label>Aylık Limit (₺)</label><input class="f-input" type="number" id="b-limit" placeholder="örn. 5000"></div>
      <button class="btn btn-primary" style="width:100%" onclick="saveBudget()">Kaydet</button>
    </div>
    <div class="card" id="budget-display">
      <div class="section-title">Bu Ay Durum</div>
      <div id="budget-rows"><div class="empty-state"><div class="icon">🎯</div>Henüz hedef yok</div></div>
    </div>
  </div>
</div>

</div><!-- /main -->
</div><!-- /shell -->
<div id="toast"></div>

<script>
// ── GLOBALS ──────────────────────────────────────────────────────────────────
var MONTHS=['','Ocak','Şubat','Mart','Nisan','Mayıs','Haziran',
            'Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'];
var CLRS=['#6366f1','#f59e0b','#a855f7','#ef4444','#22c55e','#06b6d4',
          '#f97316','#ec4899','#84cc16','#14b8a6','#e11d48','#0ea5e9'];
var curYear=new Date().getFullYear(), curMonth=new Date().getMonth()+1;
var curTab='gelir', summaryData={}, allTx=[], filteredTx=[];
var sortCol='date', sortDir=-1;
var CATS={gelir:[],gider:[],all:[]};

// ── INIT ─────────────────────────────────────────────────────────────────────
window.onload=function(){
  document.getElementById('f-date').value=new Date().toISOString().split('T')[0];
  updateMonthLabel();
  loadCats(function(){
    loadDashboard();
    loadAllTx();
    populateYearFilter();
  });
  setupDrop();
};

function updateMonthLabel(){
  document.getElementById('mlabel').textContent=MONTHS[curMonth]+' '+curYear;
  document.getElementById('db-sub').textContent=MONTHS[curMonth]+' '+curYear+' özeti';
}

// ── NAVIGATION ───────────────────────────────────────────────────────────────
function goPage(id, el){
  document.querySelectorAll('.page').forEach(function(p){p.classList.remove('active')});
  document.querySelectorAll('.nl').forEach(function(n){n.classList.remove('active')});
  document.getElementById('page-'+id).classList.add('active');
  if(el) el.classList.add('active');
  if(id==='ledger') renderLedger();
  if(id==='dashboard') loadDashboard();
}

// ── MONTH NAV ─────────────────────────────────────────────────────────────────
function changeMonth(d){
  curMonth+=d;
  if(curMonth>12){curMonth=1;curYear++}
  if(curMonth<1){curMonth=12;curYear--}
  updateMonthLabel();
  loadDashboard();
}

// ── CATS ─────────────────────────────────────────────────────────────────────
function loadCats(cb){
  xhr('/api/categories',null,function(d){
    CATS=d;
    fillSel('f-cat',CATS[curTab]);
    fillSel('b-cat',CATS.gider);
    // ledger filter
    var fc=document.getElementById('f-cat');
    fc.innerHTML='<option value="">Tüm Kategoriler</option>';
    CATS.all.forEach(function(c){fc.innerHTML+='<option>'+c+'</option>'});
    if(cb)cb();
  });
}
function fillSel(id,list){
  var s=document.getElementById(id); s.innerHTML='';
  list.forEach(function(c){s.innerHTML+='<option>'+c+'</option>'});
}
function setTab(t){
  curTab=t;
  document.getElementById('tab-g').className='type-tab'+(t==='gelir'?' tg':'');
  document.getElementById('tab-r').className='type-tab'+(t==='gider'?' tr':'');
  document.getElementById('add-btn').className='btn '+(t==='gelir'?'btn-green':'btn-danger');
  fillSel('f-cat',CATS[t]);
}

// ── DASHBOARD ─────────────────────────────────────────────────────────────────
function loadDashboard(){
  xhr('/api/summary?year='+curYear+'&month='+curMonth,null,function(d){
    summaryData=d;
    renderStats(d);
    drawBar(d.bar);
    drawDonut(d.gider_cats);
    renderBudgetPage(d.gider_cats,d.budgets);
  });
  xhr('/api/motivation',null,renderMotivation);
}

function fmt(n){return '₺'+Number(n).toLocaleString('tr-TR',{minimumFractionDigits:2,maximumFractionDigits:2})}
function fmtK(n){if(n>=1e6)return(n/1e6).toFixed(1)+'M';if(n>=1e3)return(n/1e3).toFixed(0)+'K';return Math.round(n)+''}

function renderStats(d){
  var b=document.getElementById('s-bal');
  b.textContent=fmt(d.balance);
  b.style.color=d.balance>=0?'var(--g)':'var(--r)';
  document.getElementById('s-gelir').textContent=fmt(d.gelir);
  document.getElementById('s-gider').textContent=fmt(d.gider);
  document.getElementById('s-net').textContent=fmt(d.net);
  document.getElementById('s-net').style.color=d.net>=0?'var(--g)':'var(--r)';
  var pct=d.gelir>0?Math.round(d.net/d.gelir*100):0;
  document.getElementById('s-net-sub').textContent='Gelirin %'+pct+' tasarruf';
  document.getElementById('s-gelir-sub').textContent=topCat(d.gelir_cats)?'En çok: '+topCat(d.gelir_cats):'';
  document.getElementById('s-gider-sub').textContent=topCat(d.gider_cats)?'En çok: '+topCat(d.gider_cats):'';
}
function topCat(o){var t=null,m=0;Object.keys(o).forEach(function(k){if(o[k]>m){m=o[k];t=k}});return t}

function renderMotivation(d){
  document.getElementById('motiv-fill').style.width=d.score+'%';
  document.getElementById('motiv-fill').style.background=d.color;
  var badge=document.getElementById('health-badge');
  badge.textContent=d.label; badge.style.color=d.color; badge.style.borderColor=d.color+'44';
  var el=document.getElementById('motiv-msgs');
  if(!d.msgs||!d.msgs.length){el.innerHTML='<div style="color:var(--txt2);font-size:.83rem">Veri girdikçe analiz burada görünür.</div>';return}
  el.innerHTML=d.msgs.map(function(m){
    return '<div class="motiv-msg"><span class="ico">'+m.icon+'</span><span>'+m.text+'</span></div>';
  }).join('');
}

// ── BAR CHART ─────────────────────────────────────────────────────────────────
function drawBar(data){
  var cv=document.getElementById('barChart');
  var W=cv.parentElement.clientWidth||400, H=190;
  cv.width=W; cv.height=H;
  var ctx=cv.getContext('2d');
  ctx.clearRect(0,0,W,H);
  var maxVal=0;
  data.forEach(function(d){if(d.gelir>maxVal)maxVal=d.gelir;if(d.gider>maxVal)maxVal=d.gider});
  if(!maxVal)maxVal=1;
  var p={t:10,r:10,b:28,l:52}, cw=W-p.l-p.r, ch=H-p.t-p.b, gap=cw/12, bw=gap*0.28;
  ctx.strokeStyle='#1e2233'; ctx.lineWidth=1;
  [0,.25,.5,.75,1].forEach(function(f){
    var y=p.t+ch*(1-f);
    ctx.beginPath();ctx.moveTo(p.l,y);ctx.lineTo(W-p.r,y);ctx.stroke();
    ctx.fillStyle='#475569';ctx.font='10px Inter,system-ui';ctx.textAlign='right';
    ctx.fillText(fmtK(maxVal*f),p.l-4,y+3);
  });
  data.forEach(function(d,i){
    var x=p.l+i*gap+gap/2;
    var gh=ch*(d.gelir/maxVal), eh=ch*(d.gider/maxVal);
    if(d.gelir>0){ctx.fillStyle='#22c55e66';ctx.beginPath();rr(ctx,x-bw-2,p.t+ch-gh,bw,gh,3);ctx.fill()}
    if(d.gider>0){ctx.fillStyle='#ef444466';ctx.beginPath();rr(ctx,x+2,p.t+ch-eh,bw,eh,3);ctx.fill()}
    if(i+1===curMonth&&curYear===new Date().getFullYear()){
      ctx.strokeStyle='#6366f1';ctx.lineWidth=1.5;
      ctx.strokeRect(x-bw-4,p.t,bw*2+8,ch);
    }
    ctx.fillStyle='#475569';ctx.font='9px Inter,system-ui';ctx.textAlign='center';
    ctx.fillText(MONTHS[i+1].slice(0,3),x,H-6);
  });
}
function rr(ctx,x,y,w,h,r){
  if(h<=0)return;
  ctx.moveTo(x+r,y);ctx.lineTo(x+w-r,y);ctx.quadraticCurveTo(x+w,y,x+w,y+r);
  ctx.lineTo(x+w,y+h);ctx.lineTo(x,y+h);ctx.lineTo(x,y+r);ctx.quadraticCurveTo(x,y,x+r,y);ctx.closePath();
}

// ── DONUT ────────────────────────────────────────────────────────────────────
function drawDonut(cats){
  var cv=document.getElementById('donut');
  var W=cv.parentElement.clientWidth||400, H=190;
  cv.width=W; cv.height=H;
  var ctx=cv.getContext('2d');
  ctx.clearRect(0,0,W,H);
  var keys=Object.keys(cats).filter(function(k){return cats[k]>0});
  if(!keys.length){
    ctx.fillStyle='#475569';ctx.font='13px Inter,system-ui';ctx.textAlign='center';
    ctx.fillText('Bu ay gider yok',W/2,H/2);return;
  }
  var total=keys.reduce(function(s,k){return s+cats[k]},0);
  var cx=H/2,cy=H/2,R=cy-14,r=cy*0.46,a=-Math.PI/2;
  keys.forEach(function(k,i){
    var sl=cats[k]/total*2*Math.PI;
    ctx.beginPath();ctx.moveTo(cx,cy);ctx.arc(cx,cy,R,a,a+sl);ctx.closePath();
    ctx.fillStyle=CLRS[i%CLRS.length];ctx.fill();a+=sl;
  });
  ctx.beginPath();ctx.arc(cx,cy,r,0,2*Math.PI);ctx.fillStyle=getComputedStyle(document.documentElement).getPropertyValue('--bg2')||'#111318';ctx.fill();
  ctx.fillStyle='#e2e8f0';ctx.font='bold 12px Inter,system-ui';ctx.textAlign='center';
  ctx.fillText(fmtK(total)+'₺',cx,cy-3);
  ctx.fillStyle='#64748b';ctx.font='9px Inter,system-ui';ctx.fillText('toplam',cx,cy+10);
  var lx=H+12,ly=10,lh=20;
  keys.slice(0,8).forEach(function(k,i){
    ctx.fillStyle=CLRS[i%CLRS.length];ctx.beginPath();ctx.arc(lx+5,ly+i*lh+6,4,0,2*Math.PI);ctx.fill();
    var pct=Math.round(cats[k]/total*100);
    ctx.fillStyle='#e2e8f0';ctx.font='10px Inter,system-ui';ctx.textAlign='left';
    var lbl=k.length>13?k.slice(0,13)+'…':k;
    ctx.fillText(lbl,lx+14,ly+i*lh+10);
    ctx.fillStyle='#64748b';ctx.textAlign='right';ctx.fillText(pct+'%',W-2,ly+i*lh+10);
  });
}

// ── BUDGET PAGE ───────────────────────────────────────────────────────────────
function renderBudgetPage(gider_cats,budgets){
  var el=document.getElementById('budget-rows');
  var keys=Object.keys(budgets);
  if(!keys.length){el.innerHTML='<div class="empty-state"><div class="icon">🎯</div>Henüz hedef yok</div>';return}
  el.innerHTML=keys.map(function(cat){
    var lim=budgets[cat],spent=gider_cats[cat]||0;
    var pct=Math.min(100,Math.round(spent/lim*100));
    var color=spent>lim?'var(--r)':pct>75?'var(--y)':'var(--g)';
    return '<div class="budget-row"><div class="btop"><span>'+cat+'</span>'+
      '<span style="color:var(--txt2)">'+fmt(spent)+' / '+fmt(lim)+
      ' <span class="badge '+(spent>lim?'badge-r':'badge-g')+'">%'+pct+'</span></span></div>'+
      '<div class="prog-bg"><div class="prog-fill" style="width:'+pct+'%;background:'+color+'"></div></div></div>';
  }).join('');
}
function saveBudget(){
  var cat=document.getElementById('b-cat').value, limit=parseFloat(document.getElementById('b-limit').value);
  if(!cat||!limit||limit<=0){toast('Kategori ve limit giriniz');return}
  xhr('/api/budgets',{category:cat,limit:limit},function(){
    document.getElementById('b-limit').value='';
    loadDashboard();toast('Bütçe kaydedildi ✓');
  });
}

// ── ADD TX ────────────────────────────────────────────────────────────────────
function addTx(){
  var amount=parseFloat(document.getElementById('f-amount').value);
  var cat=document.getElementById('f-cat').value;
  var desc=document.getElementById('f-desc').value;
  var dt=document.getElementById('f-date').value;
  if(!amount||amount<=0){toast('Tutar giriniz');return}
  xhr('/api/transactions',{type:curTab,amount:amount,category:cat,description:desc,date:dt},function(r){
    if(r.ok){
      toast('İşlem eklendi ✓');
      document.getElementById('f-amount').value='';
      document.getElementById('f-desc').value='';
      loadDashboard();loadAllTx();
    }
  });
}

// ── LEDGER ────────────────────────────────────────────────────────────────────
function loadAllTx(){
  xhr('/api/transactions',null,function(d){allTx=d;filteredTx=d;renderLedger();});
}

function populateYearFilter(){
  var fy=document.getElementById('f-year');
  fy.innerHTML='<option value="">Tüm Yıllar</option>';
  var now=new Date().getFullYear();
  for(var y=now;y>=now-4;y--){fy.innerHTML+='<option value="'+y+'"'+(y===now?' selected':'')+'>'+y+'</option>'}
  // trigger load for current year only
  filterLedger();
}

var _sortIcos={};
function sortBy(col){
  if(sortCol===col) sortDir*=-1; else{sortCol=col;sortDir=-1}
  document.querySelectorAll('.sort-ico').forEach(function(s){s.textContent='↕';s.style.opacity='.3'});
  var ico=document.getElementById('sort-'+col);
  if(ico){ico.textContent=sortDir===-1?'↓':'↑';ico.style.opacity='1'}
  renderLedger();
}

function filterLedger(){
  var q=(document.getElementById('ledger-search').value||'').toLowerCase();
  var ft=document.getElementById('f-type').value;
  var fc=document.getElementById('f-cat').value;
  var fy=document.getElementById('f-year').value;
  filteredTx=allTx.filter(function(t){
    if(fy&&!t.date.startsWith(fy))return false;
    if(ft&&t.type!==ft)return false;
    if(fc&&t.category!==fc)return false;
    if(q&&!(t.description||'').toLowerCase().includes(q)&&!t.category.toLowerCase().includes(q)&&!t.date.includes(q))return false;
    return true;
  });
  renderLedger();
}

function renderLedger(){
  var data=filteredTx.slice().sort(function(a,b){
    var av=a[sortCol]||'',bv=b[sortCol]||'';
    if(sortCol==='amount'){av=parseFloat(av);bv=parseFloat(bv)}
    return av<bv?sortDir:av>bv?-sortDir:0;
  });
  var tbody=document.getElementById('ledger-body');
  if(!data.length){
    tbody.innerHTML='<tr><td colspan="7"><div class="empty-state"><div class="icon">📋</div>İşlem bulunamadı</div></td></tr>';
    document.getElementById('ledger-count').textContent='';
    return;
  }
  tbody.innerHTML=data.map(function(t){
    var isG=t.type==='gelir';
    return '<tr data-id="'+t.id+'" data-type="'+t.type+'">'+
      '<td><div class="cell"><input type="checkbox" class="row-chk" data-id="'+t.id+'" onchange="rowChkChange()"></div></td>'+
      '<td class="editable" data-field="date" data-id="'+t.id+'"><div class="cell">'+t.date+'</div></td>'+
      '<td><div class="cell"><span class="badge '+(isG?'badge-g':'badge-r')+'">'+(isG?'Gelir':'Gider')+'</span></div></td>'+
      '<td class="editable" data-field="category" data-id="'+t.id+'"><div class="cell"><span class="badge badge-cat">'+t.category+'</span></div></td>'+
      '<td class="editable" data-field="description" data-id="'+t.id+'"><div class="cell">'+(t.description||'<span style="color:var(--txt2);font-size:.78rem">—</span>')+'</div></td>'+
      '<td class="editable" data-field="amount" data-id="'+t.id+'" style="text-align:right">'+
        '<div class="cell" style="justify-content:flex-end;color:'+(isG?'var(--g)':'var(--r)')+'">'+
          (isG?'+':'-')+fmt(t.amount)+'</div></td>'+
      '<td><div class="cell"><button class="del-row" onclick="delTx('+t.id+')">✕</button></div></td>'+
    '</tr>';
  }).join('');
  document.getElementById('ledger-count').textContent=data.length+' işlem';

  // inline editing
  [].forEach.call(document.querySelectorAll('.editable'),function(td){
    td.addEventListener('click',function(e){startEdit(td)});
  });
}

function startEdit(td){
  if(td.classList.contains('cell-editing'))return;
  var field=td.dataset.field, id=td.dataset.id;
  var tx=allTx.find(function(t){return t.id==id});
  if(!tx)return;
  td.classList.add('cell-editing');
  var val=tx[field];
  var inp;
  if(field==='category'){
    inp=document.createElement('select');
    inp.className='cell-edit';
    var list=tx.type==='gelir'?CATS.gelir:CATS.gider;
    list.forEach(function(c){inp.innerHTML+='<option'+(c===val?' selected':'')+'>'+c+'</option>'});
  } else if(field==='amount'){
    inp=document.createElement('input');
    inp.type='number'; inp.step='0.01'; inp.value=val;
  } else if(field==='date'){
    inp=document.createElement('input');
    inp.type='date'; inp.value=val;
  } else {
    inp=document.createElement('input');
    inp.type='text'; inp.value=val||'';
  }
  inp.style.cssText='width:100%;padding:10px 12px;background:transparent;border:none;color:var(--txt);font-size:.83rem;outline:none;font-family:inherit';
  td.innerHTML=''; td.appendChild(inp);
  inp.focus();
  if(inp.type==='text'||inp.type==='number')inp.select();

  function save(){
    var newVal=inp.value.trim();
    if(newVal!==String(val)){
      var body={};body[field]=newVal;
      xhr('/api/transactions/'+id,body,function(r){if(r.ok){toast('Kaydedildi');loadAllTx();loadDashboard()}},true);
    } else {
      td.classList.remove('cell-editing');loadAllTx();
    }
  }
  inp.addEventListener('blur',save);
  inp.addEventListener('keydown',function(e){
    if(e.key==='Enter'){e.preventDefault();inp.blur()}
    if(e.key==='Escape'){td.classList.remove('cell-editing');loadAllTx()}
    if(e.key==='Tab'){e.preventDefault();inp.blur();
      var cells=[].slice.call(td.parentElement.querySelectorAll('.editable'));
      var idx=cells.indexOf(td);if(idx<cells.length-1)setTimeout(function(){startEdit(cells[idx+1])},80);
    }
  });
}

function rowChkChange(){
  var any=[].some.call(document.querySelectorAll('.row-chk'),function(c){return c.checked});
  document.getElementById('del-sel-btn').style.display=any?'':'none';
}
function toggleAllChk(v){
  [].forEach.call(document.querySelectorAll('.row-chk'),function(c){c.checked=v});
  rowChkChange();
}
function bulkDelete(){
  var ids=[].filter.call(document.querySelectorAll('.row-chk'),function(c){return c.checked}).map(function(c){return parseInt(c.dataset.id)});
  if(!ids.length)return;
  if(!confirm(ids.length+' işlem silinecek. Emin misiniz?'))return;
  xhr('/api/transactions/bulk-delete',ids,function(r){if(r.ok){toast(r.deleted+' işlem silindi');loadAllTx();loadDashboard()}});
}
function delTx(id){
  xhr('/api/transactions/'+id,null,function(){loadAllTx();loadDashboard();},false,true);
}

function exportCsv(){
  var h='Tarih,Tür,Kategori,Açıklama,Tutar\n';
  var rows=filteredTx.map(function(t){
    return [t.date,t.type,t.category,'"'+(t.description||'')+'"',t.amount].join(',');
  }).join('\n');
  var a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,﻿'+encodeURIComponent(h+rows);
  a.download='cashflow.csv'; a.click();
}

// ── CSV IMPORT ────────────────────────────────────────────────────────────────
var csvRows=[];

function setupDrop(){
  var dz=document.getElementById('drop-zone');
  dz.addEventListener('dragover',function(e){e.preventDefault();dz.classList.add('drag')});
  dz.addEventListener('dragleave',function(){dz.classList.remove('drag')});
  dz.addEventListener('drop',function(e){e.preventDefault();dz.classList.remove('drag');if(e.dataTransfer.files[0])uploadCsv(e.dataTransfer.files[0])});
}
function csvSelected(inp){if(inp.files[0])uploadCsv(inp.files[0])}
function uploadCsv(file){
  if(file.size>5*1024*1024){toast('Dosya çok büyük');return}
  var dz=document.getElementById('drop-zone');
  dz.innerHTML='<div class="dz-icon">⏳</div><div class="dz-title">Analiz ediliyor…</div>';
  var fd=new FormData(); fd.append('file',file);
  var req=new XMLHttpRequest(); req.open('POST','/api/import/preview');
  req.onload=function(){
    var d=JSON.parse(req.responseText);
    if(!d.ok){toast('Hata: '+d.error);csvReset();return}
    csvRows=d.rows; renderCsvPreview(d);
  };
  req.onerror=function(){toast('Yükleme başarısız');csvReset()};
  req.send(fd);
}
function renderCsvPreview(d){
  document.getElementById('csv-stats').textContent=d.rows.length+' işlem bulundu'+(d.skipped?', '+d.skipped+' satır atlandı':'');
  var tbody=document.getElementById('prev-body');
  tbody.innerHTML=d.rows.map(function(r,i){
    var isG=r.type==='gelir';
    var catSel='<select class="csv-cat-sel" data-i="'+i+'" onchange="csvRows[parseInt(this.dataset.i)].category=this.value" style="max-width:130px">'+
      (isG?CATS.gelir:CATS.gider).map(function(c){return'<option'+(c===r.category?' selected':'')+'>'+c+'</option>'}).join('')+'</select>';
    return '<tr><td><input type="checkbox" class="prev-chk" data-i="'+i+'" checked></td>'+
      '<td>'+r.date+'</td>'+
      '<td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="'+r.description+'">'+(r.description||'—')+'</td>'+
      '<td><span class="badge '+(isG?'badge-g':'badge-r')+'">'+(isG?'Gelir':'Gider')+'</span></td>'+
      '<td>'+catSel+'</td>'+
      '<td style="text-align:right;font-weight:600;color:'+(isG?'var(--g)':'var(--r)')+'">'+(isG?'+':'-')+fmt(r.amount)+'</td></tr>';
  }).join('');
  document.getElementById('csv-preview').style.display='block';
}
function prevToggleAll(v){[].forEach.call(document.querySelectorAll('.prev-chk'),function(c){c.checked=v})}
function csvConfirm(){
  var toImport=[].filter.call(document.querySelectorAll('.prev-chk'),function(c){return c.checked})
    .map(function(c){return csvRows[parseInt(c.dataset.i)]});
  if(!toImport.length){toast('Hiç satır seçili değil');return}
  var btn=document.getElementById('csv-ok-btn'); btn.textContent='Kaydediliyor…'; btn.disabled=true;
  xhr('/api/import/confirm',toImport,function(d){toast(d.imported+' işlem içe aktarıldı ✓');csvReset();loadAllTx();loadDashboard()});
}
function csvReset(){
  csvRows=[];
  document.getElementById('csv-preview').style.display='none';
  var dz=document.getElementById('drop-zone');
  dz.innerHTML='<div class="dz-icon">📂</div><div class="dz-title">Dosyayı sürükle veya tıkla</div>'+
    '<div class="dz-sub">CSV · XLS · XLSX &nbsp;—&nbsp; Garanti, İş Bankası, Akbank, YKB desteklenir</div>'+
    '<input type="file" id="csv-file" accept=".csv,.xls,.xlsx" style="display:none" onchange="csvSelected(this)">';
  dz.classList.remove('drag');
}

// ── XHR HELPER ───────────────────────────────────────────────────────────────
function xhr(url,body,cb,isPut,isDel){
  var r=new XMLHttpRequest();
  var method=isDel?'DELETE':body?(isPut?'PUT':'POST'):'GET';
  r.open(method,url);
  if(body){r.setRequestHeader('Content-Type','application/json')}
  r.onload=function(){try{cb&&cb(JSON.parse(r.responseText))}catch(e){}};
  r.send(body?JSON.stringify(body):null);
}

// ── TOAST ─────────────────────────────────────────────────────────────────────
function toast(msg){
  var el=document.getElementById('toast'); el.textContent=msg; el.classList.add('show');
  setTimeout(function(){el.classList.remove('show')},2500);
}

// ── RESIZE ────────────────────────────────────────────────────────────────────
window.addEventListener('resize',function(){
  if(summaryData.bar){drawBar(summaryData.bar);drawDonut(summaryData.gider_cats||{})}
});
</script>
</body>
</html>"""

@app.route("/")
def index(): return HTML

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)

init_db()
