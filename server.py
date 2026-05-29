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
        """CREATE TABLE IF NOT EXISTS invoices (
            id                  SERIAL PRIMARY KEY,
            user_id             INTEGER NOT NULL DEFAULT 1,
            profile_id          INTEGER NOT NULL DEFAULT 1,
            project_name        TEXT NOT NULL,
            client_name         TEXT NOT NULL DEFAULT '',
            description         TEXT DEFAULT '',
            amount              DOUBLE PRECISION NOT NULL DEFAULT 0,
            currency            TEXT NOT NULL DEFAULT 'TRY',
            invoice_date        TEXT NOT NULL,
            due_date            TEXT NOT NULL,
            status              TEXT NOT NULL DEFAULT 'bekliyor',
            paid_date           TEXT DEFAULT '',
            early_discount_pct  DOUBLE PRECISION NOT NULL DEFAULT 0,
            early_discount_days INTEGER NOT NULL DEFAULT 0,
            late_penalty_pct    DOUBLE PRECISION NOT NULL DEFAULT 0,
            notes               TEXT DEFAULT '',
            created_at          TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS goals (
            id             SERIAL PRIMARY KEY,
            user_id        INTEGER NOT NULL DEFAULT 1,
            profile_id     INTEGER NOT NULL DEFAULT 1,
            name           TEXT NOT NULL,
            goal_type      TEXT NOT NULL DEFAULT 'diger',
            monthly_target DOUBLE PRECISION NOT NULL DEFAULT 0,
            note           TEXT DEFAULT '',
            created_at     TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS todos (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL DEFAULT 1,
            profile_id  INTEGER NOT NULL DEFAULT 1,
            text        TEXT NOT NULL,
            date        TEXT NOT NULL,
            done        INTEGER NOT NULL DEFAULT 0,
            archived    INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS invoices (
            id                  SERIAL PRIMARY KEY,
            user_id             INTEGER NOT NULL DEFAULT 1,
            profile_id          INTEGER NOT NULL DEFAULT 1,
            project_name        TEXT NOT NULL,
            client_name         TEXT NOT NULL DEFAULT '',
            description         TEXT DEFAULT '',
            amount              DOUBLE PRECISION NOT NULL DEFAULT 0,
            currency            TEXT NOT NULL DEFAULT 'TRY',
            invoice_date        TEXT NOT NULL,
            due_date            TEXT NOT NULL,
            status              TEXT NOT NULL DEFAULT 'bekliyor',
            paid_date           TEXT DEFAULT '',
            early_discount_pct  DOUBLE PRECISION NOT NULL DEFAULT 0,
            early_discount_days INTEGER NOT NULL DEFAULT 0,
            late_penalty_pct    DOUBLE PRECISION NOT NULL DEFAULT 0,
            notes               TEXT DEFAULT '',
            created_at          TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS suppliers (
            id                  SERIAL PRIMARY KEY,
            user_id             INTEGER NOT NULL DEFAULT 1,
            profile_id          INTEGER NOT NULL DEFAULT 1,
            name                TEXT NOT NULL,
            tax_no              TEXT DEFAULT '',
            contact             TEXT DEFAULT '',
            phone               TEXT DEFAULT '',
            email               TEXT DEFAULT '',
            address             TEXT DEFAULT '',
            payment_terms_days  INTEGER NOT NULL DEFAULT 30,
            notes               TEXT DEFAULT '',
            created_at          TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS supplier_invoices (
            id              SERIAL PRIMARY KEY,
            user_id         INTEGER NOT NULL DEFAULT 1,
            profile_id      INTEGER NOT NULL DEFAULT 1,
            supplier_id     INTEGER NOT NULL DEFAULT 0,
            supplier_name   TEXT NOT NULL DEFAULT '',
            invoice_no      TEXT DEFAULT '',
            description     TEXT DEFAULT '',
            amount          DOUBLE PRECISION NOT NULL DEFAULT 0,
            currency        TEXT NOT NULL DEFAULT 'TRY',
            invoice_date    TEXT NOT NULL,
            due_date        TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'bekliyor',
            paid_date       TEXT DEFAULT '',
            reference_rate  DOUBLE PRECISION NOT NULL DEFAULT 50,
            notes           TEXT DEFAULT '',
            created_at      TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS assets (
            id                  SERIAL PRIMARY KEY,
            user_id             INTEGER NOT NULL DEFAULT 1,
            profile_id          INTEGER NOT NULL DEFAULT 1,
            name                TEXT NOT NULL,
            asset_type          TEXT NOT NULL DEFAULT 'diger',
            plate_no            TEXT DEFAULT '',
            serial_no           TEXT DEFAULT '',
            purchase_date       TEXT NOT NULL,
            purchase_price      DOUBLE PRECISION NOT NULL DEFAULT 0,
            useful_life_years   INTEGER NOT NULL DEFAULT 5,
            depreciation_method TEXT NOT NULL DEFAULT 'normal',
            depreciation_rate   DOUBLE PRECISION NOT NULL DEFAULT 20,
            maintenance_date    TEXT DEFAULT '',
            insurance_date      TEXT DEFAULT '',
            insurance_company   TEXT DEFAULT '',
            notes               TEXT DEFAULT '',
            active              INTEGER NOT NULL DEFAULT 1,
            created_at          TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS asset_maintenance (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL DEFAULT 1,
            profile_id  INTEGER NOT NULL DEFAULT 1,
            asset_id    INTEGER NOT NULL,
            date        TEXT NOT NULL,
            mtype       TEXT NOT NULL DEFAULT 'bakim',
            description TEXT DEFAULT '',
            cost        DOUBLE PRECISION NOT NULL DEFAULT 0,
            odometer    DOUBLE PRECISION NOT NULL DEFAULT 0,
            next_date   TEXT DEFAULT '',
            notes       TEXT DEFAULT '',
            created_at  TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS card_daily_balance (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL DEFAULT 1,
            profile_id  INTEGER NOT NULL DEFAULT 1,
            card_id     INTEGER NOT NULL,
            date        TEXT NOT NULL,
            balance     DOUBLE PRECISION NOT NULL DEFAULT 0,
            notes       TEXT DEFAULT '',
            created_at  TEXT NOT NULL
        )""",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_card_daily ON card_daily_balance(card_id, date)",
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
        ("users",        "avatar",          "TEXT NOT NULL DEFAULT ''"),
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
    uid = session.get("user_id")
    db  = get_db()
    row = db.execute("SELECT display_name,username,email,avatar FROM users WHERE id=?", (uid,)).fetchone()
    avatar = row["avatar"] if row else ""
    return jsonify({
        "username":     session.get("username"),
        "display":      session.get("display") or (row["display_name"] if row else ""),
        "profile_id":   session.get("profile_id"),
        "profile_name": session.get("profile_name"),
        "profile_type": session.get("profile_type"),
        "email":        row["email"] if row else "",
        "avatar":       avatar or "",
    })

@app.route("/api/me/update", methods=["POST"])
@login_required
def api_me_update():
    data    = request.get_json(force=True)
    display = (data.get("display_name") or "").strip()
    avatar  = data.get("avatar", None)
    uid     = session["user_id"]
    db      = get_db()
    if display:
        db.execute("UPDATE users SET display_name=? WHERE id=?", (display, uid))
        session["display"] = display
    if avatar is not None:
        db.execute("UPDATE users SET avatar=? WHERE id=?", (avatar, uid))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/me/password", methods=["POST"])
@login_required
def api_me_password():
    data    = request.get_json(force=True)
    current = data.get("current", "")
    new_pw  = data.get("new", "")
    confirm = data.get("confirm", "")
    uid     = session["user_id"]
    db      = get_db()
    user    = db.execute("SELECT password_hash FROM users WHERE id=?", (uid,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], current):
        return jsonify({"ok": False, "error": "Mevcut şifre yanlış"})
    if len(new_pw) < 6:
        return jsonify({"ok": False, "error": "Şifre en az 6 karakter olmalı"})
    if new_pw != confirm:
        return jsonify({"ok": False, "error": "Şifreler eşleşmiyor"})
    db.execute("UPDATE users SET password_hash=? WHERE id=?", (generate_password_hash(new_pw), uid))
    db.commit()
    return jsonify({"ok": True})

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
    today_d = date.today()
    year  = request.args.get("year",  today_d.year,  type=int)
    month = request.args.get("month", today_d.month, type=int)
    period = request.args.get("period", "month")  # month | year | all
    rstart = request.args.get("start","")
    rend   = request.args.get("end","")
    if rstart and rend:
        start, end = rstart, rend
    elif period == "year":
        year_param = request.args.get("year", today_d.year, type=int)
        start = f"{year_param}-01-01"
        end   = f"{year_param}-12-31"
    elif period == "all":
        start = "0001-01-01"
        end   = "9999-12-31"
    else:  # month (default)
        start, end = month_range(today_d.year, today_d.month)
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
        s,e2 = month_range(today_d.year, m)
        totals = db.execute("SELECT type,SUM(amount) as t FROM transactions WHERE profile_id=? AND date BETWEEN ? AND ? GROUP BY type",(pid,s,e2)).fetchall()
        g_val  = next((r["t"] for r in totals if r["type"]=="gelir"),0)
        ex_val = next((r["t"] for r in totals if r["type"]=="gider"),0)
        bar.append({"month":m,"gelir":round(g_val,2),"gider":round(ex_val,2)})
    bal = db.execute("SELECT SUM(CASE WHEN type='gelir' THEN amount ELSE -amount END) as b FROM transactions WHERE profile_id=?",(pid,)).fetchone()
    budgets = {r["category"]:r["limit_"] for r in db.execute("SELECT * FROM budgets WHERE profile_id=?",(pid,)).fetchall()}
    return jsonify({"gelir":round(gelir_total,2),"gider":round(gider_total,2),
                    "net":round(gelir_total-gider_total,2),"balance":round(bal["b"] or 0,2),
                    "gelir_cats":gelir_cats,"gider_cats":gider_cats,"bar":bar,"budgets":budgets,
                    "period":period})

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

@app.route("/api/goals", methods=["GET"])
@login_required
def list_goals():
    pid = get_pid(); db = get_db()
    rows = db.execute("SELECT * FROM goals WHERE profile_id=? ORDER BY created_at", (pid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/goals", methods=["POST"])
@login_required
def add_goal():
    uid = session["user_id"]; pid = get_pid()
    d = request.get_json(force=True)
    name = d.get("name","").strip()
    gtype = d.get("goal_type","diger")
    monthly = float(d.get("monthly_target",0))
    note = d.get("note","").strip()
    if not name or monthly <= 0:
        return jsonify({"ok":False,"error":"İsim ve aylık hedef zorunlu"}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO goals (user_id,profile_id,name,goal_type,monthly_target,note,created_at) VALUES (?,?,?,?,?,?,?)",
        (uid, pid, name, gtype, monthly, note, datetime.now().isoformat())
    )
    db.commit()
    return jsonify({"ok":True,"id":cur.lastrowid})

@app.route("/api/goals/<int:gid>", methods=["DELETE"])
@login_required
def del_goal(gid):
    pid = get_pid(); db = get_db()
    db.execute("DELETE FROM goals WHERE id=? AND profile_id=?", (gid, pid))
    db.commit()
    return jsonify({"ok":True})

# ── TODOS ────────────────────────────────────────────────────────────────────

@app.route("/api/todos", methods=["GET"])
@login_required
def list_todos():
    pid = get_pid(); db = get_db()
    dt = request.args.get("date", date.today().isoformat())
    rows = db.execute(
        "SELECT * FROM todos WHERE profile_id=? AND date=? ORDER BY id", (pid, dt)
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/todos", methods=["POST"])
@login_required
def add_todo():
    uid = session["user_id"]; pid = get_pid()
    d = request.get_json(force=True)
    text = d.get("text","").strip()
    dt   = d.get("date", date.today().isoformat())
    if not text: return jsonify({"ok":False,"error":"Görev metni gerekli"}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO todos (user_id,profile_id,text,date,done,archived,created_at) VALUES (?,?,?,?,0,0,?)",
        (uid, pid, text, dt, datetime.now().isoformat())
    )
    db.commit()
    return jsonify({"ok":True,"id":cur.lastrowid})

@app.route("/api/todos/<int:tid>", methods=["PUT"])
@login_required
def update_todo(tid):
    pid = get_pid(); db = get_db()
    d = request.get_json(force=True)
    fields, params = [], []
    for col in ("text","done","archived","date"):
        if col in d:
            fields.append(f"{col}=?")
            params.append(d[col])
    if not fields: return jsonify({"ok":False}), 400
    params += [tid, pid]
    db.execute(f"UPDATE todos SET {','.join(fields)} WHERE id=? AND profile_id=?", params)
    db.commit()
    return jsonify({"ok":True})

@app.route("/api/todos/<int:tid>", methods=["DELETE"])
@login_required
def del_todo(tid):
    pid = get_pid(); db = get_db()
    db.execute("DELETE FROM todos WHERE id=? AND profile_id=?", (tid, pid))
    db.commit()
    return jsonify({"ok":True})

# ── SUPPLIERS ────────────────────────────────────────────────────────────────

@app.route("/api/suppliers", methods=["GET"])
@login_required
def list_suppliers():
    pid = get_pid(); db = get_db()
    rows = db.execute("SELECT * FROM suppliers WHERE profile_id=? ORDER BY name", (pid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/suppliers", methods=["POST"])
@login_required
def add_supplier():
    uid = session["user_id"]; pid = get_pid()
    d = request.get_json(force=True)
    name = d.get("name","").strip()
    if not name: return jsonify({"ok":False,"error":"Tedarikçi adı zorunlu"}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO suppliers (user_id,profile_id,name,tax_no,contact,phone,email,address,payment_terms_days,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (uid, pid, name, d.get("tax_no",""), d.get("contact",""), d.get("phone",""),
         d.get("email",""), d.get("address",""), int(d.get("payment_terms_days",30)),
         d.get("notes",""), datetime.now().isoformat())
    )
    db.commit()
    return jsonify({"ok":True,"id":cur.lastrowid})

@app.route("/api/suppliers/<int:sid>", methods=["PUT"])
@login_required
def update_supplier(sid):
    pid = get_pid(); db = get_db()
    d = request.get_json(force=True)
    fields, params = [], []
    for col in ("name","tax_no","contact","phone","email","address","payment_terms_days","notes"):
        if col in d:
            fields.append(f"{col}=?")
            params.append(d[col])
    if not fields: return jsonify({"ok":False}), 400
    params += [sid, pid]
    db.execute(f"UPDATE suppliers SET {','.join(fields)} WHERE id=? AND profile_id=?", params)
    db.commit()
    return jsonify({"ok":True})

@app.route("/api/suppliers/<int:sid>", methods=["DELETE"])
@login_required
def del_supplier(sid):
    pid = get_pid(); db = get_db()
    db.execute("DELETE FROM suppliers WHERE id=? AND profile_id=?", (sid, pid))
    db.commit()
    return jsonify({"ok":True})

# ── SUPPLIER INVOICES ─────────────────────────────────────────────────────────

@app.route("/api/supplier-invoices", methods=["GET"])
@login_required
def list_supplier_invoices():
    pid = get_pid(); db = get_db()
    status = request.args.get("status","")
    if status:
        rows = db.execute(
            "SELECT * FROM supplier_invoices WHERE profile_id=? AND status=? ORDER BY due_date", (pid, status)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM supplier_invoices WHERE profile_id=? ORDER BY due_date DESC", (pid,)
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/supplier-invoices", methods=["POST"])
@login_required
def add_supplier_invoice():
    uid = session["user_id"]; pid = get_pid()
    d = request.get_json(force=True)
    sup_name = d.get("supplier_name","").strip()
    amount   = float(d.get("amount",0))
    inv_date = d.get("invoice_date", date.today().isoformat())
    due_date = d.get("due_date","")
    if not sup_name or amount <= 0 or not due_date:
        return jsonify({"ok":False,"error":"Tedarikçi, tutar ve vade zorunlu"}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO supplier_invoices (user_id,profile_id,supplier_id,supplier_name,invoice_no,description,amount,currency,invoice_date,due_date,status,paid_date,reference_rate,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (uid, pid, int(d.get("supplier_id",0)), sup_name, d.get("invoice_no",""),
         d.get("description",""), amount, d.get("currency","TRY"), inv_date, due_date,
         "bekliyor", "", float(d.get("reference_rate",50)), d.get("notes",""),
         datetime.now().isoformat())
    )
    db.commit()
    return jsonify({"ok":True,"id":cur.lastrowid})

@app.route("/api/supplier-invoices/<int:iid>", methods=["PUT"])
@login_required
def update_supplier_invoice(iid):
    pid = get_pid(); db = get_db()
    d = request.get_json(force=True)
    fields, params = [], []
    for col in ("supplier_name","invoice_no","description","amount","currency","invoice_date","due_date","status","paid_date","reference_rate","notes"):
        if col in d:
            fields.append(f"{col}=?")
            params.append(float(d[col]) if col in ("amount","reference_rate") else d[col])
    if not fields: return jsonify({"ok":False}), 400
    params += [iid, pid]
    db.execute(f"UPDATE supplier_invoices SET {','.join(fields)} WHERE id=? AND profile_id=?", params)
    db.commit()
    return jsonify({"ok":True})

@app.route("/api/supplier-invoices/<int:iid>", methods=["DELETE"])
@login_required
def del_supplier_invoice(iid):
    pid = get_pid(); db = get_db()
    db.execute("DELETE FROM supplier_invoices WHERE id=? AND profile_id=?", (iid, pid))
    db.commit()
    return jsonify({"ok":True})

@app.route("/api/supplier-invoices/<int:iid>/pay", methods=["POST"])
@login_required
def pay_supplier_invoice(iid):
    pid = get_pid(); db = get_db()
    d = request.get_json(force=True)
    paid_date = d.get("paid_date", date.today().isoformat())
    db.execute(
        "UPDATE supplier_invoices SET status='odendi',paid_date=? WHERE id=? AND profile_id=?",
        (paid_date, iid, pid)
    )
    db.commit()
    return jsonify({"ok":True})

@app.route("/api/supplier-invoices/aging")
@login_required
def supplier_invoices_aging():
    pid = get_pid(); db = get_db()
    today_d = date.today()
    rows = db.execute(
        "SELECT * FROM supplier_invoices WHERE profile_id=? AND status='bekliyor' ORDER BY due_date",
        (pid,)
    ).fetchall()
    buckets = {"0_30":[],"31_60":[],"61_90":[],"90plus":[]}
    totals  = {"0_30":0.0,"31_60":0.0,"61_90":0.0,"90plus":0.0}
    for r in rows:
        try:
            due = date.fromisoformat(r["due_date"])
            days_overdue = (today_d - due).days
        except:
            days_overdue = 0
        item = dict(r)
        item["days_overdue"] = days_overdue
        if days_overdue <= 0:
            buckets["0_30"].append(item); totals["0_30"] += float(r["amount"])
        elif days_overdue <= 30:
            buckets["0_30"].append(item); totals["0_30"] += float(r["amount"])
        elif days_overdue <= 60:
            buckets["31_60"].append(item); totals["31_60"] += float(r["amount"])
        elif days_overdue <= 90:
            buckets["61_90"].append(item); totals["61_90"] += float(r["amount"])
        else:
            buckets["90plus"].append(item); totals["90plus"] += float(r["amount"])
    grand_total = sum(totals.values())
    return jsonify({"ok":True,"buckets":buckets,"totals":totals,"grand_total":grand_total})

@app.route("/api/supplier-invoices/float-gain")
@login_required
def supplier_invoices_float_gain():
    pid = get_pid(); db = get_db()
    today_d = date.today()
    rows = db.execute(
        "SELECT * FROM supplier_invoices WHERE profile_id=? AND status='odendi' AND paid_date!=''",
        (pid,)
    ).fetchall()
    results = []
    total_gain = 0.0
    for r in rows:
        try:
            due  = date.fromisoformat(r["due_date"])
            paid = date.fromisoformat(r["paid_date"])
            delayed_days = (paid - due).days
            if delayed_days > 0:
                rate = float(r["reference_rate"] or 50)
                gain = float(r["amount"]) * (delayed_days / 365) * (rate / 100)
                total_gain += gain
                results.append({
                    "supplier_name": r["supplier_name"],
                    "amount": float(r["amount"]),
                    "due_date": r["due_date"],
                    "paid_date": r["paid_date"],
                    "delayed_days": delayed_days,
                    "reference_rate": rate,
                    "float_gain": round(gain, 2)
                })
        except:
            continue
    results.sort(key=lambda x: x["float_gain"], reverse=True)
    return jsonify({"ok":True,"items":results,"total_gain":round(total_gain,2)})

# ── ASSETS & DEPRECIATION ─────────────────────────────────────────────────────

DEPRECIATION_RATES = {
    "arac":       {"rate": 20.0, "life": 5},
    "bilgisayar": {"rate": 33.33, "life": 3},
    "makine":     {"rate": 20.0, "life": 5},
    "mobilya":    {"rate": 20.0, "life": 5},
    "bina":       {"rate": 2.0,  "life": 50},
    "diger":      {"rate": 20.0, "life": 5},
}

def calc_depreciation(purchase_price, purchase_date_str, rate, method="normal"):
    today_d = date.today()
    try:
        p_date = date.fromisoformat(purchase_date_str)
    except:
        return {"book_value": purchase_price, "accumulated": 0, "annual": 0, "entries": []}
    years_used = (today_d - p_date).days / 365.25
    annual = purchase_price * rate / 100
    accumulated = min(annual * years_used, purchase_price)
    book_value   = max(purchase_price - accumulated, 0)
    entries = []
    for yr in range(1, int(years_used) + 2):
        yr_dep = min(annual, purchase_price - annual * (yr - 1))
        if yr_dep <= 0: break
        entries.append({"year": p_date.year + yr - 1, "depreciation": round(yr_dep, 2),
                        "cumulative": round(min(annual * yr, purchase_price), 2),
                        "book_value": round(max(purchase_price - min(annual * yr, purchase_price), 0), 2)})
    return {"book_value": round(book_value, 2), "accumulated": round(accumulated, 2),
            "annual": round(annual, 2), "entries": entries}

@app.route("/api/assets", methods=["GET"])
@login_required
def list_assets():
    pid = get_pid(); db = get_db()
    rows = db.execute("SELECT * FROM assets WHERE profile_id=? AND active=1 ORDER BY name", (pid,)).fetchall()
    result = []
    for r in rows:
        item = dict(r)
        dep = calc_depreciation(float(r["purchase_price"]), r["purchase_date"],
                                float(r["depreciation_rate"]), r["depreciation_method"])
        item["book_value"]   = dep["book_value"]
        item["accumulated"]  = dep["accumulated"]
        item["annual_dep"]   = dep["annual"]
        result.append(item)
    return jsonify(result)

@app.route("/api/assets", methods=["POST"])
@login_required
def add_asset():
    uid = session["user_id"]; pid = get_pid()
    d = request.get_json(force=True)
    name = d.get("name","").strip()
    if not name: return jsonify({"ok":False,"error":"Varlık adı zorunlu"}), 400
    atype = d.get("asset_type","diger")
    defaults = DEPRECIATION_RATES.get(atype, DEPRECIATION_RATES["diger"])
    rate = float(d.get("depreciation_rate", defaults["rate"]))
    life = int(d.get("useful_life_years", defaults["life"]))
    db = get_db()
    cur = db.execute(
        "INSERT INTO assets (user_id,profile_id,name,asset_type,plate_no,serial_no,purchase_date,purchase_price,useful_life_years,depreciation_method,depreciation_rate,maintenance_date,insurance_date,insurance_company,notes,active,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?)",
        (uid, pid, name, atype, d.get("plate_no",""), d.get("serial_no",""),
         d.get("purchase_date", date.today().isoformat()), float(d.get("purchase_price",0)),
         life, d.get("depreciation_method","normal"), rate,
         d.get("maintenance_date",""), d.get("insurance_date",""), d.get("insurance_company",""),
         d.get("notes",""), datetime.now().isoformat())
    )
    db.commit()
    return jsonify({"ok":True,"id":cur.lastrowid})

@app.route("/api/assets/<int:aid>", methods=["PUT"])
@login_required
def update_asset(aid):
    pid = get_pid(); db = get_db()
    d = request.get_json(force=True)
    fields, params = [], []
    for col in ("name","asset_type","plate_no","serial_no","purchase_date","purchase_price",
                "useful_life_years","depreciation_method","depreciation_rate",
                "maintenance_date","insurance_date","insurance_company","notes","active"):
        if col in d:
            fields.append(f"{col}=?")
            params.append(float(d[col]) if col in ("purchase_price","depreciation_rate") else d[col])
    if not fields: return jsonify({"ok":False}), 400
    params += [aid, pid]
    db.execute(f"UPDATE assets SET {','.join(fields)} WHERE id=? AND profile_id=?", params)
    db.commit()
    return jsonify({"ok":True})

@app.route("/api/assets/<int:aid>", methods=["DELETE"])
@login_required
def del_asset(aid):
    pid = get_pid(); db = get_db()
    db.execute("UPDATE assets SET active=0 WHERE id=? AND profile_id=?", (aid, pid))
    db.commit()
    return jsonify({"ok":True})

@app.route("/api/assets/<int:aid>/maintenance", methods=["GET"])
@login_required
def list_asset_maintenance(aid):
    pid = get_pid(); db = get_db()
    rows = db.execute(
        "SELECT * FROM asset_maintenance WHERE profile_id=? AND asset_id=? ORDER BY date DESC",
        (pid, aid)
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/assets/<int:aid>/maintenance", methods=["POST"])
@login_required
def add_asset_maintenance(aid):
    uid = session["user_id"]; pid = get_pid()
    d = request.get_json(force=True)
    dt = d.get("date", date.today().isoformat())
    db = get_db()
    cur = db.execute(
        "INSERT INTO asset_maintenance (user_id,profile_id,asset_id,date,mtype,description,cost,odometer,next_date,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (uid, pid, aid, dt, d.get("mtype","bakim"), d.get("description",""),
         float(d.get("cost",0)), float(d.get("odometer",0)),
         d.get("next_date",""), d.get("notes",""), datetime.now().isoformat())
    )
    db.commit()
    # Update asset maintenance_date
    db.execute("UPDATE assets SET maintenance_date=? WHERE id=? AND profile_id=?",
               (d.get("next_date",""), aid, pid))
    db.commit()
    return jsonify({"ok":True,"id":cur.lastrowid})

@app.route("/api/assets/maintenance/<int:mid>", methods=["DELETE"])
@login_required
def del_asset_maintenance(mid):
    pid = get_pid(); db = get_db()
    db.execute("DELETE FROM asset_maintenance WHERE id=? AND profile_id=?", (mid, pid))
    db.commit()
    return jsonify({"ok":True})

# ── CARD DAILY BALANCE ────────────────────────────────────────────────────────

@app.route("/api/cards/daily-report", methods=["GET"])
@login_required
def card_daily_report():
    pid = get_pid(); db = get_db()
    cards = db.execute("SELECT * FROM cards WHERE profile_id=? ORDER BY bank_name", (pid,)).fetchall()
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - __import__("datetime").timedelta(days=1)).isoformat()
    result = []
    for c in cards:
        cid = c["id"]
        today_row = db.execute(
            "SELECT balance FROM card_daily_balance WHERE profile_id=? AND card_id=? AND date=?",
            (pid, cid, today_str)
        ).fetchone()
        yest_row = db.execute(
            "SELECT balance FROM card_daily_balance WHERE profile_id=? AND card_id=? AND date=?",
            (pid, cid, yesterday_str)
        ).fetchone()
        today_bal = float(today_row["balance"]) if today_row else None
        yest_bal  = float(yest_row["balance"])  if yest_row  else None
        spent = None
        if today_bal is not None and yest_bal is not None:
            spent = today_bal - yest_bal
        result.append({
            "card_id": cid,
            "bank_name": c["bank_name"],
            "card_name": c["card_name"] or "",
            "today_balance": today_bal,
            "yesterday_balance": yest_bal,
            "spent_today": round(spent, 2) if spent is not None else None
        })
    return jsonify({"ok":True,"cards":result,"date":today_str})

@app.route("/api/cards/daily-balance", methods=["POST"])
@login_required
def save_card_daily_balance():
    uid = session["user_id"]; pid = get_pid()
    d = request.get_json(force=True)
    cid = int(d.get("card_id",0))
    bal = float(d.get("balance",0))
    dt  = d.get("date", date.today().isoformat())
    if not cid: return jsonify({"ok":False,"error":"Kart gerekli"}), 400
    db = get_db()
    # Upsert
    existing = db.execute(
        "SELECT id FROM card_daily_balance WHERE profile_id=? AND card_id=? AND date=?",
        (pid, cid, dt)
    ).fetchone()
    if existing:
        db.execute("UPDATE card_daily_balance SET balance=?,notes=? WHERE id=?",
                   (bal, d.get("notes",""), existing["id"]))
    else:
        db.execute(
            "INSERT INTO card_daily_balance (user_id,profile_id,card_id,date,balance,notes,created_at) VALUES (?,?,?,?,?,?,?)",
            (uid, pid, cid, dt, bal, d.get("notes",""), datetime.now().isoformat())
        )
    db.commit()
    return jsonify({"ok":True})

# ── EXCEL EXPORT ──────────────────────────────────────────────────────────────

@app.route("/api/export/excel")
@login_required
def export_excel():
    import io
    from openpyxl import Workbook
    from openpyxl.styles import (Font, PatternFill, Alignment, Border, Side,
                                  GradientFill)
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, Reference

    pid = get_pid(); db = get_db()
    today_d = date.today()

    NAVY   = "1A3557"
    ORANGE = "E8773A"
    LGRAY  = "F0F4F8"
    WHITE  = "FFFFFF"
    GREEN  = "1D7A46"
    RED    = "C0392B"
    YELLOW = "D4A017"

    def hdr_font(bold=True, size=11, color=WHITE):
        return Font(name="Calibri", bold=bold, size=size, color=color)
    def body_font(bold=False, size=10, color="1C1C1E"):
        return Font(name="Calibri", bold=bold, size=size, color=color)
    def navy_fill():
        return PatternFill("solid", fgColor=NAVY)
    def orange_fill():
        return PatternFill("solid", fgColor=ORANGE)
    def gray_fill():
        return PatternFill("solid", fgColor=LGRAY)
    def thin_border():
        s = Side(style="thin", color="D1D1D6")
        return Border(left=s, right=s, top=s, bottom=s)
    def center():
        return Alignment(horizontal="center", vertical="center", wrap_text=True)
    def left():
        return Alignment(horizontal="left", vertical="center", wrap_text=True)

    def write_sheet_header(ws, title, subtitle=""):
        ws.merge_cells("A1:H1")
        c = ws["A1"]
        c.value = f"🦔 KIRPI — {title}"
        c.font  = Font(name="Calibri", bold=True, size=16, color=WHITE)
        c.fill  = navy_fill()
        c.alignment = center()
        ws.row_dimensions[1].height = 36
        if subtitle:
            ws.merge_cells("A2:H2")
            c2 = ws["A2"]
            c2.value = subtitle
            c2.font  = Font(name="Calibri", size=10, color="A0AEC0")
            c2.fill  = navy_fill()
            c2.alignment = center()
            ws.row_dimensions[2].height = 20
            return 3
        return 2

    def write_col_headers(ws, row, headers, col_widths=None):
        for ci, h in enumerate(headers, 1):
            c = ws.cell(row=row, column=ci, value=h)
            c.font = Font(name="Calibri", bold=True, size=10, color=WHITE)
            c.fill = orange_fill()
            c.alignment = center()
            c.border = thin_border()
        ws.row_dimensions[row].height = 22
        if col_widths:
            for ci, w in enumerate(col_widths, 1):
                ws.column_dimensions[get_column_letter(ci)].width = w

    def alt_fill(row_idx):
        return gray_fill() if row_idx % 2 == 0 else PatternFill("solid", fgColor=WHITE)

    wb = Workbook()

    # ── Sheet 1: Hesap Hareketleri ────────────────────────────────────────────
    ws0 = wb.active
    ws0.title = "Hesap Hareketleri"
    txs = db.execute(
        "SELECT * FROM transactions WHERE profile_id=? ORDER BY date DESC, id DESC", (pid,)
    ).fetchall()
    profile_row = db.execute("SELECT name FROM profiles WHERE id=?", (pid,)).fetchone()
    profile_name = profile_row["name"] if profile_row else ""

    ws0.merge_cells("A1:F1")
    c = ws0["A1"]
    c.value = f"🦔 KIRPI — HESAP HAREKETLERİ"
    c.font = Font(name="Calibri", bold=True, size=16, color=WHITE)
    c.fill = navy_fill()
    c.alignment = center()
    ws0.row_dimensions[1].height = 36

    ws0.merge_cells("A2:F2")
    c2 = ws0["A2"]
    c2.value = f"{profile_name}  •  {today_d.strftime('%d.%m.%Y')}  •  {len(txs)} işlem"
    c2.font = Font(name="Calibri", size=10, color="A0AEC0")
    c2.fill = navy_fill()
    c2.alignment = center()
    ws0.row_dimensions[2].height = 20

    write_col_headers(ws0, 3, ["Tarih","Tür","Kategori","Açıklama","Tutar","Not"],
                      [14, 10, 18, 32, 14, 20])
    ws0.freeze_panes = "A4"
    ws0.auto_filter.ref = "A3:F3"

    gelir_total = 0.0
    gider_total = 0.0
    GREEN_LIGHT = "D6F5E3"
    RED_LIGHT   = "FDE8E8"

    for ri, row in enumerate(txs):
        dr = 4 + ri
        is_gelir = row["type"] == "gelir"
        amt = float(row["amount"])
        if is_gelir: gelir_total += amt
        else:        gider_total += amt

        row_fill = PatternFill("solid", fgColor=(GREEN_LIGHT if is_gelir else RED_LIGHT) if ri%2==0
                               else ("EDFAF3" if is_gelir else "FAF0F0"))
        vals = [row["date"],
                "Gelir" if is_gelir else "Gider",
                row["category"] or "",
                row["description"] or "",
                amt,
                row["note"] or ""]
        for ci, v in enumerate(vals, 1):
            c = ws0.cell(row=dr, column=ci, value=v)
            c.fill   = row_fill
            c.border = thin_border()
            if ci == 1:
                c.font = body_font(size=10, color="555555")
                c.alignment = center()
            elif ci == 2:
                c.font = Font(name="Calibri", bold=True, size=10,
                              color=GREEN if is_gelir else RED)
                c.alignment = center()
            elif ci == 5:
                c.font = Font(name="Calibri", bold=True, size=10,
                              color=GREEN if is_gelir else RED)
                c.number_format = '#,##0.00'
                c.alignment = center()
            else:
                c.font = body_font(size=10)
                c.alignment = left()
        ws0.row_dimensions[dr].height = 18

    # Totals row
    tot_row = 4 + len(txs) + 1
    ws0.merge_cells(f"A{tot_row}:D{tot_row}")
    tc = ws0.cell(row=tot_row, column=1, value="TOPLAM")
    tc.font = Font(name="Calibri", bold=True, size=11, color=WHITE)
    tc.fill = navy_fill(); tc.alignment = center()
    for ci, (v, col) in enumerate([(gelir_total, GREEN),(gider_total, RED)], 5):
        c = ws0.cell(row=tot_row, column=ci, value=v)
        c.font = Font(name="Calibri", bold=True, size=11, color=col)
        c.fill = navy_fill(); c.number_format = '#,##0.00'; c.alignment = center()
    ws0.row_dimensions[tot_row].height = 26

    # ── Sheet 2: Aylık Özet ───────────────────────────────────────────────────
    ws_mo = wb.create_sheet("Aylik Ozet")
    ws_mo.merge_cells("A1:E1")
    c = ws_mo["A1"]
    c.value = "🦔 KIRPI — AYLIK ÖZET"
    c.font = Font(name="Calibri", bold=True, size=16, color=WHITE)
    c.fill = navy_fill(); c.alignment = center()
    ws_mo.row_dimensions[1].height = 36
    write_col_headers(ws_mo, 2, ["Yıl","Ay","Gelir","Gider","Net"], [8,14,16,16,16])
    ws_mo.freeze_panes = "A3"

    from collections import defaultdict
    monthly = defaultdict(lambda: {"gelir":0.0,"gider":0.0})
    for row in txs:
        try:
            ym = row["date"][:7]
            monthly[ym][row["type"]] += float(row["amount"])
        except: pass
    MONTHS_TR = ["","Ocak","Şubat","Mart","Nisan","Mayıs","Haziran",
                 "Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
    for ri, ym in enumerate(sorted(monthly.keys(), reverse=True)):
        dr = 3 + ri
        yr, mo = int(ym[:4]), int(ym[5:7])
        g = monthly[ym]["gelir"]; gz = monthly[ym]["gider"]; net = g - gz
        row_fill = gray_fill() if ri%2==0 else PatternFill("solid", fgColor=WHITE)
        for ci, v in enumerate([yr, MONTHS_TR[mo] if mo<=12 else mo, g, gz, net], 1):
            c = ws_mo.cell(row=dr, column=ci, value=v)
            c.fill = row_fill; c.border = thin_border()
            if ci in (3,4,5):
                c.number_format = '#,##0.00'
                c.font = Font(name="Calibri", bold=(ci==5), size=10,
                              color=(GREEN if (ci==5 and net>=0) else (RED if ci==5 else "1C1C1E")))
                c.alignment = center()
            else:
                c.font = body_font(size=10); c.alignment = center()
        ws_mo.row_dimensions[dr].height = 18

    # ── Sheet 3: Tedarikçi Faturalar ──────────────────────────────────────────
    ws1 = wb.create_sheet("Tedarikci Faturalar")
    data_row = write_sheet_header(ws1, "TEDARİKÇİ FATURALARI",
                                  f"Oluşturma Tarihi: {today_d.strftime('%d.%m.%Y')}")
    cols = ["Tedarikçi","Fatura No","Tutar","Para Birimi","Fatura Tarihi","Vade Tarihi","Durum","Notlar"]
    write_col_headers(ws1, data_row, cols, [22,14,14,10,14,14,12,20])
    data_row += 1
    invoices = db.execute(
        "SELECT * FROM supplier_invoices WHERE profile_id=? ORDER BY due_date", (pid,)
    ).fetchall()
    for ri, row in enumerate(invoices):
        vals = [row["supplier_name"], row["invoice_no"], float(row["amount"]),
                row["currency"], row["invoice_date"], row["due_date"],
                "Ödendi" if row["status"]=="odendi" else "Bekliyor", row["notes"] or ""]
        for ci, v in enumerate(vals, 1):
            c = ws1.cell(row=data_row+ri, column=ci, value=v)
            c.font   = body_font()
            c.fill   = alt_fill(ri)
            c.border = thin_border()
            c.alignment = center() if ci in (3,4,5,6,7) else left()
            if ci == 3:
                c.number_format = '#,##0.00'
            if ci == 7:
                if row["status"] == "odendi":
                    c.font = Font(name="Calibri", size=10, color=GREEN, bold=True)
                else:
                    try:
                        due = date.fromisoformat(row["due_date"])
                        if due < today_d:
                            c.font = Font(name="Calibri", size=10, color=RED, bold=True)
                    except:
                        pass

    # ── Sheet 2: Ödeme Yaşlandırma ────────────────────────────────────────────
    ws2 = wb.create_sheet("Odeme Yaslandirma")
    data_row = write_sheet_header(ws2, "ÖDEME YAŞLANDIRma RAPORU",
                                  f"Rapor Tarihi: {today_d.strftime('%d.%m.%Y')}")
    aging_data = {"0-30 Gün (Güncel)":[],"31-60 Gün":[],"61-90 Gün":[],"90+ Gün (Kritik)":[]}
    aging_totals = {k:0.0 for k in aging_data}
    pending = db.execute(
        "SELECT * FROM supplier_invoices WHERE profile_id=? AND status='bekliyor' ORDER BY due_date",
        (pid,)
    ).fetchall()
    for row in pending:
        try:
            due = date.fromisoformat(row["due_date"])
            days_over = (today_d - due).days
        except:
            days_over = 0
        amt = float(row["amount"])
        item = (row["supplier_name"], float(row["amount"]), row["due_date"], days_over)
        if days_over <= 30:
            aging_data["0-30 Gün (Güncel)"].append(item); aging_totals["0-30 Gün (Güncel)"] += amt
        elif days_over <= 60:
            aging_data["31-60 Gün"].append(item); aging_totals["31-60 Gün"] += amt
        elif days_over <= 90:
            aging_data["61-90 Gün"].append(item); aging_totals["61-90 Gün"] += amt
        else:
            aging_data["90+ Gün (Kritik)"].append(item); aging_totals["90+ Gün (Kritik)"] += amt

    BUCKET_COLORS = {"0-30 Gün (Güncel)":"1D7A46","31-60 Gün":"D4A017",
                     "61-90 Gün":"E07B39","90+ Gün (Kritik)":"C0392B"}
    cur_row = data_row
    for bucket, items in aging_data.items():
        ws2.merge_cells(f"A{cur_row}:F{cur_row}")
        hc = ws2.cell(row=cur_row, column=1, value=f"  {bucket}  —  ₺{aging_totals[bucket]:,.2f}")
        hc.font  = Font(name="Calibri", bold=True, size=11, color=WHITE)
        hc.fill  = PatternFill("solid", fgColor=BUCKET_COLORS[bucket])
        hc.alignment = left()
        ws2.row_dimensions[cur_row].height = 22
        cur_row += 1
        if items:
            write_col_headers(ws2, cur_row, ["Tedarikçi","Tutar","Vade","Gecikme (Gün)","",""], [22,14,14,16,1,1])
            cur_row += 1
            for ri, (sup, amt, due_d, days_o) in enumerate(items):
                for ci, v in enumerate([sup, amt, due_d, days_o, "", ""], 1):
                    c = ws2.cell(row=cur_row+ri, column=ci, value=v)
                    c.font = body_font(bold=(ci==4 and days_o>30))
                    c.fill = alt_fill(ri)
                    c.border = thin_border()
                    if ci == 2: c.number_format = '#,##0.00'
                    if ci == 4 and days_o > 90:
                        c.font = Font(name="Calibri", bold=True, size=10, color=RED)
            cur_row += len(items) + 1
        else:
            c = ws2.cell(row=cur_row, column=1, value="  (Bu kategoride bekleyen fatura yok)")
            c.font = Font(name="Calibri", size=9, color="888888", italic=True)
            cur_row += 2

    # ── Sheet 3: Vadeden Kazanç ───────────────────────────────────────────────
    ws3 = wb.create_sheet("Vadeden Kazanc")
    data_row = write_sheet_header(ws3, "VADEDEN KAZANÇ PANOSU",
                                  "Geç ödeme ile elde edilen nakit faiz fırsatı analizi")
    cols3 = ["Tedarikçi","Fatura Tutarı","Vade","Ödeme Tarihi","Gecikme (Gün)","Referans Oran %","Kazanım (₺)"]
    write_col_headers(ws3, data_row, cols3, [22,14,14,14,14,14,14])
    data_row += 1
    paid_inv = db.execute(
        "SELECT * FROM supplier_invoices WHERE profile_id=? AND status='odendi' AND paid_date!=''",
        (pid,)
    ).fetchall()
    total_gain = 0.0
    for ri, row in enumerate(paid_inv):
        try:
            due  = date.fromisoformat(row["due_date"])
            paid = date.fromisoformat(row["paid_date"])
            delayed = (paid - due).days
            if delayed <= 0: continue
            rate = float(row["reference_rate"] or 50)
            gain = float(row["amount"]) * (delayed / 365) * (rate / 100)
            total_gain += gain
        except:
            continue
        vals = [row["supplier_name"], float(row["amount"]), row["due_date"],
                row["paid_date"], delayed, rate, round(gain, 2)]
        for ci, v in enumerate(vals, 1):
            c = ws3.cell(row=data_row+ri, column=ci, value=v)
            c.font = body_font()
            c.fill = alt_fill(ri)
            c.border = thin_border()
            c.alignment = center() if ci > 1 else left()
            if ci in (2, 7): c.number_format = '#,##0.00'
            if ci == 7:
                c.font = Font(name="Calibri", bold=True, size=10, color=GREEN)
    # Total row
    total_row = data_row + len(paid_inv) + 1
    ws3.merge_cells(f"A{total_row}:F{total_row}")
    tc = ws3.cell(row=total_row, column=1, value="TOPLAM KAZANIM")
    tc.font  = Font(name="Calibri", bold=True, size=11, color=WHITE)
    tc.fill  = navy_fill()
    tc.alignment = center()
    tv = ws3.cell(row=total_row, column=7, value=round(total_gain, 2))
    tv.font   = Font(name="Calibri", bold=True, size=11, color=ORANGE)
    tv.fill   = navy_fill()
    tv.number_format = '#,##0.00'
    tv.alignment = center()

    # ── Sheet 4: Varlıklar & Amortisman ──────────────────────────────────────
    ws4 = wb.create_sheet("Varliklar Amortisman")
    data_row = write_sheet_header(ws4, "VARLIKLAR & AMORTİSMAN",
                                  f"Türk Vergi Mevzuatına Göre Normal Amortisman ({today_d.year})")
    cols4 = ["Varlık Adı","Tür","Alış Tarihi","Alış Bedeli","Oran %","Yıllık Amortisman","Birikmiş","Defter Değeri"]
    write_col_headers(ws4, data_row, cols4, [22,14,14,14,10,16,14,14])
    data_row += 1
    assets = db.execute("SELECT * FROM assets WHERE profile_id=? AND active=1 ORDER BY name", (pid,)).fetchall()
    for ri, row in enumerate(assets):
        dep = calc_depreciation(float(row["purchase_price"]), row["purchase_date"],
                                float(row["depreciation_rate"]))
        vals = [row["name"], row["asset_type"], row["purchase_date"],
                float(row["purchase_price"]), float(row["depreciation_rate"]),
                dep["annual"], dep["accumulated"], dep["book_value"]]
        for ci, v in enumerate(vals, 1):
            c = ws4.cell(row=data_row+ri, column=ci, value=v)
            c.font = body_font()
            c.fill = alt_fill(ri)
            c.border = thin_border()
            c.alignment = center() if ci > 2 else left()
            if ci in (4,6,7,8): c.number_format = '#,##0.00'

    # ── Sheet 5: Özet ─────────────────────────────────────────────────────────
    ws5 = wb.create_sheet("Ozet")
    write_sheet_header(ws5, "ÖZET RAPOR", f"Tüm modüller — {today_d.strftime('%d.%m.%Y')}")
    summary_data = [
        ("Toplam Bekleyen Tedarikçi Faturası", sum(float(r["amount"]) for r in pending)),
        ("Bekleyen Fatura Adedi", len(pending)),
        ("Toplam Vadeden Kazanım", round(total_gain, 2)),
        ("Aktif Varlık Sayısı", len(assets)),
        ("Toplam Varlık Defter Değeri", sum(
            calc_depreciation(float(r["purchase_price"]), r["purchase_date"],
                              float(r["depreciation_rate"]))["book_value"] for r in assets
        )),
    ]
    for ri, (label, value) in enumerate(summary_data, 1):
        r = 3 + ri
        c1 = ws5.cell(row=r, column=1, value=label)
        c2 = ws5.cell(row=r, column=2, value=value)
        c1.font  = body_font(bold=True, size=11)
        c2.font  = Font(name="Calibri", bold=True, size=12, color=NAVY)
        c1.fill  = alt_fill(ri)
        c2.fill  = alt_fill(ri)
        c1.border = thin_border(); c2.border = thin_border()
        c1.alignment = left(); c2.alignment = center()
        if isinstance(value, float): c2.number_format = '#,##0.00'
        ws5.row_dimensions[r].height = 24
    ws5.column_dimensions["A"].width = 36
    ws5.column_dimensions["B"].width = 20

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    fname = f"kirpi_rapor_{today_d.strftime('%Y%m%d')}.xlsx"
    from flask import send_file
    return send_file(buf, as_attachment=True, download_name=fname,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route("/api/goals/analysis")
@login_required
def goals_analysis():
    pid = get_pid(); db = get_db()
    today_d = date.today()
    from calendar import monthrange as mr

    # Last 3 months of data
    months_data = []
    for i in range(3):
        if today_d.month - i <= 0:
            m = today_d.month - i + 12; y = today_d.year - 1
        else:
            m = today_d.month - i; y = today_d.year
        _, last = mr(y, m)
        s = f"{y:04d}-{m:02d}-01"; e = f"{y:04d}-{m:02d}-{last:02d}"
        rows = db.execute(
            "SELECT type,SUM(amount) as t FROM transactions WHERE profile_id=? AND date BETWEEN ? AND ? GROUP BY type",
            (pid, s, e)
        ).fetchall()
        gelir = next((float(r["t"]) for r in rows if r["type"]=="gelir"), 0)
        gider = next((float(r["t"]) for r in rows if r["type"]=="gider"), 0)
        months_data.append({"gelir": gelir, "gider": gider, "net": gelir - gider})

    avg_gelir = sum(x["gelir"] for x in months_data) / max(len(months_data), 1)
    avg_gider = sum(x["gider"] for x in months_data) / max(len(months_data), 1)
    avg_net   = avg_gelir - avg_gider

    # Category breakdown for current month
    _, last = mr(today_d.year, today_d.month)
    m_start = today_d.replace(day=1).isoformat()
    m_end   = today_d.replace(day=last).isoformat()
    cat_rows = db.execute(
        "SELECT category,SUM(amount) as t FROM transactions WHERE profile_id=? AND type='gider' AND date BETWEEN ? AND ? GROUP BY category ORDER BY t DESC",
        (pid, m_start, m_end)
    ).fetchall()
    cat_spend = {r["category"]: float(r["t"]) for r in cat_rows}

    # Goals
    goals = db.execute("SELECT * FROM goals WHERE profile_id=?", (pid,)).fetchall()
    total_monthly_goals = sum(float(g["monthly_target"]) for g in goals)
    leftover = avg_net - total_monthly_goals

    # Build commentary
    comments = []

    if avg_gelir == 0:
        comments.append({"icon":"💡","text":"Henüz yeterli veri yok. Birkaç ay gelir ve gider girdikten sonra sana özel tasarruf önerileri sunabilirim.","type":"info"})
        return jsonify({"ok":True,"avg_gelir":0,"avg_gider":0,"avg_net":0,"total_monthly_goals":0,"leftover":0,"comments":comments})

    # Savings capacity comment
    save_rate = round(avg_net / avg_gelir * 100) if avg_gelir > 0 else 0
    if avg_net > 0:
        if save_rate >= 30:
            comments.append({"icon":"🏆","text":f"Harika! Gelirinin %{save_rate}'ini tasarruf ediyorsun. Ortalama aylık ₺{avg_net:,.0f} kenara ayırabiliyorsun. Yatırım hedeflerin için güçlü bir taban var.","type":"success"})
        elif save_rate >= 15:
            comments.append({"icon":"😊","text":f"İyi gidiyorsun! Aylık ortalama ₺{avg_net:,.0f} tasarruf potansiyelin var. Küçük harcamaları kısarak yatırım hedeflerine daha hızlı ulaşabilirsin.","type":"good"})
        else:
            comments.append({"icon":"⚠️","text":f"Bu ay aylık ₺{avg_net:,.0f} tasarruf yapabiliyorsun — gelirinin %{save_rate}'i. Giderlerini %10 azaltsan aylık ₺{avg_gelir*0.1:,.0f} ekstra tasarruf edersin.","type":"warn"})
    else:
        comments.append({"icon":"🔴","text":f"Son 3 ayda ortalama ₺{abs(avg_net):,.0f} açık veriyorsun. Yatırım hedefi koymadan önce giderleri dengelemeyi öneririm.","type":"danger"})

    # Goal allocation comment
    if goals and avg_net > 0:
        if total_monthly_goals <= avg_net:
            if leftover > 500:
                comments.append({"icon":"💰","text":f"Tüm hedeflerini karşılayıp aylık ₺{leftover:,.0f} fazlan kalıyor. Bu fazlayı acil fona ya da yeni bir yatırım hedefine yönlendirebilirsin.","type":"success"})
            else:
                comments.append({"icon":"✅","text":f"Hedeflerin mevcut tasarruf kapasitene sığıyor. ₺{leftover:,.0f} küçük bir buffer var — bir şaşırtıcı gider olursa diye fazla zorlamaya gerek yok.","type":"good"})
        else:
            diff = total_monthly_goals - avg_net
            comments.append({"icon":"⚠️","text":f"Aylık hedeflerinin toplamı (₺{total_monthly_goals:,.0f}) tasarruf kapasiteni ₺{diff:,.0f} aşıyor. Bir veya daha fazla hedefi küçültmeyi düşün.","type":"warn"})

    # Category-specific insights
    TRAVEL_CATS = ["Ulaşım", "Yemek / Restoran", "Eğlence"]
    travel_total = sum(cat_spend.get(c, 0) for c in TRAVEL_CATS)
    if travel_total > avg_gelir * 0.25:
        comments.append({"icon":"✈️","text":f"Bu ay eğlence & ulaşım harcamaların gelirinin %{round(travel_total/avg_gelir*100)}'ini oluşturuyor (₺{travel_total:,.0f}). Bu kategoriyi %20 kıssaydın, döviz ya da altın hedefinize ₺{travel_total*0.2:,.0f} ekleyebilirdin.","type":"warn"})

    food_spend = cat_spend.get("Market / Gıda", 0) + cat_spend.get("Yemek / Restoran", 0)
    if food_spend > avg_gelir * 0.30:
        comments.append({"icon":"🛒","text":f"Market ve yemek harcaman aylık gelirinin %{round(food_spend/avg_gelir*100)}'ini oluşturuyor. Haftalık menü planlaması ile bu kalemi %15 azaltmak mümkün — aylık ₺{food_spend*0.15:,.0f} tasarruf demek.","type":"info"})

    # Goal-type specific tips
    for g in goals:
        gtype = g["goal_type"]
        mt = float(g["monthly_target"])
        if gtype in ("eur","usd","gbp"):
            sym = {"eur":"€","usd":"$","gbp":"£"}[gtype]
            comments.append({"icon":"💶" if gtype=="eur" else ("💵" if gtype=="usd" else "💷"),
                "text":f"'{g['name']}' hedefin için aylık ₺{mt:,.0f} ayırıyorsun. Düzenli alımlar kur dalgalanmalarını dengelemek için ideal — her ay sabit bir günde al.","type":"tip"})
        elif gtype == "gold":
            comments.append({"icon":"🥇","text":f"'{g['name']}' için aylık ₺{mt:,.0f} hedefin var. Altın uzun vadeli bir güvence — gram altın fiyatlarını takip ederek küsürat gramları biriktirebilirsin.","type":"tip"})
        elif gtype == "bitcoin":
            comments.append({"icon":"₿","text":f"'{g['name']}' için aylık ₺{mt:,.0f} ayrılıyor. Bitcoin'de aylık düzenli alım (DCA) volatiliteye karşı en sağlıklı strateji. Tüm birikimini tek seferde yatırmaktan kaçın.","type":"tip"})
        elif gtype == "arsa":
            comments.append({"icon":"🏠","text":f"'{g['name']}' için aylık ₺{mt:,.0f} biriktiriyorsun. Arsa alımında hedef tutarını ve süreyi belirleyip bu tasarrufları vadeli hesapta tutmak getiri sağlar.","type":"tip"})

    # If no goals yet
    if not goals:
        comments.append({"icon":"🎯","text":"Henüz bir yatırım hedefin yok. Euro, dolar, altın, bitcoin veya arsa gibi hedefler ekleyerek aylık ne kadar ayırman gerektiğini görüntüle.","type":"info"})

    return jsonify({
        "ok": True,
        "avg_gelir": round(avg_gelir, 2),
        "avg_gider": round(avg_gider, 2),
        "avg_net": round(avg_net, 2),
        "total_monthly_goals": round(total_monthly_goals, 2),
        "leftover": round(leftover, 2),
        "comments": comments
    })


@app.route("/api/categories")
@login_required
def categories():
    return jsonify({"gelir":GELIR_CATS,"gider":GIDER_CATS,"all":ALL_CATS})

@app.route("/api/today")
@login_required
def today_summary():
    pid  = get_pid(); db = get_db()
    today_str = request.args.get("date") or date.today().isoformat()

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

    # Supplier invoices due today → expected income entries
    try:
        due_invs = db.execute(
            "SELECT * FROM supplier_invoices WHERE profile_id=? AND due_date=? AND status='bekliyor'",
            (pid, today_str)
        ).fetchall()
        for inv in due_invs:
            gelir_list.append({
                "id": None,
                "amount": float(inv["amount"]),
                "category": "Tahsilat",
                "description": "📄 " + (inv["supplier_name"] or "Fatura"),
                "type": "gelir",
                "is_invoice": True
            })
    except Exception:
        pass

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

    # Check for recurring income expected today
    today_dt = date.fromisoformat(today_str)
    recurring_gelir_today = False
    recs = db.execute(
        "SELECT * FROM recurring WHERE profile_id=? AND active=1 AND type='gelir'", (pid,)
    ).fetchall()
    for r in recs:
        if r["day_of_month"] == today_dt.day:
            recurring_gelir_today = True
            break

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
        "recurring_gelir_today": recurring_gelir_today,
    })

def generate_notifications(pid, profile_type, db, today):
    """Return list of notification dicts sorted by urgency."""
    notifs = []

    def days_until(target_date):
        return (target_date - today).days

    def urgency(d):
        if d <= 0:   return "urgent"
        if d <= 2:   return "urgent"
        if d <= 5:   return "soon"
        return "normal"

    def add(icon, title, body, d, category=""):
        notifs.append({
            "icon": icon, "title": title, "body": body,
            "days": d, "urgency": urgency(d), "category": category
        })

    # ── CREDIT CARD DUE DATES ──────────────────────────────────────────────
    cards = db.execute("SELECT * FROM cards WHERE profile_id=?", (pid,)).fetchall()
    for c in cards:
        due_day = c["due_day"] or 1
        used = c["used_"] or 0
        if used <= 0:
            continue
        # compute next due date
        if today.day <= due_day:
            due_date = today.replace(day=due_day)
        else:
            # next month
            if today.month == 12:
                due_date = today.replace(year=today.year+1, month=1, day=due_day)
            else:
                due_date = today.replace(month=today.month+1, day=due_day)
        d = days_until(due_date)
        if -3 <= d <= 10:
            min_pay = round(used * (c["min_pct"] or 25) / 100, 2)
            name = c["bank_name"] + (" - " + c["card_name"] if c["card_name"] else "")
            if d <= 0:
                msg = f"Bugün son ödeme günü! 💳 {name} kartının asgari ödemesi ₺{min_pay:,.0f}"
                ico = "🚨"
            elif d == 1:
                msg = f"Yarın son gün! 💳 {name} kartının asgari ödemesi ₺{min_pay:,.0f}"
                ico = "⚠️"
            else:
                msg = f"{d} gün içinde: {name} kartının asgari ödemesi ₺{min_pay:,.0f}"
                ico = "💳"
            add(ico, "Kredi Kartı Ödemesi", msg, d, "kart")

    # ── RECURRING PAYMENTS ────────────────────────────────────────────────
    recurrings = db.execute(
        "SELECT * FROM recurring WHERE profile_id=? AND active=1", (pid,)
    ).fetchall()
    for r in recurrings:
        dom = r["day_of_month"] or 1
        if today.day <= dom:
            due_date = today.replace(day=dom)
        else:
            if today.month == 12:
                due_date = today.replace(year=today.year+1, month=1, day=dom)
            else:
                due_date = today.replace(month=today.month+1, day=dom)
        d = days_until(due_date)
        if -1 <= d <= 7:
            desc = r["description"] or r["category"]
            amt  = float(r["amount"])
            rtype = r["type"]
            if rtype == "gelir":
                if d <= 0:
                    msg = f"Bugün beklenen gelir: {desc} — ₺{amt:,.0f} 🎉"
                    ico = "🎉"
                elif d == 1:
                    msg = f"Yarın beklenen gelir: {desc} — ₺{amt:,.0f} 😊"
                    ico = "😊"
                else:
                    msg = f"{d} gün içinde beklenen gelir: {desc} — ₺{amt:,.0f} 💰"
                    ico = "💰"
            else:
                if d <= 0:
                    msg = f"Bugün ödenmesi gereken: {desc} — ₺{amt:,.0f}"
                    ico = "🔔"
                elif d == 1:
                    msg = f"Yarın ödenmesi gereken: {desc} — ₺{amt:,.0f}"
                    ico = "⏰"
                else:
                    msg = f"{d} gün içinde: {desc} — ₺{amt:,.0f}"
                    ico = "📅"
            add(ico, "Düzenli Ödeme" if rtype=="gider" else "Beklenen Gelir", msg, d, "duzenli")

    # ── BUDGET OVERRUN ─────────────────────────────────────────────────────
    from calendar import monthrange as mr
    _, last_day = mr(today.year, today.month)
    m_start = today.replace(day=1).isoformat()
    m_end   = today.replace(day=last_day).isoformat()
    budgets = db.execute("SELECT * FROM budgets WHERE profile_id=?", (pid,)).fetchall()
    for b in budgets:
        limit = b["limit_"] or 0
        if limit <= 0:
            continue
        spent_row = db.execute(
            "SELECT COALESCE(SUM(amount),0) as s FROM transactions WHERE profile_id=? AND category=? AND type='gider' AND date BETWEEN ? AND ?",
            (pid, b["category"], m_start, m_end)
        ).fetchone()
        spent = float(spent_row["s"] or 0)
        if spent >= limit:
            pct = round(spent / limit * 100)
            msg = f"{b['category']} bütçesi aşıldı! Hedef ₺{limit:,.0f}, harcama ₺{spent:,.0f} (%{pct})"
            add("🎯", "Bütçe Aşımı", msg, 0, "butce")

    # ── ŞİRKET: TURKISH TAX CALENDAR ─────────────────────────────────────
    if profile_type == "sirket":
        year  = today.year
        month = today.month

        def tax(icon, title, body, due_date):
            d = days_until(due_date)
            if -3 <= d <= 14:
                add(icon, title, body, d, "vergi")

        # Monthly deadlines — due the 26th of current month
        monthly_26 = today.replace(day=26) if today.day <= 26 else (
            today.replace(month=month+1, day=26) if month < 12
            else today.replace(year=year+1, month=1, day=26)
        )
        tax("📋", "SGK Primi",
            f"SGK primi bildirimi ve ödemesi — son gün {monthly_26.strftime('%d %B')}",
            monthly_26)
        tax("📄", "Muhtasar Beyanname",
            f"Aylık muhtasar beyanname — son gün {monthly_26.strftime('%d %B')}",
            monthly_26)
        tax("📊", "KDV Beyannamesi",
            f"Aylık KDV beyannamesi — son gün {monthly_26.strftime('%d %B')}",
            monthly_26)
        tax("🪙", "Damga Vergisi",
            f"Damga vergisi beyannamesi — son gün {monthly_26.strftime('%d %B')}",
            monthly_26)

        # Ba-Bs: 5th of each month (for 2 months prior)
        monthly_5 = today.replace(day=5) if today.day <= 5 else (
            today.replace(month=month+1, day=5) if month < 12
            else today.replace(year=year+1, month=1, day=5)
        )
        tax("📑", "Ba-Bs Bildirimi",
            f"Ba-Bs form bildirimi — son gün {monthly_5.strftime('%d %B')}",
            monthly_5)

        # Geçici Vergi: quarterly — 2nd month of each quarter, 14th
        gecici_months = {2: "1. Çeyrek", 5: "2. Çeyrek", 8: "3. Çeyrek", 11: "4. Çeyrek"}
        for gm, label in gecici_months.items():
            gd = date(year, gm, 14)
            tax("💹", f"Geçici Vergi ({label})",
                f"{label} geçici vergi beyannamesi — son gün {gd.strftime('%d %B')}",
                gd)

        # Annual deadlines
        annual = [
            (date(year, 4, 30), "🏛️",  "Kurumlar Vergisi",
             f"Yıllık kurumlar vergisi beyannamesi — son gün 30 Nisan"),
            (date(year, 3, 31), "💼",  "Gelir Vergisi 1. Taksit",
             f"Gelir vergisi 1. taksit ödemesi — son gün 31 Mart"),
            (date(year, 7, 31), "💼",  "Gelir Vergisi 2. Taksit",
             f"Gelir vergisi 2. taksit ödemesi — son gün 31 Temmuz"),
        ]
        for ad, aico, atitle, abody in annual:
            tax(aico, atitle, abody, ad)

    # ── SUPPLIER INVOICE DUE DATES ────────────────────────────────────────────
    sup_invs = db.execute(
        "SELECT * FROM supplier_invoices WHERE profile_id=? AND status='bekliyor'", (pid,)
    ).fetchall()
    for si in sup_invs:
        try:
            due = date.fromisoformat(si["due_date"])
        except:
            continue
        d_val = days_until(due)
        if -5 <= d_val <= 14:
            amt   = float(si["amount"])
            sname = si["supplier_name"]
            if d_val <= 0:
                msg = f"⚠️ Gecikmiş ödeme: {sname} — ₺{amt:,.0f} ({abs(d_val)} gün gecikti)"
                ico = "🚨"
            elif d_val <= 2:
                msg = f"Yarın/bugün ödeme: {sname} — ₺{amt:,.0f}"
                ico = "⚠️"
            else:
                msg = f"{d_val} gün içinde: {sname} tedarikçi ödemesi ₺{amt:,.0f}"
                ico = "🏭"
            add(ico, "Tedarikçi Ödemesi", msg, d_val, "tedarikci")

    # ── ASSET MAINTENANCE & INSURANCE ────────────────────────────────────────
    assets_rows = db.execute(
        "SELECT * FROM assets WHERE profile_id=? AND active=1", (pid,)
    ).fetchall()
    for a in assets_rows:
        name = a["name"]
        if a["maintenance_date"]:
            try:
                mdate = date.fromisoformat(a["maintenance_date"])
                d_val = days_until(mdate)
                if -3 <= d_val <= 21:
                    if d_val <= 0:
                        msg = f"{name} bakım tarihi geçti! Servis planlamanız gerekiyor."
                        ico = "🔧"
                    else:
                        msg = f"{name} için {d_val} gün içinde bakım/servis planlanmış"
                        ico = "🔧"
                    add(ico, "Araç/Varlık Bakımı", msg, d_val, "bakim")
            except:
                pass
        if a["insurance_date"]:
            try:
                idate = date.fromisoformat(a["insurance_date"])
                d_val = days_until(idate)
                if -3 <= d_val <= 30:
                    if d_val <= 0:
                        msg = f"{name} sigortası süresi doldu! Yenilenmesi gerekiyor."
                        ico = "🛡️"
                    else:
                        msg = f"{name} sigortası {d_val} gün içinde yenilenmeli"
                        ico = "🛡️"
                    add(ico, "Sigorta Yenileme", msg, d_val, "sigorta")
            except:
                pass

    # Sort: urgent first, then by days
    notifs.sort(key=lambda x: (0 if x["urgency"]=="urgent" else 1 if x["urgency"]=="soon" else 2, x["days"]))
    return notifs


@app.route("/api/notifications")
@login_required
def api_notifications():
    db   = get_db()
    pid  = get_pid()
    uid  = session["user_id"]
    prof = db.execute("SELECT type FROM profiles WHERE id=?", (pid,)).fetchone()
    ptype = prof["type"] if prof else "sahis"
    today_ = date.today()
    notifs = generate_notifications(pid, ptype, db, today_)
    return jsonify({"ok": True, "items": notifs, "count": len(notifs)})


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
<meta name="theme-color" content="#f2f2f7">
<title>Kirpi — __MODE_TITLE__</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#f2f2f7;color:#1c1c1e;font-family:'Inter',system-ui,sans-serif;
  min-height:100vh;display:grid;grid-template-columns:1fr 1fr;align-items:stretch}
@media(max-width:700px){body{grid-template-columns:1fr}}
.hero{background:linear-gradient(145deg,#ffffff 0%,#f0f0f8 100%);
  display:flex;flex-direction:column;align-items:center;justify-content:center;padding:48px 40px;
  position:relative;overflow:hidden}
@media(max-width:700px){.hero{display:none}}
.hero-title{font-size:2rem;font-weight:900;letter-spacing:-.04em;margin-bottom:8px;
  background:linear-gradient(135deg,#818cf8,#a78bfa,#6ee7b7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero-sub{font-size:.9rem;color:#6d6d72;text-align:center;max-width:280px;line-height:1.6;margin-bottom:32px}
.hero-pills{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;max-width:300px}
.pill{background:#e5e5ea;border:1px solid #d1d1d6;border-radius:20px;padding:6px 14px;
  font-size:.75rem;color:#6d6d72;display:flex;align-items:center;gap:6px}
.right{display:flex;align-items:center;justify-content:center;padding:40px 36px;background:#f2f2f7}
.box{background:#ffffff;border:1px solid #d1d1d6;border-radius:20px;padding:40px 36px;
  width:100%;max-width:400px;box-shadow:0 4px 24px rgba(0,0,0,.08)}
.logo{text-align:center;margin-bottom:32px}
.logo img{width:64px;height:64px;border-radius:16px;margin-bottom:12px}
.logo h1{font-size:1.4rem;font-weight:800;letter-spacing:-.02em;color:#1c1c1e}
.logo p{font-size:.82rem;color:#6d6d72;margin-top:4px}
label{display:block;font-size:.78rem;color:#6d6d72;margin-bottom:5px;font-weight:500}
input{width:100%;background:#f2f2f7;border:1px solid #d1d1d6;color:#1c1c1e;
  padding:12px 14px;border-radius:10px;font-size:.9rem;outline:none;margin-bottom:14px;
  font-family:inherit;transition:.15s}
input:focus{border-color:#007aff;background:#ffffff}
.btn{width:100%;padding:13px;background:#007aff;color:#fff;border:none;border-radius:10px;
  font-size:.92rem;font-weight:700;cursor:pointer;transition:.2s;margin-top:4px}
.btn:hover{background:#0062cc}
.msg{text-align:center;font-size:.82rem;padding:10px 14px;border-radius:10px;margin-bottom:16px}
.msg.err{background:#ff3b3014;color:#c0281e;border:1px solid #ff3b3028}
.msg.ok{background:#34c75914;color:#1a8a3a;border:1px solid #34c75928}
.link{text-align:center;margin-top:18px;font-size:.82rem;color:#6d6d72}
.link a{color:#007aff;text-decoration:none;font-weight:600}
.link a:hover{color:#0062cc}
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
      <div id="reg-sahis" onclick="setRegType(this,'sahis')" style="border:2px solid #6366f1;border-radius:12px;padding:14px 10px;text-align:center;cursor:pointer;background:#3a3a3c;transition:.2s">
        <div style="font-size:1.6rem;margin-bottom:4px">&#128100;</div>
        <div style="font-size:.82rem;font-weight:700;color:#f2f2f7">Bireysel</div>
        <div style="font-size:.7rem;color:#aeaeb2;margin-top:2px">Şahıs hesabı</div>
      </div>
      <div id="reg-sirket" onclick="setRegType(this,'sirket')" style="border:2px solid #48484a;border-radius:12px;padding:14px 10px;text-align:center;cursor:pointer;background:#2c2c2e;transition:.2s">
        <div style="font-size:1.6rem;margin-bottom:4px">&#127970;</div>
        <div style="font-size:.82rem;font-weight:700;color:#aeaeb2">Ticari</div>
        <div style="font-size:.7rem;color:#8e8e93;margin-top:2px">Şirket hesabı</div>
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
      document.getElementById("reg-sahis").style.background=t==="sahis"?"#3a3a3c":"#2c2c2e";
      document.getElementById("reg-sirket").style.borderColor=t==="sirket"?"#6366f1":"#48484a";
      document.getElementById("reg-sirket").style.background=t==="sirket"?"#3a3a3c":"#2c2c2e";
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
      <div id="login-bir" onclick="setLoginType('bireysel')" style="border:2px solid #6366f1;border-radius:12px;padding:12px 10px;text-align:center;cursor:pointer;background:#3a3a3c;transition:.2s">
        <div style="font-size:1.3rem;margin-bottom:3px">&#128100;</div>
        <div id="login-bir-lbl" style="font-size:.82rem;font-weight:700;color:#f2f2f7">Bireysel</div>
      </div>
      <div id="login-tic" onclick="setLoginType('ticari')" style="border:2px solid #48484a;border-radius:12px;padding:12px 10px;text-align:center;cursor:pointer;background:#2c2c2e;transition:.2s">
        <div style="font-size:1.3rem;margin-bottom:3px">&#127970;</div>
        <div id="login-tic-lbl" style="font-size:.82rem;font-weight:700;color:#aeaeb2">Ticari</div>
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
      document.getElementById("login-bir").style.background=isBir?"#3a3a3c":"#2c2c2e";
      document.getElementById("login-bir-lbl").style.color=isBir?"#f2f2f7":"#aeaeb2";
      document.getElementById("login-tic").style.borderColor=!isBir?"#6366f1":"#48484a";
      document.getElementById("login-tic").style.background=!isBir?"#3a3a3c":"#2c2c2e";
      document.getElementById("login-tic-lbl").style.color=!isBir?"#f2f2f7":"#aeaeb2";
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
  --bg:#f2f2f7;--bg2:#ffffff;--bg3:#e5e5ea;--bg4:#d1d1d6;
  --g:#34c759;--r:#ff3b30;--b:#007aff;--b2:#5856d6;--y:#ff9500;--p:#af52de;--c:#32ade6;
  --txt:#1c1c1e;--txt2:#6d6d72;--border:#d1d1d6;--border2:#c6c6c8;
  --radius:14px;--shadow:0 2px 16px rgba(0,0,0,.08);
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
.nav-links{flex:1;padding:4px 8px;display:flex;flex-direction:column;gap:2px;overflow-y:auto}
.nav-sect{font-size:.57rem;text-transform:uppercase;letter-spacing:.13em;color:var(--txt2);
          font-weight:700;padding:12px 12px 3px;opacity:.45;pointer-events:none}
.nl{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;
    cursor:pointer;color:var(--txt2);font-size:.86rem;font-weight:500;transition:.14s;
    user-select:none;position:relative}
.nl:hover{background:var(--bg3);color:var(--txt)}
.nl.active{background:rgba(0,122,255,.09);color:var(--b);font-weight:600;
  box-shadow:inset 3px 0 0 var(--b)}
.nl .ico{font-size:1.1rem;width:22px;text-align:center;flex-shrink:0}

/* ── MOBILE NAV ── */
@media(max-width:768px){
  .nav-links{flex-direction:row;padding:0;gap:0;justify-content:space-around;align-items:center;height:100%}
  .nav-sect{display:none}
  .nl{flex-direction:column;gap:1px;font-size:.6rem;padding:4px 6px;min-width:48px;flex:1;
      max-width:72px;border-radius:0;box-shadow:none;background:transparent!important}
  .nl .ico{font-size:1.22rem;width:auto;transition:transform .18s cubic-bezier(.34,1.56,.64,1)}
  .nl span:not(.ico){color:var(--txt2);transition:color .15s;font-weight:500}
  /* Active: blue dot above label + icon pops */
  .nl.active .ico{transform:scale(1.12)}
  .nl.active span:not(.ico){color:var(--b);font-weight:700}
  .nl::after{content:'';display:block;width:18px;height:3px;border-radius:2px;
             background:transparent;margin:1px auto 0;transition:background .2s}
  .nl.active::after{background:var(--b)}
  .nl-add::after,.nl-more::after{display:none}
}

/* ── ADD BUTTON (mobile center) ── */
@media(max-width:768px){
  .nl-add{flex:0 0 64px;position:relative}
  .nl-add .ico{
    background:linear-gradient(135deg,#007aff,#5856d6);
    color:#fff;border-radius:50%;
    width:46px;height:46px;
    display:flex;align-items:center;justify-content:center;
    font-size:1.4rem;
    box-shadow:0 4px 18px rgba(0,122,255,.45);
    margin-top:-20px;
    border:3px solid var(--bg);
  }
  .nl-add span:not(.ico){color:var(--b);font-weight:700}
  /* More button */
  .nl-more .ico{font-size:1.4rem}
}

/* ── MORE SHEET ── */
.more-backdrop{display:none;position:fixed;inset:0;background:rgba(0,0,0,.35);
               z-index:9000;backdrop-filter:blur(3px);-webkit-backdrop-filter:blur(3px)}
.more-sheet{position:fixed;bottom:0;left:0;right:0;
            background:var(--bg2);border-radius:22px 22px 0 0;
            z-index:9001;padding:0 0 env(safe-area-inset-bottom,12px);
            box-shadow:0 -6px 32px rgba(0,0,0,.18);
            transform:translateY(100%);transition:transform .32s cubic-bezier(.4,0,.2,1);
            max-height:80vh;overflow-y:auto}
.more-sheet.open{transform:translateY(0)}
.more-backdrop.open{display:block}
.more-sheet-handle{width:38px;height:4px;border-radius:2px;background:var(--border2);
                   margin:12px auto 16px}
.more-sheet-title{font-size:.72rem;font-weight:700;text-transform:uppercase;
                  letter-spacing:.1em;color:var(--txt2);padding:0 20px 10px}
.more-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;
           background:var(--border);margin:0 0 2px}
.more-tile{display:flex;flex-direction:column;align-items:center;gap:6px;
           padding:18px 8px 16px;background:var(--bg2);cursor:pointer;
           transition:.12s;-webkit-tap-highlight-color:transparent}
.more-tile:active{background:var(--bg3)}
.more-tile .mt-ico{font-size:1.6rem;line-height:1}
.more-tile .mt-lbl{font-size:.72rem;font-weight:600;color:var(--txt);text-align:center}
.more-tile[data-sirket]{display:none}

.nav-bottom{padding:16px;border-top:1px solid var(--border);font-size:.72rem;color:var(--txt2);line-height:1.6}
@media(max-width:768px){.nav-bottom{display:none}}

/* ── PAGE ── */
.main{display:flex;flex-direction:column}
.page{display:none;padding:20px 28px;max-width:1280px;will-change:opacity,transform;opacity:0;transform:translateY(10px)}
.page.active{display:block;opacity:1;transform:translateY(0);transition:opacity .22s ease,transform .22s ease}
@media(max-width:600px){.page{padding:14px 14px 20px}}
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

/* ── BUDGET (legacy) ── */
.budget-row{margin-bottom:14px}
.budget-row .btop{display:flex;justify-content:space-between;font-size:.8rem;margin-bottom:5px}
.prog-bg{background:var(--bg3);border-radius:4px;height:6px;overflow:hidden}
.prog-fill{height:100%;border-radius:4px;transition:width .7s cubic-bezier(.4,0,.2,1)}

/* ── GOALS / TASARRUF ── */
.goals-capacity-card{background:linear-gradient(160deg,#eef3ff,#f0f0f8);border-color:#007aff18}
.goals-stat-cell{background:var(--bg3);border-radius:12px;padding:12px 14px;text-align:center}
.gsc-lbl{font-size:.63rem;text-transform:uppercase;letter-spacing:.09em;color:var(--txt2);font-weight:700;margin-bottom:4px}
.gsc-val{font-size:1.05rem;font-weight:800;letter-spacing:-.02em}
.gsc-val.gn{color:var(--g)}
.gsc-val.rd{color:var(--r)}
.goal-item{display:flex;align-items:center;gap:12px;padding:11px 12px;background:var(--bg3);border:1px solid var(--border);border-radius:13px;margin-bottom:8px}
.goal-icon-wrap{width:38px;height:38px;border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;flex-shrink:0}
.goal-info{flex:1;min-width:0}
.goal-name{font-size:.86rem;font-weight:700;color:var(--txt);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.goal-meta{font-size:.72rem;color:var(--txt2);margin-top:2px}
.goal-amount{font-size:.9rem;font-weight:800;color:var(--b2);text-align:right;flex-shrink:0}
.goal-del{background:none;border:none;color:var(--txt2);cursor:pointer;padding:4px 6px;border-radius:6px;transition:.15s;font-size:.85rem}
.goal-del:hover{color:var(--r);background:#ff453a18}
.comment-bubble{display:flex;gap:12px;align-items:flex-start;padding:14px 14px;border-radius:14px;margin-bottom:10px;border:1px solid transparent}
.comment-bubble.success{background:#30d15812;border-color:#30d15828}
.comment-bubble.good{background:#6366f112;border-color:#6366f128}
.comment-bubble.warn{background:#ffd60a10;border-color:#ffd60a28}
.comment-bubble.danger{background:#ff453a12;border-color:#ff453a28}
.comment-bubble.info{background:var(--bg3);border-color:var(--border)}
.comment-bubble.tip{background:#bf5af212;border-color:#bf5af228}
.cb-ico{font-size:1.3rem;flex-shrink:0;margin-top:1px}
.cb-text{font-size:.82rem;color:var(--txt);line-height:1.55}

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

/* ── NOTIFICATION BELL ─────────────────────────────────────── */
.notif-bell-wrap{position:relative}
.notif-bell{
  width:36px;height:36px;border-radius:50%;
  background:var(--bg3);border:1px solid var(--border2);
  color:var(--txt2);font-size:1.05rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  transition:.15s;outline:none;flex-shrink:0;
}
.notif-bell:hover{background:var(--bg4);color:var(--txt);transform:scale(1.06)}
.notif-badge{
  position:absolute;top:-3px;right:-3px;
  background:#ef4444;color:#fff;font-size:.58rem;font-weight:800;
  min-width:16px;height:16px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;padding:0 3px;
  border:2px solid var(--bg);line-height:1;
}
.notif-badge.hidden{display:none}

/* ── NOTIFICATION PANEL ────────────────────────────────────── */
.notif-overlay{
  position:fixed;inset:0;z-index:490;background:rgba(0,0,0,.45);
  opacity:0;pointer-events:none;transition:opacity .22s;
}
.notif-overlay.open{opacity:1;pointer-events:all}
.notif-panel{
  position:fixed;top:0;right:0;bottom:0;width:340px;max-width:100vw;
  background:var(--bg2);border-left:1px solid var(--border2);
  z-index:500;display:flex;flex-direction:column;
  transform:translateX(100%);transition:transform .26s cubic-bezier(.4,0,.2,1);
  box-shadow:-8px 0 40px rgba(0,0,0,.12);
}
.notif-panel.open{transform:translateX(0)}
.notif-panel-head{
  display:flex;align-items:center;justify-content:space-between;
  padding:16px 18px;border-bottom:1px solid var(--border);flex-shrink:0;
}
.notif-panel-title{font-size:.95rem;font-weight:800;color:var(--txt)}
.notif-close-btn{
  width:30px;height:30px;border-radius:50%;border:1px solid var(--border2);
  background:var(--bg3);color:var(--txt2);font-size:.9rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;transition:.15s;
}
.notif-close-btn:hover{background:var(--bg4);color:var(--txt)}
.notif-list{flex:1;overflow-y:auto;padding:10px 10px 80px}
.notif-item{
  display:flex;gap:11px;align-items:flex-start;
  padding:12px 12px;border-radius:12px;margin-bottom:7px;
  border:1px solid transparent;transition:.15s;cursor:default;
}
.notif-item.urgent{background:#ef444412;border-color:#ef444430}
.notif-item.soon{background:#f59e0b10;border-color:#f59e0b28}
.notif-item.normal{background:var(--bg3);border-color:var(--border)}
.notif-item-ico{font-size:1.3rem;flex-shrink:0;margin-top:1px}
.notif-item-body{flex:1;min-width:0}
.notif-item-title{font-size:.78rem;font-weight:700;color:var(--txt);margin-bottom:3px}
.notif-item.urgent .notif-item-title{color:#f87171}
.notif-item.soon .notif-item-title{color:#fbbf24}
.notif-item-msg{font-size:.74rem;color:var(--txt2);line-height:1.45}
.notif-item-days{font-size:.67rem;font-weight:700;margin-top:4px;opacity:.7}
.notif-item.urgent .notif-item-days{color:#f87171}
.notif-item.soon .notif-item-days{color:#fbbf24}
.notif-empty{text-align:center;padding:52px 20px;color:var(--txt2);font-size:.88rem}
.notif-empty-ico{font-size:2.8rem;margin-bottom:12px;opacity:.5}
.notif-section-lbl{
  font-size:.64rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
  color:var(--txt2);padding:8px 12px 4px;opacity:.7;
}

/* ── TOP HEADER ─────────────────────────────────────────────── */
.top-header{
  position:sticky;top:0;z-index:90;height:54px;
  background:rgba(242,242,247,.92);backdrop-filter:blur(20px) saturate(180%);
  -webkit-backdrop-filter:blur(20px) saturate(180%);
  border-bottom:1px solid rgba(0,0,0,.1);
  display:flex;align-items:center;justify-content:flex-end;
  padding:0 24px;flex-shrink:0;
}
@media(max-width:768px){.top-header{padding:0 16px;justify-content:space-between}}
.top-header-logo{font-size:.95rem;font-weight:800;display:none;align-items:center;gap:8px;color:var(--txt)}
@media(max-width:768px){.top-header-logo{display:flex}}
.top-header-right{display:flex;align-items:center;gap:10px}
.avatar-btn{
  width:36px;height:36px;border-radius:50%;
  background:linear-gradient(135deg,#6366f1,#818cf8);
  border:2px solid #6366f140;color:#fff;
  font-size:.85rem;font-weight:800;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  overflow:hidden;transition:.15s;outline:none;flex-shrink:0;
}
.avatar-btn:hover{transform:scale(1.06);box-shadow:0 0 0 3px #6366f128}
.avatar-btn img,.avatar-btn-inner-img{width:100%;height:100%;object-fit:cover;border-radius:50%}

/* ── USER DROPDOWN ───────────────────────────────────────────── */
.udrop-wrap{position:relative}
.user-dropdown{
  position:absolute;right:0;top:calc(100% + 10px);
  width:290px;background:rgba(255,255,255,.96);border:1px solid rgba(0,0,0,.1);
  border-radius:18px;box-shadow:0 8px 40px rgba(0,0,0,.15);
  z-index:500;overflow:hidden;
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  opacity:0;transform:translateY(-8px) scale(.96);
  pointer-events:none;
  transition:opacity .2s,transform .2s cubic-bezier(.4,0,.2,1);
}
.user-dropdown.open{opacity:1;transform:translateY(0) scale(1);pointer-events:all}
.udrop-head{
  padding:14px 14px 12px;
  background:rgba(242,242,247,.8);
  border-bottom:1px solid rgba(0,0,0,.06);
  display:flex;align-items:center;gap:12px;
}
.udrop-ava-lg{
  width:42px;height:42px;border-radius:50%;flex-shrink:0;
  background:linear-gradient(135deg,#6366f1,#818cf8);
  color:#fff;font-size:.95rem;font-weight:800;
  display:flex;align-items:center;justify-content:center;
  overflow:hidden;border:2px solid #6366f140;
}
.udrop-name{font-size:.88rem;font-weight:700;color:var(--txt)}
.udrop-sub{font-size:.72rem;color:var(--txt2);margin-top:2px}
.udrop-prof-item{
  display:flex;align-items:center;gap:9px;padding:8px 10px;
  border-radius:9px;cursor:pointer;transition:.1s;font-size:.82rem;color:var(--txt2);
}
.udrop-prof-item:hover{background:var(--bg3)}
.udrop-prof-item.cur{background:#6366f112;color:var(--b2);font-weight:600}
.udrop-prof-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.udrop-add-btn{
  width:100%;margin-top:5px;padding:7px;background:transparent;
  border:1px dashed var(--border2);border-radius:8px;
  color:var(--b2);font-size:.75rem;cursor:pointer;font-weight:600;transition:.15s;
}
.udrop-add-btn:hover{border-color:var(--b2);background:#6366f110}
.udrop-divider{height:1px;background:var(--border);margin:4px 0}
.udrop-actions{padding:8px}
.udrop-action{
  display:flex;align-items:center;gap:10px;padding:9px 10px;
  border-radius:10px;cursor:pointer;transition:.1s;font-size:.83rem;
  color:var(--txt2);font-weight:500;width:100%;text-align:left;
  background:none;border:none;font-family:inherit;text-decoration:none;
}
.udrop-action:hover{background:var(--bg3);color:var(--txt)}
.udrop-action.danger{color:var(--r)}
.udrop-action.danger:hover{background:#ef444412}
.udrop-action-ico{
  width:30px;height:30px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;font-size:.88rem;flex-shrink:0;
}

/* ── SETTINGS PAGE ────────────────────────────────────────────── */
.settings-card{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:16px}
.settings-sect-title{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--txt2);margin-bottom:16px}
.avatar-upload-wrap{display:flex;align-items:center;gap:16px;margin-bottom:16px}
.avatar-lg{
  width:68px;height:68px;border-radius:50%;flex-shrink:0;
  background:linear-gradient(135deg,#6366f1,#818cf8);
  color:#fff;font-size:1.5rem;font-weight:800;
  display:flex;align-items:center;justify-content:center;
  overflow:hidden;border:3px solid #6366f140;
}
.avatar-lg img{width:100%;height:100%;object-fit:cover}
.avatar-upload-btn{padding:7px 14px;background:var(--bg3);border:1px solid var(--border2);color:var(--txt2);border-radius:9px;font-size:.8rem;cursor:pointer;font-weight:600;transition:.15s}
.avatar-upload-btn:hover{border-color:var(--b2);color:var(--b2)}
.settings-link-row{
  display:flex;align-items:center;justify-content:space-between;
  padding:12px 4px;border-bottom:1px solid var(--border);
  font-size:.84rem;color:var(--txt);text-decoration:none;cursor:pointer;
  background:none;border-left:none;border-right:none;border-top:none;
  width:100%;text-align:left;font-family:inherit;
  transition:.1s;
}
.settings-link-row:last-child{border-bottom:none}
.settings-link-row:hover{color:var(--b2)}
.settings-profile-item{
  display:flex;align-items:center;justify-content:space-between;
  padding:10px 12px;background:var(--bg3);border-radius:10px;margin-bottom:8px;
}
.settings-profile-item .sp-info{font-size:.83rem;font-weight:600;color:var(--txt)}
.settings-profile-item .sp-type{font-size:.72rem;color:var(--txt2)}
.settings-profile-item .sp-active{font-size:.68rem;color:var(--g);font-weight:700;padding:2px 8px;background:#22c55e15;border-radius:8px;border:1px solid #22c55e25}

/* ── HERO BALANCE CARD ────────────────────────────────────── */
.hero-card{background:linear-gradient(145deg,#0d1f3c 0%,#16305a 55%,#1a3565 100%);border:none;border-radius:26px;padding:26px 22px 22px;margin-bottom:16px;position:relative;overflow:hidden;box-shadow:0 14px 52px rgba(8,28,80,.5),0 2px 10px rgba(0,0,0,.2)}
.hero-card::before{content:'';position:absolute;top:-70px;right:-60px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(99,160,255,.18),transparent 70%)}
.hero-card::after{content:'';position:absolute;bottom:-60px;left:-40px;width:210px;height:210px;border-radius:50%;background:radial-gradient(circle,rgba(52,199,89,.13),transparent 70%)}
.hero-top-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;position:relative}
.hero-greeting{font-size:.82rem;color:rgba(255,255,255,.55);font-weight:500}
.hero-kirpi{font-size:1.8rem;line-height:1;transition:transform .4s cubic-bezier(.34,1.56,.64,1),opacity .3s;user-select:none}
.hero-kirpi.bounce{animation:kirpi-bounce .5s cubic-bezier(.34,1.56,.64,1)}
@keyframes kirpi-bounce{0%{transform:scale(1)}40%{transform:scale(1.35)}100%{transform:scale(1)}}
.hero-period-tabs{display:flex;gap:4px;background:rgba(255,255,255,.1);border-radius:9px;padding:3px;margin-bottom:8px;position:relative;width:fit-content}
.hero-period-tab{padding:4px 14px;border-radius:7px;font-size:.7rem;font-weight:600;color:rgba(255,255,255,.45);cursor:pointer;transition:.18s;border:none;background:transparent}
.hero-period-tab.active{background:#fff;color:#0d1f3c;box-shadow:0 1px 6px rgba(0,0,0,.2)}
.hero-year-nav{display:none;align-items:center;gap:8px;margin-bottom:8px}
.hero-year-btn{width:26px;height:26px;border-radius:50%;border:none;background:rgba(255,255,255,.1);color:rgba(255,255,255,.7);font-size:.85rem;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.15s}
.hero-year-btn:hover{background:rgba(255,255,255,.2);color:#fff}
.hero-year-val{font-size:.82rem;font-weight:700;color:rgba(255,255,255,.88);min-width:38px;text-align:center}
.hero-bal-lbl{font-size:.63rem;text-transform:uppercase;letter-spacing:.14em;color:rgba(255,255,255,.42);margin-bottom:6px;font-weight:700;position:relative}
.hero-balance{font-size:2.7rem;font-weight:900;letter-spacing:-.05em;line-height:1;margin-bottom:4px;color:#fff;position:relative;text-shadow:0 2px 16px rgba(0,0,0,.25)}
.hero-net-sub{font-size:.72rem;color:rgba(255,255,255,.42);margin-bottom:16px;min-height:14px;position:relative}
.hero-chips{display:flex;gap:7px;flex-wrap:wrap;position:relative}
.hero-chip{display:flex;align-items:center;gap:4px;padding:6px 14px;border-radius:20px;font-size:.76rem;font-weight:600}
.hero-chip.gn{background:rgba(52,199,89,.22);color:#5edc80;border:1px solid rgba(52,199,89,.35)}
.hero-chip.rd{background:rgba(255,59,48,.22);color:#ff7e78;border:1px solid rgba(255,59,48,.35)}
.hero-chip.nt{background:rgba(255,255,255,.13);color:rgba(255,255,255,.85);border:1px solid rgba(255,255,255,.22)}

/* ── CLICKABLE CHIP ──────────────────────────────────────────── */
.hero-chip{cursor:pointer;transition:.15s}
.hero-chip:hover{opacity:.85;transform:translateY(-1px)}
.hero-chip:active{opacity:.6}

/* ── DASH SECTION CARDS ─────────────────────────────────────── */
.dash-section{background:var(--bg2);border:1px solid var(--border);border-radius:18px;margin-bottom:12px;overflow:hidden;box-shadow:0 2px 16px rgba(0,0,0,.05)}
.dash-section .s-header{padding:14px 16px;border-bottom:1px solid var(--border);border-radius:0}
.dash-section .s-body{padding:12px 14px 14px;margin-bottom:0;border-radius:0 0 18px 18px}
.dash-section .s-body.collapsed{padding-top:0;padding-bottom:0}

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
.today-card.gn{background:linear-gradient(135deg,#edfaf2,#dff5e9);border:1px solid #34c75930}
.today-card.gn .tc-lbl{color:#1a8a3a}.today-card.gn .tc-val{color:var(--g)}
.today-card.rd{background:linear-gradient(135deg,#fff0ef,#ffe5e3);border:1px solid #ff3b3030}
.today-card.rd .tc-lbl{color:#c0281e}.today-card.rd .tc-val{color:var(--r)}
.today-card.nt{background:linear-gradient(135deg,#eef3ff,#e6ecff);border:1px solid #007aff28}
.today-card.nt .tc-lbl{color:#004dcc}.today-card.nt .tc-val{color:var(--b)}

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
.cc-pct-badge.ok{background:#34c75914;color:var(--g);border:1px solid #34c75928}
.cc-pct-badge.warn{background:#ff950014;color:var(--y);border:1px solid #ff950028}
.cc-pct-badge.high{background:#ff3b3014;color:var(--r);border:1px solid #ff3b3028}
.cc-prog-bg{background:var(--bg3);border-radius:6px;height:5px;overflow:hidden;margin-bottom:7px}
.cc-prog-fill{height:100%;border-radius:6px;transition:width .7s cubic-bezier(.4,0,.2,1)}
.cc-nums{display:flex;justify-content:space-between;font-size:.72rem;color:var(--txt2)}
.cc-nums strong{color:var(--txt);font-weight:600}
.empty-cc{text-align:center;padding:22px 16px;color:var(--txt2);font-size:.82rem;line-height:1.7}

/* ── MOBILE NAV ENHANCEMENTS ────────────────────────────────── */
.nl-desktop{}
@media(max-width:768px){
  nav{height:64px;padding:0;box-shadow:0 -1px 0 var(--border),0 -4px 16px rgba(0,0,0,.07)}
  .main{margin-bottom:64px}
  .nl-desktop{display:none!important}
}

/* ── KIRPI WALK ANIMATION ────────────────────────────────────── */
@keyframes kirpi-float{
  0%,100%{transform:translateY(0) rotate(-2deg)}
  50%{transform:translateY(-5px) rotate(2deg)}
}
@keyframes kirpi-walk{
  0%{transform:scaleX(1) translateX(0)}
  25%{transform:scaleX(1) translateX(3px) rotate(3deg)}
  50%{transform:scaleX(-1) translateX(0)}
  75%{transform:scaleX(-1) translateX(-3px) rotate(-3deg)}
  100%{transform:scaleX(1) translateX(0)}
}
.kirpi-walk-wrap{display:inline-block;vertical-align:middle;margin-right:6px}
.kirpi-walk-img{animation:kirpi-float 3s ease-in-out infinite;display:block}
.nav-logo:hover .kirpi-walk-img{animation:kirpi-walk 1s steps(1) infinite}

/* ── PAGE TRANSITION ─────────────────────────────────────────── */
@keyframes page-in{
  from{opacity:0;transform:translateY(12px)}
  to{opacity:1;transform:translateY(0)}
}
.page.active{animation:page-in .22s ease-out}

/* ── TAP FEEDBACK ────────────────────────────────────────────── */
.tappable{cursor:pointer;-webkit-tap-highlight-color:transparent;transition:transform .1s,opacity .1s}
.tappable:active{transform:scale(.97);opacity:.85}

/* ── TODOS PAGE ──────────────────────────────────────────────── */
.todo-date-nav{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:10px 14px}
.todo-date-lbl{font-size:.95rem;font-weight:700;color:var(--txt)}
.todo-nav-btn{background:none;border:none;font-size:1.2rem;cursor:pointer;padding:4px 10px;border-radius:9px;color:var(--b);transition:.1s}
.todo-nav-btn:active{background:var(--bg3)}
.todo-add-row{display:flex;gap:8px;margin-bottom:16px}
.todo-add-input{flex:1;background:var(--bg2);border:1.5px solid var(--border2);border-radius:12px;padding:11px 14px;font-size:.9rem;color:var(--txt);outline:none;transition:.15s;font-family:var(--font)}
.todo-add-input:focus{border-color:var(--b);box-shadow:0 0 0 3px rgba(0,122,255,.1)}
.todo-add-btn{background:var(--b);border:none;border-radius:12px;padding:0 18px;color:#fff;font-size:1.1rem;cursor:pointer;font-weight:700;transition:.1s}
.todo-add-btn:active{opacity:.8;transform:scale(.96)}
.todo-list{display:flex;flex-direction:column;gap:8px}
.todo-item{display:flex;align-items:center;gap:12px;padding:12px 14px;background:var(--bg2);border:1px solid var(--border);border-radius:13px;cursor:pointer;transition:.12s;-webkit-tap-highlight-color:transparent}
.todo-item:active{background:var(--bg3);transform:scale(.99)}
.todo-item.done{opacity:.55}
.todo-item.done .todo-text{text-decoration:line-through;color:var(--txt2)}
.todo-check{width:24px;height:24px;border-radius:50%;border:2.5px solid var(--border2);display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:.2s;font-size:.8rem;background:transparent}
.todo-item.done .todo-check{background:var(--g);border-color:var(--g);color:#fff}
.todo-text{flex:1;font-size:.9rem;font-weight:500;color:var(--txt);line-height:1.4}
.todo-del{background:none;border:none;font-size:.85rem;color:var(--txt2);cursor:pointer;padding:4px 6px;border-radius:6px;opacity:0;transition:.15s}
.todo-item:hover .todo-del{opacity:1}
.todo-archive-section{margin-top:24px}
.todo-archive-hdr{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--txt2);padding:0 2px 8px;border-bottom:1px solid var(--border);margin-bottom:10px;display:flex;align-items:center;gap:6px}
@keyframes todo-check-pop{
  0%{transform:scale(.8)}
  60%{transform:scale(1.2)}
  100%{transform:scale(1)}
}
.todo-check.popping{animation:todo-check-pop .3s cubic-bezier(.4,0,.2,1)}
@keyframes todo-done-slide{
  from{max-height:80px;opacity:1}
  to{max-height:0;opacity:0;margin-bottom:0;padding:0}
}
.todo-item.archiving{animation:todo-done-slide .5s ease forwards}

/* ── SUPPLIER PAGE ───────────────────────────────────────────── */
.aging-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px}
@media(max-width:600px){.aging-grid{grid-template-columns:repeat(2,1fr)}}
.aging-card{border-radius:14px;padding:14px;text-align:center;border:1px solid transparent}
.aging-card .ac-lbl{font-size:.63rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px}
.aging-card .ac-val{font-size:1.05rem;font-weight:800;letter-spacing:-.02em}
.aging-card .ac-cnt{font-size:.7rem;margin-top:3px;opacity:.7}
.aging-card.green{background:#edfaf2;border-color:#34c75930}.aging-card.green .ac-lbl{color:#1a8a3a}.aging-card.green .ac-val{color:var(--g)}
.aging-card.yellow{background:#fffbeb;border-color:#ff950030}.aging-card.yellow .ac-lbl{color:#a06000}.aging-card.yellow .ac-val{color:var(--y)}
.aging-card.orange{background:#fff7ed;border-color:#ea730030}.aging-card.orange .ac-lbl{color:#994700}.aging-card.orange .ac-val{color:#ea7300}
.aging-card.red{background:#fff0ef;border-color:#ff3b3030}.aging-card.red .ac-lbl{color:#c0281e}.aging-card.red .ac-val{color:var(--r)}
.float-gain-banner{background:linear-gradient(135deg,var(--b),var(--b2));border-radius:14px;padding:18px 20px;color:#fff;display:flex;align-items:center;gap:16px;margin-bottom:16px}
.fgb-icon{font-size:2rem;flex-shrink:0}
.fgb-info{flex:1}
.fgb-label{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;opacity:.8;margin-bottom:4px}
.fgb-value{font-size:1.6rem;font-weight:900;letter-spacing:-.03em}
.sup-inv-item{display:flex;align-items:center;gap:12px;padding:13px 14px;background:var(--bg2);border:1px solid var(--border);border-radius:13px;margin-bottom:8px;cursor:pointer;-webkit-tap-highlight-color:transparent;transition:.1s}
.sup-inv-item:active{background:var(--bg3)}
.sup-inv-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.sup-inv-info{flex:1;min-width:0}
.sup-inv-name{font-size:.86rem;font-weight:600;color:var(--txt);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sup-inv-meta{font-size:.71rem;color:var(--txt2);margin-top:2px}
.sup-inv-right{text-align:right;flex-shrink:0}
.sup-inv-amount{font-size:.9rem;font-weight:700}
.sup-inv-days{font-size:.68rem;margin-top:3px;font-weight:600}

/* ── ASSETS PAGE ─────────────────────────────────────────────── */
.asset-card{background:var(--bg2);border:1px solid var(--border);border-radius:16px;padding:16px;margin-bottom:12px;cursor:pointer;-webkit-tap-highlight-color:transparent;transition:.12s}
.asset-card:active{background:var(--bg3);transform:scale(.99)}
.asset-card-top{display:flex;align-items:center;gap:12px;margin-bottom:12px}
.asset-icon{width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex-shrink:0}
.asset-icon.arac{background:#eef3ff;border:1px solid #007aff20}
.asset-icon.bilgisayar{background:#f0fdf4;border:1px solid #34c75920}
.asset-icon.makine{background:#fffbeb;border:1px solid #ff950020}
.asset-icon.diger{background:#f5f5f5;border:1px solid #d1d1d6}
.asset-name{font-size:.95rem;font-weight:700;color:var(--txt)}
.asset-type-badge{font-size:.62rem;font-weight:700;padding:2px 8px;border-radius:8px;background:var(--bg3);color:var(--txt2);margin-top:3px;display:inline-block}
.asset-dep-bar-bg{height:6px;background:var(--bg3);border-radius:4px;overflow:hidden;margin-bottom:8px}
.asset-dep-bar-fill{height:100%;background:linear-gradient(90deg,var(--b),var(--b2));border-radius:4px;transition:width .7s cubic-bezier(.4,0,.2,1)}
.asset-nums{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.asset-num-cell .anc-lbl{font-size:.62rem;text-transform:uppercase;letter-spacing:.07em;color:var(--txt2);font-weight:600;margin-bottom:3px}
.asset-num-cell .anc-val{font-size:.85rem;font-weight:700;color:var(--txt)}
.asset-alert{display:flex;align-items:center;gap:8px;padding:8px 12px;border-radius:9px;font-size:.76rem;font-weight:600;margin-top:10px}
.asset-alert.warn{background:#fff7ed;color:#994700;border:1px solid #ff950028}
.asset-alert.danger{background:#fff0ef;color:#c0281e;border:1px solid #ff3b3028}

/* ── CARD DAILY REPORT ───────────────────────────────────────── */
.cdr-card{background:var(--bg2);border:1px solid var(--border);border-radius:16px;padding:16px;margin-bottom:12px}
.cdr-card-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.cdr-bank{font-size:.9rem;font-weight:700;color:var(--txt)}
.cdr-date{font-size:.72rem;color:var(--txt2)}
.cdr-nums{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.cdr-cell .dc-lbl{font-size:.62rem;text-transform:uppercase;letter-spacing:.08em;color:var(--txt2);font-weight:600;margin-bottom:5px}
.cdr-cell .dc-val{font-size:1rem;font-weight:800;letter-spacing:-.02em}
.cdr-cell.spent .dc-val{color:var(--r)}
.cdr-cell.today .dc-val{color:var(--b)}
.cdr-cell.yest .dc-val{color:var(--txt2)}
.cdr-input-row{display:flex;gap:8px;margin-top:12px;border-top:1px solid var(--border);padding-top:12px}
.cdr-bal-input{flex:1;background:var(--bg);border:1.5px solid var(--border2);border-radius:10px;padding:9px 12px;font-size:.88rem;color:var(--txt);outline:none;font-family:var(--font)}
.cdr-bal-input:focus{border-color:var(--b)}
.cdr-save-btn{background:var(--b);border:none;border-radius:10px;padding:0 16px;color:#fff;font-size:.85rem;font-weight:600;cursor:pointer;transition:.1s}
.cdr-save-btn:active{opacity:.8}

/* ── MODAL BASE ──────────────────────────────────────────────── */
.mod-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.45);backdrop-filter:blur(4px);z-index:1000;display:flex;align-items:flex-end;justify-content:center}
@media(min-width:600px){.mod-backdrop{align-items:center}}
.mod-sheet{background:var(--bg);border-radius:20px 20px 0 0;width:100%;max-width:540px;padding:20px 20px 32px;max-height:88vh;overflow-y:auto}
@media(min-width:600px){.mod-sheet{border-radius:20px;padding:24px}}
.mod-handle{width:36px;height:4px;background:var(--bg4);border-radius:2px;margin:0 auto 18px}
.mod-title{font-size:1.05rem;font-weight:800;color:var(--txt);margin-bottom:16px}
.mod-field{margin-bottom:12px}
.mod-label{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--txt2);margin-bottom:5px}
.mod-input{width:100%;background:var(--bg2);border:1.5px solid var(--border2);border-radius:11px;padding:11px 13px;font-size:.9rem;color:var(--txt);outline:none;box-sizing:border-box;font-family:var(--font);transition:.15s}
.mod-input:focus{border-color:var(--b);box-shadow:0 0 0 3px rgba(0,122,255,.1)}
.mod-row{display:flex;gap:8px}
.mod-row .mod-field{flex:1}
.mod-actions{display:flex;gap:8px;margin-top:16px}
.mod-btn{flex:1;padding:13px;border:none;border-radius:12px;font-size:.9rem;font-weight:700;cursor:pointer;transition:.1s}
.mod-btn:active{opacity:.8;transform:scale(.98)}
.mod-btn.primary{background:var(--b);color:#fff}
.mod-btn.danger{background:var(--r);color:#fff}
.mod-btn.cancel{background:var(--bg3);color:var(--txt)}
</style>
</head>
<body>
<div class="shell">

<!-- ── SIDEBAR NAV ── -->
<nav>
  <div class="nav-logo" onclick="goPage('dashboard',document.querySelector('[data-page=dashboard]'))" style="cursor:pointer">
    <div class="brand">
      <div class="kirpi-walk-wrap"><img src="/icon.svg" class="kirpi-walk-img" style="width:32px;height:32px;border-radius:8px"> </div>Kirpi
    </div>
    <div class="sub">Nakit Akışı Takibi</div>
  </div>
  <div class="nav-links">
    <div class="nav-sect">Ana</div>
    <div class="nl active" data-page="dashboard" onclick="goPage('dashboard',this)">
      <span class="ico">🏠</span>Anasayfa
    </div>
    <div class="nl" data-page="ledger" onclick="goPage('ledger',this)">
      <span class="ico">📋</span>Tablo
    </div>
    <div class="nl nl-add" data-page="add" onclick="goPage('add',this)">
      <span class="ico">➕</span>Ekle
    </div>
    <div class="nl" data-page="todos" onclick="goPage('todos',this)">
      <span class="ico">✅</span>Görevler
    </div>
    <div class="nl nl-more" onclick="openMoreSheet()">
      <span class="ico">⋯</span>Daha
    </div>

    <div class="nav-sect">Araçlar</div>
    <div class="nl nl-desktop" data-page="recurring" onclick="goPage('recurring',this)">
      <span class="ico">🔁</span>Düzenli
    </div>
    <div class="nl nl-desktop" data-page="budget" onclick="goPage('budget',this)">
      <span class="ico">🎯</span>Tasarruf
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

    <div class="nav-sect">Firma</div>
    <div class="nl nl-desktop" data-page="supplier" data-sirket onclick="goPage('supplier',this)">
      <span class="ico">🏭</span>Tedarikçi
    </div>
    <div class="nl nl-desktop" data-page="assets" data-sirket onclick="goPage('assets',this)">
      <span class="ico">🚗</span>Kıymetler
    </div>
    <div class="nl nl-desktop" data-page="cardreport" data-sirket onclick="goPage('cardreport',this)">
      <span class="ico">📊</span>Kart Raporu
    </div>

    <div class="nav-sect">Sistem</div>
    <div class="nl nl-desktop" data-page="settings" onclick="goPage('settings',this)">
      <span class="ico">⚙️</span>Ayarlar
    </div>
  </div>
  <div class="nav-bottom">
    <div style="font-size:.7rem;color:var(--txt2);opacity:.5">Kirpi v1.0</div>
  </div>
</nav>

<!-- ── MORE SHEET (mobile) ── -->
<div class="more-backdrop" id="more-backdrop" onclick="closeMoreSheet()"></div>
<div class="more-sheet" id="more-sheet">
  <div class="more-sheet-handle"></div>
  <div class="more-sheet-title">Tüm Sayfalar</div>
  <div class="more-grid">
    <div class="more-tile" onclick="goPageFromSheet('recurring')">
      <div class="mt-ico">🔁</div><div class="mt-lbl">Düzenli</div>
    </div>
    <div class="more-tile" onclick="goPageFromSheet('budget')">
      <div class="mt-ico">🎯</div><div class="mt-lbl">Tasarruf</div>
    </div>
    <div class="more-tile" onclick="goPageFromSheet('invest')">
      <div class="mt-ico">📈</div><div class="mt-lbl">Yatırım</div>
    </div>
    <div class="more-tile" onclick="goPageFromSheet('cards')">
      <div class="mt-ico">💳</div><div class="mt-lbl">Kartlar</div>
    </div>
    <div class="more-tile" onclick="goPageFromSheet('import')">
      <div class="mt-ico">📂</div><div class="mt-lbl">İçe Aktar</div>
    </div>
    <div class="more-tile" onclick="goPageFromSheet('settings')">
      <div class="mt-ico">⚙️</div><div class="mt-lbl">Ayarlar</div>
    </div>
    <div class="more-tile" data-sirket onclick="goPageFromSheet('supplier')">
      <div class="mt-ico">🏭</div><div class="mt-lbl">Tedarikçi</div>
    </div>
    <div class="more-tile" data-sirket onclick="goPageFromSheet('assets')">
      <div class="mt-ico">🚗</div><div class="mt-lbl">Kıymetler</div>
    </div>
    <div class="more-tile" data-sirket onclick="goPageFromSheet('cardreport')">
      <div class="mt-ico">📊</div><div class="mt-lbl">Kart Raporu</div>
    </div>
  </div>
</div>

<!-- ── MAIN ── -->
<div class="main">

<!-- TOP HEADER -->
<div class="top-header">
  <div class="top-header-logo tappable" onclick="goPage('dashboard',document.querySelector('[data-page=dashboard]'))" style="cursor:pointer">🦔 Kirpi</div>
  <div class="top-header-right">
    <div class="notif-bell-wrap">
      <button class="notif-bell" id="notif-bell" onclick="toggleNotifPanel()" title="Bildirimler">🔔</button>
      <span class="notif-badge hidden" id="notif-badge">0</span>
    </div>
    <div class="udrop-wrap">
      <button class="avatar-btn" id="avatar-btn" onclick="toggleUserMenu(event)">
        <span id="avatar-btn-inner">?</span>
      </button>
      <div class="user-dropdown" id="user-dropdown">
        <div class="udrop-head">
          <div class="udrop-ava-lg" id="udrop-ava">?</div>
          <div class="udrop-user-info">
            <div class="udrop-name" id="udrop-name">—</div>
            <div class="udrop-sub" id="udrop-sub">—</div>
          </div>
        </div>
        <div style="padding:8px 8px 4px">
          <div style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--txt2);padding:0 6px;margin-bottom:4px">Profiller</div>
          <div id="udrop-profiles"></div>
          <button onclick="showAddProfile2()" class="udrop-add-btn">+ Yeni Profil Ekle</button>
          <div id="add-profile-form2" style="display:none;background:var(--bg);border:1px solid var(--border2);border-radius:10px;padding:10px;margin-top:6px">
            <select id="new-profile-type" style="width:100%;background:var(--bg2);border:1px solid var(--border2);color:var(--txt);padding:7px 10px;border-radius:7px;font-size:.8rem;margin-bottom:6px;outline:none">
              <option value="sahis">👤 Şahıs (Kişisel)</option>
              <option value="sirket">🏢 Şirket (Kurumsal)</option>
            </select>
            <input id="new-profile-name" placeholder="İsim ya da Ünvan" style="width:100%;background:var(--bg2);border:1px solid var(--border2);color:var(--txt);padding:7px 10px;border-radius:7px;font-size:.8rem;margin-bottom:8px;outline:none">
            <div style="display:flex;gap:6px">
              <button onclick="createProfile()" style="flex:1;padding:7px;background:var(--b);border:none;border-radius:7px;color:#fff;font-size:.78rem;cursor:pointer;font-weight:600">Oluştur</button>
              <button onclick="cancelAddProfile()" style="padding:7px 10px;background:transparent;border:1px solid var(--border2);border-radius:7px;color:var(--txt2);font-size:.78rem;cursor:pointer">İptal</button>
            </div>
          </div>
        </div>
        <div class="udrop-divider"></div>
        <div class="udrop-actions">
          <button class="udrop-action" onclick="goPage('settings',document.querySelector('[data-page=settings]'));toggleUserMenu()">
            <span class="udrop-action-ico" style="background:#6366f118;color:var(--b2)">⚙️</span>Ayarlar
          </button>
          <button class="udrop-action" onclick="triggerInstall()">
            <span class="udrop-action-ico" style="background:#22c55e18;color:var(--g)">⬇️</span>Uygulamayı Kur
          </button>
          <a class="udrop-action danger" href="/logout">
            <span class="udrop-action-ico" style="background:#ef444418;color:var(--r)">↩</span>Çıkış Yap
          </a>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- NOTIFICATION OVERLAY + PANEL -->
<div class="notif-overlay" id="notif-overlay" onclick="closeNotifPanel()"></div>
<div class="notif-panel" id="notif-panel">
  <div class="notif-panel-head">
    <span class="notif-panel-title">🔔 Bildirimler</span>
    <button class="notif-close-btn" onclick="closeNotifPanel()">✕</button>
  </div>
  <div class="notif-list" id="notif-list">
    <div class="notif-empty"><div class="notif-empty-ico">🦔</div>Yükleniyor…</div>
  </div>
</div>

<!-- DASHBOARD -->
<div class="page active" id="page-dashboard">

  <!-- ── HERO BALANCE ── -->
  <div class="hero-card">
    <div class="hero-top-row">
      <div class="hero-greeting" id="hero-greeting">Merhaba __USER_DISPLAY__ 👋</div>
      <div class="hero-kirpi" id="hero-kirpi" title="Günün durumu">🦔</div>
    </div>
    <div class="hero-period-tabs">
      <button class="hero-period-tab active" id="htab-month" onclick="setHeroPeriod('month')">Ay</button>
      <button class="hero-period-tab" id="htab-year" onclick="setHeroPeriod('year')">Yıl</button>
      <button class="hero-period-tab" id="htab-all" onclick="setHeroPeriod('all')">Tümü</button>
    </div>
    <div class="hero-year-nav" id="hero-year-nav">
      <button class="hero-year-btn" onclick="changeHeroYear(-1)">◀</button>
      <span class="hero-year-val" id="hero-year-val">2026</span>
      <button class="hero-year-btn" onclick="changeHeroYear(1)">▶</button>
    </div>
    <div class="hero-bal-lbl" id="hero-bal-lbl">BU AY NET</div>
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
  <div class="dash-section">
    <div class="s-header" onclick="toggleSection('gelir')">
      <div class="sh-left"><span class="sh-dot gn"></span><span id="gelir-section-lbl">Günün Gelirleri</span></div>
      <input type="date" id="today-date-pick" onclick="event.stopPropagation()" onchange="changeTodayDate(this.value)"
        style="background:var(--bg3);border:1px solid var(--border2);color:var(--txt2);padding:3px 8px;border-radius:7px;font-size:.72rem;outline:none;cursor:pointer">
      <span class="sh-badge" id="gelir-badge" style="display:none">0</span>
      <span class="sh-chevron" id="chevron-gelir">▾</span>
    </div>
    <div class="s-body" id="sec-gelir">
      <div id="today-gelir-list"><div class="empty-pay"><div class="ep-ico">📅</div><div class="ep-txt">Yükleniyor…</div></div></div>
      <div class="today-subtotal today-subtotal-gn" id="today-gelir-total" style="display:none">
        <span>Toplam Gelir</span><span id="today-gelir">—</span>
      </div>
    </div>
  </div>

  <!-- ── GÜNÜN GİDERLERİ ── -->
  <div class="dash-section">
    <div class="s-header" onclick="toggleSection('gider')">
      <div class="sh-left"><span class="sh-dot rd"></span><span id="gider-section-lbl">Günün Giderleri</span></div>
      <span class="sh-badge" id="gider-badge" style="display:none">0</span>
      <span class="sh-chevron" id="chevron-gider">▾</span>
    </div>
    <div class="s-body" id="sec-gider">
      <div id="today-gider-list"><div class="empty-pay"><div class="ep-ico">📅</div><div class="ep-txt">Yükleniyor…</div></div></div>
      <div class="today-subtotal today-subtotal-rd" id="today-gider-total" style="display:none">
        <span>Toplam Gider</span><span id="today-gider">—</span>
      </div>
    </div>
  </div>

  <!-- ── GÜNÜN BAKİYESİ ── -->
  <div class="today-net-row" id="today-net-row" style="display:none">
    <div class="tnr-label">Günün Bakiyesi</div>
    <div class="tnr-value" id="today-net">—</div>
  </div>

  <!-- ── KREDİ KARTLARI ── -->
  <div class="dash-section">
    <div class="s-header" onclick="toggleSection('cc')">
      <div class="sh-left"><span class="sh-dot pp"></span>Kredi Kartları</div>
      <span class="sh-chevron" id="chevron-cc">▾</span>
    </div>
    <div class="s-body" id="sec-cc">
      <div id="cc-overview"><div class="empty-cc">Yükleniyor…</div></div>
    </div>
  </div>

  <!-- ── FİNANSAL DURUM ── -->
  <div class="dash-section">
    <div class="s-header" onclick="toggleSection('health')">
      <div class="sh-left"><span class="sh-dot cy"></span>Finansal Durum</div>
      <div id="health-badge" class="health-badge" style="color:var(--txt2);border-color:var(--border2);font-size:.7rem;padding:3px 10px">—</div>
      <span class="sh-chevron" id="chevron-health">▾</span>
    </div>
    <div class="s-body" id="sec-health">
      <div class="motiv-bar-bg"><div id="motiv-fill" class="motiv-bar-fill" style="width:0%"></div></div>
      <div id="motiv-msgs" class="motiv-msgs"><div style="color:var(--txt2);font-size:.83rem">Yükleniyor…</div></div>
    </div>
  </div>

  <!-- hidden canvases needed by JS (not rendered) -->
  <div style="display:none">
    <canvas id="barChart"></canvas>
    <canvas id="donut"></canvas>
    <div id="sec-analytics"></div>
    <div id="db-sub"></div>
    <div id="mlabel"></div><div id="ylabel"></div>
    <div id="month-nav"></div><div id="year-nav"></div>
    <div id="date-range-picker"></div>
    <input id="range-start"><input id="range-end">
    <button id="view-month-btn"></button><button id="view-year-btn"></button>
    <div id="chevron-analytics"></div>
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
    <select class="filter-sel" id="f-year" onchange="onYearFilterChange()"></select>
    <button class="btn btn-ghost" onclick="exportCsv()">⬇ CSV</button>
  </div>
  <div class="ledger-toolbar" style="margin-top:-6px;margin-bottom:10px">
    <span style="font-size:.78rem;color:var(--txt2);white-space:nowrap">Tarih aralığı:</span>
    <input type="date" class="filter-sel" id="f-date-from" onchange="filterLedger()" style="font-size:.8rem;padding:6px 8px">
    <span style="font-size:.78rem;color:var(--txt2)">—</span>
    <input type="date" class="filter-sel" id="f-date-to" onchange="filterLedger()" style="font-size:.8rem;padding:6px 8px">
    <button class="btn btn-ghost" onclick="clearDateRange()" style="font-size:.78rem;padding:6px 10px">✕ Temizle</button>
  </div>

  <div id="monthly-summary" style="display:none;overflow-x:auto;margin-bottom:12px">
    <div id="monthly-summary-inner" style="display:flex;gap:8px;min-width:max-content;padding-bottom:4px"></div>
  </div>

  <div class="ledger-wrap">
    <table id="ledger-table">
      <thead>
        <tr>
          <th style="width:36px"><input type="checkbox" id="chk-all" onchange="toggleAllChk(this.checked)"></th>
          <th class="sortable" onclick="sortBy('date')">Tarih <span class="sort-ico" id="sort-date">↕</span></th>
          <th class="sortable" onclick="sortBy('type')">Tür <span class="sort-ico" id="sort-type">↕</span></th>
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
  <div id="ledger-summary" style="display:none;margin-top:8px;padding:12px 16px;background:var(--bg2);border-radius:14px;display:flex;gap:20px;flex-wrap:wrap;font-size:.83rem;border:1px solid var(--border,#e5e5ea)"></div>
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
  <div class="page-title">Tasarruf & Yatırım</div>
  <div class="page-sub">Aylık yatırım hedefleri koy, Kirpi sana ne kadar ayırman gerektiğini söylesin</div>

  <!-- Tasarruf kapasitesi -->
  <div class="card goals-capacity-card" id="goals-capacity" style="margin-bottom:16px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
      <div class="section-title" style="margin:0">Aylık Tasarruf Kapasitesi</div>
      <span class="badge" id="goals-save-badge" style="font-size:.7rem;padding:3px 10px">Hesaplanıyor…</span>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px">
      <div class="goals-stat-cell">
        <div class="gsc-lbl">Ort. Gelir</div>
        <div class="gsc-val gn" id="gs-gelir">—</div>
      </div>
      <div class="goals-stat-cell">
        <div class="gsc-lbl">Ort. Gider</div>
        <div class="gsc-val rd" id="gs-gider">—</div>
      </div>
      <div class="goals-stat-cell">
        <div class="gsc-lbl">Kalan</div>
        <div class="gsc-val" id="gs-net" style="color:var(--b2)">—</div>
      </div>
    </div>
    <div class="prog-bg" style="height:7px;margin-bottom:6px">
      <div class="prog-fill" id="goals-alloc-fill" style="width:0%;background:var(--b2);transition:width .8s cubic-bezier(.4,0,.2,1)"></div>
    </div>
    <div style="font-size:.72rem;color:var(--txt2)" id="goals-alloc-lbl">Hedeflere ayrılan: —</div>
  </div>

  <!-- Hedef ekle + liste -->
  <div class="grid2" style="margin-bottom:16px">
    <div class="card">
      <div class="section-title">Yeni Hedef Ekle</div>
      <label>Hedef Adı</label>
      <input class="f-input" id="g-name" placeholder="Euro Birikimi" style="margin-bottom:10px">
      <label>Yatırım Türü</label>
      <select class="f-input" id="g-type" style="margin-bottom:10px">
        <option value="eur">💶 Euro (EUR)</option>
        <option value="usd">💵 Dolar (USD)</option>
        <option value="gbp">💷 Sterlin (GBP)</option>
        <option value="gold">🥇 Altın</option>
        <option value="bitcoin">₿ Bitcoin</option>
        <option value="arsa">🏠 Arsa / Gayrimenkul</option>
        <option value="emeklilik">📦 Emeklilik Fonu</option>
        <option value="diger">💎 Diğer Yatırım</option>
      </select>
      <label>Aylık Hedef Tutar (₺)</label>
      <input class="f-input" type="text" inputmode="decimal" data-num id="g-monthly" placeholder="5.000" style="margin-bottom:10px">
      <label>Not <span style="color:var(--txt2);font-size:.7rem">(isteğe bağlı)</span></label>
      <input class="f-input" id="g-note" placeholder="3 yılda 10.000€ hedefi" style="margin-bottom:14px">
      <button class="btn btn-primary" style="width:100%" onclick="addGoal()">Hedef Ekle</button>
    </div>
    <div class="card">
      <div class="section-title">Hedeflerim</div>
      <div id="goals-list"><div class="empty-state"><div class="icon">🎯</div>Henüz hedef eklenmedi</div></div>
    </div>
  </div>

  <!-- Kirpi Yorumu -->
  <div class="card" id="goals-commentary-card">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">
      <div style="font-size:1.6rem">🦔</div>
      <div>
        <div style="font-weight:700;font-size:.9rem;color:var(--txt)">Kirpi'nin Yorumu</div>
        <div style="font-size:.72rem;color:var(--txt2)">Son 3 aylık verine göre kişisel analiz</div>
      </div>
      <button onclick="loadGoalsAnalysis()" style="margin-left:auto;padding:5px 12px;background:var(--bg3);border:1px solid var(--border2);border-radius:8px;color:var(--txt2);font-size:.75rem;cursor:pointer" title="Yenile">↻ Yenile</button>
    </div>
    <div id="goals-comments"><div class="empty-state" style="padding:24px"><div class="icon">🦔</div>Analiz yükleniyor…</div></div>
  </div>
</div>

<!-- SETTINGS -->
<div class="page" id="page-settings">
  <div class="page-title">Ayarlar</div>
  <div class="page-sub">Hesap bilgileri ve uygulama tercihleri</div>

  <!-- Avatar + Account -->
  <div class="settings-card">
    <div class="settings-sect-title">Profil</div>
    <div class="avatar-upload-wrap">
      <div class="avatar-lg" id="settings-avatar-img">?</div>
      <div>
        <div id="settings-display-name-show" style="font-size:.95rem;font-weight:700;color:var(--txt);margin-bottom:2px">—</div>
        <div id="settings-username-show" style="font-size:.78rem;color:var(--txt2);margin-bottom:10px">—</div>
        <button class="avatar-upload-btn" onclick="document.getElementById('avatar-file-input').click()">📷 Fotoğraf Değiştir</button>
        <input type="file" id="avatar-file-input" accept="image/*" style="display:none" onchange="handleAvatarUpload(this)">
      </div>
    </div>
    <label style="margin-top:12px">Ad Soyad / Ünvan</label>
    <input type="text" class="f-input" id="settings-display" placeholder="Ad Soyad" style="margin-bottom:10px">
    <label>Kullanıcı Adı <span style="color:var(--txt2);font-size:.72rem">(değiştirilemez)</span></label>
    <input type="text" class="f-input" id="settings-username" disabled style="margin-bottom:10px;opacity:.5">
    <label>E-posta <span style="color:var(--txt2);font-size:.72rem">(değiştirilemez)</span></label>
    <input type="email" class="f-input" id="settings-email" disabled style="margin-bottom:14px;opacity:.5">
    <button class="btn btn-primary" onclick="saveAccountInfo()" style="width:100%">Bilgileri Kaydet</button>
  </div>

  <!-- Change Password -->
  <div class="settings-card">
    <div class="settings-sect-title">Şifre Değiştir</div>
    <label>Mevcut Şifre</label>
    <input type="password" class="f-input" id="pw-current" placeholder="••••••" style="margin-bottom:10px">
    <label>Yeni Şifre</label>
    <input type="password" class="f-input" id="pw-new" placeholder="En az 6 karakter" style="margin-bottom:10px">
    <label>Yeni Şifre Tekrar</label>
    <input type="password" class="f-input" id="pw-confirm" placeholder="••••••" style="margin-bottom:14px">
    <div id="pw-msg" style="font-size:.82rem;margin-bottom:10px;min-height:18px"></div>
    <button class="btn btn-primary" onclick="changePassword()" style="width:100%">Şifreyi Güncelle</button>
  </div>

  <!-- Profil Yönetimi -->
  <div class="settings-card">
    <div class="settings-sect-title">Profil Yönetimi</div>
    <div id="settings-profile-list" style="margin-bottom:12px"></div>
    <div id="add-profile-form-settings" style="display:none;background:var(--bg3);border:1px solid var(--border2);border-radius:10px;padding:12px;margin-bottom:12px">
      <select id="new-profile-type-s" class="f-input" style="margin-bottom:8px">
        <option value="sahis">👤 Şahıs (Kişisel)</option>
        <option value="sirket">🏢 Şirket (Kurumsal)</option>
      </select>
      <input id="new-profile-name-s" class="f-input" placeholder="İsim ya da Ünvan" style="margin-bottom:8px">
      <div style="display:flex;gap:8px">
        <button class="btn btn-primary" style="flex:1" onclick="createProfileFromSettings()">Oluştur</button>
        <button class="btn btn-ghost" onclick="document.getElementById('add-profile-form-settings').style.display='none'">İptal</button>
      </div>
    </div>
    <button class="btn btn-ghost" style="width:100%" onclick="document.getElementById('add-profile-form-settings').style.display='block'">+ Yeni Profil Ekle</button>
  </div>

  <!-- Ses -->
  <div class="settings-card">
    <div style="display:flex;align-items:center;justify-content:space-between">
      <div style="font-size:.88rem;font-weight:600;color:var(--txt)">🔔 Ses</div>
      <label style="display:flex;align-items:center;gap:8px;cursor:pointer">
        <span id="sound-lbl" style="font-size:.8rem;color:var(--txt2)">Kapalı</span>
        <div id="sound-toggle" onclick="toggleSound(!_soundEnabled)" style="width:44px;height:26px;border-radius:13px;background:#c7c7cc;cursor:pointer;position:relative;transition:background .2s">
          <div id="sound-knob" style="width:22px;height:22px;border-radius:50%;background:#fff;position:absolute;top:2px;left:2px;transition:left .2s;box-shadow:0 1px 4px rgba(0,0,0,.25)"></div>
        </div>
      </label>
    </div>
  </div>

  <!-- Para Birimi -->
  <div class="settings-card">
    <div class="settings-sect-title">Para Birimi</div>
    <div style="font-size:.82rem;color:var(--txt2);margin-bottom:12px">Seçilen birim: <strong id="cur-label">TRY ₺</strong></div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">
      <button class="btn btn-ghost" onclick="setCurrency('TRY')" style="font-size:.85rem">₺ TRY</button>
      <button class="btn btn-ghost" onclick="setCurrency('USD')" style="font-size:.85rem">$ USD</button>
      <button class="btn btn-ghost" onclick="setCurrency('EUR')" style="font-size:.85rem">€ EUR</button>
      <button class="btn btn-ghost" onclick="setCurrency('GBP')" style="font-size:.85rem">£ GBP</button>
      <button class="btn btn-ghost" onclick="setCurrency('JPY')" style="font-size:.85rem">¥ JPY</button>
    </div>
  </div>

  <!-- App Info -->
  <div class="settings-card">
    <div class="settings-sect-title">Uygulama</div>
    <button class="settings-link-row" onclick="triggerInstall()">
      <span>⬇️ Uygulamayı Telefona Kur</span><span style="color:var(--txt2);font-size:.8rem">›</span>
    </button>
    <a class="settings-link-row" href="/kvkk" target="_blank">
      <span>📋 KVKK Aydınlatma Metni</span><span style="color:var(--txt2);font-size:.8rem">›</span>
    </a>
    <a class="settings-link-row" href="/gizlilik" target="_blank">
      <span>🔒 Gizlilik Politikası</span><span style="color:var(--txt2);font-size:.8rem">›</span>
    </a>
    <a class="settings-link-row" href="/kullanim-kosullari" target="_blank">
      <span>📄 Kullanım Koşulları</span><span style="color:var(--txt2);font-size:.8rem">›</span>
    </a>
    <div style="font-size:.72rem;color:var(--txt2);margin-top:12px;text-align:center">Kirpi v1.0 • 🦔</div>
  </div>
</div>

<!-- ── GÖREVLER (TODOS) ──────────────────────────────────────── -->
<div class="page" id="page-todos">
  <div class="page-title">Görevler</div>
  <div class="page-sub">Bugünün yapılacakları</div>

  <div class="todo-date-nav">
    <button class="todo-nav-btn tappable" onclick="todoChangeDate(-1)">‹</button>
    <div class="todo-date-lbl" id="todo-date-lbl">—</div>
    <button class="todo-nav-btn tappable" onclick="todoChangeDate(1)">›</button>
  </div>

  <div class="todo-add-row">
    <input class="todo-add-input" id="todo-input" placeholder="Yeni görev ekle…" onkeydown="if(event.key==='Enter')addTodo()">
    <button class="todo-add-btn tappable" onclick="addTodo()">＋</button>
  </div>

  <div class="todo-list" id="todo-active-list"></div>

  <div class="todo-archive-section" id="todo-archive-section" style="display:none">
    <div class="todo-archive-hdr">📦 Arşiv — Tamamlananlar <span id="todo-archive-count" style="background:var(--bg3);color:var(--txt2);padding:2px 8px;border-radius:8px;font-size:.68rem"></span></div>
    <div class="todo-list" id="todo-archive-list"></div>
  </div>
</div>

<!-- ── TEDARİKÇİ & ÖDEME YAŞLANDIRma ───────────────────────── -->
<div class="page" id="page-supplier">
  <div class="page-title">Tedarikçi & Ödemeler</div>
  <div class="page-sub">Fatura takibi, yaşlandırma ve vadeden kazanım</div>

  <div class="float-gain-banner" id="sup-float-banner">
    <div class="fgb-icon">💹</div>
    <div class="fgb-info">
      <div class="fgb-label">Vadeden Toplam Kazanım</div>
      <div class="fgb-value" id="sup-float-value">₺0</div>
    </div>
    <button onclick="exportExcel()" style="background:rgba(255,255,255,.25);border:1.5px solid rgba(255,255,255,.4);border-radius:10px;color:#fff;padding:8px 14px;font-size:.8rem;font-weight:700;cursor:pointer" class="tappable">📥 Excel</button>
  </div>

  <div class="aging-grid">
    <div class="aging-card green tappable"><div class="ac-lbl">0–30 Gün</div><div class="ac-val" id="ag-0-30">₺0</div><div class="ac-cnt" id="ag-0-30-cnt">0 fatura</div></div>
    <div class="aging-card yellow tappable"><div class="ac-lbl">31–60 Gün</div><div class="ac-val" id="ag-31-60">₺0</div><div class="ac-cnt" id="ag-31-60-cnt">0 fatura</div></div>
    <div class="aging-card orange tappable"><div class="ac-lbl">61–90 Gün</div><div class="ac-val" id="ag-61-90">₺0</div><div class="ac-cnt" id="ag-61-90-cnt">0 fatura</div></div>
    <div class="aging-card red tappable"><div class="ac-lbl">90+ Gün</div><div class="ac-val" id="ag-90plus">₺0</div><div class="ac-cnt" id="ag-90plus-cnt">0 fatura</div></div>
  </div>

  <div style="display:flex;gap:8px;margin-bottom:14px">
    <button class="btn tappable" id="sup-tab-pending" onclick="setSupTab('pending')" style="flex:1;background:var(--b);color:#fff;border:none">Bekleyenler</button>
    <button class="btn btn-ghost tappable" id="sup-tab-paid" onclick="setSupTab('paid')" style="flex:1">Ödenmiş</button>
    <button class="btn btn-ghost tappable" onclick="openSupInvModal()" style="flex:0 0 auto;padding:0 16px">＋</button>
  </div>

  <div id="sup-inv-list"></div>
</div>

<!-- ── KIYMETLER (ASSETS) ────────────────────────────────────── -->
<div class="page" id="page-assets">
  <div class="page-title">Varlıklar & Amortisman</div>
  <div class="page-sub">Araçlar, makineler, bilgisayarlar ve diğer sabit kıymetler</div>

  <div style="display:flex;gap:8px;margin-bottom:16px">
    <button class="btn btn-primary tappable" style="flex:1" onclick="openAssetModal()">＋ Varlık Ekle</button>
    <button class="btn btn-ghost tappable" onclick="exportExcel()" style="padding:0 16px">📥 Excel</button>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px">
    <div style="background:linear-gradient(135deg,#eef3ff,#e6ecff);border:1px solid #007aff20;border-radius:14px;padding:14px">
      <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#004dcc;margin-bottom:5px">Toplam Defter Değeri</div>
      <div style="font-size:1.1rem;font-weight:900;color:var(--b)" id="asset-total-book">₺0</div>
    </div>
    <div style="background:linear-gradient(135deg,#fff7ed,#fff0e0);border:1px solid #ff950020;border-radius:14px;padding:14px">
      <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#994700;margin-bottom:5px">Yıllık Amortisman</div>
      <div style="font-size:1.1rem;font-weight:900;color:var(--y)" id="asset-total-dep">₺0</div>
    </div>
  </div>

  <div id="asset-list"></div>
</div>

<!-- ── KART GÜNLÜK RAPORU ─────────────────────────────────────── -->
<div class="page" id="page-cardreport">
  <div class="page-title">Günlük Kart Raporu</div>
  <div class="page-sub">Dünkü ve bugünkü bakiyeyi karşılaştır</div>

  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
    <div style="font-size:.82rem;color:var(--txt2);font-weight:600" id="cdr-report-date">—</div>
    <button class="btn btn-ghost tappable" onclick="loadCardReport()" style="padding:6px 14px;font-size:.82rem">↻ Yenile</button>
  </div>

  <div id="card-daily-report-list"></div>

  <div style="background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:16px;margin-top:8px">
    <div style="font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--txt2);margin-bottom:10px">ℹ️ Nasıl kullanılır?</div>
    <div style="font-size:.82rem;color:var(--txt2);line-height:1.7">Her gün kartınızın mevcut bakiyesini girin. Sistem otomatik olarak bir önceki günle karşılaştırarak günlük harcamayı hesaplar.</div>
  </div>
</div>

<!-- ── MODALS ──────────────────────────────────────────────────── -->
<div id="mod-sup-inv" class="mod-backdrop" style="display:none" onclick="if(event.target===this)closeMod('mod-sup-inv')">
  <div class="mod-sheet">
    <div class="mod-handle"></div>
    <div class="mod-title" id="mod-sup-inv-title">Tedarikçi Faturası</div>
    <div class="mod-field">
      <div class="mod-label">Tedarikçi Adı / Ticari Ünvan</div>
      <input class="mod-input" id="sup-inv-name" placeholder="ABC Ticaret Ltd. Şti.">
    </div>
    <div class="mod-row">
      <div class="mod-field">
        <div class="mod-label">Fatura No</div>
        <input class="mod-input" id="sup-inv-no" placeholder="FTR-2024-001">
      </div>
      <div class="mod-field">
        <div class="mod-label">Tutar (₺)</div>
        <input class="mod-input" type="text" inputmode="decimal" data-num id="sup-inv-amount" placeholder="1.234,56">
      </div>
    </div>
    <div class="mod-row">
      <div class="mod-field">
        <div class="mod-label">Fatura Tarihi</div>
        <input class="mod-input" type="date" id="sup-inv-date">
      </div>
      <div class="mod-field">
        <div class="mod-label">Vade Tarihi</div>
        <input class="mod-input" type="date" id="sup-inv-due">
      </div>
    </div>
    <div class="mod-field">
      <div class="mod-label">Referans Faiz Oranı (%)</div>
      <input class="mod-input" type="text" inputmode="decimal" data-num id="sup-inv-rate" value="50" placeholder="50">
    </div>
    <div class="mod-field">
      <div class="mod-label">Notlar</div>
      <input class="mod-input" id="sup-inv-notes" placeholder="İsteğe bağlı">
    </div>
    <div class="mod-actions">
      <button class="mod-btn cancel" onclick="closeMod('mod-sup-inv')">İptal</button>
      <button class="mod-btn primary" id="sup-inv-save-btn" onclick="saveSupInv()">Kaydet</button>
    </div>
  </div>
</div>

<div id="mod-asset" class="mod-backdrop" style="display:none" onclick="if(event.target===this)closeMod('mod-asset')">
  <div class="mod-sheet">
    <div class="mod-handle"></div>
    <div class="mod-title">Varlık Ekle</div>
    <div class="mod-field">
      <div class="mod-label">Varlık Adı</div>
      <input class="mod-input" id="asset-name" placeholder="Ford Transit 2021">
    </div>
    <div class="mod-row">
      <div class="mod-field">
        <div class="mod-label">Tür</div>
        <select class="mod-input" id="asset-type" onchange="onAssetTypeChange()">
          <option value="arac">🚗 Araç</option>
          <option value="bilgisayar">💻 Bilgisayar</option>
          <option value="makine">⚙️ Makine</option>
          <option value="mobilya">🪑 Mobilya</option>
          <option value="bina">🏢 Bina</option>
          <option value="diger">📦 Diğer</option>
        </select>
      </div>
      <div class="mod-field">
        <div class="mod-label">Plaka / Seri No</div>
        <input class="mod-input" id="asset-plate" placeholder="34 ABC 123">
      </div>
    </div>
    <div class="mod-row">
      <div class="mod-field">
        <div class="mod-label">Alış Tarihi</div>
        <input class="mod-input" type="date" id="asset-purchase-date">
      </div>
      <div class="mod-field">
        <div class="mod-label">Alış Bedeli (₺)</div>
        <input class="mod-input" type="text" inputmode="decimal" data-num id="asset-price" placeholder="1.234,56">
      </div>
    </div>
    <div class="mod-row">
      <div class="mod-field">
        <div class="mod-label">Amortisman Oranı %</div>
        <input class="mod-input" type="text" inputmode="decimal" id="asset-dep-rate" placeholder="20">
      </div>
      <div class="mod-field">
        <div class="mod-label">Sonraki Bakım</div>
        <input class="mod-input" type="date" id="asset-maint-date">
      </div>
    </div>
    <div class="mod-row">
      <div class="mod-field">
        <div class="mod-label">Sigorta Bitiş</div>
        <input class="mod-input" type="date" id="asset-ins-date">
      </div>
      <div class="mod-field">
        <div class="mod-label">Sigorta Şirketi</div>
        <input class="mod-input" id="asset-ins-co" placeholder="Allianz">
      </div>
    </div>
    <div class="mod-actions">
      <button class="mod-btn cancel" onclick="closeMod('mod-asset')">İptal</button>
      <button class="mod-btn primary" onclick="saveAsset()">Kaydet</button>
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
var _todayDate=new Date().toISOString().split('T')[0];

// ── INIT ─────────────────────────────────────────────────────────────────────
window.onload=function(){
  var todayISO=new Date().toISOString().split('T')[0];
  document.getElementById('f-date').value=todayISO;
  var dpick=document.getElementById('today-date-pick');
  if(dpick) dpick.value=todayISO;
  _todayDate=todayISO;
  updateMonthLabel();
  var h=new Date().getHours();
  var prefix=h<5?'İyi geceler':h<12?'Günaydın':h<18?'İyi günler':'İyi akşamlar';
  var gEl=document.getElementById('hero-greeting');
  if(gEl) gEl.textContent=gEl.textContent.replace('Merhaba',prefix);
  loadCats();
  loadAllTx();
  populateYearFilter();
  loadDashboard();
  setupDrop();
  loadProfiles();
  setupNumInputs();
  loadNotifications();
  requestBrowserNotifPermission();
  // Buton/kart tıklamalarında ses
  document.addEventListener('click',function(e){
    var t=e.target.closest('button,.btn,.tappable,.tx-day-item,.hero-chip,.aging-card,.asset-card,.todo-item,.sup-inv-item,.settings-link-row');
    if(t) playClick();
  },true);
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
    playClick();
    if(id==='ledger') renderLedger();
    if(id==='dashboard') loadDashboard();
    if(id==='recurring') initRecurringPage();
    if(id==='invest') initInvestPage();
    if(id==='cards') loadCards();
    if(id==='settings') initSettingsPage();
    if(id==='budget') loadGoalsPage();
    if(id==='todos') initTodosPage();
    if(id==='supplier') initSupplierPage();
    if(id==='assets') initAssetsPage();
    if(id==='cardreport') loadCardReport();
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

// ── MORE SHEET ───────────────────────────────────────────────────────────────
function openMoreSheet(){
  var bd=document.getElementById('more-backdrop');
  var sh=document.getElementById('more-sheet');
  if(!sh) return;
  bd.classList.add('open');
  sh.classList.add('open');
  document.body.style.overflow='hidden';
}
function closeMoreSheet(){
  var bd=document.getElementById('more-backdrop');
  var sh=document.getElementById('more-sheet');
  if(!sh) return;
  bd.classList.remove('open');
  sh.classList.remove('open');
  document.body.style.overflow='';
}
function goPageFromSheet(id){
  closeMoreSheet();
  var el=document.querySelector('[data-page='+id+']');
  setTimeout(function(){ goPage(id, el); }, 200);
}

// ── PROFILE SWITCHER ─────────────────────────────────────────────────────────
var _profiles=[];
var _curAvatar = '';

var _curProfileType = 'sahis';

function applyProfileType(ptype){
  _curProfileType = ptype || 'sahis';
  var isSirket = _curProfileType === 'sirket';
  document.querySelectorAll('[data-sirket]').forEach(function(el){
    el.style.display = isSirket ? '' : 'none';
  });
  // If currently on a sirket-only page, redirect to dashboard
  if(!isSirket){
    var cur = document.querySelector('.page.active');
    if(cur && ['page-supplier','page-assets','page-cardreport'].indexOf(cur.id) !== -1){
      goPage('dashboard', document.querySelector('[data-page=dashboard]'));
    }
  }
}

function loadProfiles(){
  xhr('/api/me',null,function(me){
    _curAvatar = me.avatar || '';
    if(me.profile_id) sessionStorage.setItem('cur_pid', me.profile_id);
    setAvatarDisplay(me.avatar, me.display || me.username || '?');
    var n=document.getElementById('udrop-name');
    var s=document.getElementById('udrop-sub');
    if(n) n.textContent=me.display||me.username||'—';
    if(s) s.textContent='@'+me.username+(me.email?' · '+me.email:'');
    applyProfileType(me.profile_type);
  });
  xhr('/api/profiles',null,function(list){
    _profiles=list;
    renderDropdownProfiles();
    renderSettingsProfiles();
    var preferred=parseInt(localStorage.getItem('preferred_pid')||'0');
    var curPid=parseInt(sessionStorage.getItem('cur_pid')||'0');
    if(preferred && preferred!==curPid){
      var match=list.find(function(p){return p.id===preferred;});
      if(match) switchProfile(preferred);
    }
  });
}

function setAvatarDisplay(avatar, name){
  var initials = (name||'?').slice(0,1).toUpperCase();
  var btn = document.getElementById('avatar-btn-inner');
  var avaDrop = document.getElementById('udrop-ava');
  var avaSet = document.getElementById('settings-avatar-img');
  function setAva(el){
    if(!el) return;
    if(avatar){
      el.innerHTML='<img src="'+avatar+'" style="width:100%;height:100%;object-fit:cover;border-radius:50%">';
    } else {
      el.textContent = initials;
    }
  }
  if(btn){ if(avatar){btn.innerHTML='<img src="'+avatar+'" style="width:100%;height:100%;object-fit:cover;border-radius:50%">';} else {btn.textContent=initials;} }
  setAva(avaDrop); setAva(avaSet);
}

function toggleUserMenu(e){
  if(e) e.stopPropagation();
  var d=document.getElementById('user-dropdown');
  d.classList.toggle('open');
}

document.addEventListener('click',function(e){
  var wrap=document.querySelector('.udrop-wrap');
  if(wrap&&!wrap.contains(e.target)){
    var d=document.getElementById('user-dropdown');
    if(d) d.classList.remove('open');
  }
});

function renderDropdownProfiles(){
  var pid=parseInt(sessionStorage.getItem('cur_pid')||'0');
  var el=document.getElementById('udrop-profiles');
  if(!el) return;
  el.innerHTML=_profiles.map(function(p){
    var icon=p.type==='sirket'?'🏢':'👤';
    var cur=(p.id===pid)?'cur':'';
    return '<div class="udrop-prof-item '+cur+'" onclick="switchProfile('+p.id+')">'
      +'<span class="udrop-prof-dot" style="background:'+(p.type==='sirket'?'var(--c)':'var(--b2)')+'"></span>'
      +icon+' '+p.name
      +(cur?' <span style="margin-left:auto;font-size:.65rem;color:var(--b2)">Aktif</span>':'')
      +'</div>';
  }).join('');
}

function renderSettingsProfiles(){
  var el=document.getElementById('settings-profile-list');
  if(!el) return;
  var pid=parseInt(sessionStorage.getItem('cur_pid')||'0');
  el.innerHTML=_profiles.map(function(p){
    var icon=p.type==='sirket'?'🏢':'👤';
    var isActive=p.id===pid;
    return '<div class="settings-profile-item">'
      +'<div><div class="sp-info">'+icon+' '+p.name+'</div>'
      +'<div class="sp-type">'+(p.type==='sirket'?'Şirket':'Kişisel')+'</div></div>'
      +(isActive?'<span class="sp-active">Aktif</span>':'<button onclick="switchProfile('+p.id+')" style="padding:5px 12px;background:var(--b);border:none;border-radius:8px;color:#fff;font-size:.75rem;cursor:pointer;font-weight:600">Geç</button>')
      +'</div>';
  }).join('');
}

function switchProfile(pid){
  xhr('/api/profiles/'+pid+'/switch','POST',function(d){
    if(!d.ok) return;
    document.getElementById('user-dropdown').classList.remove('open');
    sessionStorage.setItem('cur_pid', pid);
    localStorage.setItem('preferred_pid', pid);
    renderDropdownProfiles();
    renderSettingsProfiles();
    showToast('Profil: '+d.name,'#6366f1');
    applyProfileType(d.type);
    loadDashboard(); renderLedger();
  });
}

function showAddProfile(){ showAddProfile2(); }
function showAddProfile2(){
  var f=document.getElementById('add-profile-form2');
  if(f) f.style.display=f.style.display==='none'?'block':'none';
}
function cancelAddProfile(){
  var f=document.getElementById('add-profile-form2');
  if(f) f.style.display='none';
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
    cancelAddProfile();
    showToast('Profil oluşturuldu: '+d.name,'#22c55e');
  });
}
function createProfileFromSettings(){
  var name=document.getElementById('new-profile-name-s').value.trim();
  var type=document.getElementById('new-profile-type-s').value;
  if(!name){ showToast('İsim / Ünvan zorunlu','#ef4444'); return; }
  xhr('/api/profiles',{name:name,type:type},function(d){
    if(!d.ok){ showToast('Hata','#ef4444'); return; }
    _profiles.push(d);
    renderSettingsProfiles();
    document.getElementById('add-profile-form-settings').style.display='none';
    document.getElementById('new-profile-name-s').value='';
    showToast('Profil oluşturuldu: '+d.name,'#22c55e');
  });
}

// ── NOTIFICATIONS ────────────────────────────────────────────────────────────
var _notifItems=[];

function loadNotifications(){
  xhr('/api/notifications',null,function(d){
    if(!d.ok) return;
    _notifItems=d.items||[];
    updateNotifBadge();
    renderNotifList();
    sendUrgentBrowserNotifs();
  });
}

function updateNotifBadge(){
  var badge=document.getElementById('notif-badge');
  if(!badge) return;
  var urgent=_notifItems.filter(function(x){return x.urgency==='urgent';}).length;
  var total=_notifItems.length;
  if(total===0){ badge.classList.add('hidden'); }
  else {
    badge.classList.remove('hidden');
    badge.textContent=total>9?'9+':total;
    badge.style.background=urgent>0?'#ef4444':'#f59e0b';
  }
}

function renderNotifList(){
  var el=document.getElementById('notif-list');
  if(!el) return;
  if(_notifItems.length===0){
    el.innerHTML='<div class="notif-empty"><div class="notif-empty-ico">✅</div>Harika! Yaklaşan bildirim yok.</div>';
    return;
  }
  var sections={urgent:[],soon:[],normal:[]};
  _notifItems.forEach(function(item){sections[item.urgency].push(item);});
  var html='';
  if(sections.urgent.length){
    html+='<div class="notif-section-lbl">⚠️ Acil</div>';
    html+=sections.urgent.map(renderNotifItem).join('');
  }
  if(sections.soon.length){
    html+='<div class="notif-section-lbl">🕐 Yakında</div>';
    html+=sections.soon.map(renderNotifItem).join('');
  }
  if(sections.normal.length){
    html+='<div class="notif-section-lbl">📋 Planlanmış</div>';
    html+=sections.normal.map(renderNotifItem).join('');
  }
  el.innerHTML=html;
}

function renderNotifItem(item){
  var dayLabel='';
  if(item.days<=0) dayLabel='<span class="notif-item-days">Bugün</span>';
  else if(item.days===1) dayLabel='<span class="notif-item-days">Yarın</span>';
  else dayLabel='<span class="notif-item-days">'+item.days+' gün sonra</span>';
  return '<div class="notif-item '+item.urgency+'">'
    +'<div class="notif-item-ico">'+item.icon+'</div>'
    +'<div class="notif-item-body">'
      +'<div class="notif-item-title">'+item.title+'</div>'
      +'<div class="notif-item-msg">'+item.body+'</div>'
      +dayLabel
    +'</div>'
    +'</div>';
}

function toggleNotifPanel(){
  var panel=document.getElementById('notif-panel');
  var overlay=document.getElementById('notif-overlay');
  var isOpen=panel.classList.contains('open');
  if(isOpen){ closeNotifPanel(); }
  else {
    panel.classList.add('open');
    overlay.classList.add('open');
    loadNotifications();
  }
}

function closeNotifPanel(){
  document.getElementById('notif-panel').classList.remove('open');
  document.getElementById('notif-overlay').classList.remove('open');
}

function requestBrowserNotifPermission(){
  if(!('Notification' in window)) return;
  if(Notification.permission==='default'){
    setTimeout(function(){
      Notification.requestPermission();
    },3000);
  }
}

function sendUrgentBrowserNotifs(){
  if(!('Notification' in window)) return;
  if(Notification.permission!=='granted') return;
  var urgent=_notifItems.filter(function(x){return x.urgency==='urgent';});
  var sent=sessionStorage.getItem('notif_sent_'+new Date().toISOString().split('T')[0]);
  if(sent) return;
  if(urgent.length>0){
    sessionStorage.setItem('notif_sent_'+new Date().toISOString().split('T')[0],'1');
    urgent.slice(0,3).forEach(function(item,i){
      setTimeout(function(){
        try{
          new Notification('🦔 Kirpi — '+item.title,{
            body:item.body,
            icon:'/icon-192.png',
            tag:'kirpi-'+item.category+'-'+i,
            badge:'/icon-192.png'
          });
        }catch(e){}
      },i*800);
    });
  }
}

// ── SETTINGS PAGE ────────────────────────────────────────────────────────────
function initSettingsPage(){
  xhr('/api/me',null,function(me){
    var d=document.getElementById('settings-display');
    var u=document.getElementById('settings-username');
    var em=document.getElementById('settings-email');
    var dn=document.getElementById('settings-display-name-show');
    var un=document.getElementById('settings-username-show');
    if(d) d.value=me.display||'';
    if(u) u.value=me.username||'';
    if(em) em.value=me.email||'';
    if(dn) dn.textContent=me.display||me.username||'—';
    if(un) un.textContent='@'+(me.username||'');
    setAvatarDisplay(me.avatar, me.display||me.username||'?');
  });
  renderSettingsProfiles();
  var el=document.getElementById('cur-label');
  var c=_CURRENCIES[_curCode]||_CURRENCIES['TRY'];
  if(el) el.textContent=_curCode+' '+c.sym;
  _syncSoundToggleUI();
}

function saveAccountInfo(){
  var display=document.getElementById('settings-display').value.trim();
  if(!display){ showToast('Ad Soyad boş olamaz','#ef4444'); return; }
  xhr('/api/me/update',{display_name:display},function(d){
    if(d.ok){
      document.getElementById('settings-display-name-show').textContent=display;
      document.getElementById('udrop-name').textContent=display;
      showToast('Bilgiler kaydedildi ✓','#22c55e');
    }
  });
}

function changePassword(){
  var cur=document.getElementById('pw-current').value;
  var nw=document.getElementById('pw-new').value;
  var conf=document.getElementById('pw-confirm').value;
  var msg=document.getElementById('pw-msg');
  if(!cur||!nw||!conf){ msg.textContent='Tüm alanları doldurun'; msg.style.color='var(--r)'; return; }
  xhr('/api/me/password',{current:cur,new:nw,confirm:conf},function(d){
    if(d.ok){
      msg.textContent='Şifre güncellendi ✓'; msg.style.color='var(--g)';
      document.getElementById('pw-current').value='';
      document.getElementById('pw-new').value='';
      document.getElementById('pw-confirm').value='';
    } else {
      msg.textContent=d.error||'Hata'; msg.style.color='var(--r)';
    }
  });
}

function handleAvatarUpload(input){
  if(!input.files||!input.files[0]) return;
  var file=input.files[0];
  var reader=new FileReader();
  reader.onload=function(e){
    var img=new Image();
    img.onload=function(){
      var cv=document.createElement('canvas');
      cv.width=cv.height=128;
      var ctx=cv.getContext('2d');
      var s=Math.min(img.width,img.height);
      var sx=(img.width-s)/2, sy=(img.height-s)/2;
      ctx.drawImage(img,sx,sy,s,s,0,0,128,128);
      var dataUrl=cv.toDataURL('image/jpeg',.85);
      setAvatarDisplay(dataUrl,'');
      xhr('/api/me/update',{avatar:dataUrl},function(d){
        if(d.ok) showToast('Fotoğraf güncellendi ✓','#22c55e');
      });
    };
    img.src=e.target.result;
  };
  reader.readAsDataURL(file);
  input.value='';
}

// ── TODAY DATE PICKER ────────────────────────────────────────────────────────
var _todayDate = new Date().toISOString().split('T')[0];
function changeTodayDate(val){
  _todayDate = val || new Date().toISOString().split('T')[0];
  loadTodayWidgets();
  // Update section label
  var d = new Date(_todayDate+'T12:00:00');
  var today = new Date().toISOString().split('T')[0];
  var dateLabel = _todayDate===today?'Günün':d.toLocaleDateString('tr-TR',{day:'numeric',month:'long'});
  var g1=document.getElementById('gelir-section-lbl');
  var g2=document.getElementById('gider-section-lbl');
  if(g1) g1.textContent=dateLabel+' Gelirleri';
  if(g2) g2.textContent=dateLabel+' Giderleri';
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
  var s=document.getElementById(id); if(!s)return; s.innerHTML='';
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
    var action=t.is_invoice
      ? 'goPage(\'supplier\',document.querySelector(\'[data-page=supplier]\'))'
      : 'goToTx('+t.id+')';
    return '<div class="tx-day-item" onclick="'+action+'">'+
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
  xhr('/api/today?date='+_todayDate,null,function(d){
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

    // Hedgehog mood on hero card
    var kirpi=document.getElementById('hero-kirpi');
    if(kirpi){
      var prevMood=kirpi.dataset.mood||'';
      var newMood;
      if(d.gelir_list&&d.gelir_list.length>0){ newMood='happy'; }
      else if(d.recurring_gelir_today){ newMood='expected'; }
      else { newMood='sad'; }
      if(prevMood!==newMood){
        kirpi.dataset.mood=newMood;
        kirpi.textContent='🦔';
        kirpi.classList.remove('bounce');
        void kirpi.offsetWidth;
        kirpi.classList.add('bounce');
      }
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

var _heroPeriod='month';
var _heroYear=new Date().getFullYear();
var _dashReqId=0;

function setHeroPeriod(p){
  _heroPeriod=p;
  ['month','year','all'].forEach(function(id){
    var tab=document.getElementById('htab-'+id);
    if(tab) tab.classList.toggle('active',id===p);
  });
  var ynav=document.getElementById('hero-year-nav');
  if(ynav) ynav.style.display=p==='year'?'flex':'none';
  updateHeroLabel();
  loadDashboard();
}

function changeHeroYear(delta){
  _heroYear+=delta;
  var yv=document.getElementById('hero-year-val');
  if(yv) yv.textContent=_heroYear;
  updateHeroLabel();
  loadDashboard();
}

function updateHeroLabel(){
  var lbl=document.getElementById('hero-bal-lbl');
  if(!lbl) return;
  if(_heroPeriod==='month') lbl.textContent='BU AY NET';
  else if(_heroPeriod==='year') lbl.textContent=_heroYear+' YILI NET';
  else lbl.textContent='TÜM ZAMANLAR';
}

function loadDashboard(){
  var url;
  if(_dateRangeActive){
    url='/api/summary?start='+_rangeStart+'&end='+_rangeEnd;
  } else if(_heroPeriod==='year'){
    url='/api/summary?period=year&year='+_heroYear;
  } else {
    url='/api/summary?period='+_heroPeriod;
  }
  var reqId = ++_dashReqId;
  xhr(url,null,function(d){
    if(reqId !== _dashReqId) return; // discard stale response
    summaryData=d;
    renderStats(d);
    drawBar(d.bar);
    drawDonut(d.gider_cats);
    renderBudgetPage(d.gider_cats,d.budgets);
  });
  xhr('/api/motivation',null,renderMotivation);
  loadTodayWidgets();
}

// ── SES SİSTEMİ ──────────────────────────────────────────────────────────────
var _soundEnabled=(localStorage.getItem('kirpi_sound')==='1');
var _audioCtx=null;
function _getACtx(){
  if(!_audioCtx||_audioCtx.state==='closed')
    _audioCtx=new(window.AudioContext||window.webkitAudioContext)();
  if(_audioCtx.state==='suspended') _audioCtx.resume();
  return _audioCtx;
}
function playClick(){
  if(!_soundEnabled) return;
  try{
    var ctx=_getACtx(), t=ctx.currentTime;
    var master=ctx.createGain();
    master.gain.setValueAtTime(0.06,t);
    master.gain.exponentialRampToValueAtTime(0.001,t+0.07);
    master.connect(ctx.destination);
    var o1=ctx.createOscillator(); o1.type='sine';
    o1.frequency.setValueAtTime(820,t);
    o1.frequency.exponentialRampToValueAtTime(680,t+0.07);
    o1.connect(master); o1.start(t); o1.stop(t+0.07);
  }catch(e){}
}
function toggleSound(on){
  _soundEnabled=on;
  localStorage.setItem('kirpi_sound',on?'1':'0');
  _syncSoundToggleUI();
  if(on) setTimeout(playClick,80);
}
function _syncSoundToggleUI(){
  var lbl=document.getElementById('sound-lbl');
  var tog=document.getElementById('sound-toggle');
  var knob=document.getElementById('sound-knob');
  if(lbl) lbl.textContent=_soundEnabled?'Açık':'Kapalı';
  if(tog) tog.style.background=_soundEnabled?'var(--g)':'#c7c7cc';
  if(knob) knob.style.left=_soundEnabled?'20px':'2px';
}

var _CURRENCIES={
  'TRY':{sym:'₺',locale:'tr-TR',pos:'before'},
  'USD':{sym:'$',locale:'en-US',pos:'before'},
  'EUR':{sym:'€',locale:'de-DE',pos:'before'},
  'GBP':{sym:'£',locale:'en-GB',pos:'before'},
  'JPY':{sym:'¥',locale:'ja-JP',pos:'before'}
};
var _curCode=(localStorage.getItem('kirpi_currency')||'TRY');
var _curSym=(_CURRENCIES[_curCode]||_CURRENCIES['TRY']).sym;
var _curLocale=(_CURRENCIES[_curCode]||_CURRENCIES['TRY']).locale;
function setCurrency(code){
  _curCode=code;
  var c=_CURRENCIES[code]||_CURRENCIES['TRY'];
  _curSym=c.sym; _curLocale=c.locale;
  localStorage.setItem('kirpi_currency',code);
  var el=document.getElementById('cur-label');
  if(el) el.textContent=code+' '+c.sym;
  if(summaryData) { renderStats(summaryData); if(summaryData.bar) drawBar(summaryData.bar); if(summaryData.gider_cats) drawDonut(summaryData.gider_cats); }
}
function fmt(n){
  var s=Number(n).toLocaleString(_curLocale,{minimumFractionDigits:2,maximumFractionDigits:2});
  return _curSym+s;
}
function fmtK(n){if(n>=1e6)return(n/1e6).toFixed(1)+'M';if(n>=1e3)return(n/1e3).toFixed(0)+'K';return Math.round(n)+''}
function fmtNum(n){return Number(n).toLocaleString(_curLocale,{minimumFractionDigits:2,maximumFractionDigits:2})}

// ── HERO FILTER SHORTCUT ────────────────────────────────────────────────────
function _applyHeroPeriodToLedger(){
  var fd=document.getElementById('f-date-from');
  var fdt=document.getElementById('f-date-to');
  var fy=document.getElementById('f-year');
  if(!fd||!fdt) return;
  if(_heroPeriod==='month'){
    // Seçili ay'ın ilk ve son günü
    var d=new Date(curYear,curMonth-1,1);
    var last=new Date(curYear,curMonth,0).getDate();
    var mo=String(curMonth).padStart(2,'0');
    fd.value=curYear+'-'+mo+'-01';
    fdt.value=curYear+'-'+mo+'-'+String(last).padStart(2,'0');
    if(fy) fy.value='';
  } else if(_heroPeriod==='year'){
    fd.value=_heroYear+'-01-01';
    fdt.value=_heroYear+'-12-31';
    if(fy) fy.value='';
  } else {
    fd.value=''; fdt.value='';
    if(fy) fy.value='';
  }
}
function filterLedgerTo(type){
  var ledgerEl=document.querySelector('[data-page="ledger"]');
  goPage('ledger',ledgerEl);
  setTimeout(function(){
    _applyHeroPeriodToLedger();
    var sel=document.getElementById('f-type');
    var cat=document.getElementById('ledger-f-cat');
    var ls=document.getElementById('ledger-search');
    if(cat) cat.value='';
    if(ls) ls.value='';
    if(sel) sel.value=type;
    filterLedger();
  },200);
}
function filterLedgerToCat(type, cat){
  var ledgerEl=document.querySelector('[data-page="ledger"]');
  goPage('ledger',ledgerEl);
  setTimeout(function(){
    _applyHeroPeriodToLedger();
    var selType=document.getElementById('f-type');
    var selCat=document.getElementById('ledger-f-cat');
    var ls=document.getElementById('ledger-search');
    if(ls) ls.value='';
    if(selType) selType.value=type;
    if(selCat){
      if(!selCat.querySelector('option[value="'+cat+'"]')){
        var o=document.createElement('option'); o.value=cat; o.textContent=cat;
        selCat.appendChild(o);
      }
      selCat.value=cat;
    }
    filterLedger();
  },200);
}

// Tutar girişi: binlik nokta + kuruş virgülle (5.000,75)
function setupNumInputs(){
  document.querySelectorAll('input[data-num]').forEach(function(el){
    el.addEventListener('keydown',function(e){
      // allow: backspace/del/tab/esc/enter/arrows, ctrl combos, digits, comma
      if([8,9,13,27,35,36,37,38,39,40,46].indexOf(e.keyCode)!==-1) return;
      if(e.ctrlKey||e.metaKey) return;
      if((e.keyCode>=48&&e.keyCode<=57)||(e.keyCode>=96&&e.keyCode<=105)) return;
      if(e.keyCode===188||e.keyCode===110) return; // comma / decimal
      e.preventDefault();
    });
    el.addEventListener('input',function(){
      var val=el.value;
      var cursor=el.selectionStart;
      var prevLen=val.length;
      // Split on comma
      var commaIdx=val.indexOf(',');
      var intRaw, decRaw, hasComma;
      if(commaIdx!==-1){
        intRaw=val.substring(0,commaIdx).replace(/[^\d]/g,'');
        decRaw=val.substring(commaIdx+1).replace(/[^\d]/g,'').slice(0,2);
        hasComma=true;
      } else {
        intRaw=val.replace(/[^\d]/g,'');
        decRaw='';
        hasComma=false;
      }
      el.dataset.raw=intRaw+(decRaw?'.'+decRaw:'');
      var formatted=intRaw?intRaw.replace(/\B(?=(\d{3})+(?!\d))/g,'.'):'';
      var newVal=hasComma?formatted+','+decRaw:formatted;
      if(el.value!==newVal){
        el.value=newVal;
        var diff=newVal.length-prevLen;
        var newCursor=Math.max(0,cursor+diff);
        try{el.setSelectionRange(newCursor,newCursor);}catch(e){}
      }
    });
    el.addEventListener('blur',function(){
      var raw=parseFloat((el.dataset.raw||'').replace(',','.'));
      if(!isNaN(raw)&&raw>0){
        var parts=raw.toFixed(2).split('.');
        parts[0]=parts[0].replace(/\B(?=(\d{3})+(?!\d))/g,'.');
        el.value=parts[0]+','+parts[1];
        el.dataset.raw=raw;
      } else {
        el.dataset.raw='';
      }
    });
    el.addEventListener('focus',function(){
      var raw=parseFloat(el.dataset.raw||'');
      el.value=(!isNaN(raw)&&raw>0)?raw.toString().replace('.',','):'';
      setTimeout(function(){el.select();},10);
    });
  });
}
function getNumVal(el){
  var raw=el.dataset.raw||el.value.replace(/\./g,'').replace(',','.');
  return parseFloat(raw)||0;
}

function renderStats(d){
  var b=document.getElementById('s-bal');
  // For all-time show cumulative balance, for period show net
  var heroVal=(_heroPeriod==='all')?d.balance:d.net;
  b.textContent=fmt(heroVal);
  b.style.color=heroVal>=0?'#fff':'#ff7e78';
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
var _barCols=[], _barYear=new Date().getFullYear();
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
  _barCols=[]; _barYear=(_heroPeriod==='year')?_heroYear:curYear;
  ctx.strokeStyle='#d1d1d6'; ctx.lineWidth=1;
  [0,.25,.5,.75,1].forEach(function(f){
    var y=p.t+ch*(1-f);
    ctx.beginPath();ctx.moveTo(p.l,y);ctx.lineTo(W-p.r,y);ctx.stroke();
    ctx.fillStyle='#6d6d72';ctx.font='10px Inter,system-ui';ctx.textAlign='right';
    ctx.fillText(fmtK(maxVal*f),p.l-4,y+3);
  });
  data.forEach(function(d,i){
    var x=p.l+i*gap+gap/2;
    _barCols.push({month:i+1, x:x, halfGap:gap/2});
    var gh=ch*(d.gelir/maxVal), eh=ch*(d.gider/maxVal);
    if(d.gelir>0){ctx.fillStyle='#30d15870';ctx.beginPath();rr(ctx,x-bw-2,p.t+ch-gh,bw,gh,3);ctx.fill()}
    if(d.gider>0){ctx.fillStyle='#ff453a70';ctx.beginPath();rr(ctx,x+2,p.t+ch-eh,bw,eh,3);ctx.fill()}
    if(i+1===curMonth&&curYear===new Date().getFullYear()){
      ctx.strokeStyle='#6366f1';ctx.lineWidth=1.5;
      ctx.strokeRect(x-bw-4,p.t,bw*2+8,ch);
    }
    ctx.fillStyle='#475569';ctx.font='9px Inter,system-ui';ctx.textAlign='center';
    ctx.fillText(MONTHS[i+1].slice(0,3),x,H-6);
  });
  cv.style.cursor='pointer';
  cv.onclick=function(e){
    var rect=cv.getBoundingClientRect();
    var mx=(e.clientX-rect.left)*(cv.width/rect.width);
    for(var i=0;i<_barCols.length;i++){
      if(Math.abs(mx-_barCols[i].x)<=_barCols[i].halfGap){
        var mo=String(_barCols[i].month).padStart(2,'0');
        filterLedgerToMonth(_barYear+'-'+mo);
        playClick();
        return;
      }
    }
  };
}
function rr(ctx,x,y,w,h,r){
  if(h<=0)return;
  ctx.moveTo(x+r,y);ctx.lineTo(x+w-r,y);ctx.quadraticCurveTo(x+w,y,x+w,y+r);
  ctx.lineTo(x+w,y+h);ctx.lineTo(x,y+h);ctx.lineTo(x,y+r);ctx.quadraticCurveTo(x,y,x+r,y);ctx.closePath();
}

// ── DONUT ────────────────────────────────────────────────────────────────────
var _donutSlices=[], _donutCX=0, _donutCY=0, _donutR=0, _donutr=0;
function drawDonut(cats){
  var cv=document.getElementById('donut');
  var W=cv.parentElement.clientWidth||400, H=190;
  cv.width=W; cv.height=H;
  var ctx=cv.getContext('2d');
  ctx.clearRect(0,0,W,H);
  var keys=Object.keys(cats).filter(function(k){return cats[k]>0});
  _donutSlices=[];
  if(!keys.length){
    ctx.fillStyle='#475569';ctx.font='13px Inter,system-ui';ctx.textAlign='center';
    ctx.fillText('Bu dönem gider yok',W/2,H/2);return;
  }
  var total=keys.reduce(function(s,k){return s+cats[k]},0);
  var cx=H/2,cy=H/2,R=cy-14,r=cy*0.46,a=-Math.PI/2;
  _donutCX=cx; _donutCY=cy; _donutR=R; _donutr=r;
  keys.forEach(function(k,i){
    var sl=cats[k]/total*2*Math.PI;
    _donutSlices.push({cat:k,start:a,end:a+sl});
    ctx.beginPath();ctx.moveTo(cx,cy);ctx.arc(cx,cy,R,a,a+sl);ctx.closePath();
    ctx.fillStyle=CLRS[i%CLRS.length];ctx.fill();a+=sl;
  });
  ctx.beginPath();ctx.arc(cx,cy,r,0,2*Math.PI);ctx.fillStyle=getComputedStyle(document.documentElement).getPropertyValue('--bg2')||'#fff';ctx.fill();
  ctx.fillStyle='#334155';ctx.font='bold 12px Inter,system-ui';ctx.textAlign='center';
  ctx.fillText(fmtK(total)+_curSym,cx,cy-3);
  ctx.fillStyle='#64748b';ctx.font='9px Inter,system-ui';ctx.fillText('toplam',cx,cy+10);
  var lx=H+12,ly=10,lh=20;
  keys.slice(0,8).forEach(function(k,i){
    ctx.fillStyle=CLRS[i%CLRS.length];ctx.beginPath();ctx.arc(lx+5,ly+i*lh+6,4,0,2*Math.PI);ctx.fill();
    var pct=Math.round(cats[k]/total*100);
    ctx.fillStyle='#334155';ctx.font='10px Inter,system-ui';ctx.textAlign='left';
    var lbl=k.length>13?k.slice(0,13)+'…':k;
    ctx.fillText(lbl,lx+14,ly+i*lh+10);
    ctx.fillStyle='#64748b';ctx.textAlign='right';ctx.fillText(pct+'%',W-2,ly+i*lh+10);
  });
  cv.style.cursor='pointer';
  cv.onclick=function(e){
    var rect=cv.getBoundingClientRect();
    var mx=(e.clientX-rect.left)*(cv.width/rect.width);
    var my=(e.clientY-rect.top)*(cv.height/rect.height);
    var dx=mx-_donutCX, dy=my-_donutCY, dist=Math.sqrt(dx*dx+dy*dy);
    if(dist<_donutr||dist>_donutR) return;
    // Normalize atan2 [-π,π] → [-π/2, 3π/2] to match slice angles
    var angle=Math.atan2(dy,dx);
    if(angle < -Math.PI/2) angle += 2*Math.PI;
    for(var i=0;i<_donutSlices.length;i++){
      var s=_donutSlices[i];
      if(angle>=s.start && angle<s.end){ filterLedgerToCat('gider',s.cat); return; }
    }
    // Edge case: last slice end may be slightly past 3π/2 due to float
    if(_donutSlices.length) filterLedgerToCat('gider',_donutSlices[_donutSlices.length-1].cat);
  };
}

// ── GOALS / TASARRUF PAGE ─────────────────────────────────────────────────────
function renderBudgetPage(gider_cats,budgets){} // kept for compat, no-op now

var GOAL_ICONS={'eur':'💶','usd':'💵','gbp':'💷','gold':'🥇','bitcoin':'₿','arsa':'🏠','emeklilik':'📦','diger':'💎'};
var GOAL_COLORS={'eur':'#30d15818','usd':'#30d15818','gbp':'#30d15818','gold':'#ffd60a18','bitcoin':'#f97316 18','bitcoin':'#ff9f0a18','arsa':'#6366f118','emeklilik':'#bf5af218','diger':'#818cf818'};
var GOAL_BORDER={'eur':'#30d15830','usd':'#30d15830','gbp':'#30d15830','gold':'#ffd60a30','bitcoin':'#ff9f0a30','arsa':'#6366f130','emeklilik':'#bf5af230','diger':'#818cf830'};

function loadGoalsPage(){
  loadGoalsList();
  loadGoalsAnalysis();
}

function loadGoalsList(){
  xhr('/api/goals',null,function(goals){
    var el=document.getElementById('goals-list');
    if(!goals||!goals.length){
      el.innerHTML='<div class="empty-state"><div class="icon">🎯</div>Henüz hedef eklenmedi</div>';
      updateCapacityBar(goals||[]);
      return;
    }
    el.innerHTML=goals.map(function(g){
      var ico=GOAL_ICONS[g.goal_type]||'💎';
      var bg=GOAL_COLORS[g.goal_type]||'#6366f118';
      var bd=GOAL_BORDER[g.goal_type]||'#6366f130';
      return '<div class="goal-item" style="border-color:'+bd+';background:'+bg+'">'
        +'<div class="goal-icon-wrap" style="background:'+bg+'">'+ico+'</div>'
        +'<div class="goal-info">'
          +'<div class="goal-name">'+g.name+'</div>'
          +'<div class="goal-meta">'+(g.note||typeLabel(g.goal_type))+'</div>'
        +'</div>'
        +'<div class="goal-amount">'+fmt(g.monthly_target)+'/ay</div>'
        +'<button class="goal-del" onclick="deleteGoal('+g.id+')" title="Sil">✕</button>'
        +'</div>';
    }).join('');
    updateCapacityBar(goals);
  });
}

function typeLabel(t){
  var labels={'eur':'Euro (EUR)','usd':'Dolar (USD)','gbp':'Sterlin (GBP)','gold':'Altın','bitcoin':'Bitcoin','arsa':'Arsa / Gayrimenkul','emeklilik':'Emeklilik Fonu','diger':'Diğer Yatırım'};
  return labels[t]||t;
}

function updateCapacityBar(goals){
  var totalGoals=goals.reduce(function(s,g){return s+parseFloat(g.monthly_target||0);},0);
  var analysis=window._lastGoalsAnalysis;
  if(!analysis) return;
  var net=analysis.avg_net||0;
  var pct=net>0?Math.min(100,Math.round(totalGoals/net*100)):0;
  var fill=document.getElementById('goals-alloc-fill');
  var lbl=document.getElementById('goals-alloc-lbl');
  if(fill) fill.style.width=pct+'%';
  if(fill) fill.style.background=pct>100?'var(--r)':pct>75?'var(--y)':'var(--b2)';
  if(lbl) lbl.textContent='Hedeflere ayrılan: '+fmt(totalGoals)+' / '+fmt(Math.max(0,net))+' ('+pct+'%)';
}

function loadGoalsAnalysis(){
  xhr('/api/goals/analysis',null,function(d){
    window._lastGoalsAnalysis=d;
    var gelirEl=document.getElementById('gs-gelir');
    var giderEl=document.getElementById('gs-gider');
    var netEl=document.getElementById('gs-net');
    var badge=document.getElementById('goals-save-badge');
    if(gelirEl) gelirEl.textContent=fmt(d.avg_gelir);
    if(giderEl) giderEl.textContent=fmt(d.avg_gider);
    if(netEl){
      netEl.textContent=fmt(d.avg_net);
      netEl.style.color=d.avg_net>=0?'var(--b2)':'var(--r)';
    }
    if(badge){
      var sr=d.avg_gelir>0?Math.round(d.avg_net/d.avg_gelir*100):0;
      badge.textContent='%'+sr+' tasarruf';
      badge.style.background=sr>=25?'#30d15820':sr>=10?'#ffd60a20':'#ff453a20';
      badge.style.color=sr>=25?'var(--g)':sr>=10?'var(--y)':'var(--r)';
      badge.style.border='1px solid '+(sr>=25?'#30d15840':sr>=10?'#ffd60a40':'#ff453a40');
    }
    // render comments
    var el=document.getElementById('goals-comments');
    if(!el) return;
    if(!d.comments||!d.comments.length){el.innerHTML='<div class="empty-state" style="padding:24px"><div class="icon">🦔</div>Yeterli veri yok</div>';return;}
    el.innerHTML=d.comments.map(function(c){
      return '<div class="comment-bubble '+(c.type||'info')+'">'
        +'<div class="cb-ico">'+c.icon+'</div>'
        +'<div class="cb-text">'+c.text+'</div>'
        +'</div>';
    }).join('');
    // also update bar with goals
    xhr('/api/goals',null,function(goals){updateCapacityBar(goals);});
  });
}

function addGoal(){
  var name=document.getElementById('g-name').value.trim();
  var gtype=document.getElementById('g-type').value;
  var monthly=getNumVal(document.getElementById('g-monthly'));
  var note=document.getElementById('g-note').value.trim();
  if(!name){showToast('Hedef adı zorunlu','#ff453a');return}
  if(!monthly||monthly<=0){showToast('Aylık tutar giriniz','#ff453a');return}
  xhr('/api/goals',{name:name,goal_type:gtype,monthly_target:monthly,note:note},function(d){
    if(!d.ok){showToast('Hata','#ff453a');return}
    document.getElementById('g-name').value='';
    document.getElementById('g-monthly').value='';
    document.getElementById('g-note').value='';
    loadGoalsPage();
    showToast('Hedef eklendi ✓','#30d158');
  });
}

function deleteGoal(id){
  if(!confirm('Bu hedefi silmek istediğine emin misin?')) return;
  xhr('/api/goals/'+id,null,function(){
    loadGoalsPage();
    showToast('Hedef silindi','#ff453a');
  },false,true);
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
  var fd=document.getElementById('f-date-from').value;
  var fdt=document.getElementById('f-date-to').value;
  filteredTx=allTx.filter(function(t){
    if(fd&&t.date<fd) return false;
    if(fdt&&t.date>fdt) return false;
    if(!fd&&!fdt&&fy&&!t.date.startsWith(fy)) return false;
    if(ft&&t.type!==ft)return false;
    if(fc&&t.category!==fc)return false;
    if(q&&!(t.description||'').toLowerCase().includes(q)&&!t.category.toLowerCase().includes(q)&&!t.date.includes(q))return false;
    return true;
  });
  renderLedger();
}
function onYearFilterChange(){
  document.getElementById('f-date-from').value='';
  document.getElementById('f-date-to').value='';
  filterLedger();
}
function clearDateRange(){
  document.getElementById('f-date-from').value='';
  document.getElementById('f-date-to').value='';
  filterLedger();
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

  // alt toplam
  var sumEl=document.getElementById('ledger-summary');
  if(sumEl){
    var totG=0,totR=0;
    data.forEach(function(t){if(t.type==='gelir')totG+=t.amount;else totR+=t.amount;});
    var net=totG-totR;
    var parts=[];
    if(totG>0) parts.push('<span>Gelir: <strong style="color:var(--g)">+'+fmtNum(totG)+_curSym+'</strong></span>');
    if(totR>0) parts.push('<span>Gider: <strong style="color:var(--r)">-'+fmtNum(totR)+_curSym+'</strong></span>');
    if(totG>0&&totR>0) parts.push('<span>Net: <strong style="color:'+(net>=0?'var(--g)':'var(--r)')+'">'+( net>=0?'+':'')+fmtNum(net)+_curSym+'</strong></span>');
    sumEl.innerHTML=parts.join('<span style="color:var(--border,#e5e5ea)"> &nbsp;|&nbsp; </span>');
    sumEl.style.display=parts.length?'flex':'none';
  }

  // aylık özet
  renderMonthlySummary(allTx);

  // inline editing
  [].forEach.call(document.querySelectorAll('.editable'),function(td){
    td.addEventListener('click',function(e){startEdit(td)});
  });
}

function renderMonthlySummary(txList){
  var wrap=document.getElementById('monthly-summary');
  var inner=document.getElementById('monthly-summary-inner');
  if(!wrap||!inner) return;
  if(!txList||!txList.length){ wrap.style.display='none'; return; }
  var months={};
  txList.forEach(function(t){
    var m=t.date?t.date.slice(0,7):''; if(!m)return;
    if(!months[m]) months[m]={g:0,r:0};
    if(t.type==='gelir') months[m].g+=t.amount;
    else months[m].r+=t.amount;
  });
  var keys=Object.keys(months).sort().reverse();
  if(!keys.length){ wrap.style.display='none'; return; }
  inner.innerHTML=keys.map(function(m){
    var d=months[m], net=d.g-d.r;
    var parts=m.split('-');
    var label=(MONTHS[parseInt(parts[1])]||parts[1])+' '+parts[0];
    var netCol=net>=0?'var(--g)':'var(--r)';
    return '<div onclick="filterLedgerToMonth(\''+m+'\')" style="cursor:pointer;background:var(--bg2);border:1px solid var(--border,#e5e5ea);border-radius:12px;padding:10px 14px;min-width:140px;flex-shrink:0;transition:box-shadow .15s" onmouseenter="this.style.boxShadow=\'0 2px 8px rgba(0,0,0,.08)\'" onmouseleave="this.style.boxShadow=\'none\'">'
      +'<div style="font-size:.78rem;font-weight:700;color:var(--txt);margin-bottom:6px">'+label+'</div>'
      +(d.g>0?'<div style="font-size:.75rem;color:var(--g)">▲ '+fmtNum(d.g)+_curSym+'</div>':'')
      +(d.r>0?'<div style="font-size:.75rem;color:var(--r)">▼ '+fmtNum(d.r)+_curSym+'</div>':'')
      +'<div style="font-size:.78rem;font-weight:700;color:'+netCol+';margin-top:4px;border-top:1px solid var(--border,#e5e5ea);padding-top:4px">'+(net>=0?'+':'')+fmtNum(net)+_curSym+'</div>'
      +'</div>';
  }).join('');
  wrap.style.display='block';
}
function filterLedgerToMonth(ym){
  var yr=ym.split('-')[0], mo=ym.split('-')[1];
  // Tarih aralığını ayın ilk ve son günü olarak set et
  var lastDay=new Date(parseInt(yr),parseInt(mo),0).getDate();
  var fd=document.getElementById('f-date-from');
  var fdt=document.getElementById('f-date-to');
  var fy=document.getElementById('f-year');
  var ft=document.getElementById('f-type');
  var fc=document.getElementById('ledger-f-cat');
  var ls=document.getElementById('ledger-search');
  if(fd) fd.value=yr+'-'+mo+'-01';
  if(fdt) fdt.value=yr+'-'+mo+'-'+String(lastDay).padStart(2,'0');
  if(fy) fy.value='';
  if(ft) ft.value='';
  if(fc) fc.value='';
  if(ls) ls.value='';
  filterLedger();
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

loadDashboard = function(){
  loadTodayWidgets();
  var reqId = ++_dashReqId;

  // Hero period tabs (Ay / Yıl / Tüm Zamanlar) take priority
  if(_heroPeriod === 'year'){
    xhr('/api/summary?period=year&year='+_heroYear, null, function(d){
      if(reqId !== _dashReqId) return;
      summaryData=d; renderStats(d); drawBar(d.bar); drawDonut(d.gider_cats); renderBudgetPage(d.gider_cats,d.budgets);
    });
    xhr('/api/motivation',null,renderMotivation);
    return;
  }
  if(_heroPeriod === 'all'){
    xhr('/api/summary?period=all', null, function(d){
      if(reqId !== _dashReqId) return;
      summaryData=d; renderStats(d); drawBar(d.bar); drawDonut(d.gider_cats); renderBudgetPage(d.gider_cats,d.budgets);
    });
    xhr('/api/motivation',null,renderMotivation);
    return;
  }

  // Month mode — use ledger year/month nav
  if(dbView==='year'){
    xhr('/api/summary?period=year&year='+curYear, null, function(d){
      if(reqId !== _dashReqId) return;
      summaryData=d; renderStats(d); drawBar(d.bar); drawDonut(d.gider_cats); renderBudgetPage(d.gider_cats,d.budgets);
      var sub=document.getElementById('db-sub'); if(sub) sub.textContent=curYear+' yılı';
    });
    xhr('/api/motivation',null,renderMotivation);
    return;
  }
  xhr('/api/summary?year='+curYear+'&month='+curMonth, null, function(d){
    if(reqId !== _dashReqId) return;
    summaryData=d; renderStats(d); drawBar(d.bar); drawDonut(d.gider_cats); renderBudgetPage(d.gider_cats,d.budgets);
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

// ── TODOS ─────────────────────────────────────────────────────────────────────
var _todoDate = new Date().toISOString().slice(0,10);
var _todos = [];

function initTodosPage(){
  _todoDate = new Date().toISOString().slice(0,10);
  loadTodos();
}

function todoChangeDate(delta){
  var d = new Date(_todoDate);
  d.setDate(d.getDate() + delta);
  _todoDate = d.toISOString().slice(0,10);
  loadTodos();
}

function loadTodos(){
  var lbl = document.getElementById('todo-date-lbl');
  var parts = _todoDate.split('-');
  var months = ['','Ocak','Subat','Mart','Nisan','Mayis','Haziran','Temmuz','Agustos','Eylul','Ekim','Kasim','Aralik'];
  var today = new Date().toISOString().slice(0,10);
  var label = parts[2]+' '+months[parseInt(parts[1])]+' '+parts[0];
  if(_todoDate === today) label = 'Bugün — '+label;
  if(lbl) lbl.textContent = label;

  xhr('/api/todos?date='+_todoDate, null, function(items){
    _todos = items || [];
    renderTodos();
  });
}

function renderTodos(){
  var active = _todos.filter(function(t){return !t.archived && !t.done});
  var done   = _todos.filter(function(t){return t.done || t.archived});
  var al = document.getElementById('todo-active-list');
  var arl = document.getElementById('todo-archive-list');
  var ars = document.getElementById('todo-archive-section');
  var arc = document.getElementById('todo-archive-count');

  if(al) al.innerHTML = active.length ? active.map(todoItemHTML).join('') :
    '<div style="text-align:center;padding:28px 16px;color:var(--txt2);font-size:.85rem">🦔 Görev yok. Ekle!</div>';

  if(arl) arl.innerHTML = done.map(function(t){return todoItemHTML(t,true)}).join('');
  if(ars) ars.style.display = done.length ? 'block' : 'none';
  if(arc) arc.textContent = done.length;
}

function todoItemHTML(t, archived){
  var doneClass = (t.done || t.archived) ? 'done' : '';
  var check = (t.done || t.archived) ? '✓' : '';
  return '<div class="todo-item '+doneClass+'" id="todo-'+t.id+'" onclick="toggleTodo('+t.id+')">' +
    '<div class="todo-check">' + check + '</div>' +
    '<div class="todo-text">' + escHtml(t.text) + '</div>' +
    '<button class="todo-del" onclick="event.stopPropagation();delTodo('+t.id+')" title="Sil">🗑</button>' +
    '</div>';
}

function addTodo(){
  var inp = document.getElementById('todo-input');
  var text = inp.value.trim();
  if(!text) return;
  xhr('/api/todos', {text:text,date:_todoDate}, function(r){
    if(r.ok){ inp.value=''; loadTodos(); }
  });
}

function toggleTodo(id){
  var t = _todos.find(function(x){return x.id===id});
  if(!t) return;
  var el = document.getElementById('todo-'+id);
  if(el){
    var chk = el.querySelector('.todo-check');
    if(chk){ chk.classList.add('popping'); setTimeout(function(){chk.classList.remove('popping')},300); }
  }
  if(!t.done && !t.archived){
    xhr('/api/todos/'+id, {done:1}, function(r){
      if(r.ok){
        if(el){ el.classList.add('archiving'); }
        setTimeout(function(){
          xhr('/api/todos/'+id, {archived:1}, function(){ loadTodos(); }, true);
        }, 450);
      }
    }, true);
  } else {
    xhr('/api/todos/'+id, {done:0,archived:0}, function(r){
      if(r.ok) loadTodos();
    }, true);
  }
}

function delTodo(id){
  xhr('/api/todos/'+id, null, function(r){
    if(r.ok) loadTodos();
  }, false, true);
}

function escHtml(s){
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── SUPPLIER INVOICES ─────────────────────────────────────────────────────────
var _supTab = 'pending';
var _editingSupInvId = null;

function initSupplierPage(){
  loadSupAging();
  loadSupFloatGain();
  loadSupInvList();
}

function setSupTab(tab){
  _supTab = tab;
  var pb = document.getElementById('sup-tab-pending');
  var pd = document.getElementById('sup-tab-paid');
  if(pb) pb.style.cssText = tab==='pending' ?
    'flex:1;background:var(--b);color:#fff;border:none' :
    'flex:1;background:transparent;border:1px solid var(--border2);color:var(--txt)';
  if(pd) pd.style.cssText = tab==='paid' ?
    'flex:1;background:var(--b);color:#fff;border:none' :
    'flex:1;background:transparent;border:1px solid var(--border2);color:var(--txt)';
  loadSupInvList();
}

function loadSupAging(){
  xhr('/api/supplier-invoices/aging', null, function(d){
    if(!d.ok) return;
    var b = d.buckets; var t = d.totals;
    var e0 = document.getElementById('ag-0-30');
    var e1 = document.getElementById('ag-31-60');
    var e2 = document.getElementById('ag-61-90');
    var e3 = document.getElementById('ag-90plus');
    if(e0) e0.textContent = fmtShort(t['0_30']);
    document.getElementById('ag-0-30-cnt').textContent = b['0_30'].length+' fatura';
    if(e1) e1.textContent = fmtShort(t['31_60']);
    document.getElementById('ag-31-60-cnt').textContent = b['31_60'].length+' fatura';
    if(e2) e2.textContent = fmtShort(t['61_90']);
    document.getElementById('ag-61-90-cnt').textContent = b['61_90'].length+' fatura';
    if(e3) e3.textContent = fmtShort(t['90plus']);
    document.getElementById('ag-90plus-cnt').textContent = b['90plus'].length+' fatura';
  });
}

function loadSupFloatGain(){
  xhr('/api/supplier-invoices/float-gain', null, function(d){
    if(!d.ok) return;
    var el = document.getElementById('sup-float-value');
    if(el) el.textContent = fmt(d.total_gain);
  });
}

function loadSupInvList(){
  var status = _supTab === 'pending' ? 'bekliyor' : 'odendi';
  xhr('/api/supplier-invoices?status='+status, null, function(items){
    var el = document.getElementById('sup-inv-list');
    if(!el) return;
    if(!items || !items.length){
      el.innerHTML = '<div style="text-align:center;padding:28px 16px;color:var(--txt2);font-size:.85rem">🏭 '+
        (status==='bekliyor' ? 'Bekleyen fatura yok' : 'Ödenmiş fatura yok')+'</div>';
      return;
    }
    var today = new Date().toISOString().slice(0,10);
    el.innerHTML = items.map(function(inv){
      var overdue = inv.status==='bekliyor' && inv.due_date < today;
      var daysText = '';
      if(inv.status==='bekliyor'){
        var due = new Date(inv.due_date);
        var now = new Date();
        var diff = Math.round((due-now)/(1000*60*60*24));
        if(diff < 0) daysText = '<span style="color:var(--r)">'+Math.abs(diff)+' gün gecikti</span>';
        else if(diff === 0) daysText = '<span style="color:var(--y)">Bugün son gün!</span>';
        else daysText = '<span style="color:var(--txt2)">'+diff+' gün kaldı</span>';
      } else {
        daysText = '<span style="color:var(--g)">✓ Ödendi '+(inv.paid_date||'')+'</span>';
      }
      var dotColor = overdue ? 'var(--r)' : (inv.status==='odendi' ? 'var(--g)' : 'var(--y)');
      return '<div class="sup-inv-item" style="gap:10px">' +
        '<div class="sup-inv-dot" style="background:'+dotColor+';flex-shrink:0"></div>' +
        '<div class="sup-inv-info tappable" onclick="openPaySupInv('+inv.id+')" style="flex:1;min-width:0">' +
          '<div class="sup-inv-name">'+escHtml(inv.supplier_name)+'</div>' +
          '<div class="sup-inv-meta">'+(inv.invoice_no ? escHtml(inv.invoice_no)+' &bull; ' : '')+'Vade: '+inv.due_date+'</div>' +
        '</div>' +
        '<div class="sup-inv-right tappable" onclick="openPaySupInv('+inv.id+')" style="text-align:right;flex-shrink:0">' +
          '<div class="sup-inv-amount">'+fmt(inv.amount)+'</div>' +
          '<div class="sup-inv-days">'+daysText+'</div>' +
        '</div>' +
        '<button onclick="delSupInv('+inv.id+')" style="background:none;border:none;font-size:1rem;cursor:pointer;padding:4px 6px;border-radius:8px;color:var(--txt2);flex-shrink:0;-webkit-tap-highlight-color:transparent" title="Sil">🗑</button>' +
        '</div>';
    }).join('');
    // Store data for tap handler
    window._supInvData = {};
    items.forEach(function(inv){ window._supInvData[inv.id] = inv; });
  });
}

function openSupInvModal(id){
  _editingSupInvId = id || null;
  document.getElementById('mod-sup-inv-title').textContent = id ? 'Faturayı Düzenle' : 'Tedarikçi Faturası';
  document.getElementById('sup-inv-name').value = '';
  document.getElementById('sup-inv-no').value = '';
  document.getElementById('sup-inv-amount').value = '';
  document.getElementById('sup-inv-date').value = new Date().toISOString().slice(0,10);
  document.getElementById('sup-inv-due').value = '';
  var rateEl = document.getElementById('sup-inv-rate');
  rateEl.value = '50'; rateEl.dataset.raw = '50';
  document.getElementById('sup-inv-notes').value = '';
  document.getElementById('mod-sup-inv').style.display = 'flex';
  setTimeout(setupNumInputs, 50);
}

function closeMod(id){ document.getElementById(id).style.display='none'; }

function saveSupInv(){
  var body = {
    supplier_name: document.getElementById('sup-inv-name').value.trim(),
    invoice_no: document.getElementById('sup-inv-no').value.trim(),
    amount: getNumVal(document.getElementById('sup-inv-amount')),
    invoice_date: document.getElementById('sup-inv-date').value,
    due_date: document.getElementById('sup-inv-due').value,
    reference_rate: getNumVal(document.getElementById('sup-inv-rate'))||50,
    notes: document.getElementById('sup-inv-notes').value.trim()
  };
  if(!body.supplier_name || !body.amount || !body.due_date){
    showToast('Tedarikçi, tutar ve vade zorunlu','#ef4444'); return;
  }
  if(_editingSupInvId){
    xhr('/api/supplier-invoices/'+_editingSupInvId, body, function(r){
      if(r.ok){ closeMod('mod-sup-inv'); toast('Kaydedildi'); initSupplierPage(); }
    }, true);
  } else {
    xhr('/api/supplier-invoices', body, function(r){
      if(r.ok){ closeMod('mod-sup-inv'); toast('Kaydedildi'); initSupplierPage(); }
    });
  }
}

function openPaySupInv(id, el){
  var inv = window._supInvData && window._supInvData[id];
  if(!inv) return;
  if(inv.status === 'odendi'){
    toast(inv.supplier_name+' zaten ödenmiş'); return;
  }
  if(confirm(inv.supplier_name+' — '+fmt(inv.amount)+' ödenmiş olarak işaretlensin mi?')){
    xhr('/api/supplier-invoices/'+id+'/pay',
        {paid_date: new Date().toISOString().slice(0,10)},
        function(r){
          if(r.ok){ toast('Ödendi olarak işaretlendi'); initSupplierPage(); }
        });
  }
}

function delSupInv(id){
  var inv = window._supInvData && window._supInvData[id];
  var name = inv ? inv.supplier_name : 'bu fatura';
  if(!confirm(name+' silinsin mi?')) return;
  xhr('/api/supplier-invoices/'+id, null, function(r){
    if(r.ok){ toast('Fatura silindi'); initSupplierPage(); }
  }, false, true);
}

function fmtShort(n){
  if(!n) return '₺0';
  if(n>=1000000) return '₺'+(n/1000000).toFixed(1)+'M';
  if(n>=1000) return '₺'+(n/1000).toFixed(0)+'K';
  return '₺'+Math.round(n);
}

// ── ASSETS ───────────────────────────────────────────────────────────────────
function initAssetsPage(){
  loadAssets();
}

function loadAssets(){
  xhr('/api/assets', null, function(items){
    var el = document.getElementById('asset-list');
    if(!el) return;
    if(!items || !items.length){
      el.innerHTML = '<div style="text-align:center;padding:28px 16px;color:var(--txt2);font-size:.85rem">🚗 Henüz varlık eklenmedi</div>';
      document.getElementById('asset-total-book').textContent = '₺0';
      document.getElementById('asset-total-dep').textContent = '₺0';
      return;
    }
    var totalBook = 0, totalDep = 0;
    items.forEach(function(a){ totalBook += a.book_value||0; totalDep += a.annual_dep||0; });
    document.getElementById('asset-total-book').textContent = fmt(totalBook);
    document.getElementById('asset-total-dep').textContent = fmt(totalDep);

    var icons = {arac:'🚗',bilgisayar:'💻',makine:'⚙️',mobilya:'🪑',bina:'🏢',diger:'📦'};
    var typeNames = {arac:'Araç',bilgisayar:'Bilgisayar',makine:'Makine',mobilya:'Mobilya',bina:'Bina',diger:'Diğer'};
    el.innerHTML = items.map(function(a){
      var pct = a.purchase_price > 0 ? Math.min(100, Math.round(a.accumulated/a.purchase_price*100)) : 0;
      var alerts = '';
      if(a.maintenance_date){
        var daysToMaint = Math.round((new Date(a.maintenance_date)-new Date())/(1000*60*60*24));
        if(daysToMaint < 0) alerts += '<div class="asset-alert danger">🔧 Bakım tarihi geçti! ('+Math.abs(daysToMaint)+' gün)</div>';
        else if(daysToMaint <= 30) alerts += '<div class="asset-alert warn">🔧 Bakıma '+daysToMaint+' gün kaldı</div>';
      }
      if(a.insurance_date){
        var daysToIns = Math.round((new Date(a.insurance_date)-new Date())/(1000*60*60*24));
        if(daysToIns < 0) alerts += '<div class="asset-alert danger">🛡️ Sigorta süresi doldu!</div>';
        else if(daysToIns <= 30) alerts += '<div class="asset-alert warn">🛡️ Sigortaya '+daysToIns+' gün kaldı</div>';
      }
      return '<div class="asset-card tappable">' +
        '<div class="asset-card-top">' +
          '<div class="asset-icon '+(a.asset_type||'diger')+'">'+(icons[a.asset_type]||'📦')+'</div>' +
          '<div>' +
            '<div class="asset-name">'+escHtml(a.name)+'</div>' +
            '<span class="asset-type-badge">'+(typeNames[a.asset_type]||'Diğer')+'</span>' +
            (a.plate_no ? ' <span class="asset-type-badge">'+escHtml(a.plate_no)+'</span>' : '') +
          '</div>' +
        '</div>' +
        '<div class="asset-dep-bar-bg"><div class="asset-dep-bar-fill" style="width:'+pct+'%"></div></div>' +
        '<div class="asset-nums">' +
          '<div class="asset-num-cell"><div class="anc-lbl">Alış Bedeli</div><div class="anc-val">'+fmt(a.purchase_price)+'</div></div>' +
          '<div class="asset-num-cell"><div class="anc-lbl">Defter Değeri</div><div class="anc-val" style="color:var(--b)">'+fmt(a.book_value)+'</div></div>' +
          '<div class="asset-num-cell"><div class="anc-lbl">Amortisman %'+a.depreciation_rate+'</div><div class="anc-val" style="color:var(--y)">'+fmt(a.annual_dep)+'/yıl</div></div>' +
        '</div>' +
        alerts +
        '</div>';
    }).join('');
  });
}

function openAssetModal(){
  document.getElementById('asset-name').value='';
  document.getElementById('asset-type').value='arac';
  document.getElementById('asset-plate').value='';
  document.getElementById('asset-purchase-date').value=new Date().toISOString().slice(0,10);
  document.getElementById('asset-price').value='';
  document.getElementById('asset-dep-rate').value='20';
  document.getElementById('asset-maint-date').value='';
  document.getElementById('asset-ins-date').value='';
  document.getElementById('asset-ins-co').value='';
  document.getElementById('mod-asset').style.display='flex';
  setTimeout(setupNumInputs, 50);
}

function onAssetTypeChange(){
  var type = document.getElementById('asset-type').value;
  var rates = {arac:20,bilgisayar:33.33,makine:20,mobilya:20,bina:2,diger:20};
  document.getElementById('asset-dep-rate').value = rates[type]||20;
}

function saveAsset(){
  var body = {
    name: document.getElementById('asset-name').value.trim(),
    asset_type: document.getElementById('asset-type').value,
    plate_no: document.getElementById('asset-plate').value.trim(),
    purchase_date: document.getElementById('asset-purchase-date').value,
    purchase_price: getNumVal(document.getElementById('asset-price')),
    depreciation_rate: getNumVal(document.getElementById('asset-dep-rate'))||20,
    maintenance_date: document.getElementById('asset-maint-date').value||'',
    insurance_date: document.getElementById('asset-ins-date').value||'',
    insurance_company: document.getElementById('asset-ins-co').value.trim()
  };
  if(!body.name || !body.purchase_price){
    showToast('Varlık adı ve alış bedeli zorunlu','#ef4444'); return;
  }
  xhr('/api/assets', body, function(r){
    if(r.ok){
      closeMod('mod-asset');
      toast('Varlık eklendi');
      loadAssets();
    }
  });
}

// ── CARD DAILY REPORT ─────────────────────────────────────────────────────────
function loadCardReport(){
  var today = new Date().toISOString().slice(0,10);
  var el = document.getElementById('cdr-report-date');
  if(el){
    var parts = today.split('-');
    var months2 = ['','Ocak','Subat','Mart','Nisan','Mayis','Haziran','Temmuz','Agustos','Eylul','Ekim','Kasim','Aralik'];
    el.textContent = parts[2]+' '+months2[parseInt(parts[1])]+' '+parts[0]+' Raporu';
  }
  xhr('/api/cards/daily-report', null, function(d){
    if(!d.ok) return;
    var el2 = document.getElementById('card-daily-report-list');
    if(!el2) return;
    if(!d.cards || !d.cards.length){
      el2.innerHTML = '<div style="text-align:center;padding:28px 16px;color:var(--txt2)">💳 Önce Kartlar sayfasından kart ekleyin</div>';
      return;
    }
    el2.innerHTML = d.cards.map(function(c){
      var name = c.bank_name + (c.card_name ? ' — '+c.card_name : '');
      var spentHtml = c.spent_today !== null ?
        (c.spent_today > 0 ? '<div class="dc-val" style="color:var(--r)">'+fmt(c.spent_today)+'</div>' :
         c.spent_today < 0 ? '<div class="dc-val" style="color:var(--g)">'+fmt(Math.abs(c.spent_today))+' iade</div>' :
         '<div class="dc-val" style="color:var(--txt2)">₺0</div>') :
        '<div class="dc-val" style="color:var(--txt2)">—</div>';
      return '<div class="cdr-card">' +
        '<div class="cdr-card-top"><div class="cdr-bank">💳 '+escHtml(name)+'</div></div>' +
        '<div class="cdr-nums">' +
          '<div class="cdr-cell yest"><div class="dc-lbl">Dünkü</div><div class="dc-val">'+(c.yesterday_balance!==null?fmt(c.yesterday_balance):'—')+'</div></div>' +
          '<div class="cdr-cell today"><div class="dc-lbl">Bugünkü</div><div class="dc-val">'+(c.today_balance!==null?fmt(c.today_balance):'Girilmedi')+'</div></div>' +
          '<div class="cdr-cell spent"><div class="dc-lbl">Harcama</div>'+spentHtml+'</div>' +
        '</div>' +
        '<div class="cdr-input-row">' +
          '<input class="cdr-bal-input" type="text" inputmode="decimal" id="cdr-bal-'+c.card_id+'" placeholder="Bugünkü bakiye" value="'+(c.today_balance!==null?c.today_balance:'')+'">' +
          '<button class="cdr-save-btn tappable" onclick="saveCardBalance('+c.card_id+')">Kaydet</button>' +
        '</div>' +
        '</div>';
    }).join('');
  });
}

function saveCardBalance(cardId){
  var inp = document.getElementById('cdr-bal-'+cardId);
  if(!inp) return;
  var val = getNumVal(inp);
  if(!val && val !== 0){ showToast('Geçerli tutar girin','#ef4444'); return; }
  xhr('/api/cards/daily-balance', {
    card_id: cardId,
    balance: val,
    date: new Date().toISOString().slice(0,10)
  }, function(r){
    if(r.ok){ toast('Bakiye kaydedildi'); loadCardReport(); }
  });
}

// ── EXCEL EXPORT ──────────────────────────────────────────────────────────────
function exportExcel(){
  toast('Excel hazırlanıyor...');
  window.location.href = '/api/export/excel';
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
    first_name = display.split()[0] if display.strip() else display
    return HTML.replace("__USER_DISPLAY__", first_name)

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
