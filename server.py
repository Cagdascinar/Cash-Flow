import json, os, csv, io, re, requests, secrets, smtplib, threading, time, logging
import psycopg2, psycopg2.extras
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
# ── DATABASE ──────────────────────────────────────────────────────────────────
def _pg_url():
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[11:]
    return url

class _PGCursor:
    """Thin wrapper: makes psycopg2 DictCursor behave like sqlite3 cursor."""
    def __init__(self, cur):
        self._cur = cur
        self.lastrowid = None

    def execute(self, sql, params=()):
        sql = sql.replace("?", "%s")
        is_insert = sql.strip().upper().startswith("INSERT") and "RETURNING" not in sql.upper()
        if is_insert:
            sql = sql.rstrip("; ") + " RETURNING id"
        self._cur.execute(sql, params)
        if is_insert:
            row = self._cur.fetchone()
            self.lastrowid = row[0] if row else None
        return self

    def fetchone(self):  return self._cur.fetchone()
    def fetchall(self): return self._cur.fetchall()

class _PGConn:
    """Wrapper that makes psycopg2 connection look like sqlite3 connection."""
    def __init__(self):
        self._conn = psycopg2.connect(_pg_url(),
            cursor_factory=psycopg2.extras.DictCursor)
        self._conn.autocommit = False

    def execute(self, sql, params=()):
        cur = self._conn.cursor()
        c = _PGCursor(cur)
        c.execute(sql, params)
        return c

    def commit(self):   self._conn.commit()
    def rollback(self): self._conn.rollback()
    def close(self):    self._conn.close()

    def __enter__(self): return self
    def __exit__(self, exc_type, *_):
        if exc_type is None: self._conn.commit()
        else: self._conn.rollback()
        self._conn.close()
        return False

def pg_connect(): return _PGConn()

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
        g.db = pg_connect()
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db:
        try: db.commit()
        except Exception: pass
        db.close()

def init_db():
    stmts = [
        """CREATE TABLE IF NOT EXISTS users (
            id             SERIAL PRIMARY KEY,
            username       TEXT UNIQUE NOT NULL,
            display_name   TEXT NOT NULL DEFAULT '',
            password_hash  TEXT NOT NULL,
            email          TEXT NOT NULL DEFAULT '',
            email_verified INTEGER NOT NULL DEFAULT 0,
            verify_token   TEXT,
            created_at     TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            token      TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            used       INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS profiles (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            name       TEXT NOT NULL,
            type       TEXT NOT NULL DEFAULT 'sahis',
            created_at TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS transactions (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL DEFAULT 1,
            profile_id  INTEGER NOT NULL DEFAULT 1,
            type        TEXT NOT NULL,
            amount      DOUBLE PRECISION NOT NULL,
            category    TEXT NOT NULL,
            description TEXT DEFAULT '',
            date        TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS budgets (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL DEFAULT 1,
            profile_id INTEGER NOT NULL DEFAULT 1,
            category   TEXT NOT NULL,
            limit_     DOUBLE PRECISION NOT NULL,
            UNIQUE(profile_id, category)
        )""",
        """CREATE TABLE IF NOT EXISTS cards (
            id            SERIAL PRIMARY KEY,
            user_id       INTEGER NOT NULL DEFAULT 1,
            profile_id    INTEGER NOT NULL DEFAULT 1,
            bank_name     TEXT NOT NULL,
            card_name     TEXT NOT NULL DEFAULT '',
            owner         TEXT NOT NULL DEFAULT '',
            limit_        DOUBLE PRECISION NOT NULL DEFAULT 0,
            used_         DOUBLE PRECISION NOT NULL DEFAULT 0,
            due_day       INTEGER NOT NULL DEFAULT 1,
            min_pct       DOUBLE PRECISION NOT NULL DEFAULT 25,
            statement_day INTEGER NOT NULL DEFAULT 20,
            created_at    TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS investments (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL DEFAULT 1,
            profile_id  INTEGER NOT NULL DEFAULT 1,
            name        TEXT NOT NULL,
            itype       TEXT NOT NULL,
            symbol      TEXT NOT NULL DEFAULT '',
            quantity    DOUBLE PRECISION NOT NULL DEFAULT 0,
            buy_price   DOUBLE PRECISION NOT NULL DEFAULT 0,
            buy_date    TEXT NOT NULL,
            note        TEXT DEFAULT '',
            created_at  TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS recurring (
            id           SERIAL PRIMARY KEY,
            user_id      INTEGER NOT NULL DEFAULT 1,
            profile_id   INTEGER NOT NULL DEFAULT 1,
            type         TEXT NOT NULL,
            amount       DOUBLE PRECISION NOT NULL,
            category     TEXT NOT NULL,
            description  TEXT DEFAULT '',
            day_of_month INTEGER NOT NULL DEFAULT 1,
            active       INTEGER NOT NULL DEFAULT 1,
            created_at   TEXT NOT NULL
        )""",
        "CREATE INDEX IF NOT EXISTS idx_txn_profile_date ON transactions(profile_id, date)",
    ]
    migrations = [
        ("users",        "email",          "TEXT NOT NULL DEFAULT ''"),
        ("users",        "email_verified",  "INTEGER NOT NULL DEFAULT 0"),
        ("users",        "verify_token",    "TEXT"),
        ("transactions", "user_id",         "INTEGER NOT NULL DEFAULT 1"),
        ("transactions", "profile_id",      "INTEGER NOT NULL DEFAULT 1"),
        ("budgets",      "user_id",         "INTEGER NOT NULL DEFAULT 1"),
        ("budgets",      "profile_id",      "INTEGER NOT NULL DEFAULT 1"),
        ("cards",        "user_id",         "INTEGER NOT NULL DEFAULT 1"),
        ("cards",        "profile_id",      "INTEGER NOT NULL DEFAULT 1"),
        ("investments",  "user_id",         "INTEGER NOT NULL DEFAULT 1"),
        ("investments",  "profile_id",      "INTEGER NOT NULL DEFAULT 1"),
        ("recurring",    "user_id",         "INTEGER NOT NULL DEFAULT 1"),
        ("recurring",    "profile_id",      "INTEGER NOT NULL DEFAULT 1"),
    ]
    with pg_connect() as con:
        for stmt in stmts:
            con.execute(stmt)
        for table, col, col_def in migrations:
            exists = con.execute(
                "SELECT 1 FROM information_schema.columns WHERE table_name=%s AND column_name=%s",
                (table, col)
            ).fetchone()
            if not exists:
                try:
                    con.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
                    log.info("Migration: added %s.%s", table, col)
                except Exception as exc:
                    log.warning("Migration skip %s.%s: %s", table, col, exc)
        users = con.execute("SELECT id FROM users").fetchall()
        for u in users:
            uid = u["id"]
            has_profile = con.execute("SELECT id FROM profiles WHERE user_id=%s", (uid,)).fetchone()
            if not has_profile:
                con.execute(
                    "INSERT INTO profiles (user_id,name,type,created_at) VALUES (%s,%s,%s,%s)",
                    (uid, "Şahıs", "sahis", datetime.now().isoformat())
                )

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

def send_verify_email(to_email, username, token):
    verify_url = f"{APP_URL}/verify-email/{token}"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🦔 Kirpi — Email Adresinizi Doğrulayın"
    msg["From"]    = f"Kirpi Nakit Akışı <{MAIL_FROM}>"
    msg["To"]      = to_email
    text = f"Merhaba {username},\n\nKirpi'ye hoş geldiniz! Hesabınızı aktif etmek için aşağıdaki bağlantıya tıklayın:\n{verify_url}\n\nBu bağlantı 24 saat geçerlidir."
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0a0c12;font-family:'Inter',system-ui,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0c12;padding:40px 20px">
  <tr><td align="center">
    <table width="520" cellpadding="0" cellspacing="0" style="background:#111318;border:1px solid #1e2233;border-radius:16px;overflow:hidden">
      <tr><td style="background:linear-gradient(135deg,#6366f1,#a855f7);padding:32px;text-align:center">
        <div style="font-size:40px;margin-bottom:8px">🦔</div>
        <h1 style="color:#fff;font-size:1.4rem;font-weight:800;margin:0">Kirpi'ye Hoş Geldiniz!</h1>
        <p style="color:rgba(255,255,255,.7);font-size:.85rem;margin:4px 0 0">Nakit Akışı Takibi</p>
      </td></tr>
      <tr><td style="padding:36px 40px">
        <h2 style="color:#e2e8f0;font-size:1.1rem;font-weight:700;margin:0 0 12px">Merhaba, {username} 👋</h2>
        <p style="color:#94a3b8;font-size:.9rem;line-height:1.7;margin:0 0 28px">
          Kayıt olduğunuz için teşekkürler! Hesabınızı aktif etmek için<br>
          aşağıdaki butona tıklayarak email adresinizi doğrulayın.
        </p>
        <table cellpadding="0" cellspacing="0" style="margin:0 auto 28px">
          <tr><td style="background:#6366f1;border-radius:10px;text-align:center">
            <a href="{verify_url}" style="display:block;padding:14px 36px;color:#fff;font-size:.95rem;font-weight:700;text-decoration:none">Email Adresimi Doğrula</a>
          </td></tr>
        </table>
        <div style="background:#1a1d26;border:1px solid #2a2f45;border-radius:8px;padding:14px 16px;margin-bottom:24px">
          <p style="color:#64748b;font-size:.78rem;margin:0 0 6px">Ya da bu bağlantıyı tarayıcınıza yapıştırın:</p>
          <p style="color:#818cf8;font-size:.76rem;word-break:break-all;margin:0">{verify_url}</p>
        </div>
        <p style="color:#64748b;font-size:.78rem;line-height:1.6;margin:0">
          ⏰ Bu bağlantı <strong style="color:#94a3b8">24 saat</strong> geçerlidir.
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

def send_reset_email(to_email, display_name, username, token):
    reset_url = f"{APP_URL}/reset-password/{token}"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🦔 Kirpi — Şifre Sıfırlama"
    msg["From"]    = f"Kirpi Nakit Akışı <{MAIL_FROM}>"
    msg["To"]      = to_email

    text = f"Merhaba {display_name},\n\nKullanıcı adınız: {username}\n\nŞifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:\n{reset_url}\n\nBu bağlantı 1 saat geçerlidir.\n\nEğer bu talebi siz yapmadıysanız bu maili görmezden gelebilirsiniz."

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
        <h2 style="color:#e2e8f0;font-size:1.1rem;font-weight:700;margin:0 0 12px">Merhaba, {display_name} 👋</h2>
        <div style="background:#1a1d26;border:1px solid #2a2f45;border-radius:8px;padding:12px 16px;margin-bottom:20px">
          <p style="color:#64748b;font-size:.78rem;margin:0 0 4px">Giriş için kullanıcı adınız:</p>
          <p style="color:#818cf8;font-size:.92rem;font-weight:700;margin:0">👤 {username}</p>
        </div>
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

def _pg_dump_csv():
    """Export all tables as CSV and return as a combined text string."""
    tables = ["users","profiles","transactions","budgets","cards","investments","recurring"]
    out = io.StringIO()
    with pg_connect() as con:
        for t in tables:
            rows = con.execute(f"SELECT * FROM {t}").fetchall()
            if not rows:
                continue
            cols = list(rows[0].keys())
            out.write(f"-- TABLE: {t} --\n")
            w = csv.writer(out)
            w.writerow(cols)
            for r in rows:
                w.writerow([r[c] for c in cols])
            out.write("\n")
    return out.getvalue()

def send_backup_email(to_email):
    """Attach DB export as CSV and email it."""
    try:
        dump = _pg_dump_csv()
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
        ptype = request.form.get("profile_type","sahis")
        if ptype not in ("sahis","sirket"): ptype = "sahis"
        prof_name = display if display else ("Şirket" if ptype=="sirket" else "Şahıs")
        try:
            vtok = secrets.token_urlsafe(32)
            with pg_connect() as con:
                cur = con.execute(
                    "INSERT INTO users (username,display_name,password_hash,email,email_verified,verify_token,created_at) VALUES (?,?,?,?,0,?,?)",
                    (username, display or username, generate_password_hash(password), email, vtok, datetime.now().isoformat())
                )
                uid = cur.lastrowid
                con.execute(
                    "INSERT INTO profiles (user_id,name,type,created_at) VALUES (?,?,?,?)",
                    (uid, prof_name, ptype, datetime.now().isoformat())
                )
        except psycopg2.IntegrityError:
            return AUTH_HTML_render("register", "Bu kullanıcı adı veya email zaten kullanımda")
        send_verify_email(email, display or username, vtok)
        return redirect("/login?verify_sent=1")
    return AUTH_HTML_render("register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect("/")
    if request.method == "POST":
        username = request.form.get("username","").strip().lower()
        password = request.form.get("password","")
        with pg_connect() as con:
            row = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            if not row["email_verified"]:
                return AUTH_HTML_render("login", "✉️ Email adresiniz doğrulanmamış. Şifreyi biliyorsanız <a href='/forgot-password' style='color:#818cf8'>şifre sıfırla</a> yaparak hem şifreyi sıfırlayın hem de emailinizi doğrulatın. Ya da <a href='/resend-verify' style='color:#818cf8'>yeni doğrulama maili al</a>.")
            session["user_id"]  = row["id"]
            session["username"] = row["username"]
            session["display"]  = row["display_name"]
            with pg_connect() as con2:
                prof = con2.execute("SELECT * FROM profiles WHERE user_id=? ORDER BY id LIMIT 1",(row["id"],)).fetchone()
                if prof:
                    session["profile_id"]   = prof["id"]
                    session["profile_name"] = prof["name"]
                    session["profile_type"] = prof["type"]
            return redirect("/")
        return AUTH_HTML_render("login", "Kullanıcı adı veya şifre hatalı")
    msg = ""
    if request.args.get("verify_sent"):
        msg = "✅ Doğrulama linki email adresinize gönderildi. Lütfen emailinizi kontrol edin."
    elif request.args.get("verified"):
        msg = "✅ Email doğrulandı! Giriş yapabilirsiniz."
    elif request.args.get("reset"):
        msg = "Şifreniz başarıyla güncellendi. Giriş yapabilirsiniz."
    return AUTH_HTML_render("login", msg)

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        identifier = request.form.get("identifier","").strip().lower()
        with pg_connect() as con:
            row = con.execute(
                "SELECT * FROM users WHERE username=? OR email=?", (identifier, identifier)
            ).fetchone()
        if row:
            token = secrets.token_urlsafe(32)
            expires = (datetime.now() + timedelta(hours=1)).isoformat()
            with pg_connect() as con:
                con.execute(
                    "INSERT INTO password_reset_tokens (user_id,token,expires_at,created_at) VALUES (?,?,?,?)",
                    (row["id"], token, expires, datetime.now().isoformat())
                )
            sent = send_reset_email(row["email"], row["display_name"] or row["username"], row["username"], token)
            log.info("Reset email sent=%s for user=%s", sent, row["username"])
        # Always show success to prevent user enumeration
        return AUTH_HTML_render("forgot_sent", "Eğer bu hesap varsa, şifre sıfırlama linki email adresinize gönderildi.")
    return AUTH_HTML_render("forgot")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    with pg_connect() as con:
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
        with pg_connect() as con:
            con.execute(
                "UPDATE users SET password_hash=?, email_verified=1, verify_token=NULL WHERE id=?",
                (generate_password_hash(password), tok["user_id"])
            )
            con.execute("UPDATE password_reset_tokens SET used=1 WHERE token=?", (token,))
        return redirect("/login?reset=1")
    return AUTH_HTML_render("reset", token=token)

@app.route("/verify-email/<token>")
def verify_email(token):
    with pg_connect() as con:
        row = con.execute("SELECT * FROM users WHERE verify_token=? AND email_verified=0", (token,)).fetchone()
    if not row:
        return AUTH_HTML_render("reset_invalid", "Bu doğrulama linki geçersiz veya zaten kullanılmış.")
    with pg_connect() as con:
        con.execute("UPDATE users SET email_verified=1, verify_token=NULL WHERE id=?", (row["id"],))
    return redirect("/login?verified=1")

@app.route("/resend-verify", methods=["GET", "POST"])
def resend_verify():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        with pg_connect() as con:
            row = con.execute("SELECT * FROM users WHERE email=? AND email_verified=0", (email,)).fetchone()
        if row:
            vtok = secrets.token_urlsafe(32)
            with pg_connect() as con:
                con.execute("UPDATE users SET verify_token=? WHERE id=?", (vtok, row["id"]))
            send_verify_email(email, row["display_name"] or row["username"], vtok)
        return AUTH_HTML_render("forgot_sent", "Eğer bu email doğrulanmamış bir hesaba aitse, yeni doğrulama linki gönderildi.")
    return AUTH_HTML_render("resend_verify")

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
        with pg_connect() as con:
            row = con.execute("SELECT id FROM profiles WHERE user_id=? ORDER BY id LIMIT 1",(uid,)).fetchone()
            if row: pid = row["id"]; session["profile_id"] = pid
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
    count = db.execute("SELECT COUNT(*) AS n FROM profiles WHERE user_id=?",(uid,)).fetchone()["n"]
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
    rstart = request.args.get("start","")
    rend   = request.args.get("end","")
    if rstart and rend:
        start, end = rstart, rend
    else:
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

@app.route("/api/today")
@login_required
def today_summary():
    pid  = get_pid(); db = get_db()
    today_str = date.today().isoformat()

    # All today's transactions
    rows = db.execute(
        "SELECT * FROM transactions WHERE profile_id=? AND date=? ORDER BY id DESC",
        (pid, today_str)
    ).fetchall()

    def row_to_dict(r):
        return {"id": r["id"], "amount": float(r["amount"]),
                "category": r["category"], "description": r["description"] or "",
                "type": r["type"]}

    gelir_list = [row_to_dict(r) for r in rows if r["type"] == "gelir"]
    gider_list = [row_to_dict(r) for r in rows if r["type"] == "gider"]
    today_gelir = sum(x["amount"] for x in gelir_list)
    today_gider = sum(x["amount"] for x in gider_list)

    # Credit cards
    cards = db.execute("SELECT * FROM cards WHERE profile_id=? ORDER BY bank_name", (pid,)).fetchall()
    card_list = []
    total_limit = total_used = 0
    for c in cards:
        lim  = c["limit_"] or 0
        used = c["used_"]  or 0
        avail= lim - used
        total_limit += lim; total_used += used
        card_list.append({
            "bank":    c["bank_name"],
            "name":    c["card_name"],
            "limit":   lim,
            "used":    used,
            "avail":   avail,
            "due_day": c["due_day"],
            "pct":     round(used/lim*100) if lim else 0,
        })

    return jsonify({
        "today_gelir": round(today_gelir, 2),
        "today_gider": round(today_gider, 2),
        "today_net":   round(today_gelir - today_gider, 2),
        "gelir_list":  gelir_list,
        "gider_list":  gider_list,
        "cards":       card_list,
        "total_limit": round(total_limit, 2),
        "total_used":  round(total_used, 2),
        "total_avail": round(total_limit - total_used, 2),
    })

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
    year        = int(d.get("year", date.today().year))
    month_start = int(d.get("month_start", 1))
    month_end   = int(d.get("month_end",   12))
    months      = list(range(month_start, month_end + 1))

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
        dump = _pg_dump_csv()
        now_str  = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"kirpi_backup_{now_str}.csv"
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
    is_ok     = msg and (mode in ok_modes or msg.startswith("Kayıt") or msg.startswith("Şifreniz") or msg.startswith("✅"))
    msg_html  = f'<div class="msg {"ok" if is_ok else "err"}">{msg}</div>' if msg else ""

    titles = {
        "register":      "Hesap Oluştur",
        "login":         "Giriş Yap",
        "forgot":        "Şifremi Unuttum",
        "forgot_sent":   "Mail Gönderildi",
        "reset":         "Yeni Şifre Belirle",
        "reset_invalid": "Link Geçersiz",
        "resend_verify": "Doğrulama Maili",
    }
    page_title = titles.get(mode, "Kirpi")

    if mode == "register":
        form = (
    '''    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:24px">
      <div id="reg-sahis" onclick="setRegType(this,'sahis')" style="border:2px solid #6366f1;border-radius:11px;padding:14px 10px;text-align:center;cursor:pointer;background:#1a1d26;transition:.2s">
        <div style="font-size:1.6rem;margin-bottom:4px">&#128100;</div>
        <div style="font-size:.82rem;font-weight:700;color:#e2e8f0">Bireysel</div>
        <div style="font-size:.7rem;color:#94a3b8;margin-top:2px">Sahis hesabi</div>
      </div>
      <div id="reg-sirket" onclick="setRegType(this,'sirket')" style="border:2px solid #2a2f45;border-radius:11px;padding:14px 10px;text-align:center;cursor:pointer;background:#111318;transition:.2s">
        <div style="font-size:1.6rem;margin-bottom:4px">&#127970;</div>
        <div style="font-size:.82rem;font-weight:700;color:#94a3b8">Ticari</div>
        <div style="font-size:.7rem;color:#64748b;margin-top:2px">Şirket hesabı</div>
      </div>
    </div>''' + msg_html + '''
    <form method="POST" action="/register">
      <input type="hidden" name="profile_type" id="reg-type-val" value="sahis">
      <label id="reg-name-label">Ad Soyad</label>
      <input type="text" name="display_name" id="reg-name" placeholder="Ad Soyad" autocomplete="name">
      <label>Kullanıcı Adı</label>
      <input type="text" name="username" placeholder="kullanici_adi" required autocomplete="username">
      <label>E-posta</label>
      <input type="email" name="email" placeholder="ornek@gmail.com" required autocomplete="email">
      <label>Şifre (en az 6 karakter)</label>
      <input type="password" name="password" required autocomplete="new-password">
      <label>Şifre Tekrar</label>
      <input type="password" name="confirm" required autocomplete="new-password">
      <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:14px">
        <input type="checkbox" id="kvkk-check" required style="width:auto;margin:3px 0 0;flex-shrink:0">
        <label for="kvkk-check" style="font-size:.75rem;color:#64748b;cursor:pointer">
          <a href="/kvkk" target="_blank" style="color:#818cf8">KVKK</a>,
          <a href="/gizlilik" target="_blank" style="color:#818cf8">Gizlilik</a> ve
          <a href="/kullanim-kosullari" target="_blank" style="color:#818cf8">Kullanım Koşulları</a>\'nı okudum, kabul ediyorum.
        </label>
      </div>
      <button class="btn" type="submit" id="reg-btn">Bireysel Hesap Oluştur</button>
    </form>
    <div class="link">Zaten hesabın var mı? <a href="/login">Giriş Yap</a></div>
    <script>
    function setRegType(el,t){
      document.getElementById("reg-type-val").value=t;
      document.getElementById("reg-sahis").style.borderColor=t==="sahis"?"#6366f1":"#2a2f45";
      document.getElementById("reg-sahis").style.background=t==="sahis"?"#1a1d26":"#111318";
      document.getElementById("reg-sirket").style.borderColor=t==="sirket"?"#6366f1":"#2a2f45";
      document.getElementById("reg-sirket").style.background=t==="sirket"?"#1a1d26":"#111318";
      if(t==="sahis"){
        document.getElementById("reg-name-label").textContent="Ad Soyad";
        document.getElementById("reg-name").placeholder="Ad Soyad";
        document.getElementById("reg-btn").textContent="Bireysel Hesap Oluştur";
      } else {
        document.getElementById("reg-name-label").textContent="Şirket Ünvanı";
        document.getElementById("reg-name").placeholder="Şirket A.Ş.";
        document.getElementById("reg-btn").textContent="Ticari Hesap Oluştur";
      }
    }
    </script>''')

    elif mode == "login":
        form = msg_html + '''
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:24px">
      <div id="login-bir" onclick="setLoginType('bireysel')" style="border:2px solid #6366f1;border-radius:11px;padding:12px 10px;text-align:center;cursor:pointer;background:#1a1d26;transition:.2s">
        <div style="font-size:1.3rem;margin-bottom:3px">&#128100;</div>
        <div id="login-bir-lbl" style="font-size:.82rem;font-weight:700;color:#e2e8f0">Bireysel</div>
      </div>
      <div id="login-tic" onclick="setLoginType('ticari')" style="border:2px solid #2a2f45;border-radius:11px;padding:12px 10px;text-align:center;cursor:pointer;background:#111318;transition:.2s">
        <div style="font-size:1.3rem;margin-bottom:3px">&#127970;</div>
        <div id="login-tic-lbl" style="font-size:.82rem;font-weight:700;color:#94a3b8">Ticari</div>
      </div>
    </div>
    <form method="POST" action="/login">
      <label id="login-uname-label">Kullanıcı Adı</label>
      <input type="text" name="username" required autocomplete="username">
      <label>Şifre</label>
      <input type="password" name="password" required autocomplete="current-password">
      <button class="btn" type="submit" id="login-btn">Bireysel Giriş Yap</button>
    </form>
    <div class="link" style="margin-top:12px"><a href="/forgot-password">Şifremi unuttum</a></div>
    <div class="link">Hesabın yok mu? <a href="/register">Kayıt Ol</a></div>
    <script>
    function setLoginType(t){
      var isBir=t==="bireysel";
      document.getElementById("login-bir").style.borderColor=isBir?"#6366f1":"#2a2f45";
      document.getElementById("login-bir").style.background=isBir?"#1a1d26":"#111318";
      document.getElementById("login-bir-lbl").style.color=isBir?"#e2e8f0":"#94a3b8";
      document.getElementById("login-tic").style.borderColor=!isBir?"#6366f1":"#2a2f45";
      document.getElementById("login-tic").style.background=!isBir?"#1a1d26":"#111318";
      document.getElementById("login-tic-lbl").style.color=!isBir?"#e2e8f0":"#94a3b8";
      document.getElementById("login-btn").textContent=isBir?"Bireysel Giriş Yap":"Ticari Giriş Yap";
      document.getElementById("login-uname-label").textContent=isBir?"Kullanıcı Adı":"Kullanıcı Adı / Vergi No";
    }
    </script>'''

    elif mode == "forgot":
        form = f"""
    <h2 style="font-size:1.1rem;font-weight:700;margin-bottom:8px;text-align:center">Şifremi Unuttum</h2>
    <p style="text-align:center;color:#64748b;font-size:.82rem;margin-bottom:20px">Kullanıcı adın veya email adresin ile şifre sıfırlama linki alabilirsin.</p>
    {msg_html}
    <form method="POST" action="/forgot-password">
      <label>Kullanıcı Adı veya Email</label>
      <input type="text" name="identifier" required placeholder="kullanici_adi veya ornek@gmail.com" autocomplete="username email">
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

    elif mode == "resend_verify":
        form = f"""
    <h2 style="font-size:1.1rem;font-weight:700;margin-bottom:8px;text-align:center">Doğrulama Maili Gönder</h2>
    <p style="text-align:center;color:#64748b;font-size:.82rem;margin-bottom:20px">Kayıt emailini girerek yeni doğrulama linki alabilirsin.</p>
    {{msg_html}}
    <form method="POST" action="/resend-verify">
      <label>Email Adresi</label>
      <input type="email" name="email" required placeholder="ornek@gmail.com" autocomplete="email">
      <button class="btn" type="submit">Doğrulama Maili Gönder</button>
    </form>
    <div class="link"><a href="/login">← Giriş ekranına dön</a></div>"""

    else:  # reset_invalid
        form = f"""
    <div style="text-align:center;padding:20px 0">
      <div style="font-size:3rem;margin-bottom:16px">⚠️</div>
      <h2 style="font-size:1.1rem;font-weight:700;margin-bottom:12px">Link Geçersiz</h2>
      {{msg_html}}
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
.page{display:none;padding:28px 28px;max-width:1280px;will-change:opacity,transform;opacity:0;transform:translateY(10px)}
.page.active{display:block;opacity:1;transform:translateY(0);transition:opacity .22s ease,transform .22s ease}
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

/* ── HERO BALANCE CARD ────────────────────────────────────── */
.hero-card{background:linear-gradient(135deg,#1a1f3a 0%,#0d1025 100%);border:1px solid #6366f128;border-radius:20px;padding:22px 20px 18px;margin-bottom:4px;position:relative;overflow:hidden}
.hero-card::before{content:'';position:absolute;top:-50px;right:-40px;width:180px;height:180px;border-radius:50%;background:radial-gradient(circle,#6366f120,transparent 70%)}
.hero-card::after{content:'';position:absolute;bottom:-40px;left:-20px;width:140px;height:140px;border-radius:50%;background:radial-gradient(circle,#22c55e12,transparent 70%)}
.hero-greeting{font-size:.8rem;color:var(--txt2);margin-bottom:2px;font-weight:500;position:relative}
.hero-bal-lbl{font-size:.63rem;text-transform:uppercase;letter-spacing:.13em;color:#818cf8;margin-bottom:5px;font-weight:600;position:relative}
.hero-balance{font-size:2.5rem;font-weight:900;letter-spacing:-.04em;line-height:1;margin-bottom:4px;color:#e2e8f0;position:relative}
.hero-net-sub{font-size:.72rem;color:var(--txt2);margin-bottom:14px;min-height:14px;position:relative}
.hero-chips{display:flex;gap:7px;flex-wrap:wrap;position:relative}
.hero-chip{display:flex;align-items:center;gap:4px;padding:5px 11px;border-radius:20px;font-size:.76rem;font-weight:600}
.hero-chip.gn{background:#22c55e14;color:var(--g);border:1px solid #22c55e25}
.hero-chip.rd{background:#ef444414;color:var(--r);border:1px solid #ef444425}
.hero-chip.nt{background:#6366f114;color:var(--b2);border:1px solid #6366f125}

/* ── CLICKABLE CHIP ──────────────────────────────────────────── */
.hero-chip{cursor:pointer;transition:.15s}
.hero-chip:hover{opacity:.8;transform:translateY(-1px)}
.hero-chip:active{opacity:.6}

/* ── TODAY SUBTOTAL ROW ──────────────────────────────────────── */
.today-subtotal{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-radius:10px;margin-top:8px;font-size:.85rem;font-weight:700}
.today-subtotal-gn{background:#22c55e14;border:1px solid #22c55e25;color:var(--g)}
.today-subtotal-rd{background:#ef444414;border:1px solid #ef444425;color:var(--r)}
.today-net-row{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;background:var(--bg2);border:1px solid var(--border2);border-radius:14px;margin-bottom:16px}
.tnr-label{font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--txt2)}
.tnr-value{font-size:1.2rem;font-weight:900;letter-spacing:-.02em}

/* ── TODAY TX ITEM ──────────────────────────────────────────── */
.tx-day-item{display:flex;align-items:center;gap:11px;padding:10px 14px;background:var(--bg2);border:1px solid var(--border);border-radius:12px;margin-bottom:7px;cursor:pointer;transition:.1s}
.tx-day-item:last-child{margin-bottom:0}
.tx-day-item:active{background:var(--bg3)}
.tx-day-icon{width:34px;height:34px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:.82rem;font-weight:700;flex-shrink:0}
.tx-day-icon.gn{background:#22c55e14;border:1px solid #22c55e25;color:var(--g)}
.tx-day-icon.rd{background:#ef444414;border:1px solid #ef444425;color:var(--r)}
.tx-day-info{flex:1;min-width:0}
.tx-day-cat{font-size:.83rem;font-weight:600;color:var(--txt);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tx-day-desc{font-size:.71rem;color:var(--txt2);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tx-day-amt{font-size:.88rem;font-weight:700;flex-shrink:0}

/* ── COLLAPSIBLE SECTIONS ──────────────────────────────────── */
.s-header{display:flex;align-items:center;gap:10px;padding:13px 0 10px;cursor:pointer;user-select:none;-webkit-tap-highlight-color:transparent;border-bottom:1px solid var(--border)}
.s-header:active{opacity:.7}
.sh-left{display:flex;align-items:center;gap:8px;flex:1;font-size:.74rem;font-weight:700;color:var(--txt);text-transform:uppercase;letter-spacing:.07em}
.sh-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.sh-dot.gn{background:var(--g);box-shadow:0 0 5px #22c55e80}
.sh-dot.rd{background:var(--r);box-shadow:0 0 5px #ef444480}
.sh-dot.bl{background:var(--b2);box-shadow:0 0 5px #818cf880}
.sh-dot.yl{background:var(--y);box-shadow:0 0 5px #f59e0b80}
.sh-dot.cy{background:var(--c);box-shadow:0 0 5px #06b6d480}
.sh-dot.pp{background:var(--p);box-shadow:0 0 5px #a855f780}
.sh-badge{background:var(--b);color:#fff;font-size:.64rem;font-weight:800;padding:2px 8px;border-radius:10px;min-width:20px;text-align:center;line-height:1.5}
.sh-chevron{color:var(--txt2);font-size:.78rem;flex-shrink:0;display:inline-block;transition:transform .3s cubic-bezier(.4,0,.2,1)}
.sh-chevron.closed{transform:rotate(-90deg)}
.s-body{overflow:hidden;max-height:3000px;opacity:1;padding-top:12px;margin-bottom:14px;transition:max-height .4s cubic-bezier(.4,0,.2,1),opacity .3s ease,padding-top .3s,margin-bottom .3s}
.s-body.collapsed{max-height:0!important;opacity:0;padding-top:0;margin-bottom:0}

/* ── TODAY SUMMARY CARDS ────────────────────────────────────── */
.today-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
@media(max-width:360px){.today-grid{grid-template-columns:1fr 1fr}}
.today-card{border-radius:14px;padding:13px 12px}
.today-card .tc-lbl{font-size:.63rem;text-transform:uppercase;letter-spacing:.09em;font-weight:700;margin-bottom:5px}
.today-card .tc-val{font-size:1rem;font-weight:800;letter-spacing:-.02em;line-height:1}
.today-card.gn{background:linear-gradient(135deg,#0d2118,#0a1a12);border:1px solid #22c55e20}
.today-card.gn .tc-lbl,.today-card.gn .tc-val{color:var(--g)}
.today-card.rd{background:linear-gradient(135deg,#1f0e0e,#180a0a);border:1px solid #ef444420}
.today-card.rd .tc-lbl,.today-card.rd .tc-val{color:var(--r)}
.today-card.nt{background:linear-gradient(135deg,#14182a,#0f1220);border:1px solid #6366f120}
.today-card.nt .tc-lbl,.today-card.nt .tc-val{color:var(--b2)}

/* ── UPCOMING PAYMENTS ─────────────────────────────────────── */
.pay-item{display:flex;align-items:center;gap:12px;padding:11px 14px;background:var(--bg2);border:1px solid var(--border);border-radius:13px;margin-bottom:8px}
.pay-item:last-child{margin-bottom:0}
.pay-icon{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:.9rem;flex-shrink:0;font-weight:700}
.pay-icon.gn{background:#22c55e14;border:1px solid #22c55e25;color:var(--g)}
.pay-icon.rd{background:#ef444414;border:1px solid #ef444425;color:var(--r)}
.pay-info{flex:1;min-width:0}
.pay-desc{font-size:.84rem;font-weight:600;color:var(--txt);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pay-meta{font-size:.71rem;color:var(--txt2);margin-top:2px}
.pay-right{text-align:right;flex-shrink:0}
.pay-amount{font-size:.86rem;font-weight:700}
.pay-days{font-size:.69rem;margin-top:3px}
.pay-days.urgent{color:var(--r);font-weight:700}
.pay-days.soon{color:var(--y)}
.pay-days.ok{color:var(--txt2)}
.empty-pay{text-align:center;padding:22px 16px;color:var(--txt2)}
.empty-pay .ep-ico{font-size:1.8rem;opacity:.3;margin-bottom:8px}
.empty-pay .ep-txt{font-size:.8rem}

/* ── CREDIT CARD OVERVIEW ──────────────────────────────────── */
.cc-total-row{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px}
.cc-total-cell{background:var(--bg2);border:1px solid var(--border);border-radius:11px;padding:10px 12px}
.cc-total-cell .ccl{font-size:.62rem;text-transform:uppercase;letter-spacing:.08em;color:var(--txt2);margin-bottom:3px;font-weight:600}
.cc-total-cell .ccv{font-size:.88rem;font-weight:800}
.cc-item{background:var(--bg2);border:1px solid var(--border);border-radius:13px;padding:13px 14px;margin-bottom:8px}
.cc-item:last-child{margin-bottom:0}
.cc-item-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:9px}
.cc-bank{font-size:.83rem;font-weight:700;color:var(--txt)}
.cc-pct-badge{font-size:.66rem;font-weight:700;padding:3px 9px;border-radius:8px}
.cc-pct-badge.ok{background:#22c55e14;color:var(--g);border:1px solid #22c55e25}
.cc-pct-badge.warn{background:#f59e0b14;color:var(--y);border:1px solid #f59e0b25}
.cc-pct-badge.high{background:#ef444414;color:var(--r);border:1px solid #ef444425}
.cc-prog-bg{background:var(--bg3);border-radius:6px;height:5px;overflow:hidden;margin-bottom:7px}
.cc-prog-fill{height:100%;border-radius:6px;transition:width .7s cubic-bezier(.4,0,.2,1)}
.cc-nums{display:flex;justify-content:space-between;font-size:.72rem;color:var(--txt2)}
.cc-nums strong{color:var(--txt);font-weight:600}
.empty-cc{text-align:center;padding:22px 16px;color:var(--txt2);font-size:.82rem;line-height:1.7}

/* ── MOBILE NAV ENHANCEMENTS ────────────────────────────────── */
.nl-desktop{}
@media(max-width:768px){
  nav{height:64px;padding:0;box-shadow:0 -1px 0 var(--border),0 -4px 20px rgba(0,0,0,.5)}
  .main{margin-bottom:64px}
  .nl-desktop{display:none!important}
  .nav-links{justify-content:space-around}
  .nl{border-radius:10px;padding:5px 8px;min-width:50px;gap:2px;flex:1;max-width:80px}
  .nl.active{background:transparent;border:none}
  .nl.active .ico{color:var(--b2)}
  .nl.active span:not(.ico){color:var(--b2)}
  .nl-add{flex:0 0 64px;position:relative}
  .nl-add .ico{
    background:linear-gradient(135deg,#6366f1,#818cf8);
    color:#fff;border-radius:50%;
    width:44px;height:44px;
    display:flex;align-items:center;justify-content:center;
    font-size:1.3rem;
    box-shadow:0 4px 14px #6366f160;
    margin-top:-18px;
    border:3px solid var(--bg);
  }
  .nl-add span:not(.ico){color:var(--b2);font-weight:700}
}
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
    <div class="nl nl-add" data-page="add" onclick="goPage('add',this)">
      <span class="ico">➕</span>Ekle
    </div>
    <div class="nl" data-page="recurring" onclick="goPage('recurring',this)">
      <span class="ico">🔁</span>Düzenli
    </div>
    <div class="nl" data-page="budget" onclick="goPage('budget',this)">
      <span class="ico">🎯</span>Bütçe
    </div>
    <div class="nl nl-desktop" data-page="import" onclick="goPage('import',this)">
      <span class="ico">📂</span>İçe Aktar
    </div>
    <div class="nl nl-desktop" data-page="invest" onclick="goPage('invest',this)">
      <span class="ico">📈</span>Yatırım
    </div>
    <div class="nl nl-desktop" data-page="cards" onclick="goPage('cards',this)">
      <span class="ico">💳</span>Kartlar
    </div>
  </div>
  <div class="nav-bottom">
    <!-- Profil göstergesi ve geçiş -->
    <div id="profile-badge" onclick="toggleProfileMenu()" style="cursor:pointer;background:var(--bg3);border:1px solid var(--border2);border-radius:10px;padding:10px 12px;margin-bottom:10px;transition:.2s" onmouseover="this.style.borderColor='var(--b)'" onmouseout="this.style.borderColor='var(--border2)'">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <div id="profile-name-badge" style="font-size:.82rem;font-weight:700;color:var(--txt)">Şahıs</div>
          <div id="profile-type-badge" style="font-size:.7rem;color:var(--txt2)">Kişisel Profil</div>
        </div>
        <span style="color:var(--txt2);font-size:.85rem">⇅</span>
      </div>
    </div>
    <div id="profile-menu" style="display:none;background:var(--bg3);border:1px solid var(--border2);border-radius:10px;padding:8px;margin-bottom:10px">
      <div id="profile-list"></div>
      <button onclick="showAddProfile()" style="width:100%;margin-top:6px;padding:8px;background:transparent;border:1px dashed var(--border2);border-radius:7px;color:var(--b2);font-size:.75rem;cursor:pointer;font-weight:600">+ Yeni Kullanıcı Ekle</button>
    </div>
    <div id="add-profile-form" style="display:none;background:var(--bg3);border:1px solid var(--border2);border-radius:10px;padding:10px;margin-bottom:10px">
      <div style="font-size:.72rem;color:var(--txt2);margin-bottom:6px;font-weight:600">YENİ PROFİL</div>
      <select id="new-profile-type" style="width:100%;background:var(--bg);border:1px solid var(--border2);color:var(--txt);padding:7px 10px;border-radius:7px;font-size:.8rem;margin-bottom:6px;outline:none">
        <option value="sahis">👤 Şahıs (Kişisel)</option>
        <option value="sirket">🏢 Şirket (Kurumsal)</option>
      </select>
      <input id="new-profile-name" placeholder="İsim ya da Ünvan" style="width:100%;background:var(--bg);border:1px solid var(--border2);color:var(--txt);padding:7px 10px;border-radius:7px;font-size:.8rem;margin-bottom:8px;outline:none">
      <div style="display:flex;gap:6px">
        <button onclick="createProfile()" style="flex:1;padding:7px;background:var(--b);border:none;border-radius:7px;color:#fff;font-size:.78rem;cursor:pointer;font-weight:600">Profil Oluştur</button>
        <button onclick="cancelAddProfile()" style="padding:7px 10px;background:transparent;border:1px solid var(--border2);border-radius:7px;color:var(--txt2);font-size:.78rem;cursor:pointer">İptal</button>
      </div>
    </div>
    <div style="font-size:.75rem;color:var(--txt2);margin-bottom:8px">👤 <strong style="color:var(--txt)">__USER_DISPLAY__</strong></div>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <a href="/logout" style="color:#ef4444;font-size:.72rem;text-decoration:none">↩ Çıkış</a>
      <span onclick="triggerInstall()" style="color:#818cf8;font-size:.72rem;cursor:pointer;text-decoration:none">⬇ Uygulamayı Kur</span>
      <a href="/kvkk" style="color:#475569;font-size:.72rem;text-decoration:none">KVKK</a>
      <a href="/gizlilik" style="color:#475569;font-size:.72rem;text-decoration:none">Gizlilik</a>
      <a href="/kullanim-kosullari" style="color:#475569;font-size:.72rem;text-decoration:none">Koşullar</a>
    </div>
  </div>
</nav>

<!-- ── MAIN ── -->
<div class="main">

<!-- DASHBOARD -->
<div class="page active" id="page-dashboard">

  <!-- ── HERO BALANCE ── -->
  <div class="hero-card">
    <div class="hero-greeting" id="hero-greeting">Merhaba __USER_DISPLAY__ 👋</div>
    <div class="hero-bal-lbl">TOPLAM BİRİKİM</div>
    <div class="hero-balance" id="s-bal">—</div>
    <div class="hero-net-sub" id="s-net-sub"></div>
    <div class="hero-chips">
      <span class="hero-chip gn" onclick="filterLedgerTo('gelir')" title="Gelirleri görüntüle">↑ <span id="s-gelir">—</span></span>
      <span class="hero-chip rd" onclick="filterLedgerTo('gider')" title="Giderleri görüntüle">↓ <span id="s-gider">—</span></span>
      <span class="hero-chip nt" onclick="filterLedgerTo('')" title="Tüm işlemleri görüntüle">= <span id="s-net">—</span></span>
    </div>
    <span id="s-gelir-sub" style="display:none"></span>
    <span id="s-gider-sub" style="display:none"></span>
  </div>

  <!-- ── GÜNÜN GELİRLERİ ── -->
  <div class="s-header" onclick="toggleSection('gelir')">
    <div class="sh-left"><span class="sh-dot gn"></span>Günün Gelirleri</div>
    <span class="sh-badge" id="gelir-badge" style="display:none">0</span>
    <span class="sh-chevron" id="chevron-gelir">▾</span>
  </div>
  <div class="s-body" id="sec-gelir">
    <div id="today-gelir-list"><div class="empty-pay"><div class="ep-ico">📅</div><div class="ep-txt">Yükleniyor…</div></div></div>
    <div class="today-subtotal today-subtotal-gn" id="today-gelir-total" style="display:none">
      <span>Toplam Gelir</span><span id="today-gelir">—</span>
    </div>
  </div>

  <!-- ── GÜNÜN GİDERLERİ ── -->
  <div class="s-header" onclick="toggleSection('gider')">
    <div class="sh-left"><span class="sh-dot rd"></span>Günün Giderleri</div>
    <span class="sh-badge" id="gider-badge" style="display:none">0</span>
    <span class="sh-chevron" id="chevron-gider">▾</span>
  </div>
  <div class="s-body" id="sec-gider">
    <div id="today-gider-list"><div class="empty-pay"><div class="ep-ico">📅</div><div class="ep-txt">Yükleniyor…</div></div></div>
    <div class="today-subtotal today-subtotal-rd" id="today-gider-total" style="display:none">
      <span>Toplam Gider</span><span id="today-gider">—</span>
    </div>
  </div>

  <!-- ── GÜNÜN BAKİYESİ ── -->
  <div class="today-net-row" id="today-net-row" style="display:none">
    <div class="tnr-label">Günün Bakiyesi</div>
    <div class="tnr-value" id="today-net">—</div>
  </div>

  <!-- ── KREDİ KARTLARI ── -->
  <div class="s-header" onclick="toggleSection('cc')">
    <div class="sh-left"><span class="sh-dot pp"></span>Kredi Kartları</div>
    <span class="sh-chevron" id="chevron-cc">▾</span>
  </div>
  <div class="s-body" id="sec-cc">
    <div id="cc-overview"><div class="empty-cc">Yükleniyor…</div></div>
  </div>

  <!-- ── FİNANSAL DURUM ── -->
  <div class="s-header" onclick="toggleSection('health')">
    <div class="sh-left"><span class="sh-dot cy"></span>Finansal Durum</div>
    <div id="health-badge" class="health-badge" style="color:var(--txt2);border-color:var(--border2);font-size:.7rem;padding:3px 10px">—</div>
    <span class="sh-chevron" id="chevron-health">▾</span>
  </div>
  <div class="s-body" id="sec-health">
    <div class="card motiv-card" style="margin-bottom:0">
      <div class="motiv-bar-bg"><div id="motiv-fill" class="motiv-bar-fill" style="width:0%"></div></div>
      <div id="motiv-msgs" class="motiv-msgs"><div style="color:var(--txt2);font-size:.83rem">Yükleniyor…</div></div>
    </div>
  </div>

  <!-- ── ANALİZ ── -->
  <div class="s-header" onclick="toggleSection('analytics')">
    <div class="sh-left"><span class="sh-dot bl"></span>Analiz <span id="db-sub" style="font-size:.7rem;font-weight:400;color:var(--txt2);text-transform:none;letter-spacing:0;margin-left:6px"></span></div>
    <span class="sh-chevron" id="chevron-analytics">▾</span>
  </div>
  <div class="s-body" id="sec-analytics">
    <div style="display:flex;align-items:center;justify-content:flex-end;margin-bottom:14px;gap:8px;flex-wrap:wrap">
      <div style="display:flex;background:var(--bg3);border:1px solid var(--border2);border-radius:8px;overflow:hidden">
        <button id="view-month-btn" onclick="setDbView('month')"
          style="padding:6px 14px;border:none;font-size:.78rem;font-weight:600;cursor:pointer;background:var(--b);color:#fff;transition:.15s">Aylık</button>
        <button id="view-year-btn" onclick="setDbView('year')"
          style="padding:6px 14px;border:none;font-size:.78rem;font-weight:600;cursor:pointer;background:transparent;color:var(--txt2);transition:.15s">Yıllık</button>
      </div>
      <div class="mnav" id="month-nav">
        <button onclick="changeMonth(-1)">‹</button>
        <div class="ml" id="mlabel" onclick="toggleDateRange()" style="cursor:pointer;user-select:none" title="Tarih aralığı seç"></div>
        <button onclick="changeMonth(1)">›</button>
      </div>
      <div class="mnav" id="year-nav" style="display:none">
        <button onclick="changeYear(-1)">‹</button>
        <div class="ml" id="ylabel"></div>
        <button onclick="changeYear(1)">›</button>
      </div>
    </div>
    <div id="date-range-picker" style="display:none;background:var(--bg3);border:1px solid var(--border2);border-radius:10px;padding:10px;margin-bottom:12px;box-shadow:0 8px 24px rgba(0,0,0,.5)">
      <div style="font-size:.72rem;color:var(--txt2);margin-bottom:8px;font-weight:600">TARİH ARALIĞI</div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <div>
          <div style="font-size:.7rem;color:var(--txt2);margin-bottom:3px">Başlangıç</div>
          <input type="date" id="range-start" style="background:var(--bg);border:1px solid var(--border2);color:var(--txt);padding:6px 8px;border-radius:7px;font-size:.8rem;outline:none">
        </div>
        <div>
          <div style="font-size:.7rem;color:var(--txt2);margin-bottom:3px">Bitiş</div>
          <input type="date" id="range-end" style="background:var(--bg);border:1px solid var(--border2);color:var(--txt);padding:6px 8px;border-radius:7px;font-size:.8rem;outline:none">
        </div>
        <div style="display:flex;gap:6px;margin-top:16px">
          <button onclick="applyDateRange()" style="padding:6px 14px;background:var(--b);border:none;border-radius:7px;color:#fff;font-size:.78rem;cursor:pointer;font-weight:600">Uygula</button>
          <button onclick="clearDateRange()" style="padding:6px 10px;background:transparent;border:1px solid var(--border2);border-radius:7px;color:var(--txt2);font-size:.78rem;cursor:pointer">Temizle</button>
        </div>
      </div>
    </div>
    <div class="grid2">
      <div class="card"><div class="chart-lbl">Aylık Gelir / Gider</div><div class="chart-wrap"><canvas id="barChart" height="190"></canvas></div></div>
      <div class="card"><div class="chart-lbl">Gider Dağılımı</div><div class="chart-wrap"><canvas id="donut" height="190"></canvas></div></div>
    </div>
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
        <input class="f-input" type="text" inputmode="decimal" data-num id="calc-tl" placeholder="50.000" oninput="calcInvest()">
      </div>
      <div style="flex:1;min-width:120px">
        <label>O gündeki kur</label>
        <input class="f-input" type="text" inputmode="decimal" data-num id="calc-buy" placeholder="32,50" oninput="calcInvest()">
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
        <div><label id="inv-qty-lbl">Miktar</label><input class="f-input" type="text" inputmode="decimal" data-num id="inv-qty" placeholder="1.000"></div>
        <div><label id="inv-price-lbl">Alış Fiyatı (TRY)</label><input class="f-input" type="text" inputmode="decimal" data-num id="inv-price" placeholder="32,50"></div>
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
        <div><label>Tutar (₺)</label><input class="f-input" type="text" inputmode="decimal" data-num id="rec-amount" placeholder="0,00"></div>
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
      <div class="form-row" style="margin-bottom:10px">
        <div>
          <label>Yıl</label>
          <select class="f-input" id="rec-apply-year"></select>
        </div>
        <div>
          <label>Başlangıç Ayı</label>
          <select class="f-input" id="rec-apply-month-start">
            <option value="1">Ocak</option><option value="2">Şubat</option>
            <option value="3">Mart</option><option value="4">Nisan</option>
            <option value="5">Mayıs</option><option value="6">Haziran</option>
            <option value="7">Temmuz</option><option value="8">Ağustos</option>
            <option value="9">Eylül</option><option value="10">Ekim</option>
            <option value="11">Kasım</option><option value="12">Aralık</option>
          </select>
        </div>
        <div>
          <label>Bitiş Ayı</label>
          <select class="f-input" id="rec-apply-month-end">
            <option value="1">Ocak</option><option value="2">Şubat</option>
            <option value="3">Mart</option><option value="4">Nisan</option>
            <option value="5">Mayıs</option><option value="6">Haziran</option>
            <option value="7">Temmuz</option><option value="8">Ağustos</option>
            <option value="9">Eylül</option><option value="10">Ekim</option>
            <option value="11">Kasım</option><option value="12" selected>Aralık</option>
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
        <div><label>Toplam Limit (₺)</label><input class="f-input" type="text" inputmode="decimal" data-num id="card-limit" placeholder="50.000"></div>
        <div><label>Mevcut Borç (₺)</label><input class="f-input" type="text" inputmode="decimal" data-num id="card-used" placeholder="12.000"></div>
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
      <div style="margin-bottom:16px"><label>Aylık Limit (₺)</label><input class="f-input" type="text" inputmode="decimal" data-num id="b-limit" placeholder="5.000"></div>
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
  // Time-based greeting
  var h=new Date().getHours();
  var prefix=h<5?'İyi geceler':h<12?'Günaydın':h<18?'İyi günler':'İyi akşamlar';
  var gEl=document.getElementById('hero-greeting');
  if(gEl) gEl.textContent=gEl.textContent.replace('Merhaba',prefix);
  loadCats(function(){
    loadDashboard();
    loadAllTx();
    populateYearFilter();
  });
  setupDrop();
  loadProfiles();
  setupNumInputs();
};

function updateMonthLabel(){
  document.getElementById('mlabel').textContent=MONTHS[curMonth]+' '+curYear;
  document.getElementById('db-sub').textContent=MONTHS[curMonth]+' '+curYear;
}

// ── NAVIGATION ───────────────────────────────────────────────────────────────
function goPage(id, el){
  var prev = document.querySelector('.page.active');
  var next = document.getElementById('page-'+id);
  if(prev && prev === next) return;

  document.querySelectorAll('.nl').forEach(function(n){n.classList.remove('active')});
  if(el) el.classList.add('active');

  function show(){
    document.querySelectorAll('.page').forEach(function(p){
      p.classList.remove('active');
      p.style.transition='none';
      p.style.opacity='0';
      p.style.transform='translateY(12px)';
      p.style.display='none';
    });
    next.style.display='block';
    next.style.opacity='0';
    next.style.transform='translateY(12px)';
    next.style.transition='none';
    requestAnimationFrame(function(){
      requestAnimationFrame(function(){
        next.style.transition='opacity .24s ease,transform .24s ease';
        next.style.opacity='1';
        next.style.transform='translateY(0)';
        next.classList.add('active');
      });
    });
    if(id==='ledger') renderLedger();
    if(id==='dashboard') loadDashboard();
    if(id==='recurring') initRecurringPage();
    if(id==='invest') initInvestPage();
    if(id==='cards') loadCards();
  }

  if(prev){
    prev.style.transition='opacity .16s ease,transform .16s ease';
    prev.style.opacity='0';
    prev.style.transform='translateY(8px)';
    setTimeout(show, 160);
  } else {
    show();
  }
}

// ── PROFILE SWITCHER ─────────────────────────────────────────────────────────
var _profiles=[];
function loadProfiles(){
  xhr('/api/me',null,function(me){
    document.getElementById('profile-name-badge').textContent=me.profile_name||'Şahıs';
    document.getElementById('profile-type-badge').textContent=me.profile_type==='sirket'?'🏢 Şirket Profili':'👤 Kişisel Profil';
  });
  xhr('/api/profiles',null,function(list){
    _profiles=list;
  });
}
function toggleProfileMenu(){
  var m=document.getElementById('profile-menu');
  var f=document.getElementById('add-profile-form');
  if(m.style.display==='none'){
    renderProfileList();
    m.style.display='block'; f.style.display='none';
  } else {
    m.style.display='none';
  }
}
function renderProfileList(){
  var html='';
  _profiles.forEach(function(p){
    var icon=p.type==='sirket'?'🏢':'👤';
    html+='<div style="display:flex;align-items:center;justify-content:space-between;padding:7px 8px;border-radius:7px;cursor:pointer;transition:.15s" onmouseover="this.style.background=\'#1e2233\'" onmouseout="this.style.background=\'transparent\'" onclick="switchProfile('+p.id+')">'
      +'<span style="font-size:.82rem;color:var(--txt)">'+icon+' '+p.name+'</span>'
      +'</div>';
  });
  document.getElementById('profile-list').innerHTML=html;
}
function switchProfile(pid){
  xhr('/api/profiles/'+pid+'/switch','POST',function(d){
    if(!d.ok) return;
    document.getElementById('profile-menu').style.display='none';
    document.getElementById('profile-name-badge').textContent=d.name;
    document.getElementById('profile-type-badge').textContent=d.type==='sirket'?'🏢 Şirket Profili':'👤 Kişisel Profil';
    // Show toast
    showToast('Profil değiştirildi: '+d.name,'#6366f1');
    // Reload current page data
    loadDashboard(); renderLedger();
  });
}
function showAddProfile(){
  document.getElementById('add-profile-form').style.display='block';
  document.getElementById('profile-menu').style.display='none';
}
function cancelAddProfile(){
  document.getElementById('add-profile-form').style.display='none';
}
function createProfile(){
  var name=document.getElementById('new-profile-name').value.trim();
  var type=document.getElementById('new-profile-type').value;
  if(!name){ showToast('İsim / Ünvan zorunlu','#ef4444'); return; }
  xhr('/api/profiles',{name:name,type:type},function(d){
    if(!d.ok){ showToast('Hata: '+(d.error||'Oluşturulamadı'),'#ef4444'); return; }
    _profiles.push(d);
    switchProfile(d.id);
    document.getElementById('new-profile-name').value='';
    document.getElementById('add-profile-form').style.display='none';
    renderProfileList();
    showToast('Profil oluşturuldu: '+d.name,'#22c55e');
  });
}
function showToast(msg,color){
  var t=document.createElement('div');
  t.textContent=msg;
  t.style.cssText='position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:'+color+';color:#fff;padding:10px 20px;border-radius:20px;font-size:.85rem;font-weight:600;z-index:9999;opacity:0;transition:opacity .3s';
  document.body.appendChild(t);
  requestAnimationFrame(function(){ t.style.opacity='1'; });
  setTimeout(function(){ t.style.opacity='0'; setTimeout(function(){ t.remove(); },300); },2500);
}

// ── MONTH NAV & DATE RANGE ───────────────────────────────────────────────────
var _dateRangeActive=false, _rangeStart='', _rangeEnd='';
function changeMonth(d){
  if(_dateRangeActive) return;
  curMonth+=d;
  if(curMonth>12){curMonth=1;curYear++}
  if(curMonth<1){curMonth=12;curYear--}
  updateMonthLabel();
  loadDashboard();
}
function toggleDateRange(){
  var p=document.getElementById('date-range-picker');
  p.style.display = p.style.display==='none' ? 'block' : 'none';
}
function applyDateRange(){
  var s=document.getElementById('range-start').value;
  var e=document.getElementById('range-end').value;
  if(!s||!e){ showToast('Başlangıç ve bitiş tarihi seçin','#ef4444'); return; }
  if(s>e){ showToast('Başlangıç tarihi bitiş tarihinden önce olmalı','#ef4444'); return; }
  _dateRangeActive=true; _rangeStart=s; _rangeEnd=e;
  document.getElementById('mlabel').textContent=s.slice(5)+' → '+e.slice(5);
  document.getElementById('date-range-picker').style.display='none';
  loadDashboard();
}
function clearDateRange(){
  _dateRangeActive=false; _rangeStart=''; _rangeEnd='';
  document.getElementById('range-start').value='';
  document.getElementById('range-end').value='';
  document.getElementById('date-range-picker').style.display='none';
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
// ── COLLAPSIBLE SECTIONS ─────────────────────────────────────────────────────
function toggleSection(id){
  var body=document.getElementById('sec-'+id);
  var chev=document.getElementById('chevron-'+id);
  if(!body) return;
  var isOpen=!body.classList.contains('collapsed');
  body.classList.toggle('collapsed',isOpen);
  if(chev) chev.classList.toggle('closed',isOpen);
}

// ── TODAY WIDGETS ────────────────────────────────────────────────────────────
function renderTxList(listId, txns, type){
  var el=document.getElementById(listId);
  if(!el) return;
  if(!txns||!txns.length){
    var label=type==='gelir'?'Bugün gelir yok':'Bugün gider yok';
    el.innerHTML='<div class="empty-pay"><div class="ep-ico">'+(type==='gelir'?'💚':'🔴')+'</div><div class="ep-txt">'+label+'</div></div>';
    return;
  }
  el.innerHTML=txns.map(function(t){
    var cls=type==='gelir'?'gn':'rd';
    var lbl=type==='gelir'?'+':'-';
    return '<div class="tx-day-item" onclick="goToTx('+t.id+')">'+
      '<div class="tx-day-icon '+cls+'">'+lbl+'</div>'+
      '<div class="tx-day-info">'+
        '<div class="tx-day-cat">'+t.category+'</div>'+
        (t.description?'<div class="tx-day-desc">'+t.description+'</div>':'')+
      '</div>'+
      '<div class="tx-day-amt" style="color:var(--'+(type==='gelir'?'g':'r')+')">'+lbl+fmt(t.amount)+'</div>'+
    '</div>';
  }).join('');
}

function goToTx(id){
  var ledgerEl=document.querySelector('[data-page="ledger"]');
  goPage('ledger',ledgerEl);
  setTimeout(function(){
    var row=document.querySelector('tr[data-id="'+id+'"]');
    if(row){row.scrollIntoView({behavior:'smooth',block:'center'});row.style.background='#6366f120';setTimeout(function(){row.style.background=''},1500);}
  },350);
}

function loadTodayWidgets(){
  xhr('/api/today',null,function(d){
    // Gelir list
    renderTxList('today-gelir-list', d.gelir_list, 'gelir');
    var gb=document.getElementById('gelir-badge');
    var gt=document.getElementById('today-gelir-total');
    var tg=document.getElementById('today-gelir');
    if(d.gelir_list&&d.gelir_list.length){
      if(gb){gb.textContent=d.gelir_list.length;gb.style.display='';}
      if(gt) gt.style.display='flex';
      if(tg) tg.textContent=fmt(d.today_gelir);
    } else {
      if(gb) gb.style.display='none';
      if(gt) gt.style.display='none';
    }

    // Gider list
    renderTxList('today-gider-list', d.gider_list, 'gider');
    var db2=document.getElementById('gider-badge');
    var dt2=document.getElementById('today-gider-total');
    var td=document.getElementById('today-gider');
    if(d.gider_list&&d.gider_list.length){
      if(db2){db2.textContent=d.gider_list.length;db2.style.display='';}
      if(dt2) dt2.style.display='flex';
      if(td) td.textContent=fmt(d.today_gider);
    } else {
      if(db2) db2.style.display='none';
      if(dt2) dt2.style.display='none';
    }

    // Net row
    var nr=document.getElementById('today-net-row');
    var tn=document.getElementById('today-net');
    if(nr&&(d.gelir_list.length||d.gider_list.length)){
      nr.style.display='flex';
      if(tn){tn.textContent=fmt(d.today_net);tn.style.color=d.today_net>=0?'var(--g)':'var(--r)';}
    } else if(nr){
      nr.style.display='none';
    }

    // Credit cards
    var co=document.getElementById('cc-overview');
    if(co){
      if(!d.cards||!d.cards.length){
        co.innerHTML='<div class="empty-cc">💳 Kredi kartı eklenmemiş<br><span style="font-size:.75rem;color:var(--txt2)">Kartlar sayfasından ekleyebilirsiniz</span></div>';
      } else {
        var totals='<div class="cc-total-row">'+
          '<div class="cc-total-cell"><div class="ccl">Toplam Limit</div><div class="ccv" style="color:var(--b2)">'+fmt(d.total_limit)+'</div></div>'+
          '<div class="cc-total-cell"><div class="ccl">Kullanılan</div><div class="ccv" style="color:var(--r)">'+fmt(d.total_used)+'</div></div>'+
          '<div class="cc-total-cell"><div class="ccl">Kullanılabilir</div><div class="ccv" style="color:var(--g)">'+fmt(d.total_avail)+'</div></div>'+
          '</div>';
        var items=d.cards.map(function(c){
          var pct=c.pct||0;
          var pc=pct<50?'ok':pct<80?'warn':'high';
          var fc=pct<50?'var(--g)':pct<80?'var(--y)':'var(--r)';
          var nm=c.bank+(c.name?' · '+c.name:'');
          return '<div class="cc-item" onclick="goPage(\'cards\',document.querySelector(\'[data-page=cards]\'))" style="cursor:pointer">'+
            '<div class="cc-item-top"><div class="cc-bank">💳 '+nm+'</div>'+
            '<span class="cc-pct-badge '+pc+'">%'+pct+'</span></div>'+
            '<div class="cc-prog-bg"><div class="cc-prog-fill" style="width:'+pct+'%;background:'+fc+'"></div></div>'+
            '<div class="cc-nums">'+
              '<span>Kullanılan: <strong style="color:var(--r)">'+fmt(c.used)+'</strong></span>'+
              '<span>Limit: <strong style="color:var(--b2)">'+fmt(c.limit)+'</strong></span>'+
            '</div></div>';
        }).join('');
        co.innerHTML=totals+items;
      }
    }
  });
}

function loadDashboard(){
  var url;
  if(_dateRangeActive){
    url='/api/summary?start='+_rangeStart+'&end='+_rangeEnd;
  } else {
    url='/api/summary?year='+curYear+'&month='+curMonth;
  }
  xhr(url,null,function(d){
    summaryData=d;
    renderStats(d);
    drawBar(d.bar);
    drawDonut(d.gider_cats);
    renderBudgetPage(d.gider_cats,d.budgets);
  });
  xhr('/api/motivation',null,renderMotivation);
  loadTodayWidgets();
}

function fmt(n){return '₺'+Number(n).toLocaleString('tr-TR',{minimumFractionDigits:2,maximumFractionDigits:2})}
function fmtK(n){if(n>=1e6)return(n/1e6).toFixed(1)+'M';if(n>=1e3)return(n/1e3).toFixed(0)+'K';return Math.round(n)+''}
function fmtNum(n){return Number(n).toLocaleString('tr-TR',{minimumFractionDigits:2,maximumFractionDigits:2})}

// ── HERO FILTER SHORTCUT ────────────────────────────────────────────────────
function filterLedgerTo(type){
  var ledgerEl=document.querySelector('[data-page="ledger"]');
  goPage('ledger',ledgerEl);
  setTimeout(function(){
    var sel=document.getElementById('f-type');
    if(sel){sel.value=type;filterLedger();}
  },200);
}

// Tutar inputlarını yazarken formatla (5000 → 5.000 anlık göster)
function setupNumInputs(){
  document.querySelectorAll('input[data-num]').forEach(function(el){
    function formatLive(){
      var pos=el.selectionStart;
      var raw=el.value.replace(/[^\d,]/g,'').replace(',','.');
      var num=parseFloat(raw);
      el.dataset.raw=isNaN(num)?'':num;
      if(!isNaN(num)&&el.value!==''){
        var parts=num.toString().split('.');
        parts[0]=parts[0].replace(/\B(?=(\d{3})+(?!\d))/g,'.');
        var formatted=parts[0]+(parts[1]!==undefined?','+parts[1]:'');
        if(el.value!==formatted){el.value=formatted;}
      }
    }
    el.addEventListener('input',formatLive);
    el.addEventListener('blur',function(){
      var raw=parseFloat(el.dataset.raw||'');
      if(!isNaN(raw)&&raw>0){
        var parts=raw.toFixed(2).split('.');
        parts[0]=parts[0].replace(/\B(?=(\d{3})+(?!\d))/g,'.');
        el.value=parts[0]+','+parts[1];
      }
      el.dataset.raw=isNaN(raw)?'':raw;
    });
    el.addEventListener('focus',function(){
      if(el.dataset.raw) el.value=el.dataset.raw.replace('.',',');
      else el.value='';
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
  b.style.color=d.balance>=0?'#e2e8f0':'var(--r)';
  document.getElementById('s-gelir').textContent=fmt(d.gelir);
  document.getElementById('s-gider').textContent=fmt(d.gider);
  var netEl=document.getElementById('s-net');
  netEl.textContent=fmt(d.net);
  netEl.style.color=d.net>=0?'var(--g)':'var(--r)';
  var pct=d.gelir>0?Math.round(d.net/d.gelir*100):0;
  document.getElementById('s-net-sub').textContent=d.gelir>0?'Gelirin %'+pct+" tasarruf":'';
  document.getElementById('s-gelir-sub').textContent='';
  document.getElementById('s-gider-sub').textContent='';
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
  var cat=document.getElementById('b-cat').value, limit=getNumVal(document.getElementById('b-limit'));
  if(!cat||!limit||limit<=0){toast('Kategori ve limit giriniz');return}
  xhr('/api/budgets',{category:cat,limit:limit},function(){
    document.getElementById('b-limit').value='';
    loadDashboard();toast('Bütçe kaydedildi ✓');
  });
}

// ── ADD TX ────────────────────────────────────────────────────────────────────
function addTx(){
  var amount=getNumVal(document.getElementById('f-amount'));
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
  loadTodayWidgets();
  if(dbView==='year'){
    xhr('/api/summary?year='+curYear,null,function(d){
      summaryData=d;
      var totalG=0,totalE=0;
      d.bar.forEach(function(m){totalG+=m.gelir;totalE+=m.gider});
      renderStats({gelir:totalG,gider:totalE,net:totalG-totalE,balance:d.balance,
                   gelir_cats:d.gelir_cats,gider_cats:d.gider_cats,budgets:d.budgets});
      drawBar(d.bar);
      drawDonut(d.gider_cats);
      renderBudgetPage(d.gider_cats,d.budgets);
      document.getElementById('db-sub').textContent=curYear+' yılı';
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
  var tl   = getNumVal(document.getElementById('calc-tl'));
  var buy  = getNumVal(document.getElementById('calc-buy'));
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
      var priceEl=document.getElementById('inv-price');
      priceEl.value=Number(d.fiyat).toLocaleString('tr-TR',{minimumFractionDigits:4,maximumFractionDigits:4});
      priceEl.dataset.raw=d.fiyat;
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
    quantity:  getNumVal(document.getElementById('inv-qty')),
    buy_price: getNumVal(document.getElementById('inv-price')),
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
  var amount = getNumVal(document.getElementById('rec-amount'));
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
  var mStart= parseInt(document.getElementById('rec-apply-month-start').value);
  var mEnd  = parseInt(document.getElementById('rec-apply-month-end').value);
  if(mEnd < mStart){ showToast('Bitiş ayı başlangıç ayından önce olamaz','#ef4444'); return; }
  var body  = {year: year, month_start: mStart, month_end: mEnd};
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
    limit_:       getNumVal(document.getElementById('card-limit')),
    used_:        getNumVal(document.getElementById('card-used')),
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
            '<input type="text" inputmode="decimal" data-num data-raw="'+c.used_+'" id="upd-used-'+c.id+'" value="'+Number(c.used_).toLocaleString("tr-TR",{minimumFractionDigits:2,maximumFractionDigits:2})+'" class="f-input" style="flex:1" placeholder="Güncel borç">'+
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

// ── PWA INSTALL BANNER ───────────────────────────────────────────────────────
var _installPrompt = null;

window.addEventListener('beforeinstallprompt', function(e){
  e.preventDefault();
  _installPrompt = e;
  showInstallBanner();
});

window.addEventListener('appinstalled', function(){
  hideInstallBanner();
  showToast('Uygulama kuruldu! Ana ekranınızdan açabilirsiniz.','#22c55e');
});

function isIOS(){
  return /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream;
}

function isInStandaloneMode(){
  return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
}

function showInstallBanner(){
  if(isInStandaloneMode()) return;
  var b = document.getElementById('install-banner');
  if(b){ b.style.display='flex'; }
}

function hideInstallBanner(){
  var b = document.getElementById('install-banner');
  if(b) b.style.display='none';
  localStorage.setItem('install-dismissed','1');
}

function triggerInstall(){
  if(_installPrompt){
    _installPrompt.prompt();
    _installPrompt.userChoice.then(function(r){
      if(r.outcome==='accepted') hideInstallBanner();
      _installPrompt = null;
    });
  } else if(isIOS()){
    document.getElementById('ios-install-modal').style.display='flex';
  }
}

function closeIOSModal(){
  document.getElementById('ios-install-modal').style.display='none';
}

// Show iOS banner on first visit if not installed
if(isIOS() && !isInStandaloneMode() && !localStorage.getItem('install-dismissed')){
  window.addEventListener('load', function(){
    setTimeout(function(){ showInstallBanner(); }, 2000);
  });
}
</script>

<!-- INSTALL BANNER -->
<div id="install-banner" style="display:none;position:fixed;bottom:0;left:0;right:0;z-index:9000;background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:14px 20px;align-items:center;justify-content:space-between;gap:12px;box-shadow:0 -4px 24px rgba(0,0,0,.4)">
  <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0">
    <span style="font-size:1.8rem;flex-shrink:0">🦔</span>
    <div style="min-width:0">
      <div style="font-size:.88rem;font-weight:700;color:#fff">Kirpi'yi Kur</div>
      <div style="font-size:.75rem;color:rgba(255,255,255,.8);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">Ana ekrana ekle, uygulama gibi kullan</div>
    </div>
  </div>
  <div style="display:flex;gap:8px;flex-shrink:0">
    <button onclick="triggerInstall()" style="background:#fff;color:#4f46e5;border:none;border-radius:8px;padding:8px 16px;font-size:.82rem;font-weight:700;cursor:pointer">Kur</button>
    <button onclick="hideInstallBanner()" style="background:rgba(255,255,255,.15);color:#fff;border:none;border-radius:8px;padding:8px 10px;font-size:.82rem;cursor:pointer">✕</button>
  </div>
</div>

<!-- iOS INSTALL MODAL -->
<div id="ios-install-modal" style="display:none;position:fixed;inset:0;z-index:9100;background:rgba(0,0,0,.7);align-items:flex-end;justify-content:center">
  <div style="background:#1a1d26;border-radius:20px 20px 0 0;padding:28px 24px 40px;width:100%;max-width:480px;border-top:1px solid #2a2f45">
    <div style="text-align:center;margin-bottom:20px">
      <div style="font-size:2.5rem;margin-bottom:8px">🦔</div>
      <div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-bottom:6px">Kirpi'yi Ana Ekrana Ekle</div>
      <div style="font-size:.82rem;color:#64748b">iPhone/iPad'de uygulama gibi kullanmak için:</div>
    </div>
    <div style="display:flex;flex-direction:column;gap:12px;margin-bottom:24px">
      <div style="display:flex;align-items:center;gap:12px;background:#111318;border-radius:10px;padding:12px">
        <span style="font-size:1.4rem;flex-shrink:0">1️⃣</span>
        <span style="font-size:.85rem;color:#c7d2fe">Safari'de alt ortadaki <strong style="color:#818cf8">Paylaş</strong> butonuna bas <span style="font-size:1rem">⎙</span></span>
      </div>
      <div style="display:flex;align-items:center;gap:12px;background:#111318;border-radius:10px;padding:12px">
        <span style="font-size:1.4rem;flex-shrink:0">2️⃣</span>
        <span style="font-size:.85rem;color:#c7d2fe"><strong style="color:#818cf8">"Ana Ekrana Ekle"</strong> seçeneğine bas</span>
      </div>
      <div style="display:flex;align-items:center;gap:12px;background:#111318;border-radius:10px;padding:12px">
        <span style="font-size:1.4rem;flex-shrink:0">3️⃣</span>
        <span style="font-size:.85rem;color:#c7d2fe">Sağ üstten <strong style="color:#818cf8">"Ekle"</strong> ye bas</span>
      </div>
    </div>
    <button onclick="closeIOSModal();hideInstallBanner();" style="width:100%;padding:13px;background:#4f46e5;border:none;border-radius:10px;color:#fff;font-size:.9rem;font-weight:700;cursor:pointer">Anladım</button>
  </div>
</div>

</body>
</html>"""

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4f46e5"/>
      <stop offset="100%" style="stop-color:#7c3aed"/>
    </linearGradient>
    <linearGradient id="body" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#6d28d9"/>
      <stop offset="100%" style="stop-color:#4c1d95"/>
    </linearGradient>
  </defs>

  <!-- background rounded square -->
  <rect width="512" height="512" rx="110" fill="url(#bg)"/>

  <!-- SPINES — sharp triangles rising from back -->
  <g fill="#c4b5fd" stroke="#a78bfa" stroke-width="2">
    <polygon points="256,52 240,130 272,130"/>
    <polygon points="300,62 282,138 318,142"/>
    <polygon points="342,82 320,154 358,162"/>
    <polygon points="378,112 352,178 390,190"/>
    <polygon points="404,148 376,208 414,224"/>
    <polygon points="418,192 390,244 428,262"/>
    <polygon points="212,62 230,138 194,142"/>
    <polygon points="172,84 196,156 158,164"/>
    <polygon points="140,116 166,182 128,194"/>
  </g>

  <!-- BODY — dark rounded ellipse -->
  <ellipse cx="268" cy="330" rx="175" ry="130" fill="url(#body)"/>

  <!-- FACE / HEAD — lighter round bulge to left -->
  <ellipse cx="148" cy="310" rx="98" ry="90" fill="#ddd6fe"/>

  <!-- inner face -->
  <ellipse cx="138" cy="318" rx="72" ry="66" fill="#ede9fe"/>

  <!-- EYE -->
  <circle cx="118" cy="292" r="22" fill="#1e1b4b"/>
  <circle cx="112" cy="284" r="8" fill="white"/>
  <circle cx="110" cy="283" r="4" fill="white" opacity="0.6"/>

  <!-- NOSE — shiny dark oval -->
  <ellipse cx="75" cy="322" rx="22" ry="16" fill="#4c1d95"/>
  <ellipse cx="70" cy="316" rx="8" ry="5" fill="#818cf8" opacity="0.5"/>

  <!-- SMILE -->
  <path d="M85 340 Q105 362 130 348" stroke="#6d28d9" stroke-width="7" fill="none" stroke-linecap="round"/>

  <!-- CHEEK blush -->
  <ellipse cx="148" cy="350" rx="28" ry="16" fill="#a78bfa" opacity="0.35"/>

  <!-- BELLY lighter patch -->
  <ellipse cx="295" cy="348" rx="90" ry="60" fill="#7c3aed" opacity="0.5"/>
  <ellipse cx="295" cy="355" rx="60" ry="38" fill="#c4b5fd" opacity="0.15"/>

  <!-- FEET -->
  <ellipse cx="195" cy="440" rx="52" ry="28" fill="#4c1d95"/>
  <ellipse cx="305" cy="448" rx="52" ry="28" fill="#4c1d95"/>
  <ellipse cx="408" cy="438" rx="46" ry="24" fill="#4c1d95"/>

  <!-- SMALL SPARKLE top-right -->
  <circle cx="420" cy="80" r="10" fill="white" opacity="0.3"/>
  <circle cx="448" cy="56" r="6" fill="white" opacity="0.2"/>
</svg>"""

MANIFEST = json.dumps({
    "name": "Kirpi — Nakit Akışı",
    "short_name": "Kirpi",
    "description": "Gelir, gider, yatırım ve kartlarını tek ekranda yönet. Şahıs ve şirket profillerini ayrı tut.",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "display_override": ["standalone", "minimal-ui"],
    "background_color": "#0a0c12",
    "theme_color": "#6366f1",
    "orientation": "portrait-primary",
    "lang": "tr",
    "categories": ["finance", "productivity"],
    "screenshots": [
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "form_factor": "narrow"},
    ],
    "shortcuts": [
        {"name": "Dashboard", "url": "/", "description": "Ana sayfa"},
    ],
    "icons": [
        {"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"},
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
    "prefer_related_applications": False,
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

ICON_192_B64 = "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"
ICON_512_B64 = "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"

@app.route("/icon-192.png")
def icon_192():
    import base64
    return base64.b64decode(ICON_192_B64), 200, {"Content-Type": "image/png"}

@app.route("/icon-512.png")
def icon_512():
    import base64
    return base64.b64decode(ICON_512_B64), 200, {"Content-Type": "image/png"}

# Digital Asset Links for TWA (Google Play) — set ASSETLINKS_JSON env var after PWABuilder
@app.route("/.well-known/assetlinks.json")
def assetlinks():
    content = os.environ.get("ASSETLINKS_JSON", "[]")
    return content, 200, {"Content-Type": "application/json"}

@app.route("/")
@login_required
def index():
    display = session.get("display","")
    return HTML.replace("__USER_DISPLAY__", display)

# ── LEGAL PAGES ───────────────────────────────────────────────────────────────

LEGAL_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0c12;color:#e2e8f0;font-family:'Inter',system-ui,sans-serif;padding:40px 20px;line-height:1.8}
.wrap{max-width:760px;margin:0 auto}
.back{display:inline-flex;align-items:center;gap:8px;color:#818cf8;text-decoration:none;font-size:.85rem;margin-bottom:32px}
.back:hover{color:#a5b4fc}
h1{font-size:1.8rem;font-weight:900;margin-bottom:8px;background:linear-gradient(135deg,#818cf8,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.meta{color:#64748b;font-size:.82rem;margin-bottom:40px}
h2{font-size:1.05rem;font-weight:700;color:#c7d2fe;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #1e2233}
p{color:#94a3b8;margin-bottom:12px;font-size:.9rem}
ul{color:#94a3b8;margin:0 0 12px 20px;font-size:.9rem}
li{margin-bottom:6px}
.box{background:#111318;border:1px solid #1e2233;border-radius:12px;padding:20px 24px;margin-bottom:16px}
strong{color:#e2e8f0}
a{color:#818cf8}
"""

def legal_page(title, body):
    return f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Kirpi</title><style>{LEGAL_CSS}</style></head>
<body><div class="wrap">
<a class="back" href="/">← Uygulamaya Dön</a>
<h1>{title}</h1>
<p class="meta">Son güncelleme: {date.today().strftime('%d.%m.%Y')} · Kirpi Nakit Akışı</p>
{body}
</div></body></html>"""

@app.route("/kvkk")
def kvkk():
    body = """
<h2>1. Veri Sorumlusu</h2>
<p>Bu aydınlatma metni, 6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK) kapsamında Kirpi Nakit Akışı uygulaması tarafından hazırlanmıştır.</p>

<h2>2. İşlenen Kişisel Veriler</h2>
<div class="box">
<ul>
<li><strong>Kimlik verileri:</strong> Ad soyad, kullanıcı adı</li>
<li><strong>İletişim verileri:</strong> E-posta adresi</li>
<li><strong>Finansal veriler:</strong> Kullanıcının bizzat girdiği gelir, gider, yatırım ve kart bilgileri</li>
<li><strong>Teknik veriler:</strong> Giriş tarihleri, IP adresi (sunucu logları)</li>
</ul>
</div>

<h2>3. Kişisel Verilerin İşlenme Amaçları</h2>
<ul>
<li>Kullanıcı hesabının oluşturulması ve yönetimi</li>
<li>Şifre sıfırlama hizmetinin sunulması</li>
<li>Uygulama güvenliğinin sağlanması</li>
<li>Yasal yükümlülüklerin yerine getirilmesi</li>
</ul>

<h2>4. Kişisel Verilerin Aktarılması</h2>
<p>Kişisel verileriniz <strong>üçüncü şahıslarla paylaşılmamakta</strong>, satılmamakta veya kiralanmamaktadır. Yalnızca yasal zorunluluk halinde yetkili kamu kurumlarıyla paylaşılabilir.</p>

<h2>5. Kişisel Verilerin Saklanma Süresi</h2>
<p>Verileriniz hesabınızın aktif olduğu süre boyunca saklanır. Hesap silme talebinde bulunduğunuzda tüm verileriniz kalıcı olarak silinir.</p>

<h2>6. KVKK Kapsamındaki Haklarınız</h2>
<ul>
<li>Kişisel verilerinizin işlenip işlenmediğini öğrenme</li>
<li>İşlenmişse bilgi talep etme</li>
<li>İşlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme</li>
<li>Yurt içinde veya yurt dışında aktarıldığı üçüncü kişileri bilme</li>
<li>Eksik veya yanlış işlenmişse düzeltilmesini isteme</li>
<li>Silinmesini veya yok edilmesini isteme</li>
<li>İşlemenin otomatik sistemler vasıtasıyla gerçekleştirilmesi halinde aleyhine bir sonucun ortaya çıkmasına itiraz etme</li>
</ul>
<p>Başvurularınız için: <strong>kvkk@kirpiapp.com</strong></p>
"""
    return legal_page("KVKK Aydınlatma Metni", body)

@app.route("/gizlilik")
def gizlilik():
    body = """
<h2>1. Gizlilik Taahhüdümüz</h2>
<p>Kirpi, kullanıcılarının gizliliğini en üst düzeyde korumayı taahhüt eder. Bu politika, hangi verileri topladığımızı ve nasıl kullandığımızı açıklar.</p>

<h2>2. Topladığımız Veriler</h2>
<div class="box">
<ul>
<li><strong>Hesap bilgileri:</strong> Kullanıcı adı, ad soyad, e-posta</li>
<li><strong>Finansal içerik:</strong> Yalnızca siz tarafından girilen işlem, bütçe ve yatırım verileri</li>
<li><strong>Teknik veriler:</strong> Sunucu erişim logları (güvenlik amaçlı)</li>
</ul>
</div>

<h2>3. Verilerinizi Nasıl Kullanıyoruz</h2>
<ul>
<li>Hizmeti size sunmak ve hesabınızı yönetmek</li>
<li>Şifre sıfırlama e-postası göndermek</li>
<li>Uygulama güvenliğini sağlamak</li>
</ul>

<h2>4. Veri Güvenliği</h2>
<p>Şifreleriniz <strong>bcrypt</strong> algoritmasıyla hashlenerek saklanır. Ham şifreniz hiçbir zaman kaydedilmez. Verileriniz şifreli bağlantı (HTTPS) üzerinden iletilir.</p>

<h2>5. Çerezler</h2>
<p>Uygulama yalnızca oturum yönetimi için zorunlu bir oturum çerezi kullanır. Reklam veya takip çerezi kullanılmaz.</p>

<h2>6. Üçüncü Taraf Hizmetler</h2>
<ul>
<li><strong>Railway.app:</strong> Uygulama barındırma (ABD merkezli)</li>
<li><strong>Gmail SMTP:</strong> E-posta bildirimleri</li>
<li><strong>open.er-api.com:</strong> Döviz kurları (anonim)</li>
<li><strong>tefas.gov.tr:</strong> Fon fiyatları (anonim)</li>
</ul>

<h2>7. İletişim</h2>
<p>Gizlilik konularındaki sorularınız için: <strong>gizlilik@kirpiapp.com</strong></p>
"""
    return legal_page("Gizlilik Politikası", body)

@app.route("/kullanim-kosullari")
def kullanim_kosullari():
    body = """
<h2>1. Kabul</h2>
<p>Kirpi uygulamasını kullanarak bu kullanım koşullarını kabul etmiş sayılırsınız.</p>

<h2>2. Hizmet Tanımı</h2>
<p>Kirpi, kişisel ve kurumsal nakit akışı takibi için tasarlanmış bir web uygulamasıdır. Uygulama yalnızca bilgi amaçlıdır; <strong>finansal tavsiye niteliği taşımaz.</strong></p>

<h2>3. Kullanıcı Sorumlulukları</h2>
<ul>
<li>Hesap güvenliğinizi korumak sizin sorumluluğunuzdadır</li>
<li>Şifrenizi kimseyle paylaşmayınız</li>
<li>Uygulamayı yasalara aykırı amaçlarla kullanamazsınız</li>
<li>Başkalarının hesaplarına erişmeye çalışamazsınız</li>
</ul>

<h2>4. Hizmet Sürekliliği</h2>
<p>Kirpi, hizmet kesintisi yaşanmayacağını garanti etmez. Verilerinizi düzenli olarak yedeklemenizi öneririz. Uygulama içinden veri yedeği alabilirsiniz.</p>

<h2>5. Sorumluluk Sınırlaması</h2>
<p>Kirpi, kullanıcı tarafından girilen verilerin doğruluğundan sorumlu değildir. Uygulama finansal kararlarınız için kullanılan tek kaynak olmamalıdır.</p>

<h2>6. Hesap Sonlandırma</h2>
<p>Koşulları ihlal eden hesaplar önceden bildirim yapılmaksızın askıya alınabilir veya silinebilir.</p>

<h2>7. Değişiklikler</h2>
<p>Bu koşullar zaman zaman güncellenebilir. Önemli değişiklikler e-posta ile bildirilir.</p>

<h2>8. Uygulanacak Hukuk</h2>
<p>Bu sözleşme <strong>Türkiye Cumhuriyeti hukuku</strong> kapsamında yorumlanır. Uyuşmazlıklarda İstanbul Mahkemeleri yetkilidir.</p>

<h2>9. İletişim</h2>
<p>Sorularınız için: <strong>destek@kirpiapp.com</strong></p>
"""
    return legal_page("Kullanım Koşulları", body)

# ── ADMIN PANEL ───────────────────────────────────────────────────────────────

ADMIN_USER = os.environ.get("ADMIN_USERNAME", "")

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")
        if ADMIN_USER and session.get("username") != ADMIN_USER:
            return "Yetkisiz erişim", 403
        if not ADMIN_USER:
            with pg_connect() as con:
                first = con.execute("SELECT username FROM users ORDER BY id LIMIT 1").fetchone()
                if first and session.get("username") != first["username"]:
                    return "Yetkisiz erişim", 403
        return f(*args, **kwargs)
    return decorated

@app.route("/admin")
@admin_required
def admin_panel():
    db = get_db()
    total_users    = db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    total_profiles = db.execute("SELECT COUNT(*) AS n FROM profiles").fetchone()["n"]
    sahis_count    = db.execute("SELECT COUNT(*) AS n FROM profiles WHERE type='sahis'").fetchone()["n"]
    sirket_count   = db.execute("SELECT COUNT(*) AS n FROM profiles WHERE type='sirket'").fetchone()["n"]
    total_txn      = db.execute("SELECT COUNT(*) AS n FROM transactions").fetchone()["n"]
    total_cards    = db.execute("SELECT COUNT(*) AS n FROM cards").fetchone()["n"]
    total_invest   = db.execute("SELECT COUNT(*) AS n FROM investments").fetchone()["n"]
    recent_users   = db.execute("SELECT username,display_name,email,created_at FROM users ORDER BY id DESC LIMIT 20").fetchall()
    txn_by_day     = db.execute("SELECT LEFT(created_at, 10) as d, COUNT(*) as c FROM transactions GROUP BY d ORDER BY d DESC LIMIT 14").fetchall()
    new_users_week = db.execute("SELECT COUNT(*) AS n FROM users WHERE created_at >= (NOW() - INTERVAL '7 days')::TEXT").fetchone()["n"]
    new_users_month= db.execute("SELECT COUNT(*) AS n FROM users WHERE created_at >= (NOW() - INTERVAL '30 days')::TEXT").fetchone()["n"]

    rows_html = ""
    for u in recent_users:
        rows_html += f"""<tr>
        <td>{u['username']}</td>
        <td>{u['display_name']}</td>
        <td>{u['email']}</td>
        <td style="color:#64748b;font-size:.8rem">{u['created_at'][:10]}</td>
        </tr>"""

    chart_labels = [r['d'] for r in reversed(list(txn_by_day))]
    chart_data   = [r['c'] for r in reversed(list(txn_by_day))]

    return f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin — Kirpi</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0a0c12;color:#e2e8f0;font-family:'Inter',system-ui,sans-serif;padding:32px 20px}}
.wrap{{max-width:1100px;margin:0 auto}}
.back{{display:inline-flex;align-items:center;gap:8px;color:#818cf8;text-decoration:none;font-size:.85rem;margin-bottom:28px}}
h1{{font-size:1.6rem;font-weight:900;margin-bottom:28px;background:linear-gradient(135deg,#818cf8,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:32px}}
.stat{{background:#111318;border:1px solid #1e2233;border-radius:12px;padding:20px;text-align:center}}
.stat-val{{font-size:2rem;font-weight:900;color:#818cf8}}
.stat-lbl{{font-size:.78rem;color:#64748b;margin-top:4px}}
.stat-sub{{font-size:.72rem;color:#22c55e;margin-top:2px}}
.card{{background:#111318;border:1px solid #1e2233;border-radius:12px;padding:24px;margin-bottom:24px}}
h2{{font-size:1rem;font-weight:700;margin-bottom:16px;color:#c7d2fe}}
table{{width:100%;border-collapse:collapse;font-size:.85rem}}
th{{text-align:left;color:#64748b;font-weight:500;padding:8px 12px;border-bottom:1px solid #1e2233}}
td{{padding:10px 12px;border-bottom:1px solid #0d0f18;color:#cbd5e1}}
tr:hover td{{background:#13161f}}
canvas{{width:100%!important;height:200px!important}}
</style></head>
<body><div class="wrap">
<a class="back" href="/">← Uygulamaya Dön</a>
<h1>🛡️ Admin Paneli</h1>

<div class="stats">
  <div class="stat"><div class="stat-val">{total_users}</div><div class="stat-lbl">Toplam Kullanıcı</div>
    <div class="stat-sub">+{new_users_week} bu hafta · +{new_users_month} bu ay</div></div>
  <div class="stat"><div class="stat-val">{total_profiles}</div><div class="stat-lbl">Profil</div>
    <div class="stat-sub">👤 {sahis_count} şahıs · 🏢 {sirket_count} şirket</div></div>
  <div class="stat"><div class="stat-val">{total_txn}</div><div class="stat-lbl">Toplam İşlem</div></div>
  <div class="stat"><div class="stat-val">{total_cards}</div><div class="stat-lbl">Kayıtlı Kart</div></div>
  <div class="stat"><div class="stat-val">{total_invest}</div><div class="stat-lbl">Yatırım Kaydı</div></div>
</div>

<div class="card">
  <h2>📈 Son 14 Gün — Günlük İşlem</h2>
  <canvas id="chart"></canvas>
</div>

<div class="card">
  <h2>👥 Son Kayıt Olan Kullanıcılar</h2>
  <table>
    <thead><tr><th>Kullanıcı Adı</th><th>Ad Soyad</th><th>Email</th><th>Kayıt Tarihi</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>

</div>
<script>
var labels={chart_labels};
var data={chart_data};
var canvas=document.getElementById('chart');
var ctx=canvas.getContext('2d');
canvas.width=canvas.offsetWidth; canvas.height=200;
var max=Math.max(...data,1);
var pad={{l:40,r:20,t:20,b:30}};
var W=canvas.width,H=canvas.height;
var bw=(W-pad.l-pad.r)/Math.max(labels.length,1);
ctx.fillStyle='#0a0c12'; ctx.fillRect(0,0,W,H);
[0.25,0.5,0.75,1].forEach(function(f){{
  var y=pad.t+(H-pad.t-pad.b)*(1-f);
  ctx.strokeStyle='#1e2233'; ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(pad.l,y); ctx.lineTo(W-pad.r,y); ctx.stroke();
  ctx.fillStyle='#475569'; ctx.font='10px system-ui'; ctx.textAlign='right';
  ctx.fillText(Math.round(max*f),pad.l-4,y+4);
}});
data.forEach(function(v,i){{
  var x=pad.l+i*bw+bw*0.1;
  var bh=(v/max)*(H-pad.t-pad.b);
  var y=H-pad.b-bh;
  var grd=ctx.createLinearGradient(0,y,0,H-pad.b);
  grd.addColorStop(0,'#6366f1'); grd.addColorStop(1,'#4338ca44');
  ctx.fillStyle=grd;
  ctx.beginPath();
  ctx.roundRect(x,y,bw*0.8,bh,4);
  ctx.fill();
  if(i%3===0){{
    ctx.fillStyle='#64748b'; ctx.font='9px system-ui'; ctx.textAlign='center';
    ctx.fillText(labels[i]?labels[i].slice(5):'',x+bw*0.4,H-pad.b+14);
  }}
}});
</script>
</body></html>"""

if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=_daily_backup_loop, daemon=True)
    t.start()
    app.run(debug=True, port=5001)

init_db()
_backup_thread = threading.Thread(target=_daily_backup_loop, daemon=True)
_backup_thread.start()
