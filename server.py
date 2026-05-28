import sqlite3, json, os, csv, io, re, requests, secrets, smtplib, threading, time, logging
from datetime import datetime, date, timedelta
from functools import wraps
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask, request, jsonify, g, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("kirpi")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
DB = os.path.join(os.path.dirname(__file__), "cashflow.db")

# ── MAIL CONFIG ───────────────────────────────────────────────────────────────
MAIL_FROM     = os.environ.get("MAIL_FROM", "")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
BACKUP_EMAIL  = os.environ.get("BACKUP_EMAIL", MAIL_FROM)
APP_URL       = os.environ.get("APP_URL", "https://web-production-ba700.up.railway.app")

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
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            display_name  TEXT NOT NULL DEFAULT '',
            password_hash TEXT NOT NULL,
            email         TEXT NOT NULL DEFAULT '',
            created_at    TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            token      TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            used       INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS profiles (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            name       TEXT NOT NULL,
            type       TEXT NOT NULL DEFAULT 'sahis',
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL DEFAULT 1,
            profile_id  INTEGER NOT NULL DEFAULT 1,
            type        TEXT NOT NULL,
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            description TEXT DEFAULT '',
            date        TEXT NOT NULL,
            created_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS budgets (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL DEFAULT 1,
            profile_id INTEGER NOT NULL DEFAULT 1,
            category   TEXT NOT NULL,
            limit_     REAL NOT NULL,
            UNIQUE(profile_id, category)
        );
        CREATE TABLE IF NOT EXISTS cards (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 1,
            profile_id      INTEGER NOT NULL DEFAULT 1,
            bank_name       TEXT NOT NULL,
            card_name       TEXT NOT NULL DEFAULT '',
            owner           TEXT NOT NULL DEFAULT '',
            limit_          REAL NOT NULL DEFAULT 0,
            used_           REAL NOT NULL DEFAULT 0,
            due_day         INTEGER NOT NULL DEFAULT 1,
            min_pct         REAL NOT NULL DEFAULT 25,
            statement_day   INTEGER NOT NULL DEFAULT 20,
            created_at      TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS investments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL DEFAULT 1,
            profile_id  INTEGER NOT NULL DEFAULT 1,
            name        TEXT NOT NULL,
            itype       TEXT NOT NULL,
            symbol      TEXT NOT NULL DEFAULT '',
            quantity    REAL NOT NULL DEFAULT 0,
            buy_price   REAL NOT NULL DEFAULT 0,
            buy_date    TEXT NOT NULL,
            note        TEXT DEFAULT '',
            created_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS recurring (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL DEFAULT 1,
            profile_id   INTEGER NOT NULL DEFAULT 1,
            type         TEXT NOT NULL,
            amount       REAL NOT NULL,
            category     TEXT NOT NULL,
            description  TEXT DEFAULT '',
            day_of_month INTEGER NOT NULL DEFAULT 1,
            active       INTEGER NOT NULL DEFAULT 1,
            created_at   TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_txn_profile_date ON transactions(profile_id, date);
        """)
        # Migration: add missing columns to existing databases
        migrations = [
            ("users",        "email",      "TEXT NOT NULL DEFAULT ''"),
            ("transactions", "user_id",    "INTEGER NOT NULL DEFAULT 1"),
            ("transactions", "profile_id", "INTEGER NOT NULL DEFAULT 1"),
            ("budgets",      "user_id",    "INTEGER NOT NULL DEFAULT 1"),
            ("budgets",      "profile_id", "INTEGER NOT NULL DEFAULT 1"),
            ("cards",        "user_id",    "INTEGER NOT NULL DEFAULT 1"),
            ("cards",        "profile_id", "INTEGER NOT NULL DEFAULT 1"),
            ("investments",  "user_id",    "INTEGER NOT NULL DEFAULT 1"),
            ("investments",  "profile_id", "INTEGER NOT NULL DEFAULT 1"),
            ("recurring",    "user_id",    "INTEGER NOT NULL DEFAULT 1"),
            ("recurring",    "profile_id", "INTEGER NOT NULL DEFAULT 1"),
        ]
        for table, col, col_def in migrations:
            try:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
                log.info("Migration: added %s.%s", table, col)
            except sqlite3.OperationalError:
                pass  # column already exists
        # Ensure every user has at least a default "Şahıs" profile
        users = con.execute("SELECT id FROM users").fetchall()
        for u in users:
            uid = u[0]
            has_profile = con.execute("SELECT id FROM profiles WHERE user_id=?", (uid,)).fetchone()
            if not has_profile:
                con.execute(
                    "INSERT INTO profiles (user_id,name,type,created_at) VALUES (?,?,?,?)",
                    (uid, "Şahıs", "sahis", datetime.now().isoformat())
                )
        con.commit()

def row_to_dict(r): return dict(r)
def today_str():    return date.today().isoformat()

# ── EMAIL ─────────────────────────────────────────────────────────────────────

def _smtp_send(msg):
    """Send an email message via Gmail SMTP. Returns True on success."""
    if not MAIL_FROM or not MAIL_PASSWORD:
        log.warning("Mail credentials not configured — skipping email send")
        return False
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as s:
            s.ehlo(); s.starttls(); s.ehlo()
            s.login(MAIL_FROM, MAIL_PASSWORD)
            s.sendmail(MAIL_FROM, msg["To"], msg.as_string())
        log.info("Email sent to %s", msg["To"])
        return True
    except Exception as exc:
        log.error("Email send failed: %s", exc)
        return False

def send_reset_email(to_email, username, token):
    reset_url = f"{APP_URL}/reset-password/{token}"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🦔 Kirpi — Şifre Sıfırlama"
    msg["From"]    = f"Kirpi Nakit Akışı <{MAIL_FROM}>"
    msg["To"]      = to_email

    text = f"Merhaba {username},\n\nŞifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:\n{reset_url}\n\nBu bağlantı 1 saat geçerlidir.\n\nEğer bu talebi siz yapmadıysanız bu maili görmezden gelebilirsiniz."

    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0a0c12;font-family:'Inter',system-ui,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0c12;padding:40px 20px">
  <tr><td align="center">
    <table width="520" cellpadding="0" cellspacing="0" style="background:#111318;border:1px solid #1e2233;border-radius:16px;overflow:hidden">
      <tr><td style="background:linear-gradient(135deg,#6366f1,#a855f7);padding:32px;text-align:center">
        <div style="font-size:40px;margin-bottom:8px">🦔</div>
        <h1 style="color:#fff;font-size:1.4rem;font-weight:800;margin:0">Kirpi</h1>
        <p style="color:rgba(255,255,255,.7);font-size:.85rem;margin:4px 0 0">Nakit Akışı Takibi</p>
      </td></tr>
      <tr><td style="padding:36px 40px">
        <h2 style="color:#e2e8f0;font-size:1.1rem;font-weight:700;margin:0 0 12px">Merhaba, {username} 👋</h2>
        <p style="color:#94a3b8;font-size:.9rem;line-height:1.7;margin:0 0 28px">
          Kirpi hesabınız için bir <strong style="color:#e2e8f0">şifre sıfırlama talebi</strong> aldık.<br>
          Şifrenizi sıfırlamak için aşağıdaki butona tıklayın.
        </p>
        <table cellpadding="0" cellspacing="0" style="margin:0 auto 28px">
          <tr><td style="background:#6366f1;border-radius:10px;text-align:center">
            <a href="{reset_url}" style="display:block;padding:14px 36px;color:#fff;font-size:.95rem;font-weight:700;text-decoration:none">Şifremi Sıfırla</a>
          </td></tr>
        </table>
        <div style="background:#1a1d26;border:1px solid #2a2f45;border-radius:8px;padding:14px 16px;margin-bottom:24px">
          <p style="color:#64748b;font-size:.78rem;margin:0 0 6px">Ya da bu bağlantıyı tarayıcınıza yapıştırın:</p>
          <p style="color:#818cf8;font-size:.76rem;word-break:break-all;margin:0">{reset_url}</p>
        </div>
        <p style="color:#64748b;font-size:.78rem;line-height:1.6;margin:0">
          ⏰ Bu bağlantı <strong style="color:#94a3b8">1 saat</strong> geçerlidir.<br>
          🔒 Eğer bu talebi siz yapmadıysanız bu maili görmezden gelebilirsiniz.
        </p>
      </td></tr>
      <tr><td style="background:#0d0f18;border-top:1px solid #1e2233;padding:20px 40px;text-align:center">
        <p style="color:#475569;font-size:.75rem;margin:0">🦔 Kirpi Nakit Akışı • Otomatik mesaj, lütfen yanıtlamayın.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""

    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html,  "html",  "utf-8"))
    return _smtp_send(msg)

def send_backup_email(to_email):
    """Attach the SQLite DB as a .sql dump and email it."""
    try:
        with sqlite3.connect(DB) as con:
            dump = "\n".join(con.iterdump())
        dump_bytes = dump.encode("utf-8")
    except Exception as exc:
        log.error("Backup dump failed: %s", exc)
        return False

    now_str  = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"kirpi_backup_{now_str}.sql"

    msg = MIMEMultipart()
    msg["Subject"] = f"🦔 Kirpi Yedek — {now_str}"
    msg["From"]    = f"Kirpi Yedekleme <{MAIL_FROM}>"
    msg["To"]      = to_email

    body = MIMEText(
        f"Kirpi veritabanı yedeği — {now_str}\n\n"
        "Bu mail otomatik olarak oluşturulmuştur.\n"
        "Yedeği geri yüklemek için .sql dosyasını bir SQLite istemcisine aktarabilirsiniz.",
        "plain", "utf-8"
    )
    msg.attach(body)

    part = MIMEBase("application", "octet-stream")
    part.set_payload(dump_bytes)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(part)

    return _smtp_send(msg)

def _daily_backup_loop():
    """Background thread: send a DB backup email every 24 hours."""
    time.sleep(30)  # wait for app to fully start
    while True:
        if BACKUP_EMAIL:
            log.info("Running scheduled daily backup...")
            send_backup_email(BACKUP_EMAIL)
        time.sleep(86400)  # 24 hours

# ── AUTH ──────────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({"ok": False, "error": "Giriş gerekli", "auth": False}), 401
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect("/")
    if request.method == "POST":
        username = request.form.get("username","").strip().lower()
        display  = request.form.get("display_name","").strip()
        email    = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        confirm  = request.form.get("confirm","")
        error = None
        if not username or not password or not email:
            error = "Kullanıcı adı, email ve şifre zorunlu"
        elif "@" not in email or "." not in email.split("@")[-1]:
            error = "Geçerli bir email adresi girin"
        elif len(password) < 6:
            error = "Şifre en az 6 karakter olmalı"
        elif password != confirm:
            error = "Şifreler eşleşmiyor"
        if error:
            return AUTH_HTML_render("register", error)
        try:
            with sqlite3.connect(DB) as con:
                con.row_factory = sqlite3.Row
                cur = con.execute(
                    "INSERT INTO users (username,display_name,password_hash,email,created_at) VALUES (?,?,?,?,?)",
                    (username, display or username, generate_password_hash(password), email, datetime.now().isoformat())
                )
                uid = cur.lastrowid
                con.execute(
                    "INSERT INTO profiles (user_id,name,type,created_at) VALUES (?,?,?,?)",
                    (uid, "Şahıs", "sahis", datetime.now().isoformat())
                )
        except sqlite3.IntegrityError:
            return AUTH_HTML_render("register", "Bu kullanıcı adı zaten alınmış")
        return redirect("/login?registered=1")
    return AUTH_HTML_render("register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect("/")
    if request.method == "POST":
        username = request.form.get("username","").strip().lower()
        password = request.form.get("password","")
        with sqlite3.connect(DB) as con:
            con.row_factory = sqlite3.Row
            row = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session["user_id"]  = row["id"]
            session["username"] = row["username"]
            session["display"]  = row["display_name"]
            with sqlite3.connect(DB) as con2:
                con2.row_factory = sqlite3.Row
                prof = con2.execute("SELECT * FROM profiles WHERE user_id=? ORDER BY id LIMIT 1",(row["id"],)).fetchone()
                if prof:
                    session["profile_id"]   = prof["id"]
                    session["profile_name"] = prof["name"]
                    session["profile_type"] = prof["type"]
            return redirect("/")
        return AUTH_HTML_render("login", "Kullanıcı adı veya şifre hatalı")
    msg = "Kayıt başarılı! Şimdi giriş yapabilirsiniz." if request.args.get("registered") else ""
    if request.args.get("reset"):
        msg = "Şifreniz başarıyla güncellendi. Giriş yapabilirsiniz."
    return AUTH_HTML_render("login", msg)

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        identifier = request.form.get("identifier","").strip().lower()
        with sqlite3.connect(DB) as con:
            con.row_factory = sqlite3.Row
            row = con.execute(
                "SELECT * FROM users WHERE username=? OR email=?", (identifier, identifier)
            ).fetchone()
        if row:
            token = secrets.token_urlsafe(32)
            expires = (datetime.now() + timedelta(hours=1)).isoformat()
            with sqlite3.connect(DB) as con:
                con.execute(
                    "INSERT INTO password_reset_tokens (user_id,token,expires_at,created_at) VALUES (?,?,?,?)",
                    (row["id"], token, expires, datetime.now().isoformat())
                )
            sent = send_reset_email(row["email"], row["display_name"] or row["username"], token)
            log.info("Reset email sent=%s for user=%s", sent, row["username"])
        # Always show success to prevent user enumeration
        return AUTH_HTML_render("forgot_sent", "Eğer bu hesap varsa, şifre sıfırlama linki email adresinize gönderildi.")
    return AUTH_HTML_render("forgot")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        tok = con.execute(
            "SELECT * FROM password_reset_tokens WHERE token=? AND used=0", (token,)
        ).fetchone()
    if not tok or datetime.fromisoformat(tok["expires_at"]) < datetime.now():
        return AUTH_HTML_render("reset_invalid", "Bu link geçersiz veya süresi dolmuş.")
    if request.method == "POST":
        password = request.form.get("password","")
        confirm  = request.form.get("confirm","")
        if len(password) < 6:
            return AUTH_HTML_render("reset", "Şifre en az 6 karakter olmalı", token=token)
        if password != confirm:
            return AUTH_HTML_render("reset", "Şifreler eşleşmiyor", token=token)
        with sqlite3.connect(DB) as con:
            con.execute("UPDATE users SET password_hash=? WHERE id=?",
                        (generate_password_hash(password), tok["user_id"]))
            con.execute("UPDATE password_reset_tokens SET used=1 WHERE token=?", (token,))
        return redirect("/login?reset=1")
    return AUTH_HTML_render("reset", token=token)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/api/me")
@login_required
def api_me():
    return jsonify({
        "username":     session.get("username"),
        "display":      session.get("display"),
        "profile_id":   session.get("profile_id"),
        "profile_name": session.get("profile_name"),
        "profile_type": session.get("profile_type"),
    })

def get_pid():
    """Return active profile_id from session (fallback: first profile of user)."""
    pid = session.get("profile_id")
    if not pid:
        uid = session.get("user_id")
        with sqlite3.connect(DB) as con:
            row = con.execute("SELECT id FROM profiles WHERE user_id=? ORDER BY id LIMIT 1",(uid,)).fetchone()
            if row: pid = row[0]; session["profile_id"] = pid
    return pid

# ── PROFILES API ──────────────────────────────────────────────────────────────

@app.route("/api/profiles", methods=["GET"])
@login_required
def list_profiles():
    uid = session["user_id"]
    rows = get_db().execute("SELECT * FROM profiles WHERE user_id=? ORDER BY id",(uid,)).fetchall()
    return jsonify([row_to_dict(r) for r in rows])

@app.route("/api/profiles", methods=["POST"])
@login_required
def add_profile():
    uid = session["user_id"]
    d = request.get_json(force=True)
    name  = d.get("name","").strip()
    ptype = d.get("type","sahis")
    if not name or ptype not in ("sahis","sirket"):
        return jsonify({"ok":False,"error":"Geçersiz veri"}),400
    db = get_db()
    cur = db.execute(
        "INSERT INTO profiles (user_id,name,type,created_at) VALUES (?,?,?,?)",
        (uid, name, ptype, datetime.now().isoformat()))
    db.commit()
    return jsonify({"ok":True,"id":cur.lastrowid,"name":name,"type":ptype})

@app.route("/api/profiles/<int:pid>/switch", methods=["POST"])
@login_required
def switch_profile(pid):
    uid = session["user_id"]
    db  = get_db()
    prof = db.execute("SELECT * FROM profiles WHERE id=? AND user_id=?",(pid,uid)).fetchone()
    if not prof: return jsonify({"ok":False,"error":"Profil bulunamadı"}),404
    session["profile_id"]   = prof["id"]
    session["profile_name"] = prof["name"]
    session["profile_type"] = prof["type"]
    return jsonify({"ok":True,"name":prof["name"],"type":prof["type"]})

@app.route("/api/profiles/<int:pid>", methods=["DELETE"])
@login_required
def del_profile(pid):
    uid = session["user_id"]
    db  = get_db()
    count = db.execute("SELECT COUNT(*) FROM profiles WHERE user_id=?",(uid,)).fetchone()[0]
    if count <= 1: return jsonify({"ok":False,"error":"En az bir profil olmalı"}),400
    db.execute("DELETE FROM profiles WHERE id=? AND user_id=?",(pid,uid))
    db.commit()
    if session.get("profile_id") == pid:
        first = db.execute("SELECT * FROM profiles WHERE user_id=? ORDER BY id LIMIT 1",(uid,)).fetchone()
        if first:
            session["profile_id"]   = first["id"]
            session["profile_name"] = first["name"]
            session["profile_type"] = first["type"]
    return jsonify({"ok":True})

def month_range(year, month):
    from calendar import monthrange
    _, last = monthrange(year, month)
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last:02d}"

# ── CRUD ──────────────────────────────────────────────────────────────────────

@app.route("/api/transactions", methods=["GET"])
@login_required
def list_transactions():
    db    = get_db()
    year  = request.args.get("year",  type=int)
    month = request.args.get("month", type=int)
    pid   = get_pid()
    q     = "SELECT * FROM transactions WHERE profile_id=?"
    params = [pid]
    if year and month:
        s, e = month_range(year, month)
        q += " AND date BETWEEN ? AND ?"; params += [s, e]
    elif year:
        q += " AND date LIKE ?"; params.append(f"{year}-%")
    q += " ORDER BY date DESC, id DESC"
    return jsonify([row_to_dict(r) for r in db.execute(q, params).fetchall()])

@app.route("/api/transactions", methods=["POST"])
@login_required
def add_transaction():
    uid = session["user_id"]; pid = get_pid()
    d = request.get_json(force=True)
    ttype = d.get("type"); amount = float(d.get("amount", 0))
    cat = d.get("category",""); desc = d.get("description",""); dt = d.get("date", today_str())
    if ttype not in ("gelir","gider") or amount <= 0 or not cat:
        return jsonify({"ok": False, "error": "Geçersiz veri"}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO transactions (user_id,profile_id,type,amount,category,description,date,created_at) VALUES (?,?,?,?,?,?,?,?)",
        (uid, pid, ttype, amount, cat, desc, dt, datetime.now().isoformat()))
    db.commit()
    return jsonify({"ok": True, "id": cur.lastrowid})

@app.route("/api/transactions/<int:tid>", methods=["PUT"])
@login_required
def update_transaction(tid):
    pid = get_pid()
    d = request.get_json(force=True)
    fields, params = [], []
    for col in ("type","amount","category","description","date"):
        if col in d:
            fields.append(f"{col}=?")
            params.append(float(d[col]) if col == "amount" else d[col])
    if not fields: return jsonify({"ok": False}), 400
    params += [tid, pid]
    get_db().execute(f"UPDATE transactions SET {','.join(fields)} WHERE id=? AND profile_id=?", params)
    get_db().commit()
    return jsonify({"ok": True})

@app.route("/api/transactions/<int:tid>", methods=["DELETE"])
@login_required
def del_transaction(tid):
    pid = get_pid()
    get_db().execute("DELETE FROM transactions WHERE id=? AND profile_id=?", (tid, pid)); get_db().commit()
    return jsonify({"ok": True})

@app.route("/api/transactions/bulk-delete", methods=["POST"])
@login_required
def bulk_delete():
    pid = get_pid()
    ids = request.get_json(force=True)
    if not isinstance(ids, list): return jsonify({"ok": False}), 400
    placeholders = ",".join("?" * len(ids))
    get_db().execute(f"DELETE FROM transactions WHERE id IN ({placeholders}) AND profile_id=?", ids + [pid])
    get_db().commit()
    return jsonify({"ok": True, "deleted": len(ids)})

@app.route("/api/summary")
@login_required
def summary():
    pid   = get_pid()
    db    = get_db()
    year  = request.args.get("year",  date.today().year,  type=int)
    month = request.args.get("month", date.today().month, type=int)
    start, end = month_range(year, month)
    rows = db.execute(
        "SELECT type,category,SUM(amount) as total FROM transactions "
        "WHERE profile_id=? AND date BETWEEN ? AND ? GROUP BY type,category", (pid, start, end)).fetchall()
    gelir_total = gider_total = 0.0
    gelir_cats  = {}; gider_cats = {}
    for r in rows:
        if r["type"]=="gelir": gelir_total+=r["total"]; gelir_cats[r["category"]]=round(r["total"],2)
        else:                   gider_total+=r["total"]; gider_cats[r["category"]]=round(r["total"],2)
    bar = []
    for m in range(1,13):
        s,e2 = month_range(year,m)
        totals = db.execute("SELECT type,SUM(amount) as t FROM transactions WHERE profile_id=? AND date BETWEEN ? AND ? GROUP BY type",(pid,s,e2)).fetchall()
        g_val  = next((r["t"] for r in totals if r["type"]=="gelir"),0)
        ex_val = next((r["t"] for r in totals if r["type"]=="gider"),0)
        bar.append({"month":m,"gelir":round(g_val,2),"gider":round(ex_val,2)})
    bal = db.execute("SELECT SUM(CASE WHEN type='gelir' THEN amount ELSE -amount END) as b FROM transactions WHERE profile_id=?",(pid,)).fetchone()
    budgets = {r["category"]:r["limit_"] for r in db.execute("SELECT * FROM budgets WHERE profile_id=?",(pid,)).fetchall()}
    return jsonify({"gelir":round(gelir_total,2),"gider":round(gider_total,2),
                    "net":round(gelir_total-gider_total,2),"balance":round(bal["b"] or 0,2),
                    "gelir_cats":gelir_cats,"gider_cats":gider_cats,"bar":bar,"budgets":budgets})

@app.route("/api/budgets", methods=["POST"])
@login_required
def set_budget():
    uid = session["user_id"]; pid = get_pid()
    d = request.get_json(force=True)
    cat = d.get("category",""); limit = float(d.get("limit",0))
    if not cat or limit<=0: return jsonify({"ok":False}),400
    db = get_db()
    db.execute("INSERT INTO budgets(user_id,profile_id,category,limit_) VALUES(?,?,?,?) ON CONFLICT(profile_id,category) DO UPDATE SET limit_=excluded.limit_",(uid,pid,cat,limit))
    db.commit(); return jsonify({"ok":True})

@app.route("/api/categories")
@login_required
def categories():
    return jsonify({"gelir":GELIR_CATS,"gider":GIDER_CATS,"all":ALL_CATS})

@app.route("/api/motivation")
@login_required
def motivation():
    db = get_db(); today = date.today()
    year, month = today.year, today.month
    start, end  = month_range(year, month)
    pid = get_pid()
    rows = db.execute("SELECT type,SUM(amount) as t FROM transactions WHERE profile_id=? AND date BETWEEN ? AND ? GROUP BY type",(pid,start,end)).fetchall()
    gelir  = next((r["t"] for r in rows if r["type"]=="gelir"),0) or 0
    gider  = next((r["t"] for r in rows if r["type"]=="gider"),0) or 0
    net    = gelir - gider
    from calendar import monthrange as mr
    _, days_in_month = mr(year,month)
    days_passed = today.day; days_left = days_in_month - days_passed
    daily_spend = gider / max(days_passed,1)
    projected   = daily_spend * days_in_month
    bal = (db.execute("SELECT SUM(CASE WHEN type='gelir' THEN amount ELSE -amount END) as b FROM transactions WHERE profile_id=?",(pid,)).fetchone()["b"] or 0)
    budgets = {r["category"]:r["limit_"] for r in db.execute("SELECT * FROM budgets WHERE profile_id=?",(pid,)).fetchall()}
    top = db.execute("SELECT category,SUM(amount) as t FROM transactions WHERE profile_id=? AND date BETWEEN ? AND ? AND type='gider' GROUP BY category ORDER BY t DESC LIMIT 1",(pid,start,end)).fetchall()
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
            sp=(db.execute("SELECT SUM(amount) as t FROM transactions WHERE profile_id=? AND date BETWEEN ? AND ? AND type='gider' AND category=?",(pid,start,end,cat)).fetchone()["t"] or 0)
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
@login_required
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

# ── CARDS ─────────────────────────────────────────────────────────────────────

@app.route("/api/cards", methods=["GET"])
@login_required
def list_cards():
    pid = get_pid()
    return jsonify([row_to_dict(r) for r in get_db().execute("SELECT * FROM cards WHERE profile_id=? ORDER BY bank_name",(pid,)).fetchall()])

@app.route("/api/cards", methods=["POST"])
@login_required
def add_card():
    uid = session["user_id"]; pid = get_pid()
    d = request.get_json(force=True)
    bank = d.get("bank_name","").strip(); card = d.get("card_name","").strip()
    owner = d.get("owner","").strip()
    limit = float(d.get("limit_",0)); used = float(d.get("used_",0))
    due_day = int(d.get("due_day",1)); min_pct = float(d.get("min_pct",25))
    stmt_day = int(d.get("statement_day",20))
    if not bank or limit <= 0: return jsonify({"ok":False}), 400
    db = get_db()
    cur = db.execute("INSERT INTO cards (user_id,profile_id,bank_name,card_name,owner,limit_,used_,due_day,min_pct,statement_day,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                     (uid,pid,bank,card,owner,limit,used,due_day,min_pct,stmt_day,datetime.now().isoformat()))
    db.commit(); return jsonify({"ok":True,"id":cur.lastrowid})

@app.route("/api/cards/<int:cid>", methods=["PUT"])
@login_required
def update_card(cid):
    pid = get_pid()
    d = request.get_json(force=True); fields=[]; params=[]
    for col in ("bank_name","card_name","limit_","used_","due_day","min_pct","statement_day"):
        if col in d:
            fields.append(f"{col}=?")
            params.append(float(d[col]) if col in ("limit_","used_","min_pct") else int(d[col]) if col in ("due_day","statement_day") else d[col])
    if not fields: return jsonify({"ok":False}),400
    params += [cid, pid]
    get_db().execute(f"UPDATE cards SET {','.join(fields)} WHERE id=? AND profile_id=?",params); get_db().commit()
    return jsonify({"ok":True})

@app.route("/api/cards/<int:cid>", methods=["DELETE"])
@login_required
def del_card(cid):
    pid = get_pid()
    get_db().execute("DELETE FROM cards WHERE id=? AND profile_id=?",(cid,pid)); get_db().commit()
    return jsonify({"ok":True})

# ── RATES & INVESTMENTS ───────────────────────────────────────────────────────

_rates_cache = {"data": None, "ts": 0}
_rates_lock  = threading.Lock()

def _fetch_rates():
    """Fetch USD/TRY, EUR/TRY, Gold/g TRY from free APIs."""
    try:
        # Exchange rates: 1 TRY = X of each
        r = requests.get("https://open.er-api.com/v6/latest/TRY", timeout=8).json()
        rates = r.get("rates", {})
        usd_try = round(1 / rates["USD"], 4) if rates.get("USD") else None
        eur_try = round(1 / rates["EUR"], 4) if rates.get("EUR") else None
        gbp_try = round(1 / rates["GBP"], 4) if rates.get("GBP") else None
    except Exception:
        usd_try = eur_try = gbp_try = None

    gold_try = None
    try:
        # Gold spot in USD/oz → convert to TRY/gram
        g = requests.get("https://api.metals.live/v1/spot/gold", timeout=8).json()
        gold_usd_oz = float(g[0]["price"]) if isinstance(g, list) and g else None
        if gold_usd_oz and usd_try:
            gold_try = round(gold_usd_oz / 31.1035 * usd_try, 2)
    except Exception:
        pass

    return {
        "usd_try": usd_try,
        "eur_try": eur_try,
        "gbp_try": gbp_try,
        "gold_try": gold_try,   # TRY per gram
        "updated": datetime.now().strftime("%H:%M")
    }

def get_rates():
    with _rates_lock:
        if time.time() - _rates_cache["ts"] > 300 or not _rates_cache["data"]:
            _rates_cache["data"] = _fetch_rates()
            _rates_cache["ts"]   = time.time()
        return _rates_cache["data"]

@app.route("/api/rates")
@login_required
def api_rates():
    return jsonify(get_rates())

@app.route("/api/investments", methods=["GET"])
@login_required
def list_investments():
    pid = get_pid()
    rows = get_db().execute("SELECT * FROM investments WHERE profile_id=? ORDER BY buy_date DESC",(pid,)).fetchall()
    return jsonify([row_to_dict(r) for r in rows])

@app.route("/api/investments", methods=["POST"])
@login_required
def add_investment():
    uid = session["user_id"]; pid = get_pid()
    d = request.get_json(force=True)
    name     = d.get("name","").strip()
    itype    = d.get("itype","")
    symbol   = d.get("symbol","").strip().upper()
    quantity = float(d.get("quantity", 0))
    buy_price= float(d.get("buy_price", 0))
    buy_date = d.get("buy_date", today_str())
    note     = d.get("note","")
    if not name or itype not in ("doviz","altin","fon","hisse") or quantity <= 0 or buy_price <= 0:
        return jsonify({"ok": False, "error": "Geçersiz veri"}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO investments (user_id,profile_id,name,itype,symbol,quantity,buy_price,buy_date,note,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (uid, pid, name, itype, symbol, quantity, buy_price, buy_date, note, datetime.now().isoformat()))
    db.commit()
    return jsonify({"ok": True, "id": cur.lastrowid})

@app.route("/api/investments/<int:iid>", methods=["DELETE"])
@login_required
def del_investment(iid):
    pid = get_pid()
    get_db().execute("DELETE FROM investments WHERE id=? AND profile_id=?", (iid,pid)); get_db().commit()
    return jsonify({"ok": True})

@app.route("/api/investments/value", methods=["GET"])
@login_required
def investment_values():
    pid   = get_pid()
    rows  = get_db().execute("SELECT * FROM investments WHERE profile_id=?",(pid,)).fetchall()
    rates = get_rates()
    result = []
    for row in rows:
        r = row_to_dict(row)
        cur_price = None
        cur_try   = None

        if r["itype"] == "doviz":
            sym = r["symbol"].upper()
            key = f"{sym.lower()}_try"
            rate = rates.get(key)
            if rate:
                cur_price = rate
                cur_try   = round(r["quantity"] * rate, 2)

        elif r["itype"] == "altin":
            if rates.get("gold_try"):
                cur_price = rates["gold_try"]
                cur_try   = round(r["quantity"] * rates["gold_try"], 2)

        elif r["itype"] in ("fon", "hisse"):
            # manual price: user must provide current_price via query
            cp = request.args.get(f"price_{r['id']}", type=float)
            if cp:
                cur_price = cp
                cur_try   = round(r["quantity"] * cp, 2)

        buy_try    = round(r["quantity"] * r["buy_price"], 2)
        profit_try = round(cur_try - buy_try, 2) if cur_try is not None else None
        profit_pct = round((cur_try - buy_try) / buy_try * 100, 2) if cur_try and buy_try else None

        r.update({
            "cur_price":  cur_price,
            "cur_try":    cur_try,
            "buy_try":    buy_try,
            "profit_try": profit_try,
            "profit_pct": profit_pct,
        })
        result.append(r)
    return jsonify(result)

@app.route("/api/investments/<int:iid>/book-income", methods=["POST"])
@login_required
def book_investment_income(iid):
    """Add investment profit as a gelir transaction for this month."""
    d = request.get_json(force=True)
    amount = float(d.get("amount", 0))
    cat    = d.get("category", "Yatırım / Temettü")
    desc   = d.get("description", "Yatırım Getirisi")
    dt     = d.get("date", today_str())
    if amount <= 0: return jsonify({"ok": False}), 400
    db = get_db()
    uid = session["user_id"]; pid = get_pid()
    cur = db.execute(
        "INSERT INTO transactions (user_id,profile_id,type,amount,category,description,date,created_at) VALUES (?,?,?,?,?,?,?,?)",
        (uid, pid, "gelir", amount, cat, desc, dt, datetime.now().isoformat()))
    db.commit()
    return jsonify({"ok": True, "id": cur.lastrowid})

@app.route("/api/tefas/<fon_kod>")
@login_required
def tefas_fon(fon_kod):
    """Fetch latest NAV for a TEFAS fund code."""
    try:
        today_s = date.today().strftime("%d.%m.%Y")
        resp = requests.post(
            "https://www.tefas.gov.tr/api/DB/BindHistoryInfo",
            data={"fontip":"YAT","sfonkod":fon_kod.upper(),"bastarih":today_s,"bittarih":today_s},
            headers={"Referer":"https://www.tefas.gov.tr/"},
            timeout=8)
        data = resp.json().get("data", [])
        if not data:
            # try yesterday
            from datetime import timedelta
            yday = (date.today() - timedelta(days=1)).strftime("%d.%m.%Y")
            resp = requests.post(
                "https://www.tefas.gov.tr/api/DB/BindHistoryInfo",
                data={"fontip":"YAT","sfonkod":fon_kod.upper(),"bastarih":yday,"bittarih":yday},
                headers={"Referer":"https://www.tefas.gov.tr/"},
                timeout=8)
            data = resp.json().get("data", [])
        if data:
            row = data[0]
            return jsonify({"ok":True,"fiyat":float(row.get("FIYAT",0)),"tarih":row.get("TARIH",""),"fon":fon_kod.upper()})
        return jsonify({"ok":False,"error":"Fon bulunamadı"})
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)})

# ── RECURRING ────────────────────────────────────────────────────────────────

@app.route("/api/recurring", methods=["GET"])
@login_required
def list_recurring():
    pid = get_pid()
    rows = get_db().execute("SELECT * FROM recurring WHERE profile_id=? ORDER BY type DESC, day_of_month",(pid,)).fetchall()
    return jsonify([row_to_dict(r) for r in rows])

@app.route("/api/recurring", methods=["POST"])
@login_required
def add_recurring():
    uid = session["user_id"]; pid = get_pid()
    d = request.get_json(force=True)
    ttype = d.get("type"); amount = float(d.get("amount", 0))
    cat = d.get("category",""); desc = d.get("description","")
    day = int(d.get("day_of_month", 1))
    if ttype not in ("gelir","gider") or amount <= 0 or not cat or not (1 <= day <= 31):
        return jsonify({"ok": False, "error": "Geçersiz veri"}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO recurring (user_id,profile_id,type,amount,category,description,day_of_month,active,created_at) VALUES (?,?,?,?,?,?,?,1,?)",
        (uid, pid, ttype, amount, cat, desc, day, datetime.now().isoformat()))
    db.commit()
    return jsonify({"ok": True, "id": cur.lastrowid})

@app.route("/api/recurring/<int:rid>", methods=["DELETE"])
@login_required
def del_recurring(rid):
    pid = get_pid()
    get_db().execute("DELETE FROM recurring WHERE id=? AND profile_id=?", (rid,pid)); get_db().commit()
    return jsonify({"ok": True})

@app.route("/api/recurring/<int:rid>", methods=["PUT"])
@login_required
def update_recurring(rid):
    pid = get_pid()
    d = request.get_json(force=True)
    fields, params = [], []
    for col in ("type","amount","category","description","day_of_month","active"):
        if col in d:
            fields.append(f"{col}=?")
            val = float(d[col]) if col == "amount" else int(d[col]) if col in ("day_of_month","active") else d[col]
            params.append(val)
    if not fields: return jsonify({"ok": False}), 400
    params += [rid, pid]
    get_db().execute(f"UPDATE recurring SET {','.join(fields)} WHERE id=? AND profile_id=?", params)
    get_db().commit()
    return jsonify({"ok": True})

@app.route("/api/recurring/apply", methods=["POST"])
@login_required
def apply_recurring():
    uid = session["user_id"]; pid = get_pid()
    d = request.get_json(force=True)
    year   = int(d.get("year",  date.today().year))
    month  = d.get("month")
    months = [int(month)] if month else list(range(1, 13))

    db        = get_db()
    templates = db.execute("SELECT * FROM recurring WHERE profile_id=? AND active=1",(pid,)).fetchall()
    created   = 0; skipped = 0

    from calendar import monthrange
    for tpl in templates:
        for m in months:
            _, last_day = monthrange(year, m)
            day = min(tpl["day_of_month"], last_day)
            dt  = f"{year:04d}-{m:02d}-{day:02d}"
            exists = db.execute(
                "SELECT id FROM transactions WHERE profile_id=? AND type=? AND category=? AND description=? AND date=? AND amount=?",
                (pid, tpl["type"], tpl["category"], tpl["description"], dt, tpl["amount"])
            ).fetchone()
            if exists: skipped += 1; continue
            db.execute(
                "INSERT INTO transactions (user_id,profile_id,type,amount,category,description,date,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (uid, pid, tpl["type"], tpl["amount"], tpl["category"], tpl["description"], dt, datetime.now().isoformat()))
            created += 1

    db.commit()
    return jsonify({"ok": True, "created": created, "skipped": skipped})

@app.route("/api/backup/download")
@login_required
def backup_download():
    """Download the full DB as a SQL dump."""
    try:
        with sqlite3.connect(DB) as con:
            dump = "\n".join(con.iterdump())
        now_str  = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"kirpi_backup_{now_str}.sql"
        return dump, 200, {
            "Content-Type":        "application/octet-stream",
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

@app.route("/api/import/confirm", methods=["POST"])
@login_required
def import_confirm():
    uid=session["user_id"]; pid=get_pid()
    rows=request.get_json(force=True)
    if not isinstance(rows,list): return jsonify({"ok":False}),400
    db=get_db(); now=datetime.now().isoformat(); count=0
    for r in rows:
        if not r.get("skip") and r.get("amount",0)>0:
            db.execute("INSERT INTO transactions (user_id,profile_id,type,amount,category,description,date,created_at) VALUES (?,?,?,?,?,?,?,?)",
                       (uid,pid,r["type"],r["amount"],r["category"],r.get("description",""),r["date"],now))
            count+=1
    db.commit(); return jsonify({"ok":True,"imported":count})

# ── HTML ──────────────────────────────────────────────────────────────────────

AUTH_HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0a0c12">
<title>Kirpi — __MODE_TITLE__</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0c12;color:#e2e8f0;font-family:'Inter',system-ui,sans-serif;
  min-height:100vh;display:grid;grid-template-columns:1fr 1fr;align-items:stretch}
@media(max-width:700px){body{grid-template-columns:1fr}}
.hero{background:linear-gradient(145deg,#0f1525 0%,#161c35 50%,#0e1520 100%);
  display:flex;flex-direction:column;align-items:center;justify-content:center;padding:48px 40px;
  position:relative;overflow:hidden}
@media(max-width:700px){.hero{display:none}}
.hero-title{font-size:2rem;font-weight:900;letter-spacing:-.04em;margin-bottom:8px;
  background:linear-gradient(135deg,#818cf8,#a78bfa,#6ee7b7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero-sub{font-size:.9rem;color:#64748b;text-align:center;max-width:280px;line-height:1.6;margin-bottom:32px}
.hero-pills{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;max-width:300px}
.pill{background:#1e2233;border:1px solid #2a2f45;border-radius:20px;padding:6px 14px;
  font-size:.75rem;color:#94a3b8;display:flex;align-items:center;gap:6px}
.right{display:flex;align-items:center;justify-content:center;padding:40px 36px;background:#0d0f18}
.box{background:#111318;border:1px solid #1e2233;border-radius:16px;padding:40px 36px;
  width:100%;max-width:400px;box-shadow:0 20px 60px rgba(0,0,0,.6)}
.logo{text-align:center;margin-bottom:32px}
.logo img{width:64px;height:64px;border-radius:16px;margin-bottom:12px}
.logo h1{font-size:1.4rem;font-weight:800;letter-spacing:-.02em}
.logo p{font-size:.82rem;color:#64748b;margin-top:4px}
label{display:block;font-size:.78rem;color:#94a3b8;margin-bottom:5px;font-weight:500}
input{width:100%;background:#1a1d26;border:1px solid #2a2f45;color:#e2e8f0;
  padding:12px 14px;border-radius:9px;font-size:.9rem;outline:none;margin-bottom:14px;
  font-family:inherit;transition:.15s}
input:focus{border-color:#6366f1}
.btn{width:100%;padding:13px;background:#6366f1;color:#fff;border:none;border-radius:9px;
  font-size:.92rem;font-weight:700;cursor:pointer;transition:.2s;margin-top:4px}
.btn:hover{background:#4f46e5}
.msg{text-align:center;font-size:.82rem;padding:10px 14px;border-radius:8px;margin-bottom:16px}
.msg.err{background:#ef444418;color:#ef4444;border:1px solid #ef444433}
.msg.ok{background:#22c55e18;color:#22c55e;border:1px solid #22c55e33}
.link{text-align:center;margin-top:18px;font-size:.82rem;color:#64748b}
.link a{color:#818cf8;text-decoration:none;font-weight:600}
.link a:hover{color:#a5b4fc}
</style>
</head>
<body>

<!-- HERO (sol taraf) -->
<div class="hero">
  <!-- Arka plan parçacıklar -->
  <svg style="position:absolute;top:0;left:0;width:100%;height:100%;opacity:.12" viewBox="0 0 500 600" xmlns="http://www.w3.org/2000/svg">
    <circle cx="80" cy="120" r="60" fill="#6366f1"/><circle cx="420" cy="80" r="40" fill="#a855f7"/>
    <circle cx="350" cy="300" r="80" fill="#6366f1"/><circle cx="60" cy="450" r="50" fill="#8b5cf6"/>
    <circle cx="450" cy="500" r="35" fill="#a855f7"/>
  </svg>

  <!-- Finans dashboard illüstrasyonu -->
  <svg width="280" height="220" viewBox="0 0 280 220" style="margin-bottom:28px;filter:drop-shadow(0 8px 32px #6366f140)">
    <!-- Kart arka planı -->
    <rect x="20" y="10" width="240" height="200" rx="16" fill="#1a1d26" stroke="#2a2f45" stroke-width="1"/>
    <!-- Gelir bar -->
    <rect x="40" y="120" width="30" height="70" rx="6" fill="#22c55e" opacity=".8"/>
    <rect x="80" y="90" width="30" height="100" rx="6" fill="#22c55e" opacity=".9"/>
    <rect x="120" y="100" width="30" height="90" rx="6" fill="#22c55e"/>
    <rect x="160" y="70" width="30" height="120" rx="6" fill="#22c55e" opacity=".85"/>
    <rect x="200" y="85" width="30" height="105" rx="6" fill="#22c55e" opacity=".9"/>
    <!-- Gider bar overlay -->
    <rect x="40" y="150" width="30" height="40" rx="6" fill="#ef4444" opacity=".7"/>
    <rect x="80" y="140" width="30" height="50" rx="6" fill="#ef4444" opacity=".7"/>
    <rect x="120" y="145" width="30" height="45" rx="6" fill="#ef4444" opacity=".65"/>
    <rect x="160" y="130" width="30" height="60" rx="6" fill="#ef4444" opacity=".7"/>
    <rect x="200" y="135" width="30" height="55" rx="6" fill="#ef4444" opacity=".7"/>
    <!-- Trend çizgi -->
    <polyline points="55,115 95,82 135,95 175,62 215,78" stroke="#818cf8" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="55" cy="115" r="4" fill="#818cf8"/><circle cx="95" cy="82" r="4" fill="#818cf8"/>
    <circle cx="135" cy="95" r="4" fill="#818cf8"/><circle cx="175" cy="62" r="4" fill="#818cf8"/>
    <circle cx="215" cy="78" r="5" fill="#818cf8" stroke="#1a1d26" stroke-width="2"/>
    <!-- Üst bilgi -->
    <text x="40" y="42" font-family="system-ui" font-size="11" fill="#64748b">Bu Ay Net</text>
    <text x="40" y="60" font-family="system-ui" font-size="18" font-weight="800" fill="#22c55e">+₺23.400</text>
    <!-- Kirpi ikonu sağ üst -->
    <text x="210" y="48" font-size="28">🦔</text>
    <!-- Alt göstergeler -->
    <rect x="40" y="200" width="8" height="8" rx="2" fill="#22c55e"/>
    <text x="52" y="208" font-family="system-ui" font-size="9" fill="#64748b">Gelir</text>
    <rect x="95" y="200" width="8" height="8" rx="2" fill="#ef4444"/>
    <text x="107" y="208" font-family="system-ui" font-size="9" fill="#64748b">Gider</text>
    <rect x="150" y="200" width="8" height="8" rx="2" fill="#818cf8"/>
    <text x="162" y="208" font-family="system-ui" font-size="9" fill="#64748b">Trend</text>
  </svg>

  <div class="hero-title">🦔 Kirpi</div>
  <div class="hero-sub">Gelirin, giderin, yatırımın ve kartların tek ekranda</div>
  <div class="hero-pills">
    <div class="pill">📊 Dashboard</div>
    <div class="pill">💳 Kart Takibi</div>
    <div class="pill">📈 Yatırım</div>
    <div class="pill">🔁 Düzenli İşlem</div>
    <div class="pill">📂 Banka CSV</div>
    <div class="pill">🎯 Bütçe</div>
  </div>
</div>

<!-- FORM (sağ taraf) -->
<div class="right">
<div class="box">
  <div class="logo">
    <img src="/icon.svg" alt="Kirpi">
    <h1>🦔 Kirpi</h1>
    <p>Nakit Akışı Takibi</p>
  </div>

  <!-- __FORM_CONTENT__ -->
</div>
</div><!-- /right -->
</body>
</html>"""

def AUTH_HTML_render(mode, msg="", token=None):
    ok_modes  = {"forgot_sent", "reset_invalid"}
    is_ok     = msg and (mode in ok_modes or msg.startswith("Kayıt") or msg.startswith("Şifreniz"))
    msg_html  = f'<div class="msg {"ok" if is_ok else "err"}">{msg}</div>' if msg else ""

    titles = {
        "register":    "Hesap Oluştur",
        "login":       "Giriş Yap",
        "forgot":      "Şifremi Unuttum",
        "forgot_sent": "Mail Gönderildi",
        "reset":       "Yeni Şifre Belirle",
        "reset_invalid": "Link Geçersiz",
    }
    page_title = titles.get(mode, "Kirpi")

    if mode == "register":
        form = f"""
    <h2 style="font-size:1.1rem;font-weight:700;margin-bottom:20px;text-align:center">Hesap Oluştur</h2>
    {msg_html}
    <form method="POST" action="/register">
      <label>Ad Soyad</label>
      <input type="text" name="display_name" placeholder="Ad Soyad" autocomplete="name">
      <label>Kullanıcı Adı</label>
      <input type="text" name="username" placeholder="kullanici_adi" required autocomplete="username">
      <label>Email</label>
      <input type="email" name="email" placeholder="ornek@gmail.com" required autocomplete="email">
      <label>Şifre <span style="color:#64748b">(en az 6 karakter)</span></label>
      <input type="password" name="password" required autocomplete="new-password">
      <label>Şifre Tekrar</label>
      <input type="password" name="confirm" required autocomplete="new-password">
      <button class="btn" type="submit">Kayıt Ol</button>
    </form>
    <div class="link">Zaten hesabın var mı? <a href="/login">Giriş Yap</a></div>"""

    elif mode == "login":
        form = f"""
    <h2 style="font-size:1.1rem;font-weight:700;margin-bottom:20px;text-align:center">Giriş Yap</h2>
    {msg_html}
    <form method="POST" action="/login">
      <label>Kullanıcı Adı</label>
      <input type="text" name="username" required autocomplete="username">
      <label>Şifre</label>
      <input type="password" name="password" required autocomplete="current-password">
      <button class="btn" type="submit">Giriş Yap</button>
    </form>
    <div class="link" style="margin-top:12px"><a href="/forgot-password">Şifremi unuttum</a></div>
    <div class="link">Hesabın yok mu? <a href="/register">Kayıt Ol</a></div>"""

    elif mode == "forgot":
        form = f"""
    <h2 style="font-size:1.1rem;font-weight:700;margin-bottom:8px;text-align:center">Şifremi Unuttum</h2>
    <p style="text-align:center;color:#64748b;font-size:.82rem;margin-bottom:20px">Kullanıcı adın veya email adresin ile şifre sıfırlama linki alabilirsin.</p>
    {msg_html}
    <form method="POST" action="/forgot-password">
      <label>Kullanıcı Adı veya Email</label>
      <input type="text" name="identifier" required placeholder="kullanici_adi veya ornek@gmail.com" autocomplete="email">
      <button class="btn" type="submit">Sıfırlama Linki Gönder</button>
    </form>
    <div class="link"><a href="/login">← Giriş ekranına dön</a></div>"""

    elif mode == "forgot_sent":
        form = f"""
    <div style="text-align:center;padding:20px 0">
      <div style="font-size:3rem;margin-bottom:16px">📬</div>
      <h2 style="font-size:1.1rem;font-weight:700;margin-bottom:12px">Mail Gönderildi</h2>
      {msg_html}
      <p style="color:#64748b;font-size:.82rem;margin-top:12px">Spam/Junk klasörünü de kontrol etmeyi unutma.</p>
    </div>
    <div class="link"><a href="/login">← Giriş ekranına dön</a></div>"""

    elif mode == "reset":
        form = f"""
    <h2 style="font-size:1.1rem;font-weight:700;margin-bottom:20px;text-align:center">Yeni Şifre Belirle</h2>
    {msg_html}
    <form method="POST" action="/reset-password/{token}">
      <label>Yeni Şifre <span style="color:#64748b">(en az 6 karakter)</span></label>
      <input type="password" name="password" required autocomplete="new-password">
      <label>Şifre Tekrar</label>
      <input type="password" name="confirm" required autocomplete="new-password">
      <button class="btn" type="submit">Şifremi Güncelle</button>
    </form>"""

    else:  # reset_invalid
        form = f"""
    <div style="text-align:center;padding:20px 0">
      <div style="font-size:3rem;margin-bottom:16px">⚠️</div>
      <h2 style="font-size:1.1rem;font-weight:700;margin-bottom:12px">Link Geçersiz</h2>
      {msg_html}
    </div>
    <div class="link"><a href="/forgot-password">Yeni link al →</a></div>"""

    return (AUTH_HTML
        .replace("__MODE_TITLE__", page_title)
        .replace("  <!-- __FORM_CONTENT__ -->", form))

HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0a0c12">
<meta name="description" content="Kirpi — Kişisel nakit akışı takip uygulaması">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Kirpi">
<link rel="manifest" href="/manifest.json">
<title>Kirpi — Nakit Akışı</title>
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
    <div class="brand">
      <img src="/icon.svg" style="width:32px;height:32px;border-radius:8px"> Kirpi
    </div>
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
    <div class="nl" data-page="invest" onclick="goPage('invest',this)">
      <span class="ico">📈</span>Yatırım
    </div>
    <div class="nl" data-page="recurring" onclick="goPage('recurring',this)">
      <span class="ico">🔁</span>Düzenli
    </div>
    <div class="nl" data-page="cards" onclick="goPage('cards',this)">
      <span class="ico">💳</span>Kartlar
    </div>
    <div class="nl" data-page="budget" onclick="goPage('budget',this)">
      <span class="ico">🎯</span>Bütçe
    </div>
  </div>
  <div class="nav-bottom">
    <div style="font-weight:600;color:var(--txt);margin-bottom:5px">👤 __USER_DISPLAY__</div>
    <a href="/logout" style="color:#ef4444;font-size:.75rem;text-decoration:none;display:inline-flex;align-items:center;gap:4px">↩ Çıkış Yap</a>
  </div>
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
    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
      <div style="display:flex;background:var(--bg3);border:1px solid var(--border2);border-radius:9px;overflow:hidden">
        <button id="view-month-btn" onclick="setDbView('month')"
          style="padding:7px 16px;border:none;font-size:.82rem;font-weight:600;cursor:pointer;background:var(--b);color:#fff;transition:.15s">Aylık</button>
        <button id="view-year-btn" onclick="setDbView('year')"
          style="padding:7px 16px;border:none;font-size:.82rem;font-weight:600;cursor:pointer;background:transparent;color:var(--txt2);transition:.15s">Yıllık</button>
      </div>
      <div class="mnav" id="month-nav">
        <button onclick="changeMonth(-1)">‹</button>
        <div class="ml" id="mlabel"></div>
        <button onclick="changeMonth(1)">›</button>
      </div>
      <div class="mnav" id="year-nav" style="display:none">
        <button onclick="changeYear(-1)">‹</button>
        <div class="ml" id="ylabel"></div>
        <button onclick="changeYear(1)">›</button>
      </div>
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
    <select class="filter-sel" id="ledger-f-cat" onchange="filterLedger()"><option value="">Tüm Kategoriler</option></select>
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
      <div><label>Tutar (₺)</label><input class="f-input" type="text" inputmode="decimal" data-num id="f-amount" placeholder="0,00"></div>
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

<!-- INVESTMENT -->
<div class="page" id="page-invest">
  <div class="page-title">Yatırım Takibi</div>
  <div class="page-sub">Döviz · Altın · Fon — canlı kur, gerçek zamanlı kâr/zarar ve gelir yazma</div>

  <!-- LIVE RATES -->
  <div class="grid4" style="margin-bottom:20px">
    <div class="stat" style="background:linear-gradient(135deg,#1e3a5f,#162a47);border-color:#3b82f633">
      <div class="glow" style="background:#3b82f6"></div>
      <div class="lbl">🇺🇸 USD/TRY</div>
      <div class="val" id="rate-usd">—</div>
      <div class="sub" id="rate-updated"></div>
    </div>
    <div class="stat" style="background:linear-gradient(135deg,#1a2f1a,#122012);border-color:#22c55e33">
      <div class="glow" style="background:#22c55e"></div>
      <div class="lbl">🇪🇺 EUR/TRY</div>
      <div class="val" id="rate-eur">—</div>
      <div class="sub"></div>
    </div>
    <div class="stat" style="background:linear-gradient(135deg,#2a2010,#1c1508);border-color:#f59e0b33">
      <div class="glow" style="background:#f59e0b"></div>
      <div class="lbl">🇬🇧 GBP/TRY</div>
      <div class="val" id="rate-gbp">—</div>
      <div class="sub"></div>
    </div>
    <div class="stat" style="background:linear-gradient(135deg,#271a08,#1c1205);border-color:#f59e0b55">
      <div class="glow" style="background:#f59e0b"></div>
      <div class="lbl">🥇 Altın (g/TRY)</div>
      <div class="val" id="rate-gold">—</div>
      <div class="sub"></div>
    </div>
  </div>

  <!-- CALCULATOR -->
  <div class="card" style="margin-bottom:20px">
    <div class="section-title">Hesaplayıcı — X TL yatırsaydım ne olurdu?</div>
    <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end">
      <div style="flex:1;min-width:120px">
        <label>Yatırdığım TL</label>
        <input class="f-input" type="number" id="calc-tl" placeholder="50000" oninput="calcInvest()">
      </div>
      <div style="flex:1;min-width:120px">
        <label>O gündeki kur</label>
        <input class="f-input" type="number" id="calc-buy" placeholder="32.50" step="0.01" oninput="calcInvest()">
      </div>
      <div style="flex:1;min-width:140px">
        <label>Araç</label>
        <select class="f-input" id="calc-type" onchange="calcInvest()">
          <option value="usd">Dolar (USD)</option>
          <option value="eur">Euro (EUR)</option>
          <option value="gbp">Sterlin (GBP)</option>
          <option value="gold">Altın (gram)</option>
        </select>
      </div>
    </div>
    <div id="calc-result" style="margin-top:16px;display:none">
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:4px">
        <div style="background:var(--bg3);padding:14px;border-radius:10px;border:1px solid var(--border2);text-align:center">
          <div style="font-size:.72rem;color:var(--txt2);margin-bottom:4px">Aldığın miktar</div>
          <div style="font-weight:700" id="calc-qty">—</div>
        </div>
        <div style="background:var(--bg3);padding:14px;border-radius:10px;border:1px solid var(--border2);text-align:center">
          <div style="font-size:.72rem;color:var(--txt2);margin-bottom:4px">Şu anki değer</div>
          <div style="font-weight:700" id="calc-now">—</div>
        </div>
        <div style="padding:14px;border-radius:10px;border:1px solid;text-align:center" id="calc-profit-box">
          <div style="font-size:.72rem;color:var(--txt2);margin-bottom:4px">Kâr / Zarar</div>
          <div style="font-weight:700" id="calc-profit">—</div>
        </div>
      </div>
    </div>
  </div>

  <div class="grid2">
    <!-- ADD INVESTMENT FORM -->
    <div class="card">
      <div class="section-title">Portföye Ekle</div>
      <div style="margin-bottom:12px">
        <label>Yatırım Türü</label>
        <select class="f-input" id="inv-type" onchange="updateInvForm()">
          <option value="doviz">Döviz (USD/EUR/GBP)</option>
          <option value="altin">Altın</option>
          <option value="fon">Yatırım Fonu (TEFAS)</option>
          <option value="hisse">Hisse / Diğer</option>
        </select>
      </div>
      <div class="form-row">
        <div><label id="inv-name-lbl">İsim</label><input class="f-input" type="text" id="inv-name" placeholder="ör. Dolar Birikimim"></div>
        <div><label id="inv-sym-lbl">Sembol / Fon Kodu</label><input class="f-input" type="text" id="inv-sym" placeholder="USD"></div>
      </div>
      <div class="form-row">
        <div><label id="inv-qty-lbl">Miktar</label><input class="f-input" type="number" id="inv-qty" placeholder="1000" step="0.001"></div>
        <div><label id="inv-price-lbl">Alış Fiyatı (TRY)</label><input class="f-input" type="number" id="inv-price" placeholder="32.50" step="0.01"></div>
      </div>
      <div class="form-row">
        <div><label>Alış Tarihi</label><input class="f-input" type="date" id="inv-date"></div>
        <div><label>Not (opsiyonel)</label><input class="f-input" type="text" id="inv-note" placeholder="ör. Acil fon"></div>
      </div>
      <!-- Fon lookup -->
      <div id="fon-lookup" style="display:none;margin-bottom:12px">
        <div style="display:flex;gap:8px">
          <input class="f-input" type="text" id="fon-kod" placeholder="Fon kodu ör. MAC, TI2, AFT" style="flex:1;text-transform:uppercase">
          <button class="btn btn-ghost" onclick="lookupFon()">Sorgula</button>
        </div>
        <div id="fon-result" style="font-size:.82rem;margin-top:8px;color:var(--txt2)"></div>
      </div>
      <button class="btn btn-primary" style="width:100%;padding:12px" onclick="addInvestment()">Portföye Ekle</button>
    </div>

    <!-- PORTFOLIO -->
    <div class="card">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
        <div class="section-title" style="margin:0">Portföyüm</div>
        <button class="btn btn-ghost" style="font-size:.75rem;padding:6px 12px" onclick="loadInvestments()">↻ Güncelle</button>
      </div>
      <div id="inv-list"><div class="empty-state"><div class="icon">📈</div>Henüz yatırım yok</div></div>
      <div id="inv-total" style="margin-top:14px;padding-top:14px;border-top:1px solid var(--border);display:none">
        <div style="display:flex;justify-content:space-between;font-size:.85rem;margin-bottom:6px">
          <span style="color:var(--txt2)">Toplam Maliyet</span><span id="inv-total-cost" style="font-weight:600"></span>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:.85rem;margin-bottom:6px">
          <span style="color:var(--txt2)">Güncel Değer</span><span id="inv-total-val" style="font-weight:600"></span>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:.9rem">
          <span style="color:var(--txt2)">Toplam K/Z</span><span id="inv-total-pnl" style="font-weight:800"></span>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- RECURRING -->
<div class="page" id="page-recurring">
  <div class="page-title">Düzenli İşlemler</div>
  <div class="page-sub">Tekrarlayan gelir ve giderleri bir kez gir — istediğin yıla tek tuşla uygula</div>

  <div class="grid2">
    <!-- FORM -->
    <div class="card">
      <div class="section-title">Yeni Şablon Ekle</div>
      <div class="type-tabs">
        <button class="type-tab tg" id="rec-tab-g" onclick="setRecTab('gelir')">📈 Gelir</button>
        <button class="type-tab" id="rec-tab-r" onclick="setRecTab('gider')">📉 Gider</button>
      </div>
      <div class="form-row">
        <div><label>Tutar (₺)</label><input class="f-input" type="number" id="rec-amount" placeholder="0.00" min="0" step="0.01"></div>
        <div>
          <label>Her ayın kaçında?</label>
          <select class="f-input" id="rec-day">
            <option value="1">1. günü</option>
            <option value="2">2. günü</option>
            <option value="3">3. günü</option>
            <option value="4">4. günü</option>
            <option value="5" selected>5. günü</option>
            <option value="6">6. günü</option>
            <option value="7">7. günü</option>
            <option value="8">8. günü</option>
            <option value="9">9. günü</option>
            <option value="10">10. günü</option>
            <option value="14">14. günü</option>
            <option value="15">15. günü</option>
            <option value="20">20. günü</option>
            <option value="25">25. günü</option>
            <option value="28">28. günü</option>
            <option value="30">30. günü</option>
            <option value="31">Son günü</option>
          </select>
        </div>
      </div>
      <div style="margin-bottom:12px"><label>Kategori</label><select class="f-input" id="rec-cat"></select></div>
      <div style="margin-bottom:20px"><label>Açıklama</label><input class="f-input" type="text" id="rec-desc" placeholder="örn. Maaş, Kira, Elektrik"></div>
      <button class="btn btn-green" id="rec-add-btn" style="width:100%;padding:13px" onclick="addRecurring()">Şablon Kaydet</button>
    </div>

    <!-- APPLY -->
    <div class="card">
      <div class="section-title">Yıla Uygula</div>
      <p style="font-size:.84rem;color:var(--txt2);margin-bottom:16px;line-height:1.6">
        Şablonları seçili yıl için toplu olarak işlemlere dönüştür.<br>
        Zaten girilmiş olanlar atlanır, çift kayıt oluşmaz.
      </p>
      <div class="form-row" style="margin-bottom:16px">
        <div>
          <label>Yıl</label>
          <select class="f-input" id="rec-apply-year"></select>
        </div>
        <div>
          <label>Ay (opsiyonel)</label>
          <select class="f-input" id="rec-apply-month">
            <option value="">Tüm Yıl (12 ay)</option>
            <option value="1">Ocak</option><option value="2">Şubat</option>
            <option value="3">Mart</option><option value="4">Nisan</option>
            <option value="5">Mayıs</option><option value="6">Haziran</option>
            <option value="7">Temmuz</option><option value="8">Ağustos</option>
            <option value="9">Eylül</option><option value="10">Ekim</option>
            <option value="11">Kasım</option><option value="12">Aralık</option>
          </select>
        </div>
      </div>
      <button class="btn btn-primary" style="width:100%;padding:13px" onclick="applyRecurring()">
        🔁 Uygula
      </button>
      <div id="rec-apply-result" style="margin-top:14px;font-size:.84rem;color:var(--txt2)"></div>
    </div>
  </div>

  <!-- LIST -->
  <div class="card">
    <div class="section-title">Kayıtlı Şablonlar</div>
    <div id="rec-list"><div class="empty-state"><div class="icon">🔁</div>Henüz şablon yok</div></div>
  </div>
</div>

<!-- CARDS -->
<div class="page" id="page-cards">
  <div class="page-title">Kredi Kartları</div>
  <div class="page-sub">Limit, kullanım, son ödeme tarihi ve asgari ödeme takibi</div>

  <div class="grid2">
    <!-- ADD CARD FORM -->
    <div class="card">
      <div class="section-title">Kart Ekle / Güncelle</div>
      <div style="margin-bottom:12px"><label>Kart Sahibi</label><input class="f-input" type="text" id="card-owner" placeholder="ör. Ben, Eşim, Annem"></div>
      <div class="form-row">
        <div>
          <label>Banka Adı</label>
          <select class="f-input" id="card-bank">
            <option>Garanti BBVA</option><option>İş Bankası</option><option>Akbank</option>
            <option>Yapı Kredi</option><option>Ziraat Bankası</option><option>Halkbank</option>
            <option>Vakıfbank</option><option>QNB Finansbank</option><option>Denizbank</option>
            <option>ING</option><option>TEB</option><option>HSBC</option><option>Diğer</option>
          </select>
        </div>
        <div><label>Kart Adı / Türü</label><input class="f-input" type="text" id="card-name" placeholder="ör. Miles&Smiles, Bonus"></div>
      </div>
      <div class="form-row">
        <div><label>Toplam Limit (₺)</label><input class="f-input" type="number" id="card-limit" placeholder="50000"></div>
        <div><label>Mevcut Borç (₺)</label><input class="f-input" type="number" id="card-used" placeholder="12000"></div>
      </div>
      <div class="form-row">
        <div>
          <label>Son Ödeme Günü</label>
          <select class="f-input" id="card-due">
            <option value="1">1. günü</option><option value="5">5. günü</option>
            <option value="7">7. günü</option><option value="10">10. günü</option>
            <option value="12">12. günü</option><option value="14">14. günü</option>
            <option value="15">15. günü</option><option value="18">18. günü</option>
            <option value="20">20. günü</option><option value="22">22. günü</option>
            <option value="25">25. günü</option><option value="28">28. günü</option>
          </select>
        </div>
        <div>
          <label>Ekstre Günü</label>
          <select class="f-input" id="card-stmt">
            <option value="1">1. günü</option><option value="5">5. günü</option>
            <option value="8">8. günü</option><option value="10">10. günü</option>
            <option value="12">12. günü</option><option value="15">15. günü</option>
            <option value="18">18. günü</option><option value="20" selected>20. günü</option>
            <option value="22">22. günü</option><option value="25">25. günü</option>
          </select>
        </div>
      </div>
      <div style="margin-bottom:16px">
        <label>Asgari Ödeme Oranı</label>
        <select class="f-input" id="card-minpct">
          <option value="20">%20</option>
          <option value="25" selected>%25</option>
          <option value="30">%30</option>
          <option value="40">%40</option>
          <option value="100">Tamamı (%100)</option>
        </select>
      </div>
      <button class="btn btn-primary" style="width:100%;padding:12px" onclick="addCard()">Kartı Kaydet</button>
    </div>

    <!-- CARDS LIST -->
    <div class="card">
      <div class="section-title">Kartlarım</div>
      <div id="card-list"><div class="empty-state"><div class="icon">💳</div>Henüz kart eklenmedi</div></div>
      <div id="card-totals" style="display:none;margin-top:14px;padding-top:14px;border-top:1px solid var(--border)">
        <div style="display:flex;justify-content:space-between;font-size:.85rem;margin-bottom:5px">
          <span style="color:var(--txt2)">Toplam Limit</span><span id="ct-limit" style="font-weight:600"></span>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:.85rem;margin-bottom:5px">
          <span style="color:var(--txt2)">Toplam Borç</span><span id="ct-used" style="font-weight:600;color:var(--r)"></span>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:.9rem">
          <span style="color:var(--txt2)">Kullanılabilir</span><span id="ct-avail" style="font-weight:800;color:var(--g)"></span>
        </div>
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
  if(id==='recurring') initRecurringPage();
  if(id==='invest') initInvestPage();
  if(id==='cards') loadCards();
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
    // ledger filter (ayrı id)
    var fc=document.getElementById('ledger-f-cat');
    if(fc){
      fc.innerHTML='<option value="">Tüm Kategoriler</option>';
      CATS.all.forEach(function(c){fc.innerHTML+='<option>'+c+'</option>'});
    }
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
function fmtNum(n){return Number(n).toLocaleString('tr-TR',{minimumFractionDigits:2,maximumFractionDigits:2})}

// Tutar inputlarını yazarken formatla (100000 → 100.000,00)
function setupNumInputs(){
  document.querySelectorAll('input[data-num]').forEach(function(el){
    el.addEventListener('input',function(){
      var raw=el.value.replace(/\./g,'').replace(',','.');
      el.dataset.raw=raw;
    });
    el.addEventListener('blur',function(){
      var raw=parseFloat(el.value.replace(/\./g,'').replace(',','.'));
      if(!isNaN(raw)){el.value=fmtNum(raw);}
      el.dataset.raw=isNaN(raw)?'':raw;
    });
    el.addEventListener('focus',function(){
      if(el.dataset.raw) el.value=el.dataset.raw.replace('.',',');
    });
  });
}
function getNumVal(el){
  var raw=el.dataset.raw||el.value.replace(/\./g,'').replace(',','.');
  return parseFloat(raw)||0;
}

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
  var fc=document.getElementById('ledger-f-cat').value;
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

// ── DASHBOARD YEARLY VIEW ────────────────────────────────────────────────────
var dbView = 'month';  // 'month' | 'year'

function setDbView(v){
  dbView = v;
  document.getElementById('view-month-btn').style.background = v==='month' ? 'var(--b)' : 'transparent';
  document.getElementById('view-month-btn').style.color      = v==='month' ? '#fff' : 'var(--txt2)';
  document.getElementById('view-year-btn').style.background  = v==='year'  ? 'var(--b)' : 'transparent';
  document.getElementById('view-year-btn').style.color       = v==='year'  ? '#fff' : 'var(--txt2)';
  document.getElementById('month-nav').style.display = v==='month' ? '' : 'none';
  document.getElementById('year-nav').style.display  = v==='year'  ? '' : 'none';
  loadDashboard();
}
function changeYear(d){ curYear+=d; document.getElementById('ylabel').textContent=curYear+' Yılı'; loadDashboard(); }

var _origLoadDashboard = loadDashboard;
loadDashboard = function(){
  if(dbView==='year'){
    // Fetch all 12 months aggregated
    xhr('/api/summary?year='+curYear,null,function(d){
      summaryData=d;
      // For yearly: sum all months
      var totalG=0,totalE=0;
      var allGcats={},allEcats={};
      d.bar.forEach(function(m){totalG+=m.gelir;totalE+=m.gider});
      // gelir/gider cats already returned for year if no month filter
      renderStats({gelir:totalG,gider:totalE,net:totalG-totalE,balance:d.balance,
                   gelir_cats:d.gelir_cats,gider_cats:d.gider_cats,budgets:d.budgets});
      drawBar(d.bar);
      drawDonut(d.gider_cats);
      renderBudgetPage(d.gider_cats,d.budgets);
      document.getElementById('db-sub').textContent=curYear+' Yılı özeti';
    });
    xhr('/api/motivation',null,renderMotivation);
    return;
  }
  xhr('/api/summary?year='+curYear+'&month='+curMonth,null,function(d){
    summaryData=d;
    renderStats(d);
    drawBar(d.bar);
    drawDonut(d.gider_cats);
    renderBudgetPage(d.gider_cats,d.budgets);
  });
  xhr('/api/motivation',null,renderMotivation);
};

// ── INVESTMENT ────────────────────────────────────────────────────────────────
var liveRates = {};

function initInvestPage(){
  document.getElementById('inv-date').value = new Date().toISOString().split('T')[0];
  loadRates();
  loadInvestments();
  updateInvForm();
  setInterval(loadRates, 60000);
}

function loadRates(){
  xhr('/api/rates',null,function(d){
    liveRates = d;
    var fmtR = function(v){ return v ? '₺'+Number(v).toLocaleString('tr-TR',{minimumFractionDigits:2,maximumFractionDigits:2}) : '—' };
    document.getElementById('rate-usd').textContent  = fmtR(d.usd_try);
    document.getElementById('rate-eur').textContent  = fmtR(d.eur_try);
    document.getElementById('rate-gbp').textContent  = fmtR(d.gbp_try);
    document.getElementById('rate-gold').textContent = fmtR(d.gold_try);
    document.getElementById('rate-updated').textContent = d.updated ? 'Son: '+d.updated : '';
    calcInvest();
  });
}

function calcInvest(){
  var tl   = parseFloat(document.getElementById('calc-tl').value);
  var buy  = parseFloat(document.getElementById('calc-buy').value);
  var type = document.getElementById('calc-type').value;
  if(!tl || !buy || tl<=0 || buy<=0){ document.getElementById('calc-result').style.display='none'; return; }
  var curRate = type==='usd' ? liveRates.usd_try :
                type==='eur' ? liveRates.eur_try :
                type==='gbp' ? liveRates.gbp_try :
                               liveRates.gold_try;
  if(!curRate){ document.getElementById('calc-result').style.display='none'; return; }
  var qty     = tl / buy;
  var curVal  = qty * curRate;
  var profit  = curVal - tl;
  var pct     = profit / tl * 100;
  var unit    = type==='gold' ? 'gram' : type.toUpperCase();
  document.getElementById('calc-qty').textContent    = qty.toFixed(4) + ' ' + unit;
  document.getElementById('calc-now').textContent    = fmt(curVal);
  document.getElementById('calc-profit').textContent = (profit>=0?'+':'')+fmt(profit)+' (%'+pct.toFixed(1)+')';
  var box = document.getElementById('calc-profit-box');
  box.style.borderColor = profit>=0 ? 'var(--g)' : 'var(--r)';
  box.style.background  = profit>=0 ? '#22c55e10' : '#ef444410';
  document.getElementById('calc-profit').style.color = profit>=0 ? 'var(--g)' : 'var(--r)';
  document.getElementById('calc-result').style.display = 'block';
}

function updateInvForm(){
  var t = document.getElementById('inv-type').value;
  var symLbl   = document.getElementById('inv-sym-lbl');
  var symInp   = document.getElementById('inv-sym');
  var qtyLbl   = document.getElementById('inv-qty-lbl');
  var priceLbl = document.getElementById('inv-price-lbl');
  var fonDiv   = document.getElementById('fon-lookup');
  if(t==='doviz'){ symLbl.textContent='Sembol'; symInp.placeholder='USD, EUR, GBP'; qtyLbl.textContent='Miktar (adet)'; priceLbl.textContent='Alış Kuru (TRY)'; fonDiv.style.display='none'; }
  else if(t==='altin'){ symLbl.textContent='Tür'; symInp.placeholder='ALTIN'; qtyLbl.textContent='Miktar (gram)'; priceLbl.textContent='Alış Fiyatı (TRY/gram)'; fonDiv.style.display='none'; }
  else if(t==='fon'){ symLbl.textContent='Fon Kodu'; symInp.placeholder='ör. MAC, TI2'; qtyLbl.textContent='Adet (pay)'; priceLbl.textContent='Alış Fiyatı (TRY/pay)'; fonDiv.style.display=''; }
  else { symLbl.textContent='Ticker'; symInp.placeholder='ör. THYAO'; qtyLbl.textContent='Adet'; priceLbl.textContent='Alış Fiyatı (TRY)'; fonDiv.style.display='none'; }
}

function lookupFon(){
  var kod = document.getElementById('fon-kod').value.trim().toUpperCase();
  if(!kod){ return; }
  var el = document.getElementById('fon-result');
  el.textContent = 'Sorgulanıyor…';
  xhr('/api/tefas/'+kod, null, function(d){
    if(d.ok){
      el.innerHTML = '<span style="color:var(--g)">✓ '+d.fon+' — Güncel fiyat: <strong>'+d.fiyat.toFixed(4)+'₺</strong> ('+d.tarih+')</span>';
      document.getElementById('inv-sym').value   = d.fon;
      document.getElementById('inv-price').value = d.fiyat.toFixed(4);
    } else {
      el.innerHTML = '<span style="color:var(--r)">Fon bulunamadı. Fon kodu doğru mu? (ör. MAC)</span>';
    }
  });
}

function addInvestment(){
  var body = {
    name:      document.getElementById('inv-name').value.trim(),
    itype:     document.getElementById('inv-type').value,
    symbol:    document.getElementById('inv-sym').value.trim().toUpperCase(),
    quantity:  parseFloat(document.getElementById('inv-qty').value),
    buy_price: parseFloat(document.getElementById('inv-price').value),
    buy_date:  document.getElementById('inv-date').value,
    note:      document.getElementById('inv-note').value,
  };
  if(!body.name || !body.quantity || !body.buy_price){ toast('İsim, miktar ve fiyat zorunlu'); return; }
  xhr('/api/investments', body, function(r){
    if(r.ok){ toast('Portföye eklendi ✓'); loadInvestments();
      document.getElementById('inv-name').value='';
      document.getElementById('inv-qty').value='';
      document.getElementById('inv-price').value='';
    }
  });
}

function loadInvestments(){
  xhr('/api/investments/value', null, function(list){
    var el = document.getElementById('inv-list');
    if(!list.length){ el.innerHTML='<div class="empty-state"><div class="icon">📈</div>Portföy boş</div>'; document.getElementById('inv-total').style.display='none'; return; }
    var totalCost=0, totalVal=0;
    el.innerHTML = list.map(function(inv){
      var hasVal = inv.cur_try !== null;
      var profit = inv.profit_try;
      var pct    = inv.profit_pct;
      totalCost += inv.buy_try;
      if(hasVal) totalVal += inv.cur_try;
      var typeIcon = inv.itype==='doviz'?'💵':inv.itype==='altin'?'🥇':inv.itype==='fon'?'📊':'📈';
      var priceLabel = inv.itype==='fon'||inv.itype==='hisse' ?
        '<input type="number" placeholder="Güncel fiyat" step="0.0001" style="background:var(--bg4);border:1px solid var(--border2);color:var(--txt);padding:4px 8px;border-radius:6px;font-size:.75rem;width:120px" onchange="updateInvPrice('+inv.id+',this.value)">' : '';
      return '<div style="background:var(--bg3);border-radius:10px;border:1px solid var(--border);padding:12px 14px;margin-bottom:8px">'+
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">'+
          '<span style="font-size:1.2rem">'+typeIcon+'</span>'+
          '<div style="flex:1">'+
            '<div style="font-weight:600;font-size:.88rem">'+inv.name+'</div>'+
            '<div style="font-size:.72rem;color:var(--txt2)">'+inv.symbol+' · '+inv.buy_date+'</div>'+
          '</div>'+
          '<button class="del-row" onclick="delInv('+inv.id+')">✕</button>'+
        '</div>'+
        '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-size:.78rem">'+
          '<div><div style="color:var(--txt2)">Maliyet</div><div style="font-weight:600">'+fmt(inv.buy_try)+'</div></div>'+
          '<div><div style="color:var(--txt2)">Şu an</div><div style="font-weight:600">'+(hasVal?fmt(inv.cur_try):priceLabel||'—')+'</div></div>'+
          '<div><div style="color:var(--txt2)">K/Z</div>'+
            '<div style="font-weight:700;color:'+(profit>0?'var(--g)':profit<0?'var(--r)':'var(--txt2)')+'">'+
              (profit!==null?(profit>=0?'+':'')+fmt(profit)+' ('+pct+'%)':'—')+'</div></div>'+
        '</div>'+
        (hasVal && profit > 0 ? '<button class="btn btn-green" style="width:100%;margin-top:10px;padding:7px;font-size:.78rem" onclick="bookIncome('+inv.id+','+inv.profit_try+',\''+inv.name+'\')">+ Kâr olarak gelire yaz ('+fmt(profit)+')</button>' : '')+
      '</div>';
    }).join('');
    document.getElementById('inv-total').style.display = 'block';
    document.getElementById('inv-total-cost').textContent = fmt(totalCost);
    document.getElementById('inv-total-val').textContent  = totalVal ? fmt(totalVal) : '—';
    var totalPnl = totalVal - totalCost;
    document.getElementById('inv-total-pnl').textContent = totalVal ? (totalPnl>=0?'+':'')+fmt(totalPnl) : '—';
    document.getElementById('inv-total-pnl').style.color = totalPnl>=0?'var(--g)':'var(--r)';
  });
}

function updateInvPrice(id, price){
  // refresh with manual price for fon/hisse
  xhr('/api/investments/value?price_'+id+'='+price, null, function(list){
    var inv = list.find(function(i){return i.id===id});
    if(!inv) return;
    // update just that row's display without full reload
    loadInvestments();
  });
}

function delInv(id){
  xhr('/api/investments/'+id, null, function(){ loadInvestments(); toast('Silindi'); }, false, true);
}

function bookIncome(invId, amount, name){
  var today = new Date().toISOString().split('T')[0];
  xhr('/api/investments/'+invId+'/book-income',
    {amount: amount, description: name+' — Yatırım Getirisi', category: 'Yatırım / Temettü', date: today},
    function(r){ if(r.ok){ toast('Gelir hanesine yazıldı ✓'); loadDashboard(); loadAllTx(); }});
}

// ── RECURRING ─────────────────────────────────────────────────────────────────
var recTab = 'gelir';

function initRecurringPage(){
  fillSel('rec-cat', CATS[recTab]);
  var ys = document.getElementById('rec-apply-year');
  ys.innerHTML = '';
  var now = new Date().getFullYear();
  for(var y=now-1; y<=now+2; y++){
    ys.innerHTML += '<option value="'+y+'"'+(y===now?' selected':'')+'>'+y+'</option>';
  }
  loadRecurring();
}

function setRecTab(t){
  recTab = t;
  document.getElementById('rec-tab-g').className = 'type-tab' + (t==='gelir' ? ' tg' : '');
  document.getElementById('rec-tab-r').className = 'type-tab' + (t==='gider' ? ' tr' : '');
  document.getElementById('rec-add-btn').className = 'btn ' + (t==='gelir' ? 'btn-green' : 'btn-danger');
  fillSel('rec-cat', CATS[t]);
}

function loadRecurring(){
  xhr('/api/recurring', null, function(list){
    var el = document.getElementById('rec-list');
    if(!list.length){
      el.innerHTML = '<div class="empty-state"><div class="icon">🔁</div>Henüz şablon yok. Sol taraftan ekle.</div>';
      return;
    }
    var gelirler = list.filter(function(r){return r.type==='gelir'});
    var giderler = list.filter(function(r){return r.type==='gider'});
    function renderGroup(items, label, color){
      if(!items.length) return '';
      return '<div style="margin-bottom:18px">'+
        '<div style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:'+color+';margin-bottom:10px">'+label+'</div>'+
        '<div style="display:flex;flex-direction:column;gap:7px">'+
        items.map(function(r){
          return '<div style="display:flex;align-items:center;gap:12px;padding:12px 14px;background:var(--bg3);border-radius:10px;border:1px solid var(--border)">'+
            '<div style="width:36px;height:36px;border-radius:8px;background:'+(r.type==='gelir'?'#22c55e18':'#ef444418')+
            ';display:flex;align-items:center;justify-content:center;font-size:1.1rem;flex-shrink:0">'+
            (r.type==='gelir'?'📈':'📉')+'</div>'+
            '<div style="flex:1;min-width:0">'+
              '<div style="font-weight:600;font-size:.88rem">'+(r.description||r.category)+'</div>'+
              '<div style="font-size:.75rem;color:var(--txt2)">'+r.category+' &middot; Her ayın <strong>'+r.day_of_month+'. günü</strong></div>'+
            '</div>'+
            '<div style="font-weight:800;font-size:.95rem;color:'+(r.type==='gelir'?'var(--g)':'var(--r)')+'">'+
              (r.type==='gelir'?'+':'-')+fmt(r.amount)+'</div>'+
            '<button onclick="delRecurring('+r.id+')" class="del-row">✕</button>'+
          '</div>';
        }).join('')+
        '</div></div>';
    }
    el.innerHTML = renderGroup(gelirler,'Gelirler','var(--g)') + renderGroup(giderler,'Giderler','var(--r)');
  });
}

function addRecurring(){
  var amount = parseFloat(document.getElementById('rec-amount').value);
  var cat    = document.getElementById('rec-cat').value;
  var desc   = document.getElementById('rec-desc').value;
  var day    = parseInt(document.getElementById('rec-day').value);
  if(!amount || amount<=0){toast('Tutar giriniz'); return}
  xhr('/api/recurring', {type:recTab, amount:amount, category:cat, description:desc, day_of_month:day}, function(r){
    if(r.ok){
      toast('Şablon kaydedildi ✓');
      document.getElementById('rec-amount').value = '';
      document.getElementById('rec-desc').value = '';
      loadRecurring();
    }
  });
}

function delRecurring(id){
  xhr('/api/recurring/'+id, null, function(){loadRecurring(); toast('Silindi')}, false, true);
}

function applyRecurring(){
  var year  = parseInt(document.getElementById('rec-apply-year').value);
  var month = document.getElementById('rec-apply-month').value;
  var body  = {year: year};
  if(month) body.month = month;
  xhr('/api/recurring/apply', body, function(r){
    var el = document.getElementById('rec-apply-result');
    if(r.ok){
      var msg = '';
      if(r.created > 0) msg += '<span style="color:var(--g)">✓ '+r.created+' işlem oluşturuldu</span>';
      if(r.skipped > 0) msg += (msg?' &nbsp;·&nbsp; ':'')+r.skipped+' zaten vardı, atlandı';
      if(!r.created && !r.skipped) msg = 'Uygulanacak aktif şablon yok.';
      el.innerHTML = msg;
      if(r.created > 0){toast(r.created+' işlem oluşturuldu ✓'); loadAllTx(); loadDashboard();}
    }
  });
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

// ── CARDS ────────────────────────────────────────────────────────────────────
function addCard(){
  var body = {
    bank_name:    document.getElementById('card-bank').value,
    card_name:    document.getElementById('card-name').value,
    owner:        document.getElementById('card-owner').value,
    limit_:       parseFloat(document.getElementById('card-limit').value)||0,
    used_:        parseFloat(document.getElementById('card-used').value)||0,
    due_day:      parseInt(document.getElementById('card-due').value),
    statement_day:parseInt(document.getElementById('card-stmt').value),
    min_pct:      parseFloat(document.getElementById('card-minpct').value),
  };
  if(!body.limit_){ toast('Limit giriniz'); return; }
  xhr('/api/cards', body, function(r){ if(r.ok){ toast('Kart kaydedildi ✓'); loadCards();
    ['card-name','card-limit','card-used','card-owner'].forEach(function(id){document.getElementById(id).value=''});
  }});
}

function loadCards(){
  xhr('/api/cards', null, function(list){
    var el = document.getElementById('card-list');
    if(!list.length){ el.innerHTML='<div class="empty-state"><div class="icon">💳</div>Henüz kart eklenmedi</div>'; document.getElementById('card-totals').style.display='none'; return; }
    var totalLimit=0, totalUsed=0;
    var today = new Date().getDate();
    el.innerHTML = list.map(function(c){
      var avail   = c.limit_ - c.used_;
      var usePct  = Math.min(100, Math.round(c.used_ / c.limit_ * 100));
      var minPay  = Math.round(c.used_ * c.min_pct / 100);
      var color   = usePct>80 ? 'var(--r)' : usePct>50 ? 'var(--y)' : 'var(--g)';
      var daysLeft = c.due_day >= today ? c.due_day - today : 30 - today + c.due_day;
      totalLimit += c.limit_; totalUsed += c.used_;
      return '<div style="background:var(--bg3);border-radius:12px;border:1px solid var(--border);padding:16px;margin-bottom:10px">'+
        '<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:10px">'+
          '<div>'+
            '<div style="font-weight:700;font-size:.92rem">'+c.bank_name+(c.card_name?' · '+c.card_name:'')+'</div>'+
            (c.owner ? '<div style="font-size:.74rem;color:var(--b2);margin-top:2px">👤 '+c.owner+'</div>' : '')+
          '</div>'+
          '<button class="del-row" onclick="delCard('+c.id+')">✕</button>'+
        '</div>'+
        '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-size:.78rem;margin-bottom:12px">'+
          '<div><div style="color:var(--txt2)">Limit</div><div style="font-weight:700">'+fmt(c.limit_)+'</div></div>'+
          '<div><div style="color:var(--txt2)">Borç</div><div style="font-weight:700;color:var(--r)">'+fmt(c.used_)+'</div></div>'+
          '<div><div style="color:var(--txt2)">Kullanılabilir</div><div style="font-weight:700;color:var(--g)">'+fmt(avail)+'</div></div>'+
        '</div>'+
        '<div class="prog-bg" style="margin-bottom:10px"><div class="prog-fill" style="width:'+usePct+'%;background:'+color+'"></div></div>'+
        '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-size:.75rem">'+
          '<div style="background:var(--bg4);padding:8px;border-radius:8px;text-align:center">'+
            '<div style="color:var(--txt2)">Son Ödeme</div><div style="font-weight:600">'+c.due_day+'. gün</div>'+
            '<div style="color:'+(daysLeft<=3?'var(--r)':'var(--txt2)')+'">'+daysLeft+' gün kaldı</div>'+
          '</div>'+
          '<div style="background:var(--bg4);padding:8px;border-radius:8px;text-align:center">'+
            '<div style="color:var(--txt2)">Asgari (%'+c.min_pct+')</div>'+
            '<div style="font-weight:700;color:var(--y)">'+fmt(minPay)+'</div>'+
          '</div>'+
          '<div style="background:var(--bg4);padding:8px;border-radius:8px;text-align:center">'+
            '<div style="color:var(--txt2)">Ekstre Günü</div>'+
            '<div style="font-weight:600">'+c.statement_day+'. gün</div>'+
          '</div>'+
        '</div>'+
        '<div style="margin-top:10px">'+
          '<label style="font-size:.72rem">Borcu Güncelle (₺)</label>'+
          '<div style="display:flex;gap:8px;margin-top:4px">'+
            '<input type="number" id="upd-used-'+c.id+'" value="'+c.used_+'" class="f-input" style="flex:1" placeholder="Güncel borç">'+
            '<button class="btn btn-ghost" style="padding:8px 14px;font-size:.78rem" onclick="updateCardUsed('+c.id+')">Kaydet</button>'+
          '</div>'+
        '</div>'+
      '</div>';
    }).join('');
    document.getElementById('card-totals').style.display='block';
    document.getElementById('ct-limit').textContent = fmt(totalLimit);
    document.getElementById('ct-used').textContent  = fmt(totalUsed);
    document.getElementById('ct-avail').textContent = fmt(totalLimit-totalUsed);
  });
}

function updateCardUsed(id){
  var val = parseFloat(document.getElementById('upd-used-'+id).value)||0;
  xhr('/api/cards/'+id, {used_: val}, function(r){ if(r.ok){ toast('Güncellendi ✓'); loadCards(); }}, true);
}
function delCard(id){
  xhr('/api/cards/'+id, null, function(){ loadCards(); toast('Silindi'); }, false, true);
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

// ── PWA SERVICE WORKER ────────────────────────────────────────────────────────
if('serviceWorker' in navigator){
  navigator.serviceWorker.register('/sw.js').catch(function(){});
}
</script>
</body>
</html>"""

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" rx="22" fill="#1a1d26"/>
  <!-- spines -->
  <g fill="#a78bfa">
    <polygon points="50,8 46,22 54,22"/>
    <polygon points="62,10 56,23 65,25"/>
    <polygon points="73,16 65,27 74,31"/>
    <polygon points="81,26 71,34 79,40"/>
    <polygon points="85,38 74,43 80,50"/>
    <polygon points="38,10 44,23 35,25"/>
    <polygon points="27,16 35,27 26,31"/>
  </g>
  <!-- body -->
  <ellipse cx="50" cy="62" rx="32" ry="24" fill="#7c3aed"/>
  <!-- face -->
  <ellipse cx="32" cy="60" rx="16" ry="14" fill="#c4b5fd"/>
  <!-- eye -->
  <circle cx="27" cy="57" r="3.5" fill="#1a1d26"/>
  <circle cx="26" cy="56" r="1" fill="white"/>
  <!-- nose -->
  <ellipse cx="20" cy="62" rx="4" ry="3" fill="#7c3aed"/>
  <circle cx="19" cy="62" r="2" fill="#4c1d95"/>
  <!-- smile -->
  <path d="M22 66 Q26 70 30 66" stroke="#4c1d95" stroke-width="1.5" fill="none" stroke-linecap="round"/>
  <!-- feet -->
  <ellipse cx="38" cy="83" rx="8" ry="5" fill="#6d28d9"/>
  <ellipse cx="56" cy="84" rx="8" ry="5" fill="#6d28d9"/>
  <ellipse cx="70" cy="82" rx="7" ry="4" fill="#6d28d9"/>
  <!-- belly stripe -->
  <ellipse cx="50" cy="65" rx="15" ry="10" fill="#ede9fe" opacity="0.2"/>
</svg>"""

MANIFEST = json.dumps({
    "name": "Kirpi — Nakit Akışı",
    "short_name": "Kirpi",
    "description": "Kişisel gelir-gider takip uygulaması",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0a0c12",
    "theme_color": "#6366f1",
    "orientation": "portrait",
    "icons": [
        {"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"},
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
    ]
}, ensure_ascii=False)

SW_JS = """
const CACHE='kirpi-v1';
const ASSETS=['/','/manifest.json','/icon.svg'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS))));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));
});
"""

@app.route("/sw.js")
def sw(): return SW_JS, 200, {"Content-Type": "application/javascript"}

@app.route("/manifest.json")
def manifest(): return MANIFEST, 200, {"Content-Type": "application/manifest+json"}

@app.route("/icon.svg")
def icon_svg(): return ICON_SVG, 200, {"Content-Type": "image/svg+xml"}

@app.route("/icon-192.png")
@app.route("/icon-512.png")
def icon_png():
    # redirect to svg for now — works for PWA install
    from flask import redirect
    return redirect("/icon.svg")

@app.route("/")
@login_required
def index():
    display = session.get("display","")
    return HTML.replace("__USER_DISPLAY__", display)

if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=_daily_backup_loop, daemon=True)
    t.start()
    app.run(debug=True, port=5001)

init_db()
_backup_thread = threading.Thread(target=_daily_backup_loop, daemon=True)
_backup_thread.start()
