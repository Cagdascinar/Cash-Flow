from datetime import date

AUTH_HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#f2f2f7">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="icon" href="/icon-192.png" sizes="192x192" type="image/png">
<title>Kirpi — Nakit Akışın Cebinde!</title>
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

HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="theme-color" content="#0a0c12">
<meta name="description" content="Kirpi — Nakit Akışın Cebinde! Gelir, gider, kart borçları ve bütçenizi tek yerden yönetin.">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Kirpi">
<link rel="manifest" href="/manifest.json">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="icon" href="/icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="/icon-192.png">
<meta property="og:title" content="Kirpi — Nakit Akışın Cebinde!">
<meta property="og:description" content="Nakit Akışın Cebinde! Gelir, gider, kart borçları ve bütçenizi tek yerden yönetin.">
<meta property="og:image" content="/icon-512.png">
<meta property="og:type" content="website">
<title>Kirpi — Nakit Akışın Cebinde!</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
html{overflow-x:hidden}
body{position:relative;overflow-x:hidden}
/* ── Binance Dark (varsayılan) ── */
:root{
  --bg:#0b0e11;--bg2:#1e2026;--bg3:#2b2f36;--bg4:#363c45;
  --g:#0ecb81;--r:#f6465d;--b:#f0b90b;--b2:#f0b90b;--y:#f0b90b;--p:#af52de;--c:#00b8d9;
  --txt:#eaecef;--txt2:#848e9c;--border:#2b2f36;--border2:#363c45;
  --radius:12px;--shadow:0 2px 16px rgba(0,0,0,.5);
  --font:'Inter',system-ui,sans-serif;
}
/* Light mod isteyenler için */
[data-theme="light"]{
  --bg:#f0f4f8;--bg2:#ffffff;--bg3:#e8ecf0;--bg4:#d1d7de;
  --g:#0ecb81;--r:#f6465d;--b:#f0b90b;--b2:#d4a017;--y:#f0b90b;
  --txt:#1e2026;--txt2:#707a8a;--border:#dde1e7;--border2:#c8cdd4;
  --shadow:0 2px 16px rgba(0,0,0,.08);
}
:root{
  --radius:14px;--shadow:0 2px 16px rgba(0,0,0,.08);
  --font:'Inter',system-ui,sans-serif;
}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
html{height:auto;overflow-y:auto}
body{background:var(--bg);color:var(--txt);font-family:var(--font);min-height:100vh;
  overflow-x:hidden;overflow-y:auto;height:auto;
  overscroll-behavior-x:none;-webkit-overflow-scrolling:touch;touch-action:pan-y;
  -webkit-touch-callout:none;-webkit-user-select:none;user-select:none}
input,textarea,select,[contenteditable]{-webkit-user-select:text;user-select:text}

/* ── LAYOUT ── */
.shell{display:flex;min-height:100vh}
nav{width:220px;background:var(--bg2);border-right:1px solid rgba(255,255,255,.06);
    display:flex;flex-direction:column;flex-shrink:0;position:fixed;top:0;left:0;height:100vh;z-index:100}
.main{margin-left:220px;flex:1;display:flex;flex-direction:column;min-height:100vh;overflow-x:hidden;min-width:0;
  padding-top:calc(54px + env(safe-area-inset-top,0px))}
/* Tablet: 768-1200px — body kaydirir, hiçbir şey scroll'u engellemez */
@media(min-width:769px) and (max-width:1200px){
  html{height:auto;overflow-y:auto}
  body{height:auto;overflow-y:auto;-webkit-overflow-scrolling:touch;touch-action:pan-y}
  .main{overflow-y:visible;height:auto}
  .page{touch-action:pan-y}
  nav{touch-action:none;pointer-events:auto}
}
@media(max-width:768px){
  nav{width:100%;height:auto;flex-direction:row;border-right:none;border-top:none;border-bottom:none;
      position:fixed;bottom:0;left:0;right:0;top:auto;z-index:9999;
      padding-bottom:env(safe-area-inset-bottom,0px);
      overflow:visible;
      background:rgba(17,18,20,.92);
      backdrop-filter:blur(28px) saturate(200%);-webkit-backdrop-filter:blur(28px) saturate(200%);
      box-shadow:0 -0.5px 0 rgba(255,255,255,.08),0 -12px 40px rgba(0,0,0,.6)}
  [data-theme="light"] nav{background:rgba(255,255,255,.92);box-shadow:0 -0.5px 0 rgba(0,0,0,.1),0 -12px 40px rgba(0,0,0,.08)}
  .main{margin-left:0;margin-bottom:calc(70px + env(safe-area-inset-bottom,0px));position:relative;z-index:1}
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

/* ── MOBILE ALT NAV — Apple iOS Tab Bar Standard ── */
@media(max-width:768px){
  .nav-sect,.nl-desktop,.nl-desktop-only,.nl-menu,.nl-more,.nl-spacer,.nav-logo{display:none!important}

  /* Tab bar container */
  .nav-links {
    flex-direction:row;
    height:54px;
    padding:0 4px;
    gap:0;
    align-items:stretch;
    overflow:visible;
  }

  /* Her sekme — Apple HIG: min 44×44pt dokunma alanı */
  .nl {
    flex:1!important;
    display:flex!important;
    flex-direction:column!important;
    align-items:center!important;
    justify-content:center!important;
    gap:3px;
    min-height:44px;
    padding:6px 0 4px;
    box-shadow:none!important;
    background:transparent!important;
    border-radius:0;
    cursor:pointer;
    -webkit-tap-highlight-color:transparent;
    position:static!important;
    transform:none!important;
    width:auto!important;
    transition:opacity .1s;
  }
  .nl:active { opacity:.65; }

  /* İkon kabı — aktif state için pill arka plan */
  .nl .ico {
    display:flex!important;
    align-items:center;
    justify-content:center;
    width:32px; height:32px;
    font-size:1.3rem;
    line-height:1;
    border-radius:10px;
    transition:transform .18s cubic-bezier(.34,1.56,.64,1), background .12s;
  }

  /* Etiket */
  .nl span:not(.ico) {
    font-size:.58rem;
    font-weight:500;
    letter-spacing:.01em;
    color:var(--txt2);
    white-space:nowrap;
    transition:color .12s;
  }

  /* Aktif durum — ikon büyüsün + etiket renk */
  .nl.active .ico {
    transform:scale(1.08);
    background:rgba(0,122,255,.12);
  }
  .nl.active span:not(.ico) {
    color:var(--b);
    font-weight:700;
  }
  .nl::after { display:none!important }

  /* Ekle butonu — merkezi vurgulu */
  .nl-add-ghost { display:none!important }
  .nl-add .ico {
    background:linear-gradient(145deg,#007aff,#0062cc)!important;
    color:#fff!important;
    border-radius:14px;
    font-size:1.2rem;
    box-shadow:0 3px 12px rgba(0,122,255,.45);
    width:36px!important; height:36px!important;
  }
  .nl-add.active .ico { background:linear-gradient(145deg,#007aff,#0062cc)!important; }
  .nl-add span:not(.ico) { color:var(--b)!important; font-weight:700; }
  .nl-add:active .ico { transform:scale(.9)!important; box-shadow:0 1px 6px rgba(0,122,255,.3); }

  .nl-desktop,.nl-desktop-only,.nl-menu,.nl-more,.nav-sect{display:none!important}
}

/* ── MORE SHEET ── */
.more-backdrop{display:none;position:fixed;inset:0;background:rgba(0,0,0,.35);
               z-index:9000;backdrop-filter:blur(3px);-webkit-backdrop-filter:blur(3px)}
.more-sheet{position:fixed;bottom:0;left:0;right:0;
            background:var(--bg2);border-radius:28px 28px 0 0;
            z-index:9001;padding:0 0 env(safe-area-inset-bottom,16px);
            box-shadow:0 -8px 40px rgba(0,0,0,.18);
            transform:translateY(100%);transition:transform .34s cubic-bezier(.4,0,.2,1);
            max-height:82vh;overflow-y:auto}
.more-sheet.open{transform:translateY(0)}
.more-backdrop.open{display:block}
/* ── SPLASH SCREEN ── */
/* ── SPLASH — CSS ile otomatik kapanır (JS hata yapsa bile) ── */
#splash-screen{
  position:fixed;inset:0;z-index:99999;
  background:linear-gradient(160deg,#050c1a 0%,#0d1f3c 50%,#0a0e1a 100%);
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  /* 1.5s sonra CSS kendisi kapatır — JS olmadan da çalışır */
  animation:_splash-auto .45s 1.5s ease forwards;
}
@keyframes _splash-auto{to{opacity:0;pointer-events:none;visibility:hidden}}
/* JS erken kapattığında */
#splash-screen.hide{animation:_splash-auto .35s 0s ease forwards!important}
.splash-center{display:flex;flex-direction:column;align-items:center;gap:0}
.splash-icon-wrap{
  width:96px;height:96px;border-radius:28px;
  background:linear-gradient(145deg,#1a3a6b,#0d2a5c);
  border:1px solid rgba(99,160,255,.2);
  display:flex;align-items:center;justify-content:center;
  font-size:3rem;margin-bottom:20px;
  box-shadow:0 0 60px rgba(99,160,255,.15),0 20px 60px rgba(0,0,0,.5);
  opacity:0;
  animation:spl-icon .5s .05s cubic-bezier(.34,1.56,.64,1) forwards;
}
@keyframes spl-icon{
  from{opacity:0;transform:scale(.7) translateY(12px)}
  to  {opacity:1;transform:scale(1)  translateY(0)}
}
.splash-appname{
  font-size:1.9rem;font-weight:900;letter-spacing:-.04em;color:#fff;
  opacity:0;animation:spl-text .4s .3s ease forwards;
}
.splash-apptag{
  font-size:.82rem;color:rgba(255,255,255,.35);margin-top:6px;letter-spacing:.02em;
  opacity:0;animation:spl-text .4s .45s ease forwards;
}
@keyframes spl-text{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
/* İnce ilerleme çizgisi */
.splash-bar{
  position:absolute;bottom:0;left:0;height:2px;
  background:linear-gradient(90deg,#6366f1,#60a5fa,#34d399);
  animation:spl-bar 1.2s .1s ease-out forwards;
  border-radius:0 2px 2px 0;
}
@keyframes spl-bar{from{width:0}to{width:100%}}

/* Onboarding */
.ob-step{display:flex;align-items:center;gap:12px;background:rgba(255,255,255,.15);
  border-radius:12px;padding:12px 14px;cursor:pointer;transition:.12s}
.ob-step:active{background:rgba(255,255,255,.25)}
.ob-num{width:28px;height:28px;border-radius:50%;background:rgba(255,255,255,.25);
  display:flex;align-items:center;justify-content:center;font-size:.82rem;font-weight:900;flex-shrink:0}

.more-sheet-handle{width:40px;height:4px;border-radius:3px;background:var(--bg4);
                   margin:14px auto 6px;cursor:grab}
.more-sect-label{font-size:.62rem;font-weight:800;text-transform:uppercase;
                 letter-spacing:.12em;color:var(--txt2);padding:10px 20px 6px;opacity:.5}
.more-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:0 14px 8px}
.more-tile{display:flex;flex-direction:column;align-items:center;gap:7px;
           padding:16px 8px 14px;background:var(--bg3);border-radius:18px;cursor:pointer;
           transition:.14s;-webkit-tap-highlight-color:transparent;border:1px solid var(--border)}
.more-tile:active{background:var(--bg4);transform:scale(.96)}
.more-tile .mt-ico{font-size:1.7rem;line-height:1}
.more-tile .mt-lbl{font-size:.72rem;font-weight:700;color:var(--txt);text-align:center}
.more-tile[data-sirket]{display:none}
.more-tile[data-sirket].sirket-visible{display:flex}

.nav-bottom{display:flex;align-items:center;gap:10px;padding:14px 16px;border-top:1px solid var(--border);cursor:pointer;transition:.12s}
.nav-bottom:hover{background:var(--bg3)}
@media(max-width:768px){.nav-bottom{display:none!important}}

/* ── PAGE ── */
.main{display:flex;flex-direction:column}
.page{
  display:none;padding:20px 28px;max-width:1280px;
  opacity:0;transform:translateY(14px) scale(.99);
  touch-action:pan-y;
}
.page.active{
  display:block;
  opacity:1;
  transform:none;
}
.page.slide-back{transform:translateX(-12px);opacity:0}
/* Dil butonu */
.lang-btn{padding:8px 6px;border-radius:10px;border:1.5px solid var(--border2);background:var(--bg3);
  color:var(--txt);font-size:.75rem;font-weight:600;cursor:pointer;transition:.14s;text-align:center;
  -webkit-tap-highlight-color:transparent}
.lang-btn:hover{border-color:var(--b);background:rgba(0,122,255,.07)}
.lang-btn.active{border-color:var(--b);background:rgba(0,122,255,.13);color:var(--b)}
/* Ödeme yöntemi çipleri */
.pay-chip{padding:7px 13px;border-radius:10px;border:1.5px solid var(--border2);background:var(--bg3);
  color:var(--txt2);font-size:.8rem;font-weight:600;cursor:pointer;transition:.14s;
  -webkit-tap-highlight-color:transparent}
.pay-chip.active{border-color:var(--b);background:rgba(0,122,255,.1);color:var(--b)}
@media(max-width:600px){.page{padding:16px 16px 20px}}
.page-title{
  font-size:1.9rem;font-weight:900;margin-bottom:4px;
  letter-spacing:-.04em;line-height:1.1;
}
.page-sub{font-size:.84rem;color:var(--txt2);margin-bottom:22px;font-weight:400}
@media(max-width:768px){
  .page-title{font-size:1.55rem}
  .page-sub{margin-bottom:16px}
}

/* ── CARDS ── */
.card{
  background:var(--bg2);border:1px solid var(--border);
  border-radius:var(--radius);padding:20px;
  box-shadow:0 4px 20px rgba(0,0,0,.06),0 1px 4px rgba(0,0,0,.04);
  transition:box-shadow .2s,transform .2s;
}
.card:hover{box-shadow:0 8px 32px rgba(0,0,0,.1)}
[data-theme="dark"] .card{box-shadow:0 4px 20px rgba(0,0,0,.35)}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px}
@media(max-width:900px){.grid4{grid-template-columns:repeat(2,1fr)}.grid2{grid-template-columns:1fr}}
@media(max-width:900px){.grid4{grid-template-columns:repeat(2,1fr)}.grid2{grid-template-columns:1fr}}
@media(max-width:500px){.grid4{grid-template-columns:1fr}.grid3{grid-template-columns:1fr}}

/* ── GLOBAL MOBİL GRID DÜZELTME ── */
@media(max-width:600px){
  .grid2,.grid3,.grid4{grid-template-columns:1fr!important}
  [style*="grid-template-columns:repeat(3"]{grid-template-columns:1fr!important}
  [style*="grid-template-columns:repeat(4"]{grid-template-columns:1fr 1fr!important}
  [style*="grid-template-columns:1fr 1fr 1fr"]{grid-template-columns:1fr!important}
  [style*="grid-template-columns:1fr 1fr;gap"]{grid-template-columns:1fr!important}
  .form-row{grid-template-columns:1fr!important}
  .aging-grid{grid-template-columns:1fr 1fr!important}
  .today-grid{grid-template-columns:1fr 1fr 1fr}
  .asset-nums,.cdr-nums{grid-template-columns:1fr 1fr 1fr}
}

/* ── STAT CARDS ── */
.stat{
  border-radius:var(--radius);padding:20px 22px;
  position:relative;overflow:hidden;border:1px solid transparent;
  transition:transform .2s,box-shadow .2s;
}
.stat:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.2)}
.stat .lbl{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;color:var(--txt2);margin-bottom:10px;display:flex;align-items:center;gap:6px;font-weight:600}
.stat .val{font-size:2rem;font-weight:900;letter-spacing:-.04em;line-height:1;font-variant-numeric:tabular-nums}
.stat .sub{font-size:.74rem;color:var(--txt2);margin-top:8px;font-weight:500}
.stat .glow{position:absolute;width:80px;height:80px;border-radius:50%;filter:blur(28px);opacity:.4;right:-10px;top:-10px}
/* Rate cards — dark by default, lighten in light mode */
.rate-card{border-color:#3b82f622}
.rate-usd{background:linear-gradient(135deg,#1e3a5f,#162a47)}
.rate-eur{background:linear-gradient(135deg,#1a2f1a,#122012)}
.rate-gbp{background:linear-gradient(135deg,#2a2010,#1c1508)}
.rate-gold{background:linear-gradient(135deg,#271a08,#1c1205)}
.rate-usd .val,.rate-eur .val,.rate-gbp .val,.rate-gold .val{color:#fff}
.rate-usd .lbl,.rate-eur .lbl,.rate-gbp .lbl,.rate-gold .lbl{color:rgba(255,255,255,.7)}
:root:not([data-theme="dark"]) .rate-usd{background:linear-gradient(135deg,#e8f0ff,#d6e4ff);border-color:#3b82f630}
:root:not([data-theme="dark"]) .rate-eur{background:linear-gradient(135deg,#e8f9ef,#d4f5e2);border-color:#22c55e30}
:root:not([data-theme="dark"]) .rate-gbp{background:linear-gradient(135deg,#fff8e6,#fff0c4);border-color:#f59e0b30}
:root:not([data-theme="dark"]) .rate-gold{background:linear-gradient(135deg,#fff4e0,#ffe8b8);border-color:#f59e0b40}
:root:not([data-theme="dark"]) .rate-usd .val{color:#1e3a5f}
:root:not([data-theme="dark"]) .rate-eur .val{color:#1a5c2a}
:root:not([data-theme="dark"]) .rate-gbp .val,:root:not([data-theme="dark"]) .rate-gold .val{color:#7a4a00}
:root:not([data-theme="dark"]) .rate-usd .lbl,:root:not([data-theme="dark"]) .rate-eur .lbl,
:root:not([data-theme="dark"]) .rate-gbp .lbl,:root:not([data-theme="dark"]) .rate-gold .lbl{color:rgba(0,0,0,.55)}
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
.btn{
  padding:10px 20px;border-radius:12px;border:none;
  font-size:.84rem;font-weight:700;cursor:pointer;
  transition:transform .15s cubic-bezier(.34,1.56,.64,1),box-shadow .15s,filter .12s,background .15s;
  display:inline-flex;align-items:center;gap:6px;
  letter-spacing:.01em;font-family:inherit;
}
.btn:hover{transform:translateY(-1px)}
.btn:active{transform:scale(.96);filter:brightness(.92)}
.btn-primary{
  background:linear-gradient(135deg,#f0b90b,#e0a800);
  color:#1a1200;
  box-shadow:0 4px 14px rgba(240,185,11,.35),0 2px 4px rgba(0,0,0,.2);
}
.btn-primary:hover{box-shadow:0 6px 20px rgba(240,185,11,.45)}
.btn-primary:active{box-shadow:0 2px 8px rgba(240,185,11,.3);transform:translateY(1px) scale(.97)}
.btn-danger{
  background:linear-gradient(135deg,#ef4444,#dc2626);
  color:#fff;box-shadow:0 4px 14px rgba(239,68,68,.35);
}
.btn-danger:hover{box-shadow:0 6px 20px rgba(239,68,68,.45)}
.btn-ghost{
  background:var(--bg3);border:1.5px solid var(--border2);
  color:var(--txt2);box-shadow:none;
}
.btn-ghost:hover{border-color:var(--b2);color:var(--b2);background:var(--bg4)}
.btn-ghost:active{background:var(--bg4);transform:scale(.97)}
.btn-green{
  background:linear-gradient(135deg,#22c55e,#16a34a);
  color:#fff;box-shadow:0 4px 14px rgba(34,197,94,.3);
}
.btn-green:hover{box-shadow:0 6px 20px rgba(34,197,94,.4)}

.ledger-wrap{overflow-x:auto;border:1px solid var(--border);border-radius:var(--radius);
  box-shadow:0 1px 6px rgba(0,0,0,.04)}
table{width:100%;border-collapse:collapse;font-size:.83rem}
thead tr{background:var(--bg3);position:sticky;top:0;z-index:10}
th{padding:11px 12px;text-align:left;font-size:.72rem;font-weight:600;text-transform:uppercase;
   letter-spacing:.06em;color:var(--txt2);border-bottom:1px solid var(--border);white-space:nowrap;user-select:none}
th.sortable{cursor:pointer}
th.sortable:hover{color:var(--b2)}
th .sort-ico{margin-left:4px;opacity:.4}
td{padding:0;border-bottom:1px solid var(--border);vertical-align:middle}
td .cell{padding:10px 12px;display:flex;align-items:center;gap:6px;min-height:44px}
tbody tr:hover{background:rgba(0,122,255,.03)}
tbody tr.selected{background:#6366f10d}
tbody tr:last-child td{border-bottom:none}

/* Mobilde tablo → kart liste görünümü */
@media(max-width:768px){
  .ledger-wrap{border:none;border-radius:0;overflow-x:visible;box-shadow:none;background:transparent}
  table{display:block}
  thead{display:none}
  tbody{display:flex;flex-direction:column;gap:8px}
  tbody tr{display:flex;align-items:center;background:var(--bg2);border-radius:14px;
    border:1px solid var(--border);box-shadow:0 1px 6px rgba(0,0,0,.05);padding:12px 14px;
    gap:10px;cursor:pointer;transition:.12s;-webkit-tap-highlight-color:transparent}
  tbody tr:active{background:var(--bg3);transform:scale(.99)}
  tbody tr:last-child td{border-bottom:1px solid var(--border)}
  tbody tr.selected{background:#6366f108;border-color:#6366f140}
  td{padding:0;border:none;vertical-align:middle}
  td .cell{padding:0;min-height:auto}
  /* Gizlenecek sütunlar mobilde */
  td:nth-child(1){display:none} /* checkbox */
  td:nth-child(5){display:none} /* not */
  td:nth-child(6){display:none} /* aksiyon */
  /* Tarih küçük göster */
  td:nth-child(2) .cell{font-size:.72rem;color:var(--txt2);flex-direction:column;align-items:flex-start;gap:1px;min-width:52px}
  /* Tutar sağa */
  td:nth-child(5){margin-left:auto}
}

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
.f-input{width:100%;background:var(--bg3);border:1.5px solid transparent;color:var(--txt);
  padding:11px 14px;border-radius:11px;font-size:.92rem;outline:none;transition:.15s;font-family:inherit;
  -webkit-appearance:none;appearance:none;
  box-shadow:0 1px 3px rgba(0,0,0,.06) inset}
.f-input:focus{border-color:var(--b);background:var(--bg2);box-shadow:0 0 0 3px rgba(0,122,255,.12)}
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
  position:fixed;
  top:calc(54px + env(safe-area-inset-top,0px));
  right:0;bottom:0;width:360px;max-width:100vw;
  background:var(--bg2,#fff);border-left:1px solid var(--border2,#e5e5ea);
  z-index:499;display:flex;flex-direction:column;
  transform:translateX(100%);transition:transform .28s cubic-bezier(.4,0,.2,1);
  box-shadow:-12px 0 48px rgba(0,0,0,.22);
}
.notif-panel.open{transform:translateX(0)}
.notif-panel-head{
  display:flex;align-items:center;justify-content:space-between;
  padding:18px 20px 14px;border-bottom:1px solid var(--border);flex-shrink:0;
  background:var(--bg2);
}
.notif-panel-title{font-size:1rem;font-weight:800;color:var(--txt)}
.notif-panel-count{font-size:.75rem;color:var(--txt2);font-weight:500}
.notif-close-btn{
  width:32px;height:32px;border-radius:50%;border:1px solid var(--border2);
  background:var(--bg3);color:var(--txt2);font-size:.95rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;transition:.15s;flex-shrink:0;
}
.notif-close-btn:hover{background:var(--bg4);color:var(--txt)}
.notif-list{flex:1;overflow-y:auto;padding:12px 12px 80px}
.notif-item{
  display:flex;gap:12px;align-items:flex-start;
  padding:14px 14px;border-radius:14px;margin-bottom:8px;
  border:1px solid transparent;transition:.15s;cursor:default;
}
.notif-item.urgent{
  background:linear-gradient(135deg,#ef444415,#ef444408);
  border-color:#ef444435;
}
.notif-item.soon{
  background:linear-gradient(135deg,#f59e0b12,#f59e0b06);
  border-color:#f59e0b30;
}
.notif-item.normal{background:var(--bg2);border-color:var(--border)}
.notif-item-ico{
  font-size:1.5rem;flex-shrink:0;
  width:40px;height:40px;border-radius:10px;
  display:flex;align-items:center;justify-content:center;
  background:var(--bg3);
}
.notif-item.urgent .notif-item-ico{background:#ef444415}
.notif-item.soon .notif-item-ico{background:#f59e0b12}
.notif-item-body{flex:1;min-width:0;padding-top:2px}
.notif-item-title{font-size:.82rem;font-weight:700;color:var(--txt);margin-bottom:4px;line-height:1.3}
.notif-item.urgent .notif-item-title{color:#f87171}
.notif-item.soon .notif-item-title{color:#fbbf24}
.notif-item-msg{font-size:.77rem;color:var(--txt2);line-height:1.5;margin-bottom:6px}
.notif-item-days{
  display:inline-flex;align-items:center;gap:4px;
  font-size:.68rem;font-weight:700;padding:2px 8px;border-radius:6px;
  background:var(--bg3);color:var(--txt2);
}
.notif-item.urgent .notif-item-days{background:#ef444420;color:#f87171}
.notif-item.soon .notif-item-days{background:#f59e0b18;color:#fbbf24}
.notif-empty{text-align:center;padding:60px 24px;color:var(--txt2);font-size:.9rem}
.notif-empty-ico{font-size:3rem;margin-bottom:14px}
.notif-read{opacity:.55}
.notif-read .notif-item-title{opacity:.7}
.notif-section-lbl{
  font-size:.66rem;font-weight:800;text-transform:uppercase;letter-spacing:.1em;
  color:var(--txt2);padding:10px 4px 6px;opacity:.6;
}

/* ── TOP HEADER ─────────────────────────────────────────────── */
.top-header{
  position:fixed;top:0;left:0;right:0;z-index:9998;
  height:calc(54px + env(safe-area-inset-top,0px));
  padding-top:env(safe-area-inset-top,0px);
  background:rgba(17,18,20,.92);backdrop-filter:blur(20px) saturate(180%);
  -webkit-backdrop-filter:blur(20px) saturate(180%);
  border-bottom:1px solid rgba(255,255,255,.06);
  display:flex;align-items:center;justify-content:flex-end;
  padding-left:16px;padding-right:16px;flex-shrink:0;
}
[data-theme="light"] .top-header{background:rgba(255,255,255,.92);border-bottom:1px solid rgba(0,0,0,.08)}
@media(max-width:768px){.top-header{padding-left:16px;padding-right:16px;justify-content:space-between}}
.top-header-logo{font-size:.95rem;font-weight:800;display:none;align-items:center;gap:8px;color:var(--txt)}
@media(max-width:768px){
  .top-header-logo{display:flex}
  #hamburger-btn{display:flex!important}
}
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

/* ── HERO BALANCE CARD — Premium ────────────────────────────── */
.hero-card{
  background:linear-gradient(145deg,#050e22 0%,#0d1f3c 40%,#1a3a6b 80%,#0f2244 100%);
  border:1px solid rgba(99,160,255,.12);
  border-radius:28px;padding:24px 24px 20px;margin-bottom:16px;
  position:relative;overflow:hidden;
  box-shadow:0 20px 60px rgba(5,14,34,.7),0 4px 20px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.06);
}
.hero-card::before{
  content:'';position:absolute;top:-80px;right:-80px;width:320px;height:320px;border-radius:50%;
  background:radial-gradient(circle,rgba(99,160,255,.22) 0%,transparent 65%);
  animation:hero-glow 4s ease-in-out infinite;
}
.hero-card::after{
  content:'';position:absolute;bottom:-70px;left:-50px;width:250px;height:250px;border-radius:50%;
  background:radial-gradient(circle,rgba(52,199,89,.16) 0%,transparent 65%);
}
@keyframes hero-glow{0%,100%{opacity:.8;transform:scale(1)}50%{opacity:1;transform:scale(1.08)}}
.hero-top-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;position:relative}
.hero-greeting{font-size:.8rem;color:rgba(255,255,255,.45);font-weight:500;letter-spacing:.01em}
.hero-kirpi{font-size:1.8rem;line-height:1;user-select:none;
  animation:kirpi-walk-hero 1.8s ease-in-out infinite;display:inline-block}
@keyframes kirpi-walk-hero{
  0%,100%{transform:translateY(0) rotate(0deg)}
  15%    {transform:translateY(-4px) rotate(-6deg) scaleX(-1)}
  30%    {transform:translateY(0)   rotate(0deg)  scaleX(-1)}
  45%    {transform:translateY(-4px) rotate(6deg) scaleX(1)}
  60%    {transform:translateY(0)   rotate(0deg)  scaleX(1)}
  75%    {transform:translateY(-2px) rotate(-3deg) scaleX(1)}
}
.hero-kirpi.bounce{animation:kirpi-hero-pop .4s cubic-bezier(.34,1.56,.64,1)}
@keyframes kirpi-hero-pop{0%{transform:scale(1)}50%{transform:scale(1.4)}100%{transform:scale(1)}}
.hero-period-tabs{
  display:flex;gap:3px;background:rgba(255,255,255,.08);
  border-radius:10px;padding:3px;margin-bottom:10px;
  position:relative;width:fit-content;
  backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.1);
}
.hero-period-tab{padding:5px 14px;border-radius:8px;font-size:.7rem;font-weight:600;color:rgba(255,255,255,.4);cursor:pointer;transition:.2s;border:none;background:transparent;letter-spacing:.02em}
.hero-period-tab.active{background:rgba(255,255,255,.95);color:#0d1f3c;box-shadow:0 2px 8px rgba(0,0,0,.25)}
.hero-year-nav{display:none;align-items:center;gap:8px;margin-bottom:8px}
.hero-year-btn{width:26px;height:26px;border-radius:50%;border:none;background:rgba(255,255,255,.1);color:rgba(255,255,255,.7);font-size:.85rem;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.15s}
.hero-year-btn:hover{background:rgba(255,255,255,.2);color:#fff}
.hero-year-val{font-size:.82rem;font-weight:700;color:rgba(255,255,255,.88);min-width:38px;text-align:center}
.hero-bal-lbl{
  font-size:.58rem;text-transform:uppercase;letter-spacing:.18em;
  color:rgba(255,255,255,.35);margin-bottom:8px;font-weight:700;position:relative;
}
.hero-balance{
  font-size:2.6rem;font-weight:900;letter-spacing:-.05em;line-height:1;
  margin-bottom:6px;color:#fff;position:relative;
  text-shadow:0 0 40px rgba(99,160,255,.3),0 2px 12px rgba(0,0,0,.3);
  font-variant-numeric:tabular-nums;
}
.hero-net-sub{font-size:.72rem;color:rgba(255,255,255,.35);margin-bottom:18px;min-height:14px;position:relative}
.hero-my-row{display:flex;gap:8px;margin-bottom:12px;position:relative}
.hero-sel{
  background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);
  color:#fff;border-radius:10px;padding:7px 12px;font-size:.78rem;font-weight:600;
  cursor:pointer;outline:none;appearance:none;-webkit-appearance:none;font-family:inherit;
  backdrop-filter:blur(8px);
}
.hero-sel option{background:#0d1f3c;color:#fff}
.hero-chips{display:flex;gap:8px;flex-wrap:wrap;position:relative}
.hero-chip{
  display:flex;align-items:center;gap:5px;
  padding:7px 16px;border-radius:22px;font-size:.76rem;font-weight:700;
  cursor:pointer;transition:.2s;-webkit-tap-highlight-color:transparent;
  letter-spacing:.01em;
}
.hero-chip.gn{background:rgba(52,199,89,.2);color:#5edc80;border:1px solid rgba(52,199,89,.3);box-shadow:0 0 12px rgba(52,199,89,.1)}
.hero-chip.rd{background:rgba(255,59,48,.2);color:#ff7e78;border:1px solid rgba(255,59,48,.3);box-shadow:0 0 12px rgba(255,59,48,.1)}
.hero-chip.nt{background:rgba(255,255,255,.1);color:rgba(255,255,255,.85);border:1px solid rgba(255,255,255,.18)}
.hero-chip:hover{transform:translateY(-2px);filter:brightness(1.1)}
.hero-chip:active{transform:scale(.96);opacity:.8}

/* ── DASH SECTION CARDS ─────────────────────────────────────── */
.dash-section{
  background:var(--bg2);border:1px solid var(--border);
  border-radius:20px;margin-bottom:12px;overflow:hidden;
  box-shadow:0 4px 24px rgba(0,0,0,.08);
  transition:box-shadow .2s;
}
.dash-section:hover{box-shadow:0 6px 32px rgba(0,0,0,.12)}
.dash-section .s-header{padding:16px 18px;border-bottom:1px solid var(--border);border-radius:0}
.dash-section .s-body{padding:12px 14px 14px;margin-bottom:0;border-radius:0 0 20px 20px}
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
.tx-day-item{
  display:flex;align-items:center;gap:12px;padding:12px 16px;
  background:var(--bg2);border:1px solid var(--border);border-radius:16px;
  margin-bottom:8px;cursor:pointer;
  transition:transform .15s,box-shadow .15s,background .15s;
}
.tx-day-item:active{transform:scale(.98)}
.tx-day-item:hover{box-shadow:0 4px 16px rgba(0,0,0,.1);background:var(--bg3)}
.tx-day-item:last-child{margin-bottom:0}
.tx-day-icon{
  width:40px;height:40px;border-radius:12px;
  display:flex;align-items:center;justify-content:center;
  font-size:.9rem;font-weight:800;flex-shrink:0;
}
.tx-day-icon.gn{
  background:linear-gradient(135deg,#22c55e20,#16a34a15);
  border:1px solid #22c55e30;color:#22c55e;
  box-shadow:0 2px 8px rgba(34,197,94,.12);
}
.tx-day-icon.rd{
  background:linear-gradient(135deg,#ef444420,#dc262615);
  border:1px solid #ef444430;color:#ef4444;
  box-shadow:0 2px 8px rgba(239,68,68,.12);
}
.tx-day-info{flex:1;min-width:0}
.tx-day-cat{font-size:.84rem;font-weight:700;color:var(--txt);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;letter-spacing:-.01em}
.tx-day-desc{font-size:.72rem;color:var(--txt2);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tx-day-amt{font-size:.95rem;font-weight:800;flex-shrink:0;letter-spacing:-.02em}

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
@media(max-width:480px){.cc-total-row{grid-template-columns:1fr;gap:6px}}
.cc-total-cell{background:var(--bg2);border:1px solid var(--border);border-radius:11px;padding:10px 12px}
.cc-total-cell .ccl{font-size:.62rem;text-transform:uppercase;letter-spacing:.08em;color:var(--txt2);margin-bottom:3px;font-weight:600}
.cc-total-cell .ccv{font-size:.88rem;font-weight:800}
@media(max-width:480px){
  .cc-total-cell{display:flex;align-items:center;justify-content:space-between;padding:10px 14px}
  .cc-total-cell .ccl{margin-bottom:0;font-size:.7rem}
  .cc-total-cell .ccv{font-size:1rem}
}
.cc-item{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:13px 14px;margin-bottom:8px;transition:box-shadow .15s}
.cc-item:last-child{margin-bottom:0}
.cc-item:active{box-shadow:0 0 0 2px var(--b2)22}
.cc-item-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:9px}
.cc-item-logo{display:flex;align-items:center;gap:10px}
.cc-item-logo-info{min-width:0;flex:1}
.bank-logo-badge{width:38px;height:38px;border-radius:10px;flex-shrink:0;display:block;object-fit:cover}
.cc-bank{font-size:.85rem;font-weight:700;color:var(--txt);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cc-pct-badge{font-size:.66rem;font-weight:700;padding:3px 9px;border-radius:8px;flex-shrink:0}
.cc-pct-badge.ok{background:#34c75914;color:var(--g);border:1px solid #34c75928}
.cc-pct-badge.warn{background:#ff950014;color:var(--y);border:1px solid #ff950028}
.cc-pct-badge.high{background:#ff3b3014;color:var(--r);border:1px solid #ff3b3028}
.cc-prog-bg{background:var(--bg3);border-radius:6px;height:5px;overflow:hidden;margin-bottom:7px}
.cc-prog-fill{height:100%;border-radius:6px;transition:width .7s cubic-bezier(.4,0,.2,1)}
.cc-nums{display:flex;justify-content:space-between;font-size:.72rem;color:var(--txt2)}
.cc-nums strong{color:var(--txt);font-weight:600}
.empty-cc{text-align:center;padding:22px 16px;color:var(--txt2);font-size:.82rem;line-height:1.7}
.qd-btn{padding:5px 11px;border:1px solid var(--border2);border-radius:8px;font-size:.72rem;font-weight:600;color:var(--txt2);background:var(--bg3);cursor:pointer;transition:.15s;white-space:nowrap;font-family:inherit}
.qd-btn:hover{border-color:var(--b);color:var(--b)}
.qd-btn.qd-active{background:var(--b);color:#fff;border-color:var(--b)}

/* ── MOBILE NAV ENHANCEMENTS ────────────────────────────────── */
.nl-desktop{}
.nl-menu{display:none}
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
.page.active{animation:page-in .22s ease-out forwards}

/* ── TAP FEEDBACK ────────────────────────────────────────────── */
.tappable{cursor:pointer;-webkit-tap-highlight-color:transparent;transition:transform .12s,opacity .12s;touch-action:manipulation}
.tappable:active{transform:scale(.96);opacity:.85}
button{touch-action:manipulation;-webkit-tap-highlight-color:transparent}
a,div[onclick],span[onclick]{-webkit-tap-highlight-color:transparent}
.btn:active{transform:scale(.97);opacity:.9}
.btn-primary:active,.btn-green:active,.btn-danger:active{opacity:1}
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

/* ── ACCOUNTS PAGE ───────────────────────────────────────────── */
.acc-type-chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:6px}
.acc-type-chip{padding:7px 14px;border-radius:20px;border:1.5px solid var(--border2);background:var(--bg3);color:var(--txt2);font-size:.78rem;font-weight:700;cursor:pointer;transition:.15s;-webkit-tap-highlight-color:transparent;white-space:nowrap}
.acc-type-chip.active{background:var(--b);border-color:var(--b);color:#fff}
.color-dot{width:26px;height:26px;border-radius:50%;border:3px solid transparent;cursor:pointer;transition:.12s;-webkit-tap-highlight-color:transparent;flex-shrink:0}
.color-dot.active{box-shadow:0 0 0 2px var(--bg2),0 0 0 4px var(--txt)}
.acc-list-item{background:var(--bg2);border:1px solid var(--border);border-radius:16px;padding:14px 16px;margin-bottom:10px;position:relative;overflow:hidden}
.acc-list-item::before{content:'';position:absolute;left:0;top:0;bottom:0;width:4px;border-radius:16px 0 0 16px}
.acc-list-top{display:flex;align-items:flex-start;gap:10px}
.acc-list-dot{width:36px;height:36px;border-radius:10px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:1rem;color:#fff}
.acc-list-info{flex:1;min-width:0}
.acc-list-bank{font-size:.9rem;font-weight:800;color:var(--txt)}
.acc-list-name{font-size:.75rem;color:var(--txt2);margin-top:1px}
.acc-type-tag{font-size:.62rem;padding:2px 7px;border-radius:8px;font-weight:700;margin-top:4px;display:inline-block}
.acc-balance-row{display:flex;justify-content:space-between;align-items:flex-end;margin-top:10px}
.acc-balance-main{font-size:1.15rem;font-weight:800;letter-spacing:-.02em}
.acc-balance-lbl{font-size:.65rem;color:var(--txt2);margin-top:1px}
.acc-avail-lbl{font-size:.7rem;color:var(--txt2);text-align:right}
.acc-avail-val{font-size:.85rem;font-weight:700;text-align:right}
.acc-prog-wrap{background:var(--bg3);border-radius:4px;height:5px;width:100%;margin-top:8px;overflow:hidden}
.acc-prog-fill{border-radius:4px;height:5px;transition:width .4s}
.acc-actions{display:flex;gap:6px;margin-top:10px;border-top:1px solid var(--border);padding-top:10px}
.acc-act-btn{flex:1;padding:7px;border:none;border-radius:9px;font-size:.75rem;font-weight:700;cursor:pointer;transition:.1s;-webkit-tap-highlight-color:transparent}
.acc-act-btn:active{opacity:.75}
</style>
<script>
(function(){var t=localStorage.getItem('theme')||'dark';document.documentElement.setAttribute('data-theme',t);})();
</script>
<!-- Google Translate -->
<style>
.goog-te-banner-frame,.goog-te-balloon-frame,.goog-te-menu-frame{display:none!important}
body{top:0!important}
.goog-logo-link,.goog-te-gadget span{display:none!important}
.goog-te-gadget{font-size:0!important}
#google_translate_element{display:none}
</style>
<script src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit" async></script>
</head>
<body>
<div id="google_translate_element"></div>

<!-- ── SPLASH SCREEN ── -->
<div id="splash-screen">
  <div class="splash-center">
    <div class="splash-icon-wrap">🦔</div>
    <div class="splash-appname">Kirpi</div>
    <div class="splash-apptag">Nakit akışın, cebinde.</div>
  </div>
  <div class="splash-bar"></div>
</div>

<div class="shell">

<!-- ── SIDEBAR NAV ── -->
<nav>
  <div class="nav-logo" onclick="goPage('dashboard',document.querySelector('[data-page=dashboard]'))" style="cursor:pointer">
    <div class="brand">
      <div class="kirpi-walk-wrap"><img src="/icon.svg" class="kirpi-walk-img" style="width:32px;height:32px;border-radius:8px"> </div>Kirpi
    </div>
    <div class="sub">Gelir · Gider · Yatırım</div>
  </div>
  <div class="nav-links">
    <div class="nav-sect">Ana</div>
    <div class="nl active" data-page="dashboard" onclick="goPage('dashboard',this)">
      <span class="ico">🏠</span>Ana
    </div>
    <div class="nl" data-page="ledger" onclick="goPage('ledger',this)">
      <span class="ico">📋</span>İşlemler
    </div>
    <div class="nl nl-add" data-page="add" onclick="goPage('add',this)">
      <span class="ico">➕</span>Ekle
    </div>
    <div class="nl" data-page="todos" onclick="goPage('todos',this)">
      <span class="ico">✅</span>Görevler
    </div>
    <div class="nl nl-menu" onclick="openMoreSheet()">
      <span class="ico">☰</span>Menü
    </div>
    <div class="nl nl-more nl-desktop-only" onclick="openMoreSheet()">
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
    <div class="nl nl-desktop" data-page="hesaplar" onclick="goPage('hesaplar',this)">
      <span class="ico">💳</span>Kartlar & Hesaplar
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
  <div style="display:flex;align-items:center;border-top:1px solid var(--border)">
    <div class="nav-bottom" onclick="goPage('settings',document.querySelector('[data-page=settings]'))" style="flex:1;border-top:none">
      <div id="sidebar-profile-avatar" style="width:36px;height:36px;border-radius:50%;background:var(--bg3);border:1.5px solid var(--border2);flex-shrink:0;overflow:hidden;display:flex;align-items:center;justify-content:center;font-size:1rem"></div>
      <div style="min-width:0">
        <div id="sidebar-profile-name" style="font-size:.8rem;font-weight:700;color:var(--txt);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">—</div>
        <div style="font-size:.68rem;color:var(--txt2);opacity:.55">Ayarlar ›</div>
      </div>
    </div>
    <button id="dark-mode-btn" onclick="toggleDarkMode()" title="Tema değiştir"
      style="flex-shrink:0;border:none;background:transparent;cursor:pointer;font-size:1.2rem;padding:10px 14px;color:var(--txt2);transition:.15s;border-radius:10px"
      onmouseenter="this.style.background='var(--bg3)'" onmouseleave="this.style.background='transparent'">🌙</button>
  </div>
</nav>

<!-- ── MORE SHEET (mobile) ── -->
<div class="more-backdrop" id="more-backdrop" onclick="closeMoreSheet()"></div>
<div class="more-sheet" id="more-sheet">
  <div class="more-sheet-handle" id="more-sheet-handle"></div>

  <div class="more-sect-label">Araçlar</div>
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
    <div class="more-tile" onclick="goPageFromSheet('hesaplar')">
      <div class="mt-ico">🏦</div><div class="mt-lbl">Hesaplar</div>
    </div>
    <div class="more-tile" onclick="goPageFromSheet('import')">
      <div class="mt-ico">📂</div><div class="mt-lbl">İçe Aktar</div>
    </div>
    <div class="more-tile" onclick="toggleDarkMode();closeMoreSheet()">
      <div class="mt-ico" id="dark-mode-sheet-ico">🌙</div><div class="mt-lbl" id="dark-mode-sheet-lbl">Karanlık</div>
    </div>
  </div>

  <div class="more-sect-label" data-sirket style="display:none">Firma</div>
  <div class="more-grid" id="more-sirket-grid" style="display:none">
    <div class="more-tile" onclick="goPageFromSheet('supplier')">
      <div class="mt-ico">🏭</div><div class="mt-lbl">Tedarikçi</div>
    </div>
    <div class="more-tile" onclick="goPageFromSheet('assets')">
      <div class="mt-ico">🚗</div><div class="mt-lbl">Kıymetler</div>
    </div>
    <div class="more-tile" onclick="goPageFromSheet('cardreport')">
      <div class="mt-ico">📊</div><div class="mt-lbl">Kart Raporu</div>
    </div>
  </div>

  <div class="more-grid" style="margin-top:4px">
    <div class="more-tile" onclick="goPageFromSheet('settings')" style="grid-column:1/-1;flex-direction:row;justify-content:center;gap:10px;padding:12px">
      <div class="mt-ico" style="font-size:1.2rem">⚙️</div><div class="mt-lbl" style="font-size:.8rem">Ayarlar</div>
    </div>
  </div>
  <div style="height:env(safe-area-inset-bottom,8px)"></div>
</div>

<!-- ── MAIN ── -->
<div class="main">

<!-- TOP HEADER -->
<div class="top-header">
  <div style="display:flex;align-items:center;gap:12px">
    <button id="hamburger-btn" onclick="openMoreSheet()" style="display:none;flex-direction:column;gap:4.5px;background:none;border:none;cursor:pointer;padding:4px;border-radius:8px;-webkit-tap-highlight-color:transparent" aria-label="Menü">
      <span style="display:block;width:20px;height:2px;background:var(--txt);border-radius:2px;transition:.2s"></span>
      <span style="display:block;width:16px;height:2px;background:var(--txt);border-radius:2px;transition:.2s"></span>
      <span style="display:block;width:20px;height:2px;background:var(--txt);border-radius:2px;transition:.2s"></span>
    </button>
    <div class="top-header-logo tappable" onclick="openMoreSheet()" style="cursor:pointer">🦔 <span style="color:var(--b);font-weight:900">Kirpi Finans</span></div>
  </div>
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
        <!-- Abonelik satırı — JS tarafından doldurulur -->
        <div id="udrop-sub-row" style="padding:8px 8px 0"></div>
        <div class="udrop-divider" style="margin-top:4px"></div>
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
    <div>
      <span class="notif-panel-title">🔔 Bildirimler</span>
      <div id="notif-panel-count" class="notif-panel-count" style="margin-top:2px">Yükleniyor…</div>
    </div>
    <button class="notif-close-btn" onclick="closeNotifPanel()">✕</button>
  </div>
  <!-- Tümünü Okundu İşaretle -->
  <div id="notif-mark-all" style="display:none;padding:8px 16px;border-bottom:1px solid var(--border)">
    <button onclick="_markAllRead()" style="width:100%;padding:8px;background:var(--bg3);border:1px solid var(--border2);border-radius:8px;color:var(--b2);font-size:.78rem;font-weight:600;cursor:pointer">
      ✓ Tümünü Okundu İşaretle
    </button>
  </div>
  <div class="notif-list" id="notif-list">
    <div class="notif-empty"><div class="notif-empty-ico">🦔</div>Yükleniyor…</div>
  </div>
</div>

<!-- DASHBOARD -->
<div class="page active" id="page-dashboard">

  <!-- Yenile butonu — veri gelmezse görünür -->
  <div id="dash-retry-bar" style="display:none;background:#ff3b3014;border:1px solid #ff3b3030;border-radius:10px;padding:10px 14px;margin-bottom:12px;display:none;align-items:center;gap:10px;font-size:.83rem;color:var(--r)">
    <span>⚠️ Veriler yüklenemedi.</span>
    <button onclick="loadDashboard();this.parentElement.style.display='none'" style="margin-left:auto;padding:5px 14px;background:var(--b);color:#fff;border:none;border-radius:7px;font-size:.8rem;cursor:pointer;font-weight:700">↻ Yenile</button>
  </div>

  <!-- ── HERO BALANCE ── -->
  <div class="hero-card">
    <div class="hero-top-row">
      <div class="hero-greeting" id="hero-greeting">Merhaba __USER_DISPLAY__ 👋</div>
      <div class="hero-kirpi" id="hero-kirpi" title="Günün durumu">🦔</div>
    </div>
    <div class="hero-my-row">
      <select id="hero-month-sel" class="hero-sel" onchange="heroMonthYearChange()"></select>
      <select id="hero-year-sel" class="hero-sel" onchange="heroMonthYearChange()"></select>
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

  <!-- ── GÜNÜN GELİRLERİ & GİDERLERİ — hero'nun hemen altında ── -->
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

  <div class="today-net-row" id="today-net-row" style="display:none">
    <div class="tnr-label">Günün Bakiyesi</div>
    <div class="tnr-value" id="today-net">—</div>
  </div>

  <!-- ── ONBOARDING ── -->
  <div id="onboarding-card" style="display:none;background:linear-gradient(135deg,#6366f1,#a855f7);border-radius:20px;padding:24px;margin-bottom:16px;color:#fff">
    <div style="font-size:2rem;margin-bottom:10px">🦔</div>
    <div style="font-size:1.1rem;font-weight:900;margin-bottom:6px">Kirpi'ye Hoş Geldin!</div>
    <div style="font-size:.84rem;opacity:.85;margin-bottom:18px;line-height:1.6">Finansal kontrolü ele geçirmek için 3 adım:</div>
    <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:18px">
      <div class="ob-step" id="ob-step-1" onclick="goPage('add',document.querySelector('[data-page=add]'))">
        <div class="ob-num">1</div>
        <div>
          <div style="font-size:.86rem;font-weight:700">İlk işlemini ekle</div>
          <div style="font-size:.74rem;opacity:.7">Gelir veya gider gir</div>
        </div>
        <div style="margin-left:auto;opacity:.6">›</div>
      </div>
      <div class="ob-step" id="ob-step-2" onclick="goPage('budget',document.querySelector('[data-page=budget]'))">
        <div class="ob-num">2</div>
        <div>
          <div style="font-size:.86rem;font-weight:700">Bütçe belirle</div>
          <div style="font-size:.74rem;opacity:.7">Kategori limitleri koy</div>
        </div>
        <div style="margin-left:auto;opacity:.6">›</div>
      </div>
      <div class="ob-step" id="ob-step-3" onclick="goPage('recurring',document.querySelector('[data-page=recurring]'))">
        <div class="ob-num">3</div>
        <div>
          <div style="font-size:.86rem;font-weight:700">Düzenli işlemleri ekle</div>
          <div style="font-size:.74rem;opacity:.7">Kira, maaş, abonelikler</div>
        </div>
        <div style="margin-left:auto;opacity:.6">›</div>
      </div>
    </div>
    <button onclick="document.getElementById('onboarding-card').style.display='none'"
      style="background:rgba(255,255,255,.2);border:1.5px solid rgba(255,255,255,.3);color:#fff;border-radius:10px;padding:8px 18px;font-size:.82rem;font-weight:700;cursor:pointer">
      Kapat
    </button>
  </div>

  <!-- ── HATIRLATICILAR ── -->
  <div id="reminders-card" style="display:none;background:var(--bg2);border:1.5px solid #007aff30;border-radius:16px;padding:16px 18px;margin-bottom:12px">
    <div style="font-size:.7rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--b);margin-bottom:10px">🔔 Yaklaşan Ödemeler</div>
    <div id="reminders-list"></div>
  </div>

  <!-- ── INSIGHTS ── -->
  <div id="insights-section" style="display:none">

    <!-- Skor Kartı -->
    <div id="score-card" style="background:var(--bg2);border:1px solid var(--border);border-radius:16px;padding:16px 18px;margin-bottom:12px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
        <div style="font-size:.7rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--txt2)">Aylık Finansal Skor</div>
        <div id="ins-emoji" style="font-size:1.1rem"></div>
      </div>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
        <div style="flex:1;height:8px;background:var(--bg3);border-radius:4px;overflow:hidden">
          <div id="ins-score-bar" style="height:100%;border-radius:4px;background:linear-gradient(90deg,#34c759,#007aff);transition:width .8s cubic-bezier(.4,0,.2,1);width:0%"></div>
        </div>
        <div id="ins-score-val" style="font-size:1.1rem;font-weight:900;color:var(--txt);min-width:40px;text-align:right">—</div>
      </div>
      <div id="ins-msg" style="font-size:.82rem;color:var(--txt2);line-height:1.5"></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px">
        <div style="background:var(--bg3);border-radius:10px;padding:10px 12px">
          <div style="font-size:.65rem;color:var(--txt2);font-weight:700;text-transform:uppercase;margin-bottom:3px">Gelir Değişimi</div>
          <div id="ins-gelir-chg" style="font-size:.92rem;font-weight:800">—</div>
        </div>
        <div style="background:var(--bg3);border-radius:10px;padding:10px 12px">
          <div style="font-size:.65rem;color:var(--txt2);font-weight:700;text-transform:uppercase;margin-bottom:3px">Gider Değişimi</div>
          <div id="ins-gider-chg" style="font-size:.92rem;font-weight:800">—</div>
        </div>
      </div>
    </div>

    <!-- Anomali -->
    <div id="anomaly-card" style="display:none;background:var(--bg2);border:1.5px solid #ff950030;border-radius:16px;padding:16px 18px;margin-bottom:12px">
      <div style="font-size:.7rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:#ff9500;margin-bottom:10px">⚠️ Dikkat — Artan Harcamalar</div>
      <div id="anomaly-list"></div>
    </div>

    <!-- Finansal Pozisyon Kartları — 3 kart -->
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:12px">
      <!-- Net Likidite -->
      <div onclick="showLiquidityDetail()" style="background:linear-gradient(135deg,#0d2118,#0a1a12);border:1px solid #22c55e30;border-radius:16px;padding:14px;cursor:pointer;transition:.15s" onmouseenter="this.style.borderColor='#22c55e60'" onmouseleave="this.style.borderColor='#22c55e30'">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px">
          <div style="font-size:.55rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:rgba(255,255,255,.45)">💧 Net Likidite</div>
          <div style="font-size:.55rem;color:rgba(255,255,255,.25)">›</div>
        </div>
        <div id="ins-liquidity" style="font-size:1.1rem;font-weight:900;color:#4ade80">—</div>
        <div style="font-size:.62rem;color:rgba(255,255,255,.3);margin-top:3px">Hesap − Kart</div>
        <div id="ins-burn" style="font-size:.62rem;color:rgba(255,255,255,.3);margin-top:2px"></div>
      </div>
      <!-- Kullanılabilir Nakit (bu ay gelir - gider - asgari ödemeler) -->
      <div style="background:linear-gradient(135deg,#1a1300,#120e00);border:1px solid #f59e0b30;border-radius:16px;padding:14px">
        <div style="font-size:.55rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:rgba(255,255,255,.45);margin-bottom:5px">💵 Kullanılabilir</div>
        <div id="ins-kullanilabilir" style="font-size:1.1rem;font-weight:900;color:#fbbf24">—</div>
        <div style="font-size:.62rem;color:rgba(255,255,255,.3);margin-top:3px">Net − Asgari Ödemeler</div>
        <div id="ins-asgari" style="font-size:.62rem;color:rgba(255,255,255,.3);margin-top:2px"></div>
      </div>
      <!-- Net Varlık -->
      <div style="background:linear-gradient(135deg,#1e2845,#161c33);border:1px solid #6366f133;border-radius:16px;padding:14px">
        <div style="font-size:.55rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:rgba(255,255,255,.45);margin-bottom:5px">📊 Net Varlık</div>
        <div id="ins-networth" style="font-size:1.1rem;font-weight:900;color:#818cf8">—</div>
        <div style="font-size:.62rem;color:rgba(255,255,255,.3);margin-top:3px">Hesap+Yatırım−Borç</div>
        <div id="ins-days" style="font-size:.62rem;color:rgba(255,255,255,.3);margin-top:2px"></div>
      </div>
    </div>
    <!-- Kart Özeti Şeridi -->
    <div id="ins-card-strip" style="display:none;background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:10px 14px;margin-bottom:12px;font-size:.78rem">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
        <div style="color:var(--txt2)">💳 Kart borcu: <span id="ins-kart-borcu" style="font-weight:700;color:var(--r)">—</span></div>
        <div style="color:var(--txt2)">Asgari ödeme: <span id="ins-kart-asgari" style="font-weight:700;color:var(--y)">—</span></div>
        <div onclick="showAvailableLimitModal()" style="color:var(--txt2);cursor:pointer">🟢 Kullanılabilir limit: <span id="ins-kart-limit" style="font-weight:700;color:var(--g)">—</span> <span style="font-size:.65rem;opacity:.6">›</span></div>
        <button onclick="goPage('hesaplar',document.querySelector('[data-page=hesaplar]'))" style="background:var(--b);color:#fff;border:none;border-radius:8px;padding:4px 12px;font-size:.72rem;cursor:pointer;font-weight:600">Ödeme Yap →</button>
      </div>
    </div>

  </div>

  <!-- ── LİMİTLER ── -->
  <div class="dash-section">
    <div class="s-header" onclick="toggleSection('cc')">
      <div class="sh-left"><span class="sh-dot pp"></span>Limitler</div>
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

  <!-- ── GRAFİKLER ── -->
  <div class="dash-section" id="charts-section">
    <div class="s-header" onclick="toggleSection('charts')">
      <div class="sh-left"><span class="sh-dot" style="background:var(--b2)"></span>Aylık Analiz</div>
      <span class="sh-chevron" id="chevron-charts">▾</span>
    </div>
    <div class="s-body" id="sec-charts">

      <!-- Bar Chart -->
      <div style="margin-bottom:20px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
          <div class="chart-lbl">Aylık Gelir / Gider</div>
          <div style="display:flex;gap:14px;font-size:.72rem;color:var(--txt2)">
            <span><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:#30d15870;margin-right:4px"></span>Gelir</span>
            <span><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:#ff453a70;margin-right:4px"></span>Gider</span>
          </div>
        </div>
        <div class="chart-wrap" style="height:220px">
          <canvas id="barChart" style="height:220px"></canvas>
        </div>
        <div style="font-size:.72rem;color:var(--txt2);text-align:center;margin-top:6px">Bir aya tıkla → o ayın işlemlerini gör</div>
      </div>

      <!-- Donut Chart -->
      <div>
        <div class="chart-lbl">Bu Dönem Gider Dağılımı</div>
        <div class="chart-wrap" style="height:220px">
          <canvas id="donut" style="height:220px"></canvas>
        </div>
      </div>

    </div>
  </div>

  <!-- hidden elements needed by JS -->
  <div style="display:none">
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
  <!-- Aktif profil banner -->
  <div id="ledger-profile-banner" style="display:flex;align-items:center;gap:8px;background:var(--bg3);border:1px solid var(--border2);border-radius:10px;padding:8px 14px;margin-bottom:10px;font-size:.8rem">
    <span id="ledger-profile-dot" style="width:8px;height:8px;border-radius:50%;flex-shrink:0;background:#6366f1"></span>
    <span style="color:var(--txt2)">Görüntülenen profil:</span>
    <span id="ledger-profile-name" style="font-weight:700;color:var(--txt)">—</span>
    <span id="ledger-profile-type" style="font-size:.7rem;color:var(--txt2);padding:2px 8px;background:var(--bg4);border-radius:6px;margin-left:2px"></span>
  </div>
  <div class="top-row">
    <div>
      <div class="page-title">İşlemler</div>
      <div class="page-sub">Tüm gelir ve gider hareketlerin</div>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <button class="btn btn-ghost" id="del-sel-btn" onclick="bulkDelete()" style="display:none">🗑 Seçilenleri Sil</button>
      <button class="btn btn-primary" onclick="goPage('add',document.querySelector('[data-page=add]'))">+ Yeni Satır</button>
    </div>
  </div>

  <!-- Filtre Paneli — Temiz & Premium -->
  <div style="background:var(--bg2);border:1px solid var(--border);border-radius:16px;padding:14px 16px;margin-bottom:12px">

    <!-- Arama -->
    <div style="position:relative;margin-bottom:12px">
      <span style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--txt2);font-size:.9rem;pointer-events:none">🔍</span>
      <input id="ledger-search" oninput="filterLedger()" placeholder="İşlem ara…"
        style="width:100%;background:var(--bg3);border:1px solid var(--border2);color:var(--txt);padding:10px 12px 10px 36px;border-radius:10px;font-size:.88rem;outline:none;font-family:inherit">
    </div>

    <!-- Tür pilleri + Yıl + Kategori -->
    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
      <!-- Tür seçimi: pill butonlar -->
      <div style="display:flex;gap:4px;background:var(--bg3);border-radius:9px;padding:3px;flex-shrink:0" id="type-pill-group">
        <button onclick="setTypePill('')"    id="pill-all"    class="type-pill active" style="padding:5px 14px;border:none;border-radius:7px;font-size:.78rem;font-weight:600;cursor:pointer;transition:.15s;background:#fff;color:var(--txt);box-shadow:0 1px 4px rgba(0,0,0,.1)">Tümü</button>
        <button onclick="setTypePill('gelir')" id="pill-gelir" class="type-pill"       style="padding:5px 14px;border:none;border-radius:7px;font-size:.78rem;font-weight:600;cursor:pointer;transition:.15s;background:transparent;color:var(--txt2)">↑ Gelir</button>
        <button onclick="setTypePill('gider')" id="pill-gider" class="type-pill"       style="padding:5px 14px;border:none;border-radius:7px;font-size:.78rem;font-weight:600;cursor:pointer;transition:.15s;background:transparent;color:var(--txt2)">↓ Gider</button>
      </div>

      <!-- Gizli select (filterLedger için gerekli) -->
      <select id="f-type" style="display:none" onchange="filterLedger()">
        <option value="">Tümü</option><option value="gelir">Gelir</option><option value="gider">Gider</option>
      </select>

      <!-- Kategori -->
      <select id="ledger-f-cat" onchange="filterLedger()"
        style="flex:1;min-width:110px;background:var(--bg3);border:1px solid var(--border2);color:var(--txt2);padding:7px 10px;border-radius:9px;font-size:.8rem;outline:none">
        <option value="">Tüm Kategoriler</option>
      </select>

      <!-- Yıl -->
      <select id="f-year" onchange="onYearFilterChange()"
        style="background:var(--bg3);border:1px solid var(--border2);color:var(--txt2);padding:7px 10px;border-radius:9px;font-size:.8rem;outline:none;flex-shrink:0"></select>

      <!-- Export ikonları -->
      <div style="display:flex;gap:4px;flex-shrink:0;margin-left:auto">
        <button onclick="exportCsv()" title="CSV İndir" style="width:32px;height:32px;border:1px solid var(--border2);background:var(--bg3);color:var(--txt2);border-radius:8px;cursor:pointer;font-size:.8rem">⬇</button>
        <button onclick="exportPDFWithTheme()" title="PDF Rapor" style="width:32px;height:32px;border:1px solid var(--border2);background:var(--bg3);color:var(--txt2);border-radius:8px;cursor:pointer;font-size:.8rem">📄</button>
      </div>
    </div>

    <!-- Hızlı tarih filtreleri -->
    <div style="margin-top:10px">
      <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:7px">
        <button class="qd-btn" id="qd-dun" onclick="setQuickDate('dun')">Dün</button>
        <button class="qd-btn" id="qd-bugun" onclick="setQuickDate('bugun')">Bugün</button>
        <button class="qd-btn" id="qd-yarin" onclick="setQuickDate('yarin')">Yarın</button>
        <div style="width:1px;background:var(--border);margin:0 2px;align-self:stretch"></div>
        <button class="qd-btn" id="qd-gecen_ay" onclick="setQuickDate('gecen_ay')">Geçen Ay</button>
        <button class="qd-btn" id="qd-bu_ay" onclick="setQuickDate('bu_ay')">Bu Ay</button>
        <button class="qd-btn" id="qd-gelecek_ay" onclick="setQuickDate('gelecek_ay')">Gelecek Ay</button>
        <div style="width:1px;background:var(--border);margin:0 2px;align-self:stretch"></div>
        <button class="qd-btn" id="qd-gecen_yil" onclick="setQuickDate('gecen_yil')">Geçen Yıl</button>
        <button class="qd-btn" id="qd-bu_yil" onclick="setQuickDate('bu_yil')">Bu Yıl</button>
        <button class="qd-btn" id="qd-gelecek_yil" onclick="setQuickDate('gelecek_yil')">Gelecek Yıl</button>
      </div>
      <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
        <span style="font-size:.72rem;color:var(--txt2)">📅</span>
        <input type="date" id="f-date-from" onchange="onManualDateChange();filterLedger()"
          style="background:var(--bg3);border:1px solid var(--border2);color:var(--txt);padding:5px 8px;border-radius:8px;font-size:.78rem;outline:none">
        <span style="color:var(--txt2);font-size:.78rem">—</span>
        <input type="date" id="f-date-to" onchange="onManualDateChange();filterLedger()"
          style="background:var(--bg3);border:1px solid var(--border2);color:var(--txt);padding:5px 8px;border-radius:8px;font-size:.78rem;outline:none">
        <button onclick="clearDateRange()" style="font-size:.72rem;color:var(--r);background:none;border:none;cursor:pointer;padding:2px 6px">✕ Temizle</button>
      </div>
    </div>
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
          <th class="sortable" onclick="sortBy('description')">Açıklama <span class="sort-ico" id="sort-description">↕</span></th>
          <th style="min-width:110px">Ödeme Yöntemi</th>
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
  <div class="page-title">Gider / Gelir Ekle</div>
  <div id="add-profile-banner" style="display:flex;align-items:center;gap:6px;background:var(--bg3);border:1px solid var(--border2);border-radius:8px;padding:7px 12px;margin-bottom:12px;font-size:.78rem">
    <span id="add-profile-dot" style="width:7px;height:7px;border-radius:50%;flex-shrink:0;background:#6366f1"></span>
    <span style="color:var(--txt2)">Kaydedilecek profil:</span>
    <span id="add-profile-name" style="font-weight:700;color:var(--txt)">—</span>
    <span id="add-profile-type-badge" style="font-size:.68rem;color:var(--txt2);padding:1px 6px;background:var(--bg4);border-radius:4px;margin-left:2px"></span>
  </div>
  <div class="page-sub">Harcama veya gelir gir, ödeme yöntemini seç</div>

  <div class="card" style="max-width:520px">
    <div class="type-tabs">
      <button class="type-tab tr" id="tab-r" onclick="setTab('gider')">📉  Gider</button>
      <button class="type-tab" id="tab-g" onclick="setTab('gelir')">📈  Gelir</button>
      <button class="type-tab" id="tab-t" onclick="setTab('transfer')">↔️  Transfer</button>
    </div>

    <!-- GIDER / GELİR formu -->
    <div id="f-normal-form">
      <div class="form-row">
        <div><label>Tutar (₺)</label><input class="f-input" type="text" inputmode="decimal" data-num id="f-amount" placeholder="0,00"></div>
        <div><label>Tarih</label><input class="f-input" type="date" id="f-date"></div>
      </div>
      <div style="margin-bottom:12px"><label>Kategori</label><select class="f-input" id="f-cat"></select></div>
      <div style="margin-bottom:14px"><label>Açıklama</label><input class="f-input" type="text" id="f-desc" placeholder="örn. Market alışverişi"></div>

      <!-- ÖDEME YÖNTEMİ — sadece gider için -->
      <div id="f-pay-section" style="margin-bottom:16px">
        <label style="margin-bottom:8px;display:block">Ödeme Yöntemi</label>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px" id="f-pay-chips">
          <button type="button" class="pay-chip active" data-ptype="nakit" onclick="selectPayType(this)">💵 Nakit</button>
          <button type="button" class="pay-chip" data-ptype="banka_kart" onclick="selectPayType(this)">🏧 Banka Kartı</button>
          <button type="button" class="pay-chip" data-ptype="kredi_kart" onclick="selectPayType(this)">💳 Kredi Kartı</button>
          <button type="button" class="pay-chip" data-ptype="yemek_kart" onclick="selectPayType(this)">🍽️ Yemek Kartı</button>
          <button type="button" class="pay-chip" data-ptype="kmh" onclick="selectPayType(this)">🔄 KMH</button>
        </div>
        <div id="f-account-row" style="display:none">
          <label style="font-size:.78rem;color:var(--txt2);margin-bottom:4px;display:block">🏦 Hangi Hesaptan?</label>
          <select class="f-input" id="f-account"><option value="">— Hesap seçin —</option></select>
        </div>
        <div id="f-card-row" style="display:none">
          <label style="font-size:.78rem;color:var(--txt2);margin-bottom:4px;display:block" id="f-card-label">💳 Hangi Kartla?</label>
          <select class="f-input" id="f-card"><option value="">— Kart seçin —</option></select>
        </div>
      </div>

      <!-- GELİR için hesap seçici -->
      <div id="f-income-dest" style="display:none;margin-bottom:12px">
        <label>🏦 Hangi Hesaba Geldi?</label>
        <select class="f-input" id="f-income-account"><option value="">— Belirtme (Nakit) —</option></select>
      </div>
      <!-- GELİR: Kart iadesi -->
      <div id="f-income-refund" style="display:none;margin-bottom:16px">
        <label style="display:flex;align-items:center;gap:8px;cursor:pointer;margin-bottom:8px">
          <input type="checkbox" id="f-refund-check" onchange="toggleRefundCard(this.checked)" style="width:16px;height:16px;accent-color:var(--b)">
          <span style="font-size:.85rem;color:var(--txt)">💳 Kart iadesi — kart borcundan düşsün</span>
        </label>
        <div id="f-refund-card-row" style="display:none">
          <select class="f-input" id="f-refund-card"><option value="">— Kart seçin —</option></select>
        </div>
      </div>

      <button class="btn btn-danger" id="add-btn" style="width:100%;padding:13px" onclick="addTx()">Kaydet</button>
    </div>

    <!-- TRANSFER formu -->
    <div id="f-transfer-form" style="display:none">
      <div style="font-size:.8rem;color:var(--txt2);margin-bottom:14px">Hesaplar arası para transferi — iki tarafta da işlem oluşturulur.</div>
      <div style="margin-bottom:12px">
        <label>Kaynaktan (gider) 🔴</label>
        <select class="f-input" id="tr-from"><option value="">— Hesap seçin —</option></select>
      </div>
      <div style="margin-bottom:12px">
        <label>Hedefe (gelir) 🟢</label>
        <select class="f-input" id="tr-to"><option value="">— Hesap seçin —</option></select>
      </div>
      <div class="form-row">
        <div><label>Tutar (₺)</label><input class="f-input" type="text" inputmode="decimal" data-num id="tr-amount" placeholder="0,00"></div>
        <div><label>Tarih</label><input class="f-input" type="date" id="tr-date"></div>
      </div>
      <div style="margin-bottom:14px"><label>Açıklama <span style="color:var(--txt2);font-size:.7rem">(opsiyonel)</span></label>
        <input class="f-input" type="text" id="tr-desc" placeholder="ör. Maaş Akbank'a transfer">
      </div>
      <button class="btn btn-primary" style="width:100%;padding:13px" onclick="doTransfer()">↔️ Transfer Yap</button>
    </div>
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
    <div class="stat rate-card rate-usd">
      <div class="glow" style="background:#3b82f6"></div>
      <div class="lbl">🇺🇸 USD/TRY</div>
      <div class="val" id="rate-usd">—</div>
      <div class="sub" id="rate-updated"></div>
    </div>
    <div class="stat rate-card rate-eur">
      <div class="glow" style="background:#22c55e"></div>
      <div class="lbl">🇪🇺 EUR/TRY</div>
      <div class="val" id="rate-eur">—</div>
      <div class="sub"></div>
    </div>
    <div class="stat rate-card rate-gbp">
      <div class="glow" style="background:#f59e0b"></div>
      <div class="lbl">🇬🇧 GBP/TRY</div>
      <div class="val" id="rate-gbp">—</div>
      <div class="sub"></div>
    </div>
    <div class="stat rate-card rate-gold">
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
      <div style="margin-bottom:12px">
        <label>Hangi Hesaptan? <span style="color:var(--txt2);font-size:.7rem">(opsiyonel — nakit çıkışı takibi için)</span></label>
        <select class="f-input" id="inv-account"><option value="">— Hesap seçme —</option></select>
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
      <div style="margin-bottom:12px">
        <label>Tutar (₺)</label>
        <input class="f-input" type="text" inputmode="decimal" data-num id="rec-amount" placeholder="0,00">
      </div>
      <div style="margin-bottom:14px">
        <label style="display:block;margin-bottom:8px">Her ayın hangi günleri? <span id="rec-days-lbl" style="font-size:.74rem;color:var(--b);font-weight:700"></span></label>
        <div id="rec-days-chips" style="display:flex;flex-wrap:wrap;gap:6px"></div>
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
          <label>Başlangıç Yılı</label>
          <select class="f-input" id="rec-apply-year"></select>
        </div>
        <div>
          <label>Bitiş Yılı</label>
          <select class="f-input" id="rec-apply-year-end"></select>
        </div>
      </div>
      <div class="form-row" style="margin-bottom:10px">
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

<!-- HESAPLAR (Banka Ürünleri) -->
<div class="page" id="page-hesaplar">
  <div class="page-title">Kartlar & Hesaplar</div>
  <div class="page-sub">Banka hesapları ve kartların — limit, bakiye, borç takibi</div>

  <div class="grid2">
    <!-- ADD FORM -->
    <div class="card">
      <div class="section-title" id="acc-form-title">Hesap Ekle</div>
      <input type="hidden" id="acc-edit-id" value="">

      <div style="margin-bottom:14px">
        <label>Tür</label>
        <div class="acc-type-chips">
          <button type="button" class="acc-type-chip active" data-type="vadesiz" onclick="selectAccType(this)">🏦 Vadesiz</button>
          <button type="button" class="acc-type-chip" data-type="vadeli" onclick="selectAccType(this)">📅 Vadeli</button>
          <button type="button" class="acc-type-chip" data-type="kmh" onclick="selectAccType(this)">🔄 KMH</button>
        </div>
        <div id="acc-kmh-hint" style="display:none;margin-top:8px;padding:7px 10px;background:rgba(99,102,241,.08);border-radius:8px;font-size:.72rem;color:var(--txt2)">
          🔄 KMH: Vadesiz hesabınıza bağlı eksi bakiye (overdraft) limitidir. Limit alanına maksimum eksi bakiye tutarını girin.
        </div>
      </div>

      <div style="margin-bottom:12px">
        <label>Banka</label>
        <select class="f-input" id="acc-bank">
          <option value="">— Banka seç —</option>
          <optgroup label="Büyük Bankalar">
            <option>Garanti BBVA</option><option>İş Bankası</option><option>Akbank</option>
            <option>Yapı Kredi</option><option>Ziraat Bankası</option><option>Halkbank</option>
            <option>Vakıfbank</option><option>QNB Finansbank</option><option>Denizbank</option>
            <option>ING</option><option>TEB</option><option>HSBC</option>
          </optgroup>
          <optgroup label="Dijital / Neo Bankalar">
            <option>Enpara</option><option>Papara</option><option>Ininal</option>
            <option>Moka</option><option>Revolt</option><option>Wise</option>
            <option>Paysera</option><option>Param</option><option>Tosla</option>
            <option>Paycell</option><option>Sipay</option>
          </optgroup>
          <optgroup label="Katılım Bankaları">
            <option>Albaraka Türk</option><option>Kuveyt Türk</option>
            <option>Türkiye Finans</option><option>Emlak Katılım</option>
            <option>Ziraat Katılım</option><option>Vakıf Katılım</option>
          </optgroup>
          <optgroup label="Diğer Bankalar">
            <option>Odeabank</option><option>Şekerbank</option><option>Fibabanka</option>
            <option>Burgan Bank</option><option>Pasha Bank</option><option>Alternatifbank</option>
            <option>Anadolubank</option><option>ICBC Turkey</option>
          </optgroup>
          <optgroup label="Kredi / Finansman Kuruluşları">
            <option>Eminevim</option><option>Finansevim</option><option>Tam Finansman</option>
            <option>Creditas</option><option>BNP Paribas Cardif</option>
          </optgroup>
          <option>Diğer</option>
        </select>
      </div>

      <div style="margin-bottom:12px">
        <label>Ad Soyad (Hesap / Kart Sahibi)</label>
        <input class="f-input" type="text" id="acc-owner" placeholder="ör. Ali Yılmaz">
      </div>
      <div style="margin-bottom:12px">
        <label>Ürün / Hesap Adı</label>
        <input class="f-input" type="text" id="acc-name" placeholder="ör. Bonus Card, 5465 Hesabı, Flexi Card">
      </div>

      <div class="form-row">
        <div>
          <label id="acc-bal-lbl">Mevcut Bakiye (₺)</label>
          <input class="f-input" type="text" inputmode="decimal" data-num id="acc-balance" placeholder="0,00">
        </div>
        <div id="acc-limit-col" style="display:none">
          <label>Limit (₺)</label>
          <input class="f-input" type="text" inputmode="decimal" data-num id="acc-limit" placeholder="50.000">
        </div>
      </div>

      <div style="margin-bottom:18px">
        <label>Renk</label>
        <div style="display:flex;gap:7px;flex-wrap:wrap;margin-top:7px">
          <button type="button" class="color-dot active" data-color="#007aff" onclick="selectAccColor(this)" style="background:#007aff"></button>
          <button type="button" class="color-dot" data-color="#34c759" onclick="selectAccColor(this)" style="background:#34c759"></button>
          <button type="button" class="color-dot" data-color="#ff9500" onclick="selectAccColor(this)" style="background:#ff9500"></button>
          <button type="button" class="color-dot" data-color="#ff3b30" onclick="selectAccColor(this)" style="background:#ff3b30"></button>
          <button type="button" class="color-dot" data-color="#5856d6" onclick="selectAccColor(this)" style="background:#5856d6"></button>
          <button type="button" class="color-dot" data-color="#af52de" onclick="selectAccColor(this)" style="background:#af52de"></button>
          <button type="button" class="color-dot" data-color="#ff2d55" onclick="selectAccColor(this)" style="background:#ff2d55"></button>
          <button type="button" class="color-dot" data-color="#1c1c1e" onclick="selectAccColor(this)" style="background:#1c1c1e"></button>
        </div>
      </div>

      <div style="display:flex;gap:8px">
        <button class="btn btn-primary" style="flex:1;padding:12px" onclick="saveAccount()">Kaydet</button>
        <button class="btn btn-ghost" id="acc-cancel-btn" style="display:none;padding:12px 16px" onclick="resetAccForm()">İptal</button>
      </div>
    </div>

    <!-- ACCOUNTS LIST -->
    <div class="card">
      <div class="section-title">Hesaplarım</div>
      <div id="acc-list">
        <div class="empty-state"><div class="icon">🏦</div>Henüz hesap eklenmedi</div>
      </div>
    </div>
  </div>

  <!-- ── KARTLARIM ── -->
  <div style="margin-top:24px;margin-bottom:6px;font-size:1.1rem;font-weight:800;color:var(--txt);letter-spacing:-.02em">💳 Kartlarım</div>
  <div style="font-size:.82rem;color:var(--txt2);margin-bottom:16px">Kredi kartı, yemek kartı, banka kartı — limit ve borç takibi</div>
  <div class="grid2">
    <!-- KART FORM -->
    <div class="card">
      <div class="section-title">Kart Ekle</div>
      <div style="margin-bottom:14px">
        <label>Kart Türü</label>
        <div class="acc-type-chips">
          <button type="button" class="acc-type-chip active" data-ctype="kredi" onclick="selectCardType(this)">💳 Kredi Kartı</button>
          <button type="button" class="acc-type-chip" data-ctype="banka" onclick="selectCardType(this)">🏧 Banka Kartı</button>
          <button type="button" class="acc-type-chip" data-ctype="yemek" onclick="selectCardType(this)">🍽️ Yemek Kartı</button>
          <button type="button" class="acc-type-chip" data-ctype="hediye" onclick="selectCardType(this)">🎁 Hediye Kartı</button>
        </div>
        <input type="hidden" id="card-type-val" value="kredi">
      </div>
      <div style="margin-bottom:12px">
        <label>Banka / Kurum</label>
        <select class="f-input" id="card-bank">
          <option value="">— Seçin —</option>
          <optgroup label="Büyük Bankalar">
            <option>Garanti BBVA</option><option>İş Bankası</option><option>Akbank</option>
            <option>Yapı Kredi</option><option>Ziraat Bankası</option><option>Halkbank</option>
            <option>Vakıfbank</option><option>QNB Finansbank</option><option>Denizbank</option>
            <option>ING</option><option>TEB</option><option>HSBC</option>
          </optgroup>
          <optgroup label="🍽️ Yemek Kartı Firmaları">
            <option>Multinet</option><option>Edenred</option><option>Ticket Restaurant</option>
            <option>Sodexo</option><option>Pluxee</option><option>Paye</option>
          </optgroup>
          <optgroup label="Dijital / Neo">
            <option>Enpara</option><option>Papara</option><option>Param</option><option>Tosla</option><option>Ininal</option>
          </optgroup>
          <option>Diğer</option>
        </select>
      </div>
      <div style="margin-bottom:12px">
        <label>Ad Soyad (Kart Sahibi)</label>
        <input class="f-input" type="text" id="card-owner" placeholder="ör. Ali Yılmaz">
      </div>
      <div style="margin-bottom:12px">
        <label>Kart / Ürün Adı <span style="color:var(--txt2);font-size:.7rem">(opsiyonel)</span></label>
        <input class="f-input" type="text" id="card-name" placeholder="Bonus, Miles &amp; Smiles, Worldcard…">
      </div>
      <div class="form-row">
        <div>
          <label id="card-limit-lbl">Limit (₺)</label>
          <input class="f-input" type="text" inputmode="decimal" data-num id="card-limit" placeholder="50.000">
        </div>
        <div>
          <label id="card-used-lbl">Mevcut Borç (₺)</label>
          <input class="f-input" type="text" inputmode="decimal" data-num id="card-used" placeholder="0,00">
        </div>
      </div>
      <div class="form-row" id="card-credit-fields">
        <div>
          <label>Son Ödeme Günü</label>
          <input class="f-input" type="number" id="card-due" min="1" max="31" value="15">
        </div>
        <div>
          <label>Ekstre Günü</label>
          <input class="f-input" type="number" id="card-stmt" min="1" max="31" value="20">
        </div>
      </div>
      <div id="card-minpct-row" style="margin-bottom:14px">
        <label>Asgari Ödeme Oranı (%)</label>
        <input class="f-input" type="number" id="card-minpct" value="25" min="0" max="100" step="5">
      </div>
      <button class="btn btn-primary" style="width:100%;padding:12px" onclick="addCard()">Kart Ekle</button>
    </div>

    <!-- KART LİSTESİ -->
    <div class="card">
      <div class="section-title">Kayıtlı Kartlar</div>
      <div id="card-totals" style="display:none;background:var(--bg3);border-radius:10px;padding:12px;margin-bottom:14px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-size:.8rem">
        <div style="text-align:center"><div style="color:var(--txt2);margin-bottom:2px">Toplam Limit</div><div style="font-weight:700" id="ct-limit">—</div></div>
        <div style="text-align:center"><div style="color:var(--txt2);margin-bottom:2px">Toplam Borç</div><div style="font-weight:700;color:var(--r)" id="ct-used">—</div></div>
        <div style="text-align:center"><div style="color:var(--txt2);margin-bottom:2px">Kullanılabilir</div><div style="font-weight:700;color:var(--g)" id="ct-avail">—</div></div>
      </div>
      <div id="card-list">
        <div class="empty-state"><div class="icon">💳</div>Henüz kart eklenmedi</div>
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

  <!-- ── HESAP KARTI (LinkedIn tarzı) ── -->
  <div id="settings-account-card" style="background:linear-gradient(135deg,var(--bg2) 0%,var(--bg3) 100%);border:1px solid var(--border);border-radius:18px;padding:0;margin-bottom:16px;overflow:hidden">
    <!-- Üst bant -->
    <div style="height:72px;background:linear-gradient(135deg,#6366f1,#a855f7);position:relative">
      <div id="settings-account-avatar-wrap" style="position:absolute;bottom:-28px;left:20px;width:56px;height:56px;border-radius:50%;background:var(--bg2);border:3px solid var(--bg2);overflow:hidden;display:flex;align-items:center;justify-content:center;font-size:1.5rem" id="settings-account-avatar"></div>
    </div>
    <!-- Bilgiler -->
    <div style="padding:36px 20px 20px">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap">
        <div style="min-width:0">
          <div id="acct-display-name" style="font-size:1.1rem;font-weight:800;color:var(--txt);margin-bottom:2px">—</div>
          <div id="acct-username" style="font-size:.78rem;color:var(--txt2);margin-bottom:6px">—</div>
          <div id="acct-email" style="font-size:.76rem;color:var(--txt2)">—</div>
        </div>
        <!-- Plan badge -->
        <div id="acct-plan-badge" style="flex-shrink:0"></div>
      </div>
      <!-- Plan detay + aksiyon butonu -->
      <div id="acct-plan-detail" style="margin-top:16px;padding:12px 14px;border-radius:10px;background:var(--bg3);border:1px solid var(--border2)">
        <div id="acct-plan-text" style="font-size:.82rem;color:var(--txt2);margin-bottom:10px">Yükleniyor...</div>
        <a id="acct-plan-btn" href="/premium" style="display:inline-block;padding:8px 18px;border-radius:8px;font-size:.82rem;font-weight:700;text-decoration:none;background:linear-gradient(135deg,#6366f1,#a855f7);color:#fff">🚀 Premium'a Geç</a>
      </div>
    </div>
  </div>

  <!-- Avatar + Account -->
  <div class="settings-card">
    <div class="settings-sect-title">Profil Bilgileri</div>
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
    <input type="email" class="f-input" id="settings-email" disabled style="margin-bottom:10px;opacity:.5">
    <label>Telefon <span style="color:var(--txt2);font-size:.7rem">(şifre sıfırlama için)</span></label>
    <input type="tel" class="f-input" id="settings-phone" placeholder="05XX XXX XX XX" style="margin-bottom:14px">
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
  <!-- Telegram Bot -->
  <div class="settings-card">
    <div class="settings-sect-title">📱 Telegram Botu</div>

    <!-- Kurulum Rehberi (bot bağlı değilse göster) -->
    <div id="tg-setup-guide" style="margin-bottom:14px">
      <div style="font-size:.82rem;font-weight:700;color:var(--txt);margin-bottom:10px">Nasıl çalışır?</div>
      <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:14px">
        <div style="display:flex;gap:10px;align-items:flex-start">
          <div style="width:22px;height:22px;border-radius:50%;background:var(--b);color:#fff;font-size:.7rem;font-weight:900;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">1</div>
          <div style="font-size:.8rem;color:var(--txt2);line-height:1.5">Telegram'da <b id="tg-botname-lbl" style="color:var(--b)">@KirpiNakitBot</b>'u ara ve <b>Başlat</b>'a bas</div>
        </div>
        <div style="display:flex;gap:10px;align-items:flex-start">
          <div style="width:22px;height:22px;border-radius:50%;background:var(--b);color:#fff;font-size:.7rem;font-weight:900;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">2</div>
          <div style="font-size:.8rem;color:var(--txt2);line-height:1.5">Aşağıdan <b>Bağlantı Kodu Al</b> butonuna bas</div>
        </div>
        <div style="display:flex;gap:10px;align-items:flex-start">
          <div style="width:22px;height:22px;border-radius:50%;background:var(--b);color:#fff;font-size:.7rem;font-weight:900;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">3</div>
          <div style="font-size:.8rem;color:var(--txt2);line-height:1.5">Bota <code style="background:var(--bg3);padding:2px 6px;border-radius:5px">/link KOD</code> gönder — bağlandı! 🎉</div>
        </div>
        <div style="display:flex;gap:10px;align-items:flex-start">
          <div style="width:22px;height:22px;border-radius:50%;background:var(--g);color:#fff;font-size:.7rem;font-weight:900;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">✓</div>
          <div style="font-size:.8rem;color:var(--txt2);line-height:1.5">Artık bota <code style="background:var(--bg3);padding:2px 6px;border-radius:5px">market 250</code> yaz → harcama otomatik kaydolur</div>
        </div>
      </div>
      <div style="background:var(--bg3);border-radius:10px;padding:10px 12px;font-size:.76rem;color:var(--txt2);line-height:1.6">
        <b style="color:var(--txt)">Örnek komutlar:</b><br>
        <code>market 250</code> → Gider: Market/Gıda ₺250<br>
        <code>maaş 15000</code> → Gelir: Maaş ₺15.000<br>
        <code>yemek 85 öğle</code> → Açıklamayla gider
      </div>
    </div>

    <div id="tg-members-list" style="margin-bottom:12px"></div>
    <div id="tg-code-area" style="display:none;margin-bottom:12px">
      <div style="background:var(--bg3);border-radius:13px;padding:14px 16px;margin-bottom:10px;border:1px solid var(--border2)">
        <div style="font-size:.7rem;color:var(--txt2);margin-bottom:6px;font-weight:600;text-transform:uppercase;letter-spacing:.06em">Telegram botuna bu kodu gönderin</div>
        <div id="tg-code-val" style="font-size:1.5rem;font-weight:900;letter-spacing:.18em;color:var(--b);font-family:monospace">—</div>
        <div style="font-size:.7rem;color:var(--txt2);margin-top:6px">Komut: <code id="tg-cmd" style="background:var(--bg4);padding:2px 6px;border-radius:5px">/link KOD</code> &nbsp;·&nbsp; 15 dk geçerli</div>
      </div>
      <div style="font-size:.78rem;color:var(--txt2);line-height:1.7">
        1. Telegram'da <b id="tg-botname">@KirpiNakitBot</b>'u açın<br>
        2. <code>/link <span id="tg-code-inline">KOD</span></code> yazıp gönderin<br>
        3. Artık <code>market 250</code>, <code>yemek 85</code> gibi mesajlarla harcama kaydolur
      </div>
    </div>
    <button class="btn btn-primary" style="width:100%;padding:11px;font-size:.86rem" onclick="getTgCode()">🔗 Bağlantı Kodu Al</button>
  </div>

  <!-- Rapor Ayarları -->
  <div class="settings-card">
    <div class="settings-sect-title">📄 PDF Rapor Ayarları</div>
    <p style="font-size:.8rem;color:var(--txt2);margin-bottom:14px">Raporlarda görünecek logo, firma adı ve iletişim bilgisi.</p>

    <!-- Logo -->
    <label style="font-size:.78rem;color:var(--txt2);margin-bottom:6px;display:block">Firma / Kişi Logosu</label>
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
      <div id="report-logo-preview" style="width:64px;height:48px;border:1px dashed var(--border2);border-radius:8px;display:flex;align-items:center;justify-content:center;background:var(--bg3);overflow:hidden;flex-shrink:0">
        <span style="font-size:.65rem;color:var(--txt2);text-align:center">Logo<br>yok</span>
      </div>
      <div>
        <button class="btn btn-ghost" style="margin-bottom:6px" onclick="document.getElementById('report-logo-input').click()">📷 Logo Yükle</button>
        <button class="btn btn-ghost" style="font-size:.75rem;color:var(--r)" onclick="clearReportLogo()">Kaldır</button>
        <input type="file" id="report-logo-input" accept="image/*" style="display:none" onchange="handleReportLogoUpload(this)">
        <div style="font-size:.68rem;color:var(--txt2);margin-top:4px">PNG, JPG, SVG — max 375 KB</div>
      </div>
    </div>

    <label>Firma / Kişi Adı</label>
    <input type="text" class="f-input" id="report-name-inp" placeholder="Örn: ABC Danışmanlık Ltd. Şti." style="margin-bottom:10px">

    <label>İletişim / Adres <span style="color:var(--txt2);font-size:.7rem">(opsiyonel)</span></label>
    <input type="text" class="f-input" id="report-contact-inp" placeholder="Örn: info@firma.com · 0212 000 00 00" style="margin-bottom:14px">

    <!-- Tema seçici -->
    <label style="font-size:.78rem;color:var(--txt2);margin-bottom:8px;display:block">Rapor Teması</label>
    <div id="pdf-theme-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px;margin-bottom:16px"></div>

    <button class="btn btn-primary" onclick="saveReportSettings()" style="width:100%">Kaydet</button>
  </div>

  <div class="settings-card">
    <!-- DİL SEÇİCİ -->
    <div class="settings-sect-title">🌍 Dil / Language</div>
    <div style="margin-bottom:16px">
      <select class="f-input" id="lang-select" onchange="setLang(this.value)" style="font-size:.9rem">
        <option value="tr">🇹🇷 Türkçe</option>
        <option value="en">🇬🇧 English</option>
        <option value="de">🇩🇪 Deutsch</option>
        <option value="fr">🇫🇷 Français</option>
        <option value="es">🇪🇸 Español</option>
        <option value="it">🇮🇹 Italiano</option>
        <option value="pt">🇵🇹 Português</option>
        <option value="nl">🇳🇱 Nederlands</option>
        <option value="pl">🇵🇱 Polski</option>
        <option value="ru">🇷🇺 Русский</option>
        <option value="uk">🇺🇦 Українська</option>
        <option value="ro">🇷🇴 Română</option>
        <option value="cs">🇨🇿 Čeština</option>
        <option value="hu">🇭🇺 Magyar</option>
        <option value="el">🇬🇷 Ελληνικά</option>
        <option value="sv">🇸🇪 Svenska</option>
        <option value="no">🇳🇴 Norsk</option>
        <option value="da">🇩🇰 Dansk</option>
        <option value="fi">🇫🇮 Suomi</option>
        <option value="ar">🇸🇦 العربية</option>
        <option value="he">🇮🇱 עברית</option>
        <option value="fa">🇮🇷 فارسی</option>
        <option value="hi">🇮🇳 हिन्दी</option>
        <option value="zh-CN">🇨🇳 中文 (简体)</option>
        <option value="zh-TW">🇹🇼 中文 (繁體)</option>
        <option value="ja">🇯🇵 日本語</option>
        <option value="ko">🇰🇷 한국어</option>
        <option value="th">🇹🇭 ไทย</option>
        <option value="vi">🇻🇳 Tiếng Việt</option>
        <option value="id">🇮🇩 Indonesia</option>
        <option value="ms">🇲🇾 Melayu</option>
      </select>
      <div style="font-size:.72rem;color:var(--txt2);margin-top:6px">Google Translate ile otomatik çeviri yapılır.</div>
    </div>

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
    <div style="font-size:.72rem;color:var(--txt2);margin-top:12px;text-align:center;opacity:.5">🦔 Kirpi</div>
  </div>

  <!-- Hesap Sil -->
  <div class="settings-card" style="border-color:rgba(255,59,48,.25)">
    <div class="settings-sect-title" style="color:var(--r)">Tehlikeli Alan</div>
    <p style="font-size:.82rem;color:var(--txt2);margin-bottom:14px;line-height:1.6">
      Hesabınızı sildiğinizde tüm verileriniz (işlemler, kartlar, yatırımlar vb.) kalıcı olarak silinir. Bu işlem geri alınamaz.
    </p>
    <button onclick="showDeleteAccountModal()" style="width:100%;padding:11px;border-radius:10px;border:1.5px solid rgba(255,59,48,.4);background:rgba(255,59,48,.07);color:var(--r);font-weight:700;font-size:.88rem;cursor:pointer">
      Hesabı Kalıcı Olarak Sil
    </button>
  </div>
</div>

<!-- Hesap Silme Modal -->
<div id="delete-account-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;align-items:center;justify-content:center;padding:20px">
  <div style="background:var(--bg2);border-radius:20px;padding:28px 24px;max-width:360px;width:100%;box-shadow:0 8px 40px rgba(0,0,0,.25)">
    <div style="font-size:2rem;text-align:center;margin-bottom:12px">⚠️</div>
    <h3 style="text-align:center;font-size:1.05rem;font-weight:800;margin-bottom:8px">Hesabı Sil</h3>
    <p style="font-size:.82rem;color:var(--txt2);text-align:center;margin-bottom:20px;line-height:1.6">
      Tüm verileriniz kalıcı olarak silinecek. Devam etmek için şifrenizi girin.
    </p>
    <label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:6px">Şifreniz</label>
    <input type="password" id="delete-account-pw" class="f-input" placeholder="••••••" style="margin-bottom:8px;width:100%">
    <div id="delete-account-err" style="font-size:.8rem;color:var(--r);min-height:18px;margin-bottom:12px"></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
      <button onclick="hideDeleteAccountModal()" class="btn btn-ghost">İptal</button>
      <button onclick="confirmDeleteAccount()" style="padding:11px;border-radius:10px;border:none;background:var(--r);color:#fff;font-weight:700;cursor:pointer">Sil</button>
    </div>
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
// ── REMINDERS & ONBOARDING ───────────────────────────────────────────────────
function loadReminders(){
  xhr('/api/reminders',null,function(d){
    if(!d) return;

    // Onboarding
    if(d.show_onboarding){
      var ob=document.getElementById('onboarding-card');
      if(ob) ob.style.display='block';
    }

    // Hatırlatıcılar
    var all = (d.upcoming||[]).concat(d.card_reminders||[]);
    if(all.length > 0){
      var rc=document.getElementById('reminders-card');
      var rl=document.getElementById('reminders-list');
      if(rc) rc.style.display='block';
      if(rl){
        var html = all.map(function(r){
          var isCard = !!r.name;
          var label  = isCard ? r.name : r.description;
          var dayTxt = r.days_until===0?'Bugün':r.days_until===1?'Yarın':r.days_until<0?'Geçti':''+r.days_until+' gün';
          var color  = r.days_until<=0?'var(--r)':r.days_until<=2?'var(--y)':'var(--b)';
          var ico    = isCard?'💳':(r.type==='gelir'?'📈':'📉');
          return '<div style="display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--border)">'
            +'<span style="font-size:1.1rem">'+ico+'</span>'
            +'<div style="flex:1;min-width:0">'
            +'<div style="font-size:.84rem;font-weight:600;color:var(--txt);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+label+'</div>'
            +'<div style="font-size:.72rem;color:var(--txt2)">₺'+r.amount.toLocaleString('tr-TR')+'</div>'
            +'</div>'
            +'<div style="font-size:.78rem;font-weight:800;color:'+color+';flex-shrink:0">'+dayTxt+'</div>'
            +'</div>';
        }).join('');
        rl.innerHTML = html;
      }
    }
  });
}

// ── INSIGHTS ─────────────────────────────────────────────────────────────────
function loadInsights(){
  xhr('/api/insights',null,function(d){
    if(!d) return;
    window._lastInsightData=d;
    var sec=document.getElementById('insights-section');
    if(sec) sec.style.display='block';

    // Skor
    var bar=document.getElementById('ins-score-bar');
    var val=document.getElementById('ins-score-val');
    var msg=document.getElementById('ins-msg');
    var em=document.getElementById('ins-emoji');
    if(bar) setTimeout(function(){bar.style.width=d.score+'%'},100);
    if(val) val.textContent=d.score+'/100';
    if(msg) msg.textContent=d.msg;
    if(em) em.textContent=d.emoji;

    // Değişimler
    function chgHtml(pct){
      var sign=pct>=0?'▲':'▼';
      var color=pct>=0?'var(--g)':'var(--r)';
      return '<span style="color:'+color+'">'+sign+' %'+Math.abs(pct)+'</span> geçen aya göre';
    }
    var gc=document.getElementById('ins-gelir-chg');
    var zc=document.getElementById('ins-gider-chg');
    if(gc) gc.innerHTML=chgHtml(d.gelir_change);
    if(zc) zc.innerHTML=chgHtml(-d.gider_change);

    // Anomaliler
    if(d.anomalies && d.anomalies.length>0){
      var ac=document.getElementById('anomaly-card');
      var al=document.getElementById('anomaly-list');
      if(ac) ac.style.display='block';
      if(al){
        al.innerHTML=d.anomalies.map(function(a){
          return '<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border)">'
            +'<div><div style="font-size:.84rem;font-weight:700;color:var(--txt)">'+a.cat+'</div>'
            +'<div style="font-size:.72rem;color:var(--txt2)">₺'+a.prv+' → ₺'+a.cur+'</div></div>'
            +'<div style="font-size:.9rem;font-weight:900;color:#ff9500">+%'+a.pct+'</div></div>';
        }).join('');
      }
    }

    // Net Likidite
    var liq=document.getElementById('ins-liquidity');
    var burn=document.getElementById('ins-burn');
    if(liq){
      var lval=d.net_liquidity||0;
      liq.textContent=(lval>0?'+':'−')+'₺'+Math.abs(lval).toLocaleString('tr-TR');
      liq.style.color=lval>0?'#4ade80':lval<0?'#f87171':'#94a3b8';
    }
    if(burn && d.daily_burn>0){
      var dval=d.days_left;
      burn.textContent='≈ '+(dval>365?'365+':dval)+' gün dayanır';
    }

    // Kullanılabilir Nakit (bu ay net − asgari kart ödemeler)
    var kul=document.getElementById('ins-kullanilabilir');
    var asg=document.getElementById('ins-asgari');
    if(kul && d.kullanilabilir_nakit!=null){
      var kval=d.kullanilabilir_nakit;
      kul.textContent=(kval>0?'+':'−')+'₺'+Math.abs(kval).toLocaleString('tr-TR');
      kul.style.color=kval>0?'#fbbf24':kval<0?'#f87171':'#94a3b8';
    }
    if(asg && d.asgari_odeme>0){
      asg.textContent='Asgari: ₺'+Math.round(d.asgari_odeme).toLocaleString('tr-TR');
    }

    // Net Varlık
    var nw=document.getElementById('ins-networth');
    var daysEl=document.getElementById('ins-days');
    if(nw && d.net_worth!=null){
      var nval=d.net_worth;
      nw.textContent=(nval>0?'+':'−')+'₺'+Math.abs(nval).toLocaleString('tr-TR');
      nw.style.color=nval>0?'#818cf8':nval<0?'#f87171':'#94a3b8';
    }
    if(daysEl && d.invest_val!=null){
      daysEl.textContent='Yat. ₺'+Math.round(d.invest_val).toLocaleString('tr-TR');
    }

    // Kart özet şeridi
    if(d.kart_borcu>0){
      var strip=document.getElementById('ins-card-strip');
      if(strip) strip.style.display='block';
      var kb=document.getElementById('ins-kart-borcu');
      var ka=document.getElementById('ins-kart-asgari');
      var kl=document.getElementById('ins-kart-limit');
      if(kb) kb.textContent='₺'+Math.round(d.kart_borcu).toLocaleString('tr-TR');
      if(ka) ka.textContent='₺'+Math.round(d.asgari_odeme).toLocaleString('tr-TR');
      if(kl) kl.textContent='₺'+Math.round(d.kart_kullanilabilir||0).toLocaleString('tr-TR');
    }
  });
}

// ── ACCOUNT DELETION ─────────────────────────────────────────────────────────
function showDeleteAccountModal(){
  var m=document.getElementById('delete-account-modal');
  m.style.display='flex';
  document.getElementById('delete-account-pw').value='';
  document.getElementById('delete-account-err').textContent='';
}
function hideDeleteAccountModal(){
  document.getElementById('delete-account-modal').style.display='none';
}
function confirmDeleteAccount(){
  var pw=document.getElementById('delete-account-pw').value;
  var errEl=document.getElementById('delete-account-err');
  if(!pw){errEl.textContent='Şifre boş olamaz';return;}
  fetch('/api/me/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:pw})})
    .then(r=>r.json()).then(d=>{
      if(d.ok){window.location.href='/login';}
      else{errEl.textContent=d.error||'Bir hata oluştu';}
    }).catch(()=>{errEl.textContent='Bağlantı hatası';});
}

// ── SPLASH SCREEN ────────────────────────────────────────────────────────────
var _splashHidden = false;
function hideSplash(){
  if(_splashHidden) return; _splashHidden=true;
  var splash = document.getElementById('splash-screen');
  if(!splash) return;
  splash.classList.add('hide');
  setTimeout(function(){ splash.style.display='none'; }, 400);
}
(function(){
  var splash = document.getElementById('splash-screen');
  if(!splash) return;
  // En fazla 1.5 saniye — veri geldiyse daha erken kapanır
  setTimeout(hideSplash, 1500);
})();

// ── NATIVE APP FEEL ──────────────────────────────────────────────────────────
// Pull-to-refresh engeli — sadece telefonda, tablette normal kaydırma açık
var _lastTouchY = 0;
document.addEventListener('touchstart', function(e){ _lastTouchY = e.touches[0].clientY; }, {passive:true});
document.addEventListener('touchmove', function(e){
  if(window.innerWidth >= 768) return; // tablet / masaüstü → müdahale etme
  var el = e.target.closest('.s-body,.more-sheet,.mod-sheet,.ledger-wrap,[style*="overflow"]');
  var movingDown = e.touches[0].clientY > _lastTouchY;
  var atTop = window.scrollY === 0 && document.documentElement.scrollTop === 0;
  if(!el && movingDown && atTop){
    e.preventDefault();
  }
}, {passive:false});

// iOS status bar rengini sayfa geçişlerinde koru
function _setStatusBar(color){
  var m = document.querySelector('meta[name=theme-color]');
  if(m) m.content = color || (document.documentElement.getAttribute('data-theme')==='dark'?'#0a0c12':'#f2f2f7');
}

// ── HAPTIC FEEDBACK ──────────────────────────────────────────────────────────
function haptic(ms){
  if(navigator.vibrate) navigator.vibrate(ms||8);
}
// Tüm buton ve tappable'lara haptic ekle
document.addEventListener('touchstart', function(e){
  var t = e.target.closest('button,.btn,.tappable,.nl,.more-tile,.ob-step');
  if(t) haptic(6);
}, {passive:true});

// ── DARK MODE ────────────────────────────────────────────────────────────────
// ── GOOGLE TRANSLATE ─────────────────────────────────────────────────────────
function googleTranslateElementInit(){
  new google.translate.TranslateElement({
    pageLanguage:'tr',
    layout:google.translate.TranslateElement.InlineLayout.SIMPLE,
    autoDisplay:false
  },'google_translate_element');
  // Kaydedilmiş dili uygula
  var saved=localStorage.getItem('kirpi_lang');
  if(saved&&saved!=='tr') setTimeout(function(){ _applyGoogleLang(saved); },800);
  _syncLangBtns();
}

function _applyGoogleLang(lang){
  var sel=document.querySelector('.goog-te-combo');
  if(sel){ sel.value=lang; sel.dispatchEvent(new Event('change')); }
}

function setLang(lang){
  localStorage.setItem('kirpi_lang',lang);
  _syncLangBtns();
  if(lang==='tr'){
    // Türkçeye dön — sayfayı yenile (Google Translate'i sıfırla)
    var c=document.cookie.split(';');
    for(var i=0;i<c.length;i++){
      var k=c[i].split('=')[0].trim();
      if(k==='googtrans') document.cookie=k+'=;expires=Thu, 01 Jan 1970 00:00:01 GMT;path=/';
    }
    location.reload();
    return;
  }
  var sel=document.querySelector('.goog-te-combo');
  if(sel){ sel.value=lang; sel.dispatchEvent(new Event('change')); }
  else { setTimeout(function(){ _applyGoogleLang(lang); },500); }
}

function _syncLangBtns(){
  var cur=localStorage.getItem('kirpi_lang')||'tr';
  var sel=document.getElementById('lang-select');
  if(sel) sel.value=cur;
}

function _syncDarkModeUI(){
  var isDark=document.documentElement.getAttribute('data-theme')==='dark';
  var btn=document.getElementById('dark-mode-btn');
  var ico=document.getElementById('dark-mode-sheet-ico');
  var lbl=document.getElementById('dark-mode-sheet-lbl');
  if(btn) btn.textContent=isDark?'☀️':'🌙';
  if(ico) ico.textContent=isDark?'☀️':'🌙';
  if(lbl) lbl.textContent=isDark?'Aydınlık':'Karanlık';
}
function toggleDarkMode(){
  var isDark=document.documentElement.getAttribute('data-theme')==='dark';
  var next=isDark?'light':'dark';
  document.documentElement.setAttribute('data-theme',next);
  localStorage.setItem('theme',next);
  _syncDarkModeUI();
}

// ── GLOBALS ──────────────────────────────────────────────────────────────────
var MONTHS=['','Ocak','Şubat','Mart','Nisan','Mayıs','Haziran',
            'Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'];
var CLRS=['#6366f1','#f59e0b','#a855f7','#ef4444','#22c55e','#06b6d4',
          '#f97316','#ec4899','#84cc16','#14b8a6','#e11d48','#0ea5e9'];
var curYear=new Date().getFullYear(), curMonth=new Date().getMonth()+1;
var curTab='gider', summaryData={}, allTx=[], filteredTx=[];
var sortCol='date', sortDir=-1;
var CATS={gelir:[],gider:[],all:[]};
var _todayDate=new Date().toISOString().split('T')[0];
var _allCards=[], _allAccounts=[];  // /api/init'ten yüklenir

function _cardName(id){ var c=_allCards.find(function(x){return x.id==id}); return c?(c.bank_name+(c.card_name?' · '+c.card_name:'')):''; }
function _accName(id){ var a=_allAccounts.find(function(x){return x.id==id}); return a?((a.bank?a.bank+' · ':'')+a.name):''; }
function _cardIco(id){ var c=_allCards.find(function(x){return x.id==id}); var t=c&&c.card_type; return t==='yemek'?'🍽️':t==='banka'?'🏧':t==='hediye'?'🎁':'💳'; }
function _cardType(id){ var c=_allCards.find(function(x){return x.id==id}); return (c&&c.card_type)||'kredi'; }
function _blErr(img){
  img.onerror=null;
  var bg=img.getAttribute('data-bg')||'#8E8E93';
  var nm=img.getAttribute('data-bank')||'?';
  var ws=nm.trim().split(/\s+/);
  var t=ws.length>=2?ws[0][0]+ws[1][0]:nm.substring(0,2);
  var tx=t.toUpperCase();
  var fs=tx.length<=2?18:tx.length===3?13:10;
  var svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 38 38"><rect width="38" height="38" rx="10" fill="'+bg+'"/><text x="19" y="22" font-size="'+fs+'" font-weight="900" fill="white" text-anchor="middle" dominant-baseline="middle" font-family="Arial Black,Arial,sans-serif">'+tx+'</text></svg>';
  img.src='data:image/svg+xml,'+encodeURIComponent(svg);
}
function goToCard(cardId){
  var navEl=document.querySelector('[data-page=hesaplar]');
  goPage('hesaplar', navEl);
  setTimeout(function(){
    var el=document.querySelector('[data-card-id="'+cardId+'"]');
    if(!el){ loadCards(); setTimeout(function(){ var e2=document.querySelector('[data-card-id="'+cardId+'"]'); if(e2){ e2.scrollIntoView({behavior:'smooth',block:'center'}); e2.style.outline='2px solid var(--b)'; setTimeout(function(){e2.style.outline='';},2000); } },400); return; }
    el.scrollIntoView({behavior:'smooth',block:'center'});
    el.style.outline='2px solid var(--b)';
    el.style.boxShadow='0 0 0 6px #0A84FF18';
    setTimeout(function(){el.style.outline='';el.style.boxShadow='';},2000);
  }, 300);
}
function _bankLogo(name){
  var colors={
    'Garanti BBVA':'#009A44','İş Bankası':'#003087','Akbank':'#E30613',
    'Yapı Kredi':'#003087','Ziraat Bankası':'#C8102E','Halkbank':'#0072CE',
    'Vakıfbank':'#F5A623','QNB Finansbank':'#6F2D8E','Denizbank':'#00A3E0',
    'ING':'#FF6200','TEB':'#003087','HSBC':'#DB0011','Multinet':'#F7941D',
    'Edenred':'#E30613','Ticket Restaurant':'#E30613','Sodexo':'#012169',
    'Pluxee':'#7B2D8B','Paye':'#1DA462','Enpara':'#00A859','Papara':'#6F2D8E',
    'Param':'#00B050','Tosla':'#FF5C35','Ininal':'#0081FF',
    'Albaraka Türk':'#006D3B','Kuveyt Türk':'#009B77','Türkiye Finans':'#00305E',
    'Revolut':'#191C1F','Wise':'#9FE870','Paycell':'#0055A5'
  };
  var c=colors[name];
  if(c){
    return '<img class="bank-logo-badge" src="/bank-logo/'+encodeURIComponent(name)+'" '+
      'data-bank="'+name.replace(/"/g,'&quot;')+'" data-bg="'+c+'" '+
      'onerror="_blErr(this)" width="38" height="38" style="border-radius:10px;object-fit:contain;background:#fff;padding:2px" alt="">';
  }
  var bg='#8E8E93';
  var ws=(name||'?').trim().split(/\s+/);
  var t=ws.length>=2?ws[0][0]+ws[1][0]:(name||'?').substring(0,2);
  var tx=t.toUpperCase();
  var fs=tx.length<=2?18:tx.length===3?13:10;
  var svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 38 38"><rect width="38" height="38" rx="10" fill="'+bg+'"/><text x="19" y="22" font-size="'+fs+'" font-weight="900" fill="white" text-anchor="middle" dominant-baseline="middle" font-family="Arial Black,Arial,sans-serif">'+tx+'</text></svg>';
  return '<img class="bank-logo-badge" src="data:image/svg+xml,'+encodeURIComponent(svg)+'" width="38" height="38" style="border-radius:10px" alt="">';
}

// ── INIT ─────────────────────────────────────────────────────────────────────
function _appInit(){
  _syncDarkModeUI();
  var todayISO=new Date().toISOString().split('T')[0];
  var fdate=document.getElementById('f-date');
  if(fdate) fdate.value=todayISO;
  var dpick=document.getElementById('today-date-pick');
  if(dpick) dpick.value=todayISO;
  _todayDate=todayISO;
  updateMonthLabel();
  var h=new Date().getHours();
  var prefix=h<5?'İyi geceler':h<12?'Günaydın':h<18?'İyi günler':'İyi akşamlar';
  var gEl=document.getElementById('hero-greeting');
  if(gEl) gEl.textContent=gEl.textContent.replace('Merhaba',prefix);
  initHeroMonthYear();
  try{ setupDrop(); }catch(e){}
  try{ setupNumInputs(); }catch(e){}
  try{ requestBrowserNotifPermission(); }catch(e){}

  // Hemen yükle — profile bilgisi gelmeden önce
  loadDashboard();
  loadAllTx();

  // Profil + kategoriler arka planda kur
  xhr('/api/init',null,function(d){
    if(!d) { loadReminders(); loadNotifications(); return; }
    if(d.categories){ CATS=d.categories; fillSel('f-cat',CATS[curTab]); }
    if(d.cards){ _allCards=d.cards; }
    if(d.accounts){ _allAccounts=d.accounts; }
    if(d.user){
      var me=d.user;
      _curAvatar=me.avatar||'';
      if(me.profile_id){
        sessionStorage.setItem('cur_pid',me.profile_id);
        sessionStorage.setItem('cur_pname',me.profile_name||'');
        sessionStorage.setItem('cur_ptype',me.profile_type||'');
      }
      setAvatarDisplay(me.avatar,me.display||me.username||'?');
      var n=document.getElementById('udrop-name');
      var s=document.getElementById('udrop-sub');
      if(n) n.textContent=me.display||me.username||'—';
      if(s) s.textContent='@'+me.username+(me.email?' · '+me.email:'');
      applyProfileType(me.profile_type);
    }
    if(d.profiles){
      _profiles=d.profiles;
      renderDropdownProfiles(); renderSettingsProfiles();
      var curPid=parseInt(sessionStorage.getItem('cur_pid')||'0');
      var preferred=parseInt(localStorage.getItem('preferred_pid')||'0');
      var activeP=d.profiles.find(function(p){return p.id===(preferred||curPid);})||d.profiles[0];
      if(activeP){ var snEl=document.getElementById('sidebar-profile-name'); if(snEl) snEl.textContent=activeP.name; updateSidebarProfileAvatar(activeP.avatar||''); }
      if(preferred&&preferred!==curPid){
        var match=d.profiles.find(function(p){return p.id===preferred;});
        if(match){
          // Farklı profil: switch et ve yenile
          switchProfileThen(preferred, function(){ loadDashboard(); loadAllTx(); });
        }
      }
    }
    loadReminders(); loadNotifications();
    var dashPage=document.getElementById('page-dashboard');
    if(dashPage&&dashPage.classList.contains('active')) loadInsights();
  });

  // 6 saniye sonra hâlâ boşsa retry göster
  setTimeout(function(){
    var bal=document.getElementById('s-bal');
    if(bal&&(bal.textContent==='—'||!bal.textContent.trim())){
      var rb=document.getElementById('dash-retry-bar'); if(rb) rb.style.display='flex';
    }
  }, 6000);

  populateYearFilter();
  document.addEventListener('click',function(e){
    var t=e.target.closest('button,.btn,.tappable,.tx-day-item,.hero-chip,.aging-card,.asset-card,.todo-item,.sup-inv-item,.settings-link-row');
    if(t) playClick();
  },true);
}
// DOM hazır mı kontrol et — her iki durumda da tüm script çalıştıktan sonra başlat
if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', function(){ setTimeout(_appInit, 0); });
} else {
  setTimeout(_appInit, 0); // tüm var tanımları çalışsın, sonra başlat
}

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
    // Önce yeni sayfayı hazırla (gizli)
    next.style.display='block';
    next.style.opacity='0';
    next.style.transform='translateX(12px)';
    next.style.transition='none';

    requestAnimationFrame(function(){
      // Eski sayfayı fade out
      if(prev && prev !== next){
        prev.style.transition='opacity .15s ease';
        prev.style.opacity='0';
      }
      requestAnimationFrame(function(){
        // Eski gizle, yeni göster
        document.querySelectorAll('.page').forEach(function(p){
          if(p !== next){ p.classList.remove('active'); p.style.display='none'; p.style.opacity=''; p.style.transition=''; p.style.transform=''; }
        });
        next.style.transition='opacity .2s ease,transform .2s cubic-bezier(.25,.46,.45,.94)';
        next.style.opacity='1';
        next.style.transform='translateX(0)';
        next.classList.add('active');
      });
    });
    playClick();
    if(id==='ledger') loadAllTx();
    if(id==='dashboard') loadDashboard();
    if(id==='recurring') initRecurringPage();
    if(id==='invest') initInvestPage();
    if(id==='hesaplar'){ loadAccounts(); loadCards(); }
    if(id==='add'){ setTab('gider'); loadAccountsDropdown(); loadCardsDropdown(); _updateAddProfileBanner(); }
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
// Swipe-down to close more-sheet
(function(){
  var sh, startY=0, dragging=false;
  document.addEventListener('DOMContentLoaded',function(){
    sh=document.getElementById('more-sheet');
    if(!sh) return;
    sh.addEventListener('touchstart',function(e){
      if(e.touches[0].clientY < sh.getBoundingClientRect().top + 60){
        startY=e.touches[0].clientY; dragging=true;
      }
    },{passive:true});
    sh.addEventListener('touchmove',function(e){
      if(!dragging) return;
      var dy=e.touches[0].clientY - startY;
      if(dy>0) sh.style.transform='translateY('+dy+'px)';
    },{passive:true});
    sh.addEventListener('touchend',function(e){
      if(!dragging) return;
      dragging=false;
      var dy=e.changedTouches[0].clientY - startY;
      sh.style.transform='';
      if(dy>80) closeMoreSheet();
    });
  });
})();
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
  // Nav sidebar items
  document.querySelectorAll('[data-sirket]').forEach(function(el){
    if(!el.classList.contains('more-tile') && el.id !== 'more-sirket-grid'){
      el.style.display = isSirket ? '' : 'none';
    }
  });
  // More-sheet sirket section
  var sirketGrid = document.getElementById('more-sirket-grid');
  if(sirketGrid) sirketGrid.style.display = isSirket ? 'grid' : 'none';
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
    if(me.profile_id){
      sessionStorage.setItem('cur_pid', me.profile_id);
      sessionStorage.setItem('cur_pname', me.profile_name||'');
      sessionStorage.setItem('cur_ptype', me.profile_type||'');
    }
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
    var curPid=parseInt(sessionStorage.getItem('cur_pid')||'0');
    var preferred=parseInt(localStorage.getItem('preferred_pid')||'0');
    var activePid=preferred&&preferred!==curPid?preferred:curPid;
    var activeP=list.find(function(p){return p.id===activePid;})||list[0];
    if(activeP){
      var snEl=document.getElementById('sidebar-profile-name');
      if(snEl) snEl.textContent=activeP.name;
      updateSidebarProfileAvatar(activeP.avatar||'');
    }
    if(preferred && preferred!==curPid){
      var match=list.find(function(p){return p.id===preferred;});
      if(match) switchProfile(preferred);
    }
  });
}

function setAvatarDisplay(avatar, name){
  var initials = (name||'?').slice(0,1).toUpperCase();
  var imgHtml = avatar ? '<img src="'+avatar+'" style="width:100%;height:100%;object-fit:cover;border-radius:50%">' : '';
  function setAva(el, fallback){
    if(!el) return;
    if(avatar) el.innerHTML=imgHtml;
    else el.textContent=(fallback||initials);
  }
  var btn=document.getElementById('avatar-btn-inner');
  if(btn){ if(avatar) btn.innerHTML=imgHtml; else btn.textContent=initials; }
  setAva(document.getElementById('udrop-ava'));
  setAva(document.getElementById('settings-avatar-img'));
  // Desktop sidebar'da da kullanıcı avatarını göster
  var sideAvatar=document.getElementById('sidebar-profile-avatar');
  if(sideAvatar&&avatar) sideAvatar.innerHTML='<img src="'+avatar+'" style="width:100%;height:100%;object-fit:cover;border-radius:50%">';
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
    var avatarHtml=p.avatar
      ?'<img src="'+p.avatar+'" style="width:100%;height:100%;object-fit:cover;border-radius:50%">'
      :'<span style="font-size:1.2rem">'+icon+'</span>';
    return '<div class="settings-profile-item" style="align-items:center;gap:12px">'
      +'<div style="position:relative;flex-shrink:0">'
        +'<div style="width:48px;height:48px;border-radius:50%;background:var(--bg3);border:2px solid var(--border2);display:flex;align-items:center;justify-content:center;overflow:hidden;cursor:pointer" onclick="triggerProfileAvatarUpload('+p.id+')" title="Fotoğraf değiştir">'
          +avatarHtml
        +'</div>'
        +'<div style="position:absolute;bottom:0;right:0;width:16px;height:16px;background:var(--b);border-radius:50%;border:2px solid var(--bg2);display:flex;align-items:center;justify-content:center;pointer-events:none">'
          +'<span style="color:#fff;font-size:.55rem;line-height:1">📷</span>'
        +'</div>'
      +'</div>'
      +'<div style="flex:1;min-width:0">'
        +'<div class="sp-info">'+p.name+'</div>'
        +'<div class="sp-type">'+(p.type==='sirket'?'Şirket':'Kişisel')+'</div>'
      +'</div>'
      +(isActive?'<span class="sp-active">Aktif</span>':'<button onclick="switchProfile('+p.id+')" style="padding:5px 12px;background:var(--b);border:none;border-radius:8px;color:#fff;font-size:.75rem;cursor:pointer;font-weight:600">Geç</button>')
      +'</div>'
      +'<input type="file" id="pav-input-'+p.id+'" accept="image/*" style="display:none" onchange="handleProfileAvatarUpload(this,'+p.id+')">';
  }).join('');
}

function triggerProfileAvatarUpload(pid){
  var inp=document.getElementById('pav-input-'+pid);
  if(inp) inp.click();
}

function handleProfileAvatarUpload(input, pid){
  var file=input.files[0]; if(!file) return;
  var reader=new FileReader();
  reader.onload=function(e){
    var b64=e.target.result;
    xhr('/api/profiles/'+pid+'/avatar', {avatar:b64}, function(r){
      if(r.ok){
        var p=_profiles.find(function(x){return x.id===pid});
        if(p) p.avatar=b64;
        renderSettingsProfiles();
        // If active profile, update sidebar avatar display
        var curPid=parseInt(sessionStorage.getItem('cur_pid')||'0');
        if(pid===curPid) updateSidebarProfileAvatar(b64);
        toast('Profil fotoğrafı güncellendi ✓');
      }
    }, true);
  };
  reader.readAsDataURL(file);
}

function updateSidebarProfileAvatar(avatar){
  var el=document.getElementById('sidebar-profile-avatar');
  if(!el) return;
  el.innerHTML=avatar?'<img src="'+avatar+'" style="width:100%;height:100%;object-fit:cover;border-radius:50%">':'';
}

function switchProfileThen(pid, cb){
  xhr('/api/profiles/'+pid+'/switch','POST',function(d){
    if(!d||!d.ok){ if(cb) cb(); return; }
    sessionStorage.setItem('cur_pid', pid);
    sessionStorage.setItem('cur_pname', d.name||'');
    sessionStorage.setItem('cur_ptype', d.type||'');
    localStorage.setItem('preferred_pid', pid);
    // Tüm cache'i temizle — yeni profil için taze veri
    _allCards=[]; _allAccounts=[]; allTx=[]; filteredTx=[];
    renderDropdownProfiles(); renderSettingsProfiles();
    applyProfileType(d.type);
    allTx=[]; filteredTx=[];
    if(cb) cb();
  });
}
function switchProfile(pid){
  switchProfileThen(pid, function(){
    var dd=document.getElementById('user-dropdown');
    if(dd) dd.classList.remove('open');
    showToast('Profil değiştirildi','#6366f1');
    loadDashboard(); loadAllTx(); loadInsights(); loadReminders();
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

// ── NOTIFICATIONS — Monday.com tarzı ─────────────────────────────────────────
var _notifItems=[];

function _notifKey(item){
  // Stabil anahtar: günden bağımsız, aynı kart/fatura için aynı key
  return 'nrd_' + (item.category||'') + '_' + (item.title||'').replace(/\d+/g,'#').slice(0,40);
}
function _isRead(item){ return !!localStorage.getItem(_notifKey(item)); }
function _markRead(item){ localStorage.setItem(_notifKey(item),'1'); }
function _markAllRead(){
  _notifItems.forEach(function(item){ _markRead(item); });
  renderNotifList();
  updateNotifBadge();
}

function loadNotifications(){
  xhr('/api/notifications',null,function(d){
    if(!d.ok) return;
    _notifItems=d.items||[];
    updateNotifBadge();
    renderNotifList();
    sendUrgentBrowserNotifs();
  });
}

function _unreadCount(){
  return _notifItems.filter(function(x){ return !_isRead(x); }).length;
}

function updateNotifBadge(){
  var badge=document.getElementById('notif-badge');
  if(!badge) return;
  var unread=_unreadCount();
  var urgent=_notifItems.filter(function(x){return x.urgency==='urgent'&&!_isRead(x);}).length;
  if(unread===0){ badge.classList.add('hidden'); }
  else {
    badge.classList.remove('hidden');
    badge.textContent=unread>9?'9+':unread;
    badge.style.background=urgent>0?'#ef4444':'#f59e0b';
  }
}

function renderNotifList(){
  var el=document.getElementById('notif-list');
  if(!el) return;
  var unread=_unreadCount();
  var countEl=document.getElementById('notif-panel-count');
  if(countEl) countEl.textContent=_notifItems.length===0?'Bildirim yok':
    (unread>0 ? unread+' okunmamış' : 'Tümü okundu');

  // "Tümünü okundu işaretle" butonu — sadece okunmamış varsa
  var markAllBtn=document.getElementById('notif-mark-all');
  if(markAllBtn) markAllBtn.style.display=unread>0?'block':'none';

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
  var read=_isRead(item);
  var key=JSON.stringify(item).replace(/"/g,'&quot;');
  var dayLabel='';
  if(item.days<=0) dayLabel='<span class="notif-item-days">Bugün</span>';
  else if(item.days===1) dayLabel='<span class="notif-item-days">Yarın</span>';
  else dayLabel='<span class="notif-item-days">'+item.days+' gün sonra</span>';

  return '<div class="notif-item '+item.urgency+(read?' notif-read':'')+'" onclick="markNotifRead(this,'+key+')" style="cursor:pointer;position:relative">'
    // Okunmamış nokta
    +(read?'':'<div style="position:absolute;top:14px;right:14px;width:8px;height:8px;border-radius:50%;background:'+(item.urgency==='urgent'?'#ef4444':'#f59e0b')+'"></div>')
    +'<div class="notif-item-ico">'+item.icon+'</div>'
    +'<div class="notif-item-body">'
      +'<div class="notif-item-title" style="'+(read?'opacity:.5':'')+'">'+item.title+'</div>'
      +'<div class="notif-item-msg" style="'+(read?'opacity:.4':'')+'">'+item.body+'</div>'
      +dayLabel
    +'</div>'
    +'</div>';
}

function markNotifRead(el, item){
  _markRead(item);
  // Animasyonla okundu hale getir
  el.style.transition='opacity .3s';
  el.style.opacity='.5';
  var dot=el.querySelector('[style*="border-radius:50%"]');
  if(dot) dot.style.display='none';
  el.classList.add('notif-read');
  updateNotifBadge();
  var countEl=document.getElementById('notif-panel-count');
  var unread=_unreadCount();
  if(countEl) countEl.textContent=unread>0?unread+' okunmamış':'Tümü okundu';
  var markAllBtn=document.getElementById('notif-mark-all');
  if(markAllBtn) markAllBtn.style.display=unread>0?'block':'none';
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
  // Sadece hiç sorulmamışsa sor — daha önce izin verilmişse veya reddedilmişse bir daha sorma
  if(Notification.permission==='default' && !localStorage.getItem('notif_asked')){
    setTimeout(function(){
      Notification.requestPermission().then(function(){
        localStorage.setItem('notif_asked','1');
      });
    }, 5000);
  }
}

function sendUrgentBrowserNotifs(){
  if(!('Notification' in window)) return;
  if(Notification.permission!=='granted') return;
  var urgent=_notifItems.filter(function(x){return x.urgency==='urgent';});
  if(!urgent.length) return;
  urgent.slice(0,3).forEach(function(item,i){
    // Stabil key: rakamları çıkar (gün sayısı değişirse aynı bildirim tekrar gönderilmesin)
    var stableTitle=(item.title||'').replace(/\d+/g,'#').slice(0,40);
    var key='notif_v2_'+(item.category||'')+stableTitle;
    if(localStorage.getItem(key)) return;
    localStorage.setItem(key,'1');
    setTimeout(function(){
      try{
        new Notification('🦔 Kirpi — '+item.title,{
          body:item.body,
          icon:'/icon-192.png',
          tag:'kirpi-'+i,
          badge:'/icon-192.png'
        });
      }catch(e){}
    }, i*800);
  });
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
    var ph=document.getElementById('settings-phone');
    if(ph) ph.value=me.phone||'';
    setAvatarDisplay(me.avatar, me.display||me.username||'?');
    _renderAccountCard(me);
  });
  renderSettingsProfiles();
  var el=document.getElementById('cur-label');
  var c=_CURRENCIES[_curCode]||_CURRENCIES['TRY'];
  if(el) el.textContent=_curCode+' '+c.sym;
  _syncSoundToggleUI();
  initTelegramSection();
  initReportSettings();
}

function _renderAccountCard(me){
  // Avatar
  var avatarWrap=document.getElementById('settings-account-avatar-wrap');
  if(avatarWrap){
    if(me.avatar){
      avatarWrap.innerHTML='<img src="'+me.avatar+'" style="width:100%;height:100%;object-fit:cover">';
    } else {
      var initials=(me.display||me.username||'?').charAt(0).toUpperCase();
      avatarWrap.innerHTML='<span style="font-size:1.3rem;font-weight:800;color:#818cf8">'+initials+'</span>';
    }
  }
  // Metin
  var el=document.getElementById('acct-display-name');
  if(el) el.textContent=me.display||me.username||'—';
  el=document.getElementById('acct-username');
  if(el) el.textContent='@'+(me.username||'');
  el=document.getElementById('acct-email');
  if(el) el.textContent=me.email||'';

  // Abonelik
  var sub=me.subscription||{status:'free',is_premium:false,days_left:0};
  var badge=document.getElementById('acct-plan-badge');
  var detail=document.getElementById('acct-plan-detail');
  var planText=document.getElementById('acct-plan-text');
  var planBtn=document.getElementById('acct-plan-btn');

  if(sub.status==='trial'){
    if(badge) badge.innerHTML='<span style="background:#6366f120;color:#818cf8;border:1px solid #6366f140;border-radius:20px;padding:4px 12px;font-size:.72rem;font-weight:700">🎁 Deneme</span>';
    if(planText) planText.textContent='Ücretsiz deneme süreniz: '+sub.days_left+' gün kaldı. Tüm Premium özellikler açık.';
    if(planBtn){ planBtn.textContent='Premium\'a Geç →'; planBtn.style.display='inline-block'; }
  } else if(sub.status==='premium'){
    if(badge) badge.innerHTML='<span style="background:#22c55e20;color:#22c55e;border:1px solid #22c55e40;border-radius:20px;padding:4px 12px;font-size:.72rem;font-weight:700">⭐ Premium</span>';
    if(planText) planText.textContent='Aktif Premium üyelik — '+sub.days_left+' gün kaldı.';
    if(planBtn){ planBtn.textContent='Planı Görüntüle'; planBtn.style.background='#1e2233'; }
  } else {
    if(badge) badge.innerHTML='<span style="background:var(--bg3);color:var(--txt2);border:1px solid var(--border2);border-radius:20px;padding:4px 12px;font-size:.72rem;font-weight:700">Ücretsiz</span>';
    if(planText) planText.innerHTML='<strong style="color:var(--txt)">Deneme süreniz doldu.</strong> Yatırım, export, Telegram ve AI analiz özellikleri Premium gerektiriyor.';
    if(planBtn){ planBtn.textContent='🚀 Premium\'a Geç — ₺49/ay'; planBtn.style.display='inline-block'; }
  }
}

// ── TELEGRAM ─────────────────────────────────────────────────────────────────
function initTelegramSection(){
  xhr('/api/telegram/status',null,function(d){
    var listEl=document.getElementById('tg-members-list');
    if(!listEl) return;
    if(d.count>0){
      var html='';
      d.links.forEach(function(l){
        var dt=l.created_at?l.created_at.substring(0,10):'';
        html+='<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 12px;background:var(--bg3);border-radius:10px;margin-bottom:6px">'
          +'<div><span style="font-size:.82rem;font-weight:600;color:var(--g)">✅ Bağlı</span>'
          +(dt?'<span style="font-size:.7rem;color:var(--txt2);margin-left:6px">'+dt+'</span>':'')+'</div>'
          +'<button onclick="tgUnlinkOne('+l.id+')" style="border:none;background:rgba(255,59,48,.1);color:var(--r);border-radius:7px;padding:4px 10px;font-size:.72rem;font-weight:700;cursor:pointer">Kaldır</button>'
          +'</div>';
      });
      listEl.innerHTML=html;
    } else {
      listEl.innerHTML='<div style="font-size:.8rem;color:var(--txt2);margin-bottom:8px">Henüz bağlı Telegram hesabı yok.</div>';
    }
  });
}
function getTgCode(){
  xhr('/api/telegram/link-code',{},function(d){
    if(!d.ok) return;
    var code=d.code; var bot=d.bot||'AppKirpi_BOT';
    document.getElementById('tg-code-val').textContent=code;
    document.getElementById('tg-cmd').textContent='/link '+code;
    var bn=document.getElementById('tg-botname'); if(bn) bn.textContent='@'+bot;
    var bn2=document.getElementById('tg-botname-lbl'); if(bn2) bn2.textContent='@'+bot;
    var ci=document.getElementById('tg-code-inline'); if(ci) ci.textContent=code;
    document.getElementById('tg-code-area').style.display='';
  });
}
function tgUnlinkOne(id){
  if(!confirm('Bu Telegram bağlantısını kaldır?')) return;
  xhr('/api/telegram/unlink',{id:id},function(d){
    if(d.ok){toast('Kaldırıldı');initTelegramSection();}
  },false,true);
}

function saveAccountInfo(){
  var display=document.getElementById('settings-display').value.trim();
  var phone=(document.getElementById('settings-phone')||{}).value||'';
  if(!display){ showToast('Ad Soyad boş olamaz','#ef4444'); return; }
  xhr('/api/me/update',{display_name:display,phone:phone},function(d){
    if(d.ok){
      document.getElementById('settings-display-name-show').textContent=display;
      document.getElementById('udrop-name').textContent=display;
      showToast('Bilgiler kaydedildi ✓','#22c55e');
    }
  });
}

// ── RAPOR AYARLARI ────────────────────────────────────────────────────────────
var _reportLogo='';
var _pdfTheme='profesyonel';
var _PDF_THEMES=[
  {key:'profesyonel',name:'Profesyonel',color:'#2563eb'},
  {key:'minimal',name:'Minimal',color:'#111827'},
  {key:'yeşil',name:'Doğa',color:'#16a34a'},
  {key:'mor',name:'Modern',color:'#7c3aed'},
  {key:'turuncu',name:'Sıcak',color:'#ea580c'},
  {key:'lacivert',name:'Kurumsal',color:'#1e3a5f'},
  {key:'kirmizi',name:'Dinamik',color:'#dc2626'},
  {key:'siyah_beyaz',name:'Klasik B&W',color:'#000'},
  {key:'pembe',name:'Şık',color:'#db2777'},
  {key:'gri',name:'Gümüş',color:'#475569'},
];

function initReportSettings(){
  // Tema grid'i çiz
  var grid=document.getElementById('pdf-theme-grid');
  if(!grid) return;
  grid.innerHTML='';
  _PDF_THEMES.forEach(function(t){
    var div=document.createElement('div');
    div.id='theme-btn-'+t.key;
    div.style.cssText='cursor:pointer;border-radius:8px;padding:8px 6px;text-align:center;border:2px solid transparent;background:var(--bg3);transition:.15s';
    div.innerHTML='<div style="width:100%;height:20px;border-radius:5px;background:'+t.color+';margin-bottom:5px"></div>'
                 +'<div style="font-size:.68rem;color:var(--txt);font-weight:600">'+t.name+'</div>';
    div.onclick=function(){ selectPdfTheme(t.key); };
    grid.appendChild(div);
  });
  selectPdfTheme(_pdfTheme);

  // Mevcut ayarları yükle
  xhr('/api/me/report-settings',null,function(d){
    var ni=document.getElementById('report-name-inp');
    var ci=document.getElementById('report-contact-inp');
    if(ni) ni.value=d.report_name||'';
    if(ci) ci.value=d.report_contact||'';
    if(d.report_logo){
      _reportLogo=d.report_logo;
      var prev=document.getElementById('report-logo-preview');
      if(prev) prev.innerHTML='<img src="'+d.report_logo+'" style="max-width:100%;max-height:100%;object-fit:contain">';
    }
  });
}

function selectPdfTheme(key){
  _pdfTheme=key;
  _PDF_THEMES.forEach(function(t){
    var el=document.getElementById('theme-btn-'+t.key);
    if(!el) return;
    el.style.borderColor=(t.key===key)?t.color:'transparent';
    el.style.background=(t.key===key)?t.color+'18':'var(--bg3)';
  });
}

function handleReportLogoUpload(input){
  var file=input.files[0]; if(!file) return;
  if(file.size>400000){ showToast('Logo en fazla 375 KB olmalı','#ef4444'); return; }
  var reader=new FileReader();
  reader.onload=function(e){
    _reportLogo=e.target.result;
    var prev=document.getElementById('report-logo-preview');
    if(prev) prev.innerHTML='<img src="'+_reportLogo+'" style="max-width:100%;max-height:100%;object-fit:contain">';
  };
  reader.readAsDataURL(file);
}

function clearReportLogo(){
  _reportLogo='';
  var prev=document.getElementById('report-logo-preview');
  if(prev) prev.innerHTML='<span style="font-size:.65rem;color:var(--txt2);text-align:center">Logo<br>yok</span>';
}

function saveReportSettings(){
  var name=(document.getElementById('report-name-inp')||{}).value||'';
  var contact=(document.getElementById('report-contact-inp')||{}).value||'';
  xhr('/api/me/report-settings',{report_name:name,report_contact:contact,report_logo:_reportLogo},function(d){
    if(d.ok) showToast('Rapor ayarları kaydedildi ✓','#22c55e');
    else showToast(d.error||'Hata','#ef4444');
  });
}

function exportPDFWithTheme(year,month){
  var from=(document.getElementById('f-date-from')||{}).value;
  var to=(document.getElementById('f-date-to')||{}).value;
  var url;
  if(from&&to){
    url='/api/export/pdf?start='+from+'&end='+to+'&template='+_pdfTheme;
  } else {
    var y=year||curYear; var m=month||curMonth;
    url='/api/export/pdf?year='+y+'&month='+m+'&template='+_pdfTheme;
  }
  window.open(url,'_blank');
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
  syncHeroSelects();
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
  var tabT=document.getElementById('tab-t');
  if(tabT) tabT.className='type-tab'+(t==='transfer'?' active':'');
  var normalForm=document.getElementById('f-normal-form');
  var transferForm=document.getElementById('f-transfer-form');
  if(transferForm) transferForm.style.display=(t==='transfer'?'':'none');
  if(normalForm) normalForm.style.display=(t==='transfer'?'none':'');
  if(t==='transfer'){ _fillTransferDropdowns(); return; }
  var addBtn=document.getElementById('add-btn');
  if(addBtn) addBtn.className='btn '+(t==='gelir'?'btn-green':'btn-danger');
  fillSel('f-cat',CATS[t]);
  var paySection=document.getElementById('f-pay-section');
  if(paySection) paySection.style.display=(t==='gider'?'':'none');
  var incDest=document.getElementById('f-income-dest');
  if(incDest) incDest.style.display=(t==='gelir'?'':'none');
  var incRefund=document.getElementById('f-income-refund');
  if(incRefund) incRefund.style.display=(t==='gelir'?'':'none');
  if(t==='gelir'){ _fillIncomeDest(); _fillRefundCards(); }
  if(t==='gider') selectPayType(document.querySelector('.pay-chip.active')||document.querySelector('.pay-chip'));
}

function _fillTransferDropdowns(){
  var trDate=document.getElementById('tr-date');
  if(trDate&&!trDate.value) trDate.value=new Date().toISOString().split('T')[0];
  function _fill(list){
    ['tr-from','tr-to'].forEach(function(id){
      var sel=document.getElementById(id); if(!sel) return;
      var prev=sel.value;
      sel.innerHTML='<option value="">— Hesap seçin —</option>';
      (list||[]).forEach(function(a){
        var o=document.createElement('option');
        o.value=a.id;
        var bal=a.computed_balance||a.initial_balance||0;
        o.textContent=(a.bank?a.bank+' · ':'')+a.name+' ('+fmt(bal)+')';
        sel.appendChild(o);
      });
      if(prev) sel.value=prev;
    });
  }
  if(_allAccounts.length) _fill(_allAccounts);
  else xhr('/api/accounts',null,function(list){_allAccounts=list||[];_fill(_allAccounts);});
}

function doTransfer(){
  var fromId=document.getElementById('tr-from').value;
  var toId=document.getElementById('tr-to').value;
  var amount=getNumVal(document.getElementById('tr-amount'));
  var dt=document.getElementById('tr-date').value;
  var desc=document.getElementById('tr-desc').value.trim();
  if(!fromId||!toId){toast('Kaynak ve hedef hesap seçin','#ef4444');return;}
  if(fromId===toId){toast('Kaynak ve hedef aynı olamaz','#ef4444');return;}
  if(!amount||amount<=0){toast('Tutar giriniz','#ef4444');return;}
  xhr('/api/transfers',{from_account_id:parseInt(fromId),to_account_id:parseInt(toId),amount:amount,date:dt,description:desc},function(r){
    if(r.ok){
      toast('Transfer kaydedildi ✓');
      document.getElementById('tr-amount').value='';
      document.getElementById('tr-desc').value='';
      xhr('/api/accounts',null,function(list){_allAccounts=list||[];_fillTransferDropdowns();});
      loadDashboard(); loadAllTx();
    }
  });
}

function _fillRefundCards(){
  var sel=document.getElementById('f-refund-card'); if(!sel) return;
  if(sel.options.length>1) return;
  function _fill(list){
    (list||[]).forEach(function(c){
      var o=document.createElement('option');
      o.value='card:'+c.id;
      var ico=c.card_type==='yemek'?'🍽️':c.card_type==='banka'?'🏧':'💳';
      var used=parseFloat(c.used_||0);var lim=parseFloat(c.limit_||0);
      var avail=lim>0?' — '+fmt(lim-used)+' kullanılabilir':'  borç: '+fmt(used);
      o.textContent=ico+' '+c.bank_name+(c.card_name?' '+c.card_name:'')+avail;
      sel.appendChild(o);
    });
  }
  if(_allCards.length) _fill(_allCards);
  else xhr('/api/cards',null,function(list){_allCards=list||[];_fill(_allCards);});
}
function toggleRefundCard(checked){
  var row=document.getElementById('f-refund-card-row');
  if(row) row.style.display=checked?'':'none';
}
function _fillIncomeDest(){
  var sel=document.getElementById('f-income-account'); if(!sel) return;
  var prev=sel.value;
  function _doFill(list){
    sel.innerHTML='<option value="">— Belirtme (Nakit) —</option>';
    (list||[]).forEach(function(a){
      var opt=document.createElement('option');
      opt.value=a.id;
      opt.textContent=(a.bank?a.bank+' · ':'')+a.name;
      sel.appendChild(opt);
    });
    if(prev) sel.value=prev;
  }
  if(_allAccounts.length){ _doFill(_allAccounts); }
  else { xhr('/api/accounts',null,function(list){ _allAccounts=list||[]; _doFill(_allAccounts); }); }
}

function selectPayType(btn){
  if(!btn) return;
  document.querySelectorAll('.pay-chip').forEach(function(b){b.classList.remove('active')});
  btn.classList.add('active');
  var pt=btn.dataset.ptype;
  var accRow=document.getElementById('f-account-row');
  var cardRow=document.getElementById('f-card-row');
  var accLbl=document.getElementById('f-account-row')&&document.getElementById('f-account-row').querySelector('label');
  var cardLbl=document.getElementById('f-card-label');
  if(accRow) accRow.style.display=(pt==='banka_kart'||pt==='kmh'?'':'none');
  if(cardRow) cardRow.style.display=(pt==='kredi_kart'||pt==='yemek_kart'?'':'none');
  if(pt==='banka_kart') loadAccountsDropdown('vadesiz');
  if(pt==='kmh'){
    if(accLbl) accLbl.textContent='🔄 KMH Hesabı Seçin';
    loadAccountsDropdown('kmh');
  }
  if(pt==='kredi_kart'){
    if(cardLbl) cardLbl.textContent='💳 Kredi Kartı Seçin';
    _fillCardSel('kredi');
  }
  if(pt==='yemek_kart'){
    if(cardLbl) cardLbl.textContent='🍽️ Yemek Kartı Seçin';
    _fillCardSel('yemek');
  }
}

function _fillCardSel(filterType){
  var sel=document.getElementById('f-card'); if(!sel) return;
  var prev=sel.value;
  sel.innerHTML='<option value="">— Kart seçin —</option>';
  var filtered=filterType?_allCards.filter(function(c){return c.card_type===filterType;}):_allCards;
  filtered.forEach(function(c){
    var opt=document.createElement('option');
    opt.value='card:'+c.id;
    var used=parseFloat(c.used_||0); var lim=parseFloat(c.limit_||0);
    var avail=lim>0?' (kalan: '+fmt(lim-used)+')':'';
    opt.textContent=c.bank_name+(c.card_name?' '+c.card_name:'')+avail;
    sel.appendChild(opt);
  });
  if(prev) sel.value=prev;
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
      : 'showTxDayDetail('+JSON.stringify(t)+')';
    var amtStr=lbl+fmt(t.amount);
    return '<div class="tx-day-item" onclick="'+action+'">'+
      '<div class="tx-day-icon '+cls+'">'+lbl+'</div>'+
      '<div class="tx-day-info">'+
        '<div class="tx-day-cat">'+t.category+'</div>'+
        (t.description?'<div class="tx-day-desc">'+t.description+'</div>':'<div class="tx-day-desc" style="color:var(--txt2);opacity:.5">Açıklama yok</div>')+
      '</div>'+
      '<div class="tx-day-amt" style="color:var(--'+(type==='gelir'?'g':'r')+')">'+(t.amount?amtStr:'?')+'</div>'+
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
    if(!d) return;
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

    // Kartlarım + Hesaplar — kategorize
    var co=document.getElementById('cc-overview');
    if(co){
      var hasCards=(d.cards&&d.cards.length>0);
      var hasAccounts=(d.accounts&&d.accounts.length>0);
      if(!hasCards&&!hasAccounts){
        co.innerHTML='<div class="empty-cc">💳 Kart veya hesap eklenmemiş<br><span style="font-size:.75rem;color:var(--txt2)">Kartlarım veya Hesaplar sayfasından ekleyebilirsiniz</span></div>';
      } else {
        var _cico={'kredi':'💳','banka':'🏧','yemek':'🍽️','hediye':'🎁'};
        var _aico={'vadesiz':'🏦','tasarruf':'📅','vadeli':'📅','kredi_karti':'💳','kmh':'🔄','konut_kredisi':'🏠','arac_kredisi':'🚗','ihtiyac_kredisi':'💼','diger':'📋'};
        var _aname={'vadesiz':'Vadesiz','tasarruf':'Vadeli','vadeli':'Vadeli','kredi_karti':'Kredi Kartı','kmh':'KMH','konut_kredisi':'Konut Kredisi','arac_kredisi':'Araç Kredisi','ihtiyac_kredisi':'İhtiyaç Kredisi','diger':'Diğer'};
        var html='';
        // ── Özet: Kredi Kartı Kullanılabilir  |  Hesap Bakiyesi ──────────────
        var nakitColor=(d.nakit_bakiye||0)>=0?'var(--g)':'var(--r)';
        html+='<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px">'+
          // Sol: Kredi Kartı Kullanılabilir
          '<div style="background:linear-gradient(135deg,#1a3a5c,#0d2b45);border-radius:12px;padding:12px 14px;cursor:pointer" onclick="showAvailableLimitModal()">'+
            '<div style="font-size:.58rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#90b4d4;margin-bottom:4px">💳 Kredi Kartı</div>'+
            '<div style="font-size:1rem;font-weight:900;color:#fff;margin-bottom:2px">'+fmt(d.total_avail)+'</div>'+
            '<div style="font-size:.65rem;color:#90b4d4">Kullanılabilir</div>'+
            '<div style="border-top:1px solid #1e4a6e;margin-top:8px;padding-top:6px;display:flex;justify-content:space-between;font-size:.65rem;color:#90b4d4">'+
              '<span>Limit: <b style="color:#a0c4e8">'+fmt(d.total_limit)+'</b></span>'+
              '<span>Borç: <b style="color:#f87171">'+fmt(d.total_used)+'</b></span>'+
            '</div>'+
          '</div>'+
          // Sağ: Hesap Nakit Bakiyesi
          '<div style="background:linear-gradient(135deg,#0f3d24,#072b18);border-radius:12px;padding:12px 14px;cursor:pointer" onclick="goPage(\'hesaplar\',document.querySelector(\'[data-page=hesaplar]\'))">'+
            '<div style="font-size:.58rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#6bba8c;margin-bottom:4px">🏦 Hesaplarım</div>'+
            '<div style="font-size:1rem;font-weight:900;color:'+(d.nakit_bakiye>=0?'#4ade80':'#f87171')+'">'+fmt(d.nakit_bakiye||0)+'</div>'+
            '<div style="font-size:.65rem;color:#6bba8c">Nakit Bakiye</div>'+
            '<div style="border-top:1px solid #14532d;margin-top:8px;padding-top:6px;font-size:.65rem;color:#6bba8c">'+
              '<span>'+(d.accounts&&d.accounts.filter(function(a){return a.type==='vadesiz'||a.type==='vadeli'||a.type==='tasarruf';}).length||0)+' vadesiz/vadeli hesap</span>'+
            '</div>'+
          '</div>'+
        '</div>';

        // GRUP 1: Banka Hesapları (vadesiz, tasarruf vb.)
        var bankHesaplar=(d.accounts||[]).filter(function(a){return a.type!=='kredi_karti'&&a.type!=='kmh'});
        if(bankHesaplar.length){
          html+='<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--txt2);margin:4px 0 6px;padding:0 2px">🏦 Banka Hesapları</div>';
          html+=bankHesaplar.map(function(a){
            var balColor=a.balance>=0?'var(--g)':'var(--r)';
            return '<div class="cc-item" onclick="goPage(\'hesaplar\',document.querySelector(\'[data-page=hesaplar]\'))" style="cursor:pointer">'+
              '<div class="cc-item-logo">'+
                _bankLogo(a.bank)+
                '<div class="cc-item-logo-info">'+
                  '<div class="cc-bank">'+a.bank+(a.name?' · '+a.name:'')+'</div>'+
                  '<div style="font-size:.65rem;color:var(--txt2);margin-top:2px">'+(_aname[a.type]||'Hesap')+'</div>'+
                '</div>'+
                '<div style="font-size:.92rem;font-weight:800;color:'+balColor+'">'+fmt(a.balance)+'</div>'+
              '</div>'+
            '</div>';
          }).join('');
        }

        // GRUP 2: KMH / Kredi hesapları
        var kmhList=(d.accounts||[]).filter(function(a){return a.type==='kredi_karti'||a.type==='kmh'});
        if(kmhList.length){
          html+='<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--txt2);margin:10px 0 6px;padding:0 2px">🔄 KMH / Kredi Hesapları</div>';
          html+=kmhList.map(function(a){
            var pct=a.limit>0?Math.round(a.balance/a.limit*100):0;
            var fc=pct<50?'var(--g)':pct<80?'var(--y)':'var(--r)';
            return '<div class="cc-item" onclick="goPage(\'hesaplar\',document.querySelector(\'[data-page=hesaplar]\'))" style="cursor:pointer">'+
              '<div class="cc-item-logo" style="margin-bottom:9px">'+
                _bankLogo(a.bank)+
                '<div class="cc-item-logo-info">'+
                  '<div class="cc-bank">'+a.bank+(a.name?' · '+a.name:'')+'</div>'+
                  '<div style="font-size:.65rem;color:var(--txt2);margin-top:2px">'+(_aname[a.type]||'KMH')+'</div>'+
                '</div>'+
                '<span class="cc-pct-badge '+(pct<50?'ok':pct<80?'warn':'high')+'">%'+pct+'</span>'+
              '</div>'+
              (a.limit>0?'<div class="cc-prog-bg"><div class="cc-prog-fill" style="width:'+pct+'%;background:'+fc+'"></div></div>':'')+
              '<div class="cc-nums">'+
                (a.limit>0?'<span>Limit: <strong style="color:var(--b2)">'+fmt(a.limit)+'</strong></span>':'')+
                '<span>Kullanılan: <strong style="color:var(--r)">'+fmt(a.balance)+'</strong></span>'+
                (a.available!=null?'<span>Kullanılabilir: <strong style="color:'+(a.available<0?'var(--r)':'var(--g)')+'">'+fmt(a.available)+'</strong></span>':'')+
              '</div>'+
            '</div>';
          }).join('');
        }

        // GRUP 3: Kredi & Banka Kartları
        var krediCards=(d.cards||[]).filter(function(c){return c.card_type==='kredi'||c.card_type==='banka'});
        if(krediCards.length){
          html+='<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--txt2);margin:10px 0 6px;padding:0 2px">💳 Kredi & Banka Kartları</div>';
          html+=krediCards.map(function(c){
            var pct=c.pct||0; var fc=pct<50?'var(--g)':pct<80?'var(--y)':'var(--r)';
            var nm=c.bank+(c.name?' · '+c.name:'');
            var isCredi=c.card_type==='kredi';
            var minPay=isCredi&&c.min_pct>0?Math.round(c.used*c.min_pct/100):0;
            return '<div class="cc-item" onclick="goToCard('+c.id+')" style="cursor:pointer">'+
              '<div class="cc-item-logo" style="margin-bottom:9px">'+
                _bankLogo(c.bank)+
                '<div class="cc-item-logo-info">'+
                  '<div class="cc-bank">'+nm+'</div>'+
                  '<div style="font-size:.65rem;color:var(--txt2);margin-top:2px">'+(c.card_type==='banka'?'Banka Kartı':'Kredi Kartı')+'</div>'+
                '</div>'+
                '<span class="cc-pct-badge '+(pct<50?'ok':pct<80?'warn':'high')+'">%'+pct+'</span>'+
              '</div>'+
              '<div class="cc-prog-bg"><div class="cc-prog-fill" style="width:'+pct+'%;background:'+fc+'"></div></div>'+
              '<div class="cc-nums">'+
                '<span>Limit: <strong style="color:var(--b2)">'+fmt(c.limit)+'</strong></span>'+
                '<span>Borç: <strong style="color:var(--r)">'+fmt(c.used)+'</strong></span>'+
                (c.avail!=null?'<span>Kullanılabilir: <strong style="color:'+(c.avail<0?'var(--r)':'var(--g)')+'">'+fmt(c.avail)+'</strong></span>':'')+
                (minPay>0?'<span style="color:var(--y)">Asgari: '+fmt(minPay)+'</span>':'')+
              '</div>'+
            '</div>';
          }).join('');
        }

        // GRUP 4: Yemek & Hediye Kartları
        var yemekCards=(d.cards||[]).filter(function(c){return c.card_type==='yemek'||c.card_type==='hediye'});
        if(yemekCards.length){
          html+='<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--txt2);margin:10px 0 6px;padding:0 2px">🍽️ Yemek & Hediye Kartları</div>';
          html+=yemekCards.map(function(c){
            var nm=c.bank+(c.name?' · '+c.name:'');
            var pct=c.limit>0?Math.round(c.used/c.limit*100):0;
            var fc=pct<50?'var(--g)':pct<80?'var(--y)':'var(--r)';
            return '<div class="cc-item" onclick="goToCard('+c.id+')" style="cursor:pointer">'+
              '<div class="cc-item-logo"'+(c.limit>0?' style="margin-bottom:9px"':'')+'>'+
                _bankLogo(c.bank)+
                '<div class="cc-item-logo-info">'+
                  '<div class="cc-bank">'+nm+'</div>'+
                  '<div style="font-size:.65rem;color:var(--txt2);margin-top:2px">'+(c.card_type==='yemek'?'Yemek Kartı':'Hediye Kartı')+'</div>'+
                '</div>'+
                (c.limit>0?'<span class="cc-pct-badge '+(pct<50?'ok':pct<80?'warn':'high')+'">%'+pct+'</span>':'')+
              '</div>'+
              (c.limit>0?'<div class="cc-prog-bg"><div class="cc-prog-fill" style="width:'+pct+'%;background:'+fc+'"></div></div>':'')+
              '<div class="cc-nums">'+
                (c.limit>0?'<span>Limit: <strong style="color:var(--b2)">'+fmt(c.limit)+'</strong></span>':'')+
                '<span>Kullanılan: <strong style="color:var(--r)">'+fmt(c.used)+'</strong></span>'+
                (c.limit>0?'<span>Kullanılabilir: <strong style="color:'+(c.avail<0?'var(--r)':'var(--g)')+'">'+fmt(c.avail)+'</strong></span>':'')+
              '</div>'+
            '</div>';
          }).join('');
        }

        co.innerHTML=html;
      }
    }
  });
}

var _heroPeriod='month';
var _heroYear=new Date().getFullYear();
var _dashReqId=0, _dashRetry=0;

var _MONTHS_TR=['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran','Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'];

function initHeroMonthYear(){
  var ms=document.getElementById('hero-month-sel');
  var ys=document.getElementById('hero-year-sel');
  if(!ms||!ys) return;
  ms.innerHTML='';
  _MONTHS_TR.forEach(function(m,i){
    ms.innerHTML+='<option value="'+(i+1)+'"'+(i+1===curMonth?' selected':'')+'>'+m+'</option>';
  });
  ys.innerHTML='';
  var now=new Date().getFullYear();
  for(var y=now-3;y<=now+1;y++){
    ys.innerHTML+='<option value="'+y+'"'+(y===curYear?' selected':'')+'>'+y+'</option>';
  }
}

function syncHeroSelects(){
  var ms=document.getElementById('hero-month-sel');
  var ys=document.getElementById('hero-year-sel');
  if(ms) ms.value=curMonth;
  if(ys) ys.value=curYear;
}

function heroMonthYearChange(){
  var ms=document.getElementById('hero-month-sel');
  var ys=document.getElementById('hero-year-sel');
  curMonth=parseInt(ms.value);
  curYear=parseInt(ys.value);
  setHeroPeriod('month');
}

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
  if(_heroPeriod==='month') lbl.textContent=(_MONTHS_TR[curMonth-1]||'AY').toUpperCase()+' '+curYear+' NET';
  else if(_heroPeriod==='year') lbl.textContent=_heroYear+' YILI NET';
  else lbl.textContent='TÜM ZAMANLAR';
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
function fmtDate(iso){
  if(!iso||iso.length<10) return iso||'';
  var p=iso.split('-'); return p[2]+'.'+p[1]+'.'+p[0];
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
  if(!d) return;
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
  var W=cv.parentElement.clientWidth||400, H=220;
  cv.width=W; cv.height=H;
  var ctx=cv.getContext('2d');
  ctx.clearRect(0,0,W,H);
  var maxVal=0;
  data.forEach(function(d){if(d.gelir>maxVal)maxVal=d.gelir;if(d.gider>maxVal)maxVal=d.gider});
  if(!maxVal)maxVal=1;
  var p={t:10,r:10,b:28,l:52}, cw=W-p.l-p.r, ch=H-p.t-p.b, gap=cw/12, bw=gap*0.28;
  _barCols=[]; _barYear=(_heroPeriod==='year')?_heroYear:curYear;
  var isDark=document.documentElement.getAttribute('data-theme')==='dark';
  var gridColor=isDark?'#1e2233':'#e5e5ea';
  var labelColor=isDark?'#94a3b8':'#6d6d72';
  ctx.strokeStyle=gridColor; ctx.lineWidth=1;
  [0,.25,.5,.75,1].forEach(function(f){
    var y=p.t+ch*(1-f);
    ctx.beginPath();ctx.moveTo(p.l,y);ctx.lineTo(W-p.r,y);ctx.stroke();
    ctx.fillStyle=labelColor;ctx.font='10px Inter,system-ui';ctx.textAlign='right';
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
    ctx.fillStyle=labelColor;ctx.font='9px Inter,system-ui';ctx.textAlign='center';
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
  var W=cv.parentElement.clientWidth||400, H=220;
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

// ── ACCOUNTS (Banka Ürünleri) ─────────────────────────────────────────────────
var _accColor='#007aff';
var _accType='vadesiz';

function selectAccType(btn){
  document.querySelectorAll('.acc-type-chip').forEach(function(b){b.classList.remove('active')});
  btn.classList.add('active');
  _accType=btn.getAttribute('data-type');
  var isDebt=(_accType==='kmh');
  var isKmh=(_accType==='kmh');
  var lbl=document.getElementById('acc-bal-lbl');
  var limitCol=document.getElementById('acc-limit-col');
  var kmhHint=document.getElementById('acc-kmh-hint');
  if(lbl) lbl.textContent=isDebt?'Mevcut Borç / Kalan Anapara (₺)':'Mevcut Bakiye (₺)';
  if(limitCol) limitCol.style.display=isDebt?'':'none';
  if(kmhHint) kmhHint.style.display=isKmh?'block':'none';
}

function selectAccColor(btn){
  document.querySelectorAll('.color-dot').forEach(function(b){b.classList.remove('active')});
  btn.classList.add('active');
  _accColor=btn.getAttribute('data-color');
}

function resetAccForm(){
  document.getElementById('acc-edit-id').value='';
  document.getElementById('acc-form-title').textContent='Hesap Ekle';
  document.getElementById('acc-bank').value='';
  var ao=document.getElementById('acc-owner'); if(ao) ao.value='';
  document.getElementById('acc-name').value='';
  document.getElementById('acc-balance').value='';
  document.getElementById('acc-limit').value='';
  document.getElementById('acc-cancel-btn').style.display='none';
  // reset type to vadesiz
  document.querySelectorAll('.acc-type-chip').forEach(function(b){
    b.classList.toggle('active', b.getAttribute('data-type')==='vadesiz');
  });
  _accType='vadesiz';
  // reset color to blue
  document.querySelectorAll('.color-dot').forEach(function(b){
    b.classList.toggle('active', b.getAttribute('data-color')==='#007aff');
  });
  _accColor='#007aff';
  selectAccType(document.querySelector('.acc-type-chip[data-type="vadesiz"]'));
}

function saveAccount(){
  var bank=document.getElementById('acc-bank').value;
  var name=document.getElementById('acc-name').value.trim();
  var bal=getNumVal(document.getElementById('acc-balance'))||0;
  var lim=getNumVal(document.getElementById('acc-limit'))||0;
  var eid=document.getElementById('acc-edit-id').value;
  if(!bank||bank===''){toast('Banka seçin');return}
  if(!name){toast('Ürün adı girin');return}
  var owner=(document.getElementById('acc-owner')||{}).value||'';
  var body={bank:bank,name:name,type:_accType,initial_balance:bal,limit_:lim,color:_accColor,owner:owner};
  function _refreshAccounts(){
    xhr('/api/accounts',null,function(list){ if(list) _allAccounts=list; loadAccounts(); loadAccountsDropdown(); loadDashboard(); });
  }
  if(eid){
    xhr('/api/accounts/'+eid,body,function(r){
      if(r.ok){toast('Güncellendi ✓');resetAccForm();_refreshAccounts();}
    },true);
  } else {
    xhr('/api/accounts',body,function(r){
      if(r.ok){toast('Hesap eklendi ✓');resetAccForm();_refreshAccounts();}
    });
  }
}

function editAccount(a){
  document.getElementById('acc-edit-id').value=a.id;
  document.getElementById('acc-form-title').textContent='Hesabı Güncelle';
  document.getElementById('acc-bank').value=a.bank;
  var ao=document.getElementById('acc-owner'); if(ao) ao.value=a.owner||'';
  document.getElementById('acc-name').value=a.name;
  setNumVal(document.getElementById('acc-balance'), a.initial_balance||0);
  setNumVal(document.getElementById('acc-limit'), a.limit_||0);
  document.getElementById('acc-cancel-btn').style.display='';
  _accType=a.type||'vadesiz';
  document.querySelectorAll('.acc-type-chip').forEach(function(b){
    b.classList.toggle('active', b.getAttribute('data-type')===_accType);
  });
  selectAccType(document.querySelector('.acc-type-chip[data-type="'+_accType+'"]'));
  _accColor=a.color||'#007aff';
  document.querySelectorAll('.color-dot').forEach(function(b){
    b.classList.toggle('active', b.getAttribute('data-color')===_accColor);
  });
  window.scrollTo({top:0,behavior:'smooth'});
}

function deleteAccount(id){
  if(!confirm('Bu hesabı silmek istediğine emin misin?')) return;
  xhr('/api/accounts/'+id,null,function(r){
    if(r.ok){toast('Silindi','#ff3b30');loadAccounts();loadAccountsDropdown();}
  },false,true);
}

var _ACC_LABELS={kredi_karti:'Kredi Kartı',kmh:'KMH',vadesiz:'Vadesiz',tasarruf:'Vadeli',vadeli:'Vadeli',konut_kredisi:'Konut Kredisi',arac_kredisi:'Araç Kredisi',ihtiyac_kredisi:'İhtiyaç Kredisi',diger:'Diğer'};
var _ACC_ICONS={kredi_karti:'💳',kmh:'🔄',vadesiz:'🏦',tasarruf:'📅',vadeli:'📅',konut_kredisi:'🏠',arac_kredisi:'🚗',ihtiyac_kredisi:'💼',diger:'📋'};

function loadAccounts(){
  xhr('/api/accounts',null,function(list){
    var el=document.getElementById('acc-list');
    if(!el) return;
    if(!list||!list.length){
      el.innerHTML='<div class="empty-state"><div class="icon">🏦</div>Henüz hesap eklenmedi</div>';
      return;
    }
    var html='';
    list.forEach(function(a){
      var isCard=(a.type==='kredi_karti'||a.type==='kmh');
      var bal=a.computed_balance||0;
      var lim=a.limit_||0;
      var balColor=isCard?(bal>0?'var(--r)':'var(--g)'):'var(--g)';
      if(!isCard&&bal<0) balColor='var(--r)';
      var icon=_ACC_ICONS[a.type]||'🏦';
      var label=_ACC_LABELS[a.type]||'Hesap';
      var tagBg=isCard?'rgba(255,59,48,.12)':'rgba(52,199,89,.12)';
      var tagColor=isCard?'var(--r)':'var(--g)';
      html+='<div class="acc-list-item" style="border-left:4px solid '+a.color+'">';
      html+='<div class="acc-list-top">';
      html+=_bankLogo(a.bank);
      html+='<div class="acc-list-info">';
      html+='<div class="acc-list-bank">'+a.bank+'</div>';
      html+='<div class="acc-list-name">'+a.name+'</div>';
      html+='<span class="acc-type-tag" style="background:'+tagBg+';color:'+tagColor+'">'+label+'</span>';
      html+='</div>';
      html+='</div>';
      html+='<div class="acc-balance-row">';
      if(isCard){
        var debt=bal>0?bal:0;
        html+='<div><div class="acc-balance-lbl">Borç</div>';
        html+='<div class="acc-balance-main" style="color:'+balColor+'">'+fmt(debt)+'</div></div>';
        if(lim>0){
          var avail=lim-debt;
          html+='<div style="text-align:right"><div class="acc-avail-lbl">Kullanılabilir</div>';
          html+='<div class="acc-avail-val" style="color:var(--g)">'+fmt(avail>0?avail:0)+'</div></div>';
        }
      } else {
        html+='<div><div class="acc-balance-lbl">Bakiye</div>';
        html+='<div class="acc-balance-main" style="color:'+balColor+'">'+fmt(bal)+'</div></div>';
      }
      html+='</div>';
      if(isCard&&lim>0){
        var pct=Math.min(100,Math.round((bal/lim)*100));
        var fillColor=pct>80?'var(--r)':pct>50?'var(--y)':'var(--b)';
        html+='<div class="acc-prog-wrap"><div class="acc-prog-fill" style="width:'+pct+'%;background:'+fillColor+'"></div></div>';
        html+='<div style="font-size:.65rem;color:var(--txt2);margin-top:3px">Limit: '+fmt(lim)+' &nbsp;·&nbsp; %'+pct+' kullanım</div>';
      }
      html+='<div class="acc-actions">';
      html+='<button class="acc-act-btn" style="background:var(--bg3);color:var(--txt2)" data-acc="'+encodeURIComponent(JSON.stringify(a))+'" onclick="editAccount(JSON.parse(decodeURIComponent(this.dataset.acc)))">Düzenle</button>';
      html+='<button class="acc-act-btn" style="background:rgba(255,59,48,.1);color:var(--r)" onclick="deleteAccount('+a.id+')">Sil</button>';
      html+='</div>';
      html+='</div>';
    });
    el.innerHTML=html;
  });
}

function _buildAccDropdown(sel, list, prev){
  sel.innerHTML='<option value="">— Hesap Belirtme —</option>';
  var accGroups=[
    {types:['vadesiz'],           label:'🏦 Vadesiz Hesaplar'},
    {types:['tasarruf','vadeli'], label:'📅 Vadeli Hesaplar'},
    {types:['kmh','kredi_karti'], label:'🔄 KMH / Kredi Hesapları'},
    {types:['konut_kredisi','arac_kredisi','ihtiyac_kredisi','diger'], label:'💼 Diğer'},
  ];
  accGroups.forEach(function(g){
    var inGrp=(list||[]).filter(function(a){return g.types.indexOf(a.type||'vadesiz')!==-1;});
    if(!inGrp.length) return;
    var grp=document.createElement('optgroup'); grp.label=g.label;
    inGrp.forEach(function(a){
      var opt=document.createElement('option');
      opt.value=a.id;
      var bal=a.computed_balance||a.initial_balance||0;
      var balStr=bal!==0?' — '+fmt(bal):'';
      opt.textContent=(a.bank?a.bank+' · ':'')+a.name+balStr;
      grp.appendChild(opt);
    });
    sel.appendChild(grp);
  });
  if(prev) sel.value=prev;
}

function loadAccountsDropdown(filterType){
  var sel=document.getElementById('f-account');
  if(!sel) return;
  var prev=sel.value;
  var lbl=document.getElementById('f-account-row')&&document.getElementById('f-account-row').querySelector('label');
  if(lbl&&!filterType) lbl.textContent='🏦 Hangi Hesaptan?';
  function _doLoad(list){
    var filtered=filterType?list.filter(function(a){return (a.type||'vadesiz')===filterType;}):list;
    _buildAccDropdown(sel, filtered, prev);
  }
  if(!_allAccounts.length){
    xhr('/api/accounts',null,function(list){ _allAccounts=list||[]; _doLoad(_allAccounts); });
    return;
  }
  _doLoad(_allAccounts);
}

var _CARD_TYPE_ICONS={'kredi':'💳','banka':'🏧','yemek':'🍽️','hediye':'🎁'};

function loadCardsDropdown(suggestCat){
  var sel=document.getElementById('f-card');
  if(!sel) return;
  var prev=sel.value;
  sel.innerHTML='<option value="">— Nakit / Kart Seçme —</option>';
  // Yemek kategorisi ise yemek kartlarını öne al
  var isYemek=(suggestCat||'').indexOf('Yemek')!==-1||(suggestCat||'').indexOf('yemek')!==-1;
  var sorted=_allCards.slice().sort(function(a,b){
    if(isYemek){
      var ay=a.card_type==='yemek'?0:1;
      var by=b.card_type==='yemek'?0:1;
      if(ay!==by) return ay-by;
    }
    return (a.bank_name||'').localeCompare(b.bank_name||'');
  });
  // Grupla: Kredi → Banka Kartı → Yemek → Hediye
  var groups=[
    {key:'kredi',  label:'💳 Kredi Kartları'},
    {key:'banka',  label:'🏧 Banka Kartları'},
    {key:'yemek',  label:'🍽️ Yemek Kartları'},
    {key:'hediye', label:'🎁 Hediye Kartları'},
  ];
  groups.forEach(function(g){
    var inGroup=sorted.filter(function(c){return (c.card_type||'kredi')===g.key;});
    if(!inGroup.length) return;
    var grpOpt=document.createElement('optgroup');
    grpOpt.label=g.label;
    inGroup.forEach(function(c){
      var ico=_CARD_TYPE_ICONS[c.card_type]||'💳';
      var opt=document.createElement('option');
      opt.value='card:'+c.id;
      var used=parseFloat(c.used_||0); var lim=parseFloat(c.limit_||0);
      var avail=lim>0?' — '+fmt(lim-used)+' kaldı':'';
      opt.textContent=c.bank_name+(c.card_name?' '+c.card_name:'')+avail;
      grpOpt.appendChild(opt);
    });
    sel.appendChild(grpOpt);
  });
  if(prev) sel.value=prev;
}

function setNumVal(el, v){
  if(!el) return;
  el.value=v?v.toLocaleString('tr-TR',{minimumFractionDigits:2,maximumFractionDigits:2}):'';
}

// ── ADD TX ────────────────────────────────────────────────────────────────────
function addTx(){
  var amount=getNumVal(document.getElementById('f-amount'));
  var cat=document.getElementById('f-cat').value;
  var desc=document.getElementById('f-desc').value;
  var dt=document.getElementById('f-date').value;
  if(!amount||amount<=0){toast('Tutar giriniz');return}
  var payload={type:curTab,amount:amount,category:cat,description:desc,date:dt};
  if(curTab==='gider'){
    var activeChip=document.querySelector('.pay-chip.active');
    var pt=activeChip?activeChip.dataset.ptype:'nakit';
    if(pt==='banka_kart'||pt==='kmh'){
      var accSel=document.getElementById('f-account');
      if(accSel&&accSel.value) payload.account_id=parseInt(accSel.value);
    } else if(pt==='kredi_kart'||pt==='yemek_kart'){
      var cardSel=document.getElementById('f-card');
      var cv=cardSel?cardSel.value:'';
      if(cv&&cv.indexOf('card:')===0) payload.card_id=parseInt(cv.split(':')[1]);
    }
  } else {
    // Gelir: hangi hesaba
    var incAcc=document.getElementById('f-income-account');
    if(incAcc&&incAcc.value) payload.account_id=parseInt(incAcc.value);
    // Gelir: kart iadesi
    var refundChk=document.getElementById('f-refund-check');
    if(refundChk&&refundChk.checked){
      var refundSel=document.getElementById('f-refund-card');
      var rv=refundSel?refundSel.value:'';
      if(rv&&rv.indexOf('card:')===0) payload.card_id=parseInt(rv.split(':')[1]);
    }
  }
  xhr('/api/transactions',payload,function(r){
    if(r.ok){
      toast('İşlem eklendi ✓');
      document.getElementById('f-amount').value='';
      document.getElementById('f-desc').value='';
      var acc=document.getElementById('f-account'); if(acc) acc.value='';
      var crd=document.getElementById('f-card'); if(crd) crd.value='';
      var inc=document.getElementById('f-income-account'); if(inc) inc.value='';
      loadDashboard(); loadAllTx();
      // Kart veya hesap kullanıldıysa cache ve listeler güncelle
      if(payload.card_id){
        xhr('/api/cards',null,function(list){
          if(list){ _allCards=list; loadCardsDropdown(); loadCards(); }
        });
      }
      if(payload.account_id){
        xhr('/api/accounts',null,function(list){
          if(list){ _allAccounts=list; loadAccountsDropdown(); }
        });
      }
    }
  });
}

// Kategori değişince yemek kartlarını öner
document.addEventListener('change',function(e){
  if(e.target&&e.target.id==='f-cat'&&curTab==='gider'){
    loadCardsDropdown(e.target.value);
  }
});

// ── LEDGER ────────────────────────────────────────────────────────────────────
function loadAllTx(){
  // Profil banner'ı güncelle
  var pname=document.getElementById('ledger-profile-name');
  var ptype=document.getElementById('ledger-profile-type');
  var pdot=document.getElementById('ledger-profile-dot');
  if(pname) pname.textContent=sessionStorage.getItem('cur_pname')||'—';
  if(ptype){
    var t=sessionStorage.getItem('cur_ptype')||'';
    ptype.textContent=t==='sirket'?'🏢 Şirket':t==='sahis'?'👤 Şahıs':'';
    if(pdot) pdot.style.background=t==='sirket'?'#f59e0b':'#6366f1';
  }
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
function _updateAddProfileBanner(){
  var pname=sessionStorage.getItem('cur_pname')||'—';
  var ptype=sessionStorage.getItem('cur_ptype')||'';
  var el=document.getElementById('add-profile-name');
  var tb=document.getElementById('add-profile-type-badge');
  var dot=document.getElementById('add-profile-dot');
  if(el) el.textContent=pname;
  if(tb) tb.textContent=ptype==='sirket'?'🏢 Şirket':ptype==='sahis'?'👤 Şahıs':'';
  if(dot) dot.style.background=ptype==='sirket'?'#f59e0b':'#6366f1';
}

function setTypePill(val){
  document.getElementById('f-type').value=val;
  ['all','gelir','gider'].forEach(function(k){
    var btn=document.getElementById('pill-'+k);
    if(!btn) return;
    var isActive=(k==='all'&&val==='')||(k===val);
    btn.style.background=isActive?'#fff':'transparent';
    btn.style.color=isActive?'var(--txt)':'var(--txt2)';
    btn.style.boxShadow=isActive?'0 1px 4px rgba(0,0,0,.1)':'none';
  });
  filterLedger();
}

var _activeQdId=null;
function _fmtDate(d){var y=d.getFullYear(),m=d.getMonth()+1,dd=d.getDate();return y+'-'+(m<10?'0'+m:m)+'-'+(dd<10?'0'+dd:dd);}
function clearQuickDate(){if(_activeQdId){var b=document.getElementById(_activeQdId);if(b)b.classList.remove('qd-active');_activeQdId=null;}}
function onManualDateChange(){clearQuickDate();}
function setQuickDate(type){
  clearQuickDate();
  var now=new Date(),y=now.getFullYear(),m=now.getMonth(),d=now.getDate();
  var from,to;
  if(type==='bugun'){from=to=_fmtDate(now);}
  else if(type==='dun'){var d2=new Date(y,m,d-1);from=to=_fmtDate(d2);}
  else if(type==='yarin'){var d2=new Date(y,m,d+1);from=to=_fmtDate(d2);}
  else if(type==='bu_ay'){from=_fmtDate(new Date(y,m,1));to=_fmtDate(new Date(y,m+1,0));}
  else if(type==='gecen_ay'){from=_fmtDate(new Date(y,m-1,1));to=_fmtDate(new Date(y,m,0));}
  else if(type==='gelecek_ay'){from=_fmtDate(new Date(y,m+1,1));to=_fmtDate(new Date(y,m+2,0));}
  else if(type==='bu_yil'){from=_fmtDate(new Date(y,0,1));to=_fmtDate(new Date(y,11,31));}
  else if(type==='gecen_yil'){from=_fmtDate(new Date(y-1,0,1));to=_fmtDate(new Date(y-1,11,31));}
  else if(type==='gelecek_yil'){from=_fmtDate(new Date(y+1,0,1));to=_fmtDate(new Date(y+1,11,31));}
  document.getElementById('f-date-from').value=from;
  document.getElementById('f-date-to').value=to;
  var bid='qd-'+type;
  var btn=document.getElementById(bid);
  if(btn){btn.classList.add('qd-active');_activeQdId=bid;}
  // Yıl dropdown'u temizle (çakışmasın)
  var fy=document.getElementById('f-year');
  if(fy) fy.value='';
  filterLedger();
}

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
  clearQuickDate();
  filterLedger();
}
function clearDateRange(){
  document.getElementById('f-date-from').value='';
  document.getElementById('f-date-to').value='';
  clearQuickDate();
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
    tbody.innerHTML='<tr><td colspan="8"><div class="empty-state"><div class="icon">📋</div>İşlem bulunamadı</div></td></tr>';
    document.getElementById('ledger-count').textContent='';
    return;
  }
  tbody.innerHTML=data.map(function(t){
    var isG=t.type==='gelir';
    return '<tr data-id="'+t.id+'" data-type="'+t.type+'" onclick="showTxDetail('+t.id+')" style="cursor:pointer">'+
      '<td onclick="event.stopPropagation()"><div class="cell"><input type="checkbox" class="row-chk" data-id="'+t.id+'" onchange="rowChkChange()"></div></td>'+
      '<td><div class="cell">'+fmtDate(t.date)+'</div></td>'+
      '<td><div class="cell"><span class="badge '+(isG?'badge-g':'badge-r')+'">'+(isG?'Gelir':'Gider')+'</span></div></td>'+
      '<td><div class="cell"><span class="badge badge-cat">'+t.category+'</span></div></td>'+
      '<td><div class="cell" style="color:var(--txt2);font-size:.82rem">'+(t.description||'<span style="opacity:.4">—</span>')+'</div></td>'+
      '<td><div class="cell" style="font-size:.78rem;flex-direction:column;align-items:flex-start;gap:2px">'+
        (function(){
          if(t.card_id){
            var ctype=_cardType(t.card_id);
            var typeLabel=ctype==='yemek'?'🍽️ Yemek Kartı':ctype==='banka'?'🏧 Banka Kartı':ctype==='hediye'?'🎁 Hediye Kartı':'💳 Kredi Kartı';
            var name=_cardName(t.card_id);
            return '<span style="font-weight:700;color:var(--txt);font-size:.75rem">'+typeLabel+'</span>'+
                   (name?'<span style="color:var(--txt2);font-size:.7rem">'+name+'</span>':'');
          } else if(t.account_id){
            var aname=_accName(t.account_id);
            return '<span style="font-weight:700;color:var(--txt);font-size:.75rem">🏧 Banka Kartı</span>'+
                   (aname?'<span style="color:var(--txt2);font-size:.7rem">'+aname+'</span>':'');
          } else if(t.type==='gelir'){
            return '<span style="color:var(--txt2);font-size:.75rem">—</span>';
          } else {
            return '<span style="font-weight:700;color:var(--txt);font-size:.75rem">💵 Nakit</span>';
          }
        })()+
      '</div></td>'+
      '<td style="text-align:right"><div class="cell" style="justify-content:flex-end;font-weight:700;color:'+(isG?'var(--g)':'var(--r)')+'">'+
        (isG?'+':'-')+fmt(t.amount)+'</div></td>'+
      '<td onclick="event.stopPropagation()"><div class="cell" style="gap:4px">'+
        '<button class="del-row" title="Düzenle" onclick="openTxEdit('+t.id+')" style="background:var(--bg3);color:var(--txt2);border:1px solid var(--border)">✏️</button>'+
        '<button class="del-row" onclick="delTx('+t.id+')">✕</button>'+
      '</div></td>'+
    '</tr>';
  }).join('');
  document.getElementById('ledger-count').textContent=data.length+' işlem';

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
  renderMonthlySummary(allTx);
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

// ── İŞLEM DETAY MODALI ────────────────────────────────────────────────────────
function showTxDetail(id){
  var tx=allTx.find(function(t){return t.id==id}); if(!tx) return;
  var isG=tx.type==='gelir';
  var sign=isG?'+':'-';
  var col=isG?'#22c55e':'#ef4444';
  var m=document.getElementById('tx-detail-modal');
  if(!m) return;
  document.getElementById('txd-type').textContent=isG?'Gelir':'Gider';
  document.getElementById('txd-type').style.color=col;
  document.getElementById('txd-amount').textContent=sign+fmt(tx.amount);
  document.getElementById('txd-amount').style.color=col;
  document.getElementById('txd-category').textContent=tx.category||'—';
  document.getElementById('txd-desc').textContent=tx.description||'Açıklama yok';
  document.getElementById('txd-date').textContent=fmtDate(tx.date);
  document.getElementById('txd-edit-btn').onclick=function(){ closeTxDetail(); openTxEdit(id); };
  document.getElementById('txd-del-btn').onclick=function(){ closeTxDetail(); delTx(id); };
  m.style.display='flex';
}
function closeTxDetail(){
  var m=document.getElementById('tx-detail-modal'); if(m) m.style.display='none';
}

// ── İŞLEM DÜZENLEME MODALI ────────────────────────────────────────────────────
function txeSelectPayType(btn){
  document.querySelectorAll('#txe-pay-chips .pay-chip').forEach(function(b){b.classList.remove('active')});
  btn.classList.add('active');
  var pt=btn.dataset.eptype;
  var accRow=document.getElementById('txe-acc-row');
  var cardRow=document.getElementById('txe-card-row');
  if(accRow) accRow.style.display=(pt==='banka'?'block':'none');
  if(cardRow) cardRow.style.display=(pt==='kredi'||pt==='yemek'?'block':'none');
  var cardSel=document.getElementById('txe-card');
  if(cardSel&&(pt==='kredi'||pt==='yemek')){
    var filterType=pt==='yemek'?'yemek':'kredi';
    cardSel.innerHTML='<option value="">— Kart seçin —</option>';
    _allCards.filter(function(c){return c.card_type===filterType;}).forEach(function(c){
      var opt=document.createElement('option'); opt.value='card:'+c.id;
      opt.textContent=(pt==='yemek'?'🍽️':'💳')+' '+c.bank_name+(c.card_name?' · '+c.card_name:'');
      cardSel.appendChild(opt);
    });
  }
}

function openTxEdit(id){
  var tx=allTx.find(function(t){return t.id==id}); if(!tx) return;
  var m=document.getElementById('tx-edit-modal'); if(!m) return;
  document.getElementById('txe-id').value=id;
  document.getElementById('txe-date').value=tx.date||'';
  document.getElementById('txe-amount').value=tx.amount||'';
  document.getElementById('txe-desc').value=tx.description||'';
  var catSel=document.getElementById('txe-category');
  catSel.innerHTML='';
  var list=tx.type==='gelir'?CATS.gelir:CATS.gider;
  list.forEach(function(c){var o=document.createElement('option');o.value=o.textContent=c;if(c===tx.category)o.selected=true;catSel.appendChild(o);});

  var isGelir=tx.type==='gelir';
  // Ödeme türü bölümü
  var paySection=document.getElementById('txe-pay-section');
  var incAcc=document.getElementById('txe-income-acc');
  if(paySection) paySection.style.display=isGelir?'none':'block';
  if(incAcc) incAcc.style.display=isGelir?'block':'none';

  if(!isGelir){
    // Mevcut ödeme türünü belirle
    var curType='nakit';
    if(tx.card_id){
      var ctype=_cardType(tx.card_id);
      curType=ctype==='yemek'?'yemek':'kredi';
    } else if(tx.account_id){ curType='banka'; }
    var activeBtn=document.querySelector('#txe-pay-chips [data-eptype='+curType+']');
    if(activeBtn) txeSelectPayType(activeBtn);
    // Hesap dropdown doldur
    var txeAcc=document.getElementById('txe-account');
    if(txeAcc){
      txeAcc.innerHTML='<option value="">— Hesap seçin —</option>';
      (_allAccounts.length?_allAccounts:[]).forEach(function(a){
        var o=document.createElement('option');o.value=a.id;
        o.textContent=(a.bank?a.bank+' · ':'')+a.name;
        if(tx.account_id==a.id)o.selected=true;
        txeAcc.appendChild(o);
      });
    }
    // Kart mevcut seçimi
    var txeCard=document.getElementById('txe-card');
    if(txeCard&&tx.card_id){
      setTimeout(function(){
        var val='card:'+tx.card_id;
        if(txeCard.querySelector('option[value="'+val+'"]')) txeCard.value=val;
      },50);
    }
  } else {
    // Gelir hesap dropdown
    var txeInc=document.getElementById('txe-income-account');
    if(txeInc){
      txeInc.innerHTML='<option value="">— Belirtme (Nakit) —</option>';
      (_allAccounts.length?_allAccounts:[]).forEach(function(a){
        var o=document.createElement('option');o.value=a.id;
        o.textContent=(a.bank?a.bank+' · ':'')+a.name;
        if(tx.account_id==a.id)o.selected=true;
        txeInc.appendChild(o);
      });
    }
  }
  m.style.display='flex';
}
function closeTxEdit(){ var m=document.getElementById('tx-edit-modal'); if(m) m.style.display='none'; }
function saveTxEdit(){
  var id=document.getElementById('txe-id').value;
  var body={
    date:document.getElementById('txe-date').value,
    amount:document.getElementById('txe-amount').value,
    category:document.getElementById('txe-category').value,
    description:document.getElementById('txe-desc').value,
    account_id: null, card_id: null,
  };
  var activeChip=document.querySelector('#txe-pay-chips .pay-chip.active');
  var eptype=activeChip?activeChip.dataset.eptype:'nakit';
  if(eptype==='banka'){
    var txeAcc=document.getElementById('txe-account');
    if(txeAcc&&txeAcc.value) body.account_id=parseInt(txeAcc.value);
  } else if(eptype==='kredi'||eptype==='yemek'){
    var txeCard=document.getElementById('txe-card');
    var cv=txeCard?txeCard.value:'';
    if(cv&&cv.indexOf('card:')===0) body.card_id=parseInt(cv.split(':')[1]);
  } else {
    // Gelir hesabı
    var incAcc=document.getElementById('txe-income-account');
    if(incAcc&&incAcc.value) body.account_id=parseInt(incAcc.value);
  }
  xhr('/api/transactions/'+id,body,function(r){
    if(r.ok){closeTxEdit();toast('Kaydedildi');loadAllTx();loadDashboard();}
    else toast('Hata: '+(r.error||''),'#ef4444');
  },true);
}

function startEdit(td){ /* artık openTxEdit kullanılıyor */ }

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
  var url;
  if(_dateRangeActive){
    url='/api/summary?start='+_rangeStart+'&end='+_rangeEnd;
  } else if(_heroPeriod==='year'){
    url='/api/summary?period=year&year='+_heroYear;
  } else if(_heroPeriod==='all'){
    url='/api/summary?period=all';
  } else if(dbView==='year'){
    url='/api/summary?period=year&year='+curYear;
  } else {
    url='/api/summary?year='+curYear+'&month='+curMonth;
  }
  xhr(url,null,function(d){
    if(reqId !== _dashReqId) return;
    hideSplash();
    if(!d || d.error){
      if(_dashRetry < 4){
        _dashRetry++;
        var wait = _dashRetry * 3000;
        var rb=document.getElementById('dash-retry-bar');
        if(rb){ rb.style.display='flex'; rb.querySelector('span').textContent='🔄 Sunucu başlatılıyor... ('+_dashRetry+'/4)'; }
        setTimeout(function(){ loadDashboard(); }, wait);
      } else {
        var rb=document.getElementById('dash-retry-bar');
        if(rb){ rb.style.display='flex'; rb.querySelector('span').textContent='⚠️ '+(d&&d.error?d.error:'Bağlantı kurulamadı.'); }
      }
      return;
    }
    _dashRetry=0;
    var rb=document.getElementById('dash-retry-bar'); if(rb) rb.style.display='none';
    summaryData=d;
    renderStats(d);
    drawBar(d.bar);
    drawDonut(d.gider_cats);
    renderBudgetPage(d.gider_cats,d.budgets);
    if(dbView==='year'){ var sub=document.getElementById('db-sub'); if(sub) sub.textContent=curYear+' yılı'; }
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
  // Hesap dropdown'unu doldur
  var accSel=document.getElementById('inv-account');
  if(accSel&&accSel.options.length<=1){
    var src=_allAccounts.length?_allAccounts:null;
    function _fill(list){
      (list||[]).filter(function(a){return a.type==='vadesiz'||a.type==='vadeli'||a.type==='tasarruf';}).forEach(function(a){
        var o=document.createElement('option');o.value=a.id;o.textContent=(a.bank?a.bank+' · ':'')+a.name;accSel.appendChild(o);
      });
    }
    if(src) _fill(src);
    else xhr('/api/accounts',null,function(list){_allAccounts=list||[];_fill(_allAccounts);});
  }
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
  var accEl=document.getElementById('inv-account');
  var body = {
    name:       document.getElementById('inv-name').value.trim(),
    itype:      document.getElementById('inv-type').value,
    symbol:     document.getElementById('inv-sym').value.trim().toUpperCase(),
    quantity:   getNumVal(document.getElementById('inv-qty')),
    buy_price:  getNumVal(document.getElementById('inv-price')),
    buy_date:   document.getElementById('inv-date').value,
    note:       document.getElementById('inv-note').value,
    account_id: accEl&&accEl.value ? parseInt(accEl.value) : null,
  };
  if(!body.name || !body.quantity || !body.buy_price){ toast('İsim, miktar ve fiyat zorunlu'); return; }
  xhr('/api/investments', body, function(r){
    if(r.ok){
      var cost=body.quantity*body.buy_price;
      toast('Portföye eklendi — ₺'+fmt(cost)+' gider kaydedildi ✓');
      loadInvestments(); loadDashboard(); loadAllTx();
      document.getElementById('inv-name').value='';
      document.getElementById('inv-qty').value='';
      document.getElementById('inv-price').value='';
      if(accEl) accEl.value='';
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
          '<div style="display:flex;gap:6px">'+
            '<button class="btn btn-green" style="font-size:.72rem;padding:4px 10px" onclick="openSellModal('+inv.id+',\''+inv.name.replace(/'/g,'\\\'')+'\',' +inv.quantity+','+inv.buy_price+')">Sat</button>'+
            '<button class="del-row" onclick="delInv('+inv.id+')">✕</button>'+
          '</div>'+
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

var _sellInvId=null;
function openSellModal(id,name,qty,buyPrice){
  _sellInvId=id;
  var m=document.getElementById('sell-inv-modal');
  if(!m){ // modal yoksa oluştur
    m=document.createElement('div');
    m.id='sell-inv-modal';
    m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px';
    m.innerHTML='<div style="background:var(--bg2);border-radius:16px;padding:24px;width:100%;max-width:360px;box-shadow:0 8px 32px rgba(0,0,0,.3)">'
      +'<div style="font-size:1rem;font-weight:800;margin-bottom:16px">💰 Yatırım Sat</div>'
      +'<div id="sell-inv-info" style="font-size:.82rem;color:var(--txt2);margin-bottom:14px"></div>'
      +'<div style="margin-bottom:12px"><label style="font-size:.8rem;color:var(--txt2)">Satış Fiyatı (birim, TRY)</label>'
      +'<input class="f-input" type="text" inputmode="decimal" data-num id="sell-inv-price" placeholder="0,00"></div>'
      +'<div style="margin-bottom:12px"><label style="font-size:.8rem;color:var(--txt2)">Satış Tarihi</label>'
      +'<input class="f-input" type="date" id="sell-inv-date"></div>'
      +'<div style="margin-bottom:16px"><label style="font-size:.8rem;color:var(--txt2)">Gelir hangi hesaba? <span style="opacity:.6">(opsiyonel)</span></label>'
      +'<select class="f-input" id="sell-inv-account"><option value="">— Hesap seçme —</option></select></div>'
      +'<div style="display:flex;gap:8px">'
      +'<button class="btn btn-ghost" style="flex:1" onclick="document.getElementById(\'sell-inv-modal\').style.display=\'none\'">İptal</button>'
      +'<button class="btn btn-green" style="flex:1" onclick="confirmSell()">Sat & Kaydet</button>'
      +'</div></div>';
    document.body.appendChild(m);
  }
  document.getElementById('sell-inv-info').textContent=name+' — '+qty+' adet, alış: '+fmt(qty*buyPrice);
  var dp=document.getElementById('sell-inv-date'); if(dp) dp.value=new Date().toISOString().split('T')[0];
  var sp=document.getElementById('sell-inv-price'); if(sp){sp.value='';setTimeout(function(){sp.focus();},100);}
  // hesap doldur
  var accSel=document.getElementById('sell-inv-account');
  if(accSel&&accSel.options.length<=1){
    function _f(list){(list||[]).filter(function(a){return a.type==='vadesiz'||a.type==='vadeli'||a.type==='tasarruf';}).forEach(function(a){var o=document.createElement('option');o.value=a.id;o.textContent=(a.bank?a.bank+' · ':'')+a.name;accSel.appendChild(o);});}
    if(_allAccounts.length) _f(_allAccounts);
    else xhr('/api/accounts',null,function(l){_allAccounts=l||[];_f(_allAccounts);});
  }
  m.style.display='flex';
}
function confirmSell(){
  var price=getNumVal(document.getElementById('sell-inv-price'));
  var dt=document.getElementById('sell-inv-date').value;
  var accEl=document.getElementById('sell-inv-account');
  if(!price||price<=0){toast('Satış fiyatı giriniz','#ef4444');return;}
  xhr('/api/investments/'+_sellInvId+'/sell',
    {sell_price:price,sell_date:dt,account_id:accEl&&accEl.value?parseInt(accEl.value):null},
    function(r){
      if(r.ok){
        document.getElementById('sell-inv-modal').style.display='none';
        toast('Satış kaydedildi — ₺'+fmt(r.proceeds)+' gelir eklendi'+(r.profit!==0?' (K/Z: ₺'+(r.profit>=0?'+':'')+fmt(r.profit)+')':'')+'  ✓');
        loadInvestments(); loadDashboard(); loadAllTx();
      }
    });
}

function bookIncome(invId, amount, name){
  var today = new Date().toISOString().split('T')[0];
  xhr('/api/investments/'+invId+'/book-income',
    {amount: amount, description: name+' — Yatırım Getirisi', category: 'Yatırım / Temettü', date: today},
    function(r){ if(r.ok){ toast('Gelir hanesine yazıldı ✓'); loadDashboard(); loadAllTx(); }});
}

// ── RECURRING ─────────────────────────────────────────────────────────────────
var recTab = 'gelir';

var _recSelDays = [];

function _buildDayChips(){
  var el = document.getElementById('rec-days-chips');
  if(!el) return;
  el.innerHTML = '';
  for(var i=1; i<=31; i++){
    (function(day){
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = day;
      var sel = _recSelDays.indexOf(day) >= 0;
      btn.style.cssText = 'width:38px;height:38px;border-radius:10px;border:1.5px solid '+(sel?'var(--b)':'var(--border2)')+
        ';background:'+(sel?'var(--b)':'var(--bg3)')+';color:'+(sel?'#fff':'var(--txt2)')+
        ';font-size:.82rem;font-weight:700;cursor:pointer;transition:.12s;-webkit-tap-highlight-color:transparent';
      btn.onclick = function(){
        var idx = _recSelDays.indexOf(day);
        if(idx >= 0) _recSelDays.splice(idx, 1);
        else _recSelDays.push(day);
        _recSelDays.sort(function(a,b){return a-b});
        _buildDayChips();
        _updateDaysLbl();
      };
      el.appendChild(btn);
    })(i);
  }
  _updateDaysLbl();
}

function _updateDaysLbl(){
  var lbl = document.getElementById('rec-days-lbl');
  if(!lbl) return;
  lbl.textContent = _recSelDays.length ? _recSelDays.join(', ')+'. gün seçildi' : '';
}

function initRecurringPage(){
  fillSel('rec-cat', CATS[recTab]);
  var now = new Date().getFullYear();
  var opts = '';
  for(var y=now-2; y<=now+5; y++){
    opts += '<option value="'+y+'"'+(y===now?' selected':'')+'>'+y+'</option>';
  }
  var ys = document.getElementById('rec-apply-year');
  var ye = document.getElementById('rec-apply-year-end');
  if(ys) ys.innerHTML = opts;
  if(ye) ye.innerHTML = opts;
  _buildDayChips();
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
              '<div style="font-size:.75rem;color:var(--txt2)">'+r.category+' &middot; Her ayın <strong>'+(r.days_of_month&&r.days_of_month.trim()?r.days_of_month.split(',').join('. ')+(r.days_of_month.split(',').length>1?'. günleri':'. günü'):r.day_of_month+'. günü')+'</strong></div>'+
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
  if(!amount || amount<=0){toast('Tutar giriniz'); return}
  if(!_recSelDays.length){toast('En az bir gün seçiniz'); return}
  xhr('/api/recurring', {type:recTab, amount:amount, category:cat, description:desc, days_of_month:_recSelDays}, function(r){
    if(r.ok){
      toast('Şablon kaydedildi ✓');
      document.getElementById('rec-amount').value = '';
      document.getElementById('rec-desc').value = '';
      _recSelDays = []; _buildDayChips();
      loadRecurring();
    }
  });
}

function delRecurring(id){
  xhr('/api/recurring/'+id, null, function(){loadRecurring(); toast('Silindi')}, false, true);
}

function applyRecurring(){
  var yearStart = parseInt(document.getElementById('rec-apply-year').value);
  var yearEnd   = parseInt((document.getElementById('rec-apply-year-end')||{}).value || yearStart);
  var mStart    = parseInt(document.getElementById('rec-apply-month-start').value);
  var mEnd      = parseInt(document.getElementById('rec-apply-month-end').value);
  if(yearEnd < yearStart){ toast('Bitiş yılı başlangıç yılından önce olamaz'); return; }
  var body = {year_start: yearStart, year_end: yearEnd, month_start: mStart, month_end: mEnd};
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
      '<td>'+fmtDate(r.date)+'</td>'+
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
  r.onload=function(){
    if(r.status===401){ location.href='/login'; return; }
    try{cb&&cb(JSON.parse(r.responseText));}
    catch(e){ cb&&cb(null); }
  };
  r.onerror=function(){ cb&&cb(null); };
  r.ontimeout=function(){ cb&&cb(null); };
  r.timeout=30000; // 30s: Railway cold start için
  r.send(body?JSON.stringify(body):null);
}

// ── CARDS ────────────────────────────────────────────────────────────────────
function selectCardType(btn){
  document.querySelectorAll('.acc-type-chip[data-ctype]').forEach(function(b){b.classList.remove('active')});
  btn.classList.add('active');
  var t=btn.dataset.ctype;
  var typeVal=document.getElementById('card-type-val');
  if(typeVal) typeVal.value=t;
  // Kredi alanlarını göster/gizle
  var creditFields=document.getElementById('card-credit-fields');
  var minPctRow=document.getElementById('card-minpct-row');
  // Son ödeme + ekstre sadece kredi kartında; asgari ödeme de sadece kredi
  if(creditFields) creditFields.style.display=t==='kredi'?'':'none';
  if(minPctRow) minPctRow.style.display=t==='kredi'?'':'none';
  // Etiketleri güncelle
  var limitLbl=document.getElementById('card-limit-lbl');
  var usedLbl=document.getElementById('card-used-lbl');
  if(limitLbl) limitLbl.textContent=t==='yemek'?'Aylık Limit (₺)':t==='hediye'?'Bakiye (₺)':'Limit (₺)';
  if(usedLbl) usedLbl.textContent=t==='yemek'?'Kullanılan (₺)':t==='hediye'?'Harcanan (₺)':'Mevcut Borç (₺)';
}

function addCard(){
  var ctype=document.getElementById('card-type-val');
  var cardType=ctype?ctype.value:'kredi';
  var body = {
    bank_name:    document.getElementById('card-bank').value,
    card_name:    document.getElementById('card-name').value,
    owner:        document.getElementById('card-owner').value,
    limit_:       getNumVal(document.getElementById('card-limit'))||0,
    used_:        getNumVal(document.getElementById('card-used'))||0,
    due_day:      parseInt(document.getElementById('card-due').value)||15,
    statement_day:parseInt(document.getElementById('card-stmt').value)||20,
    min_pct:      parseFloat(document.getElementById('card-minpct').value)||25,
    card_type:    cardType,
  };
  if(!body.bank_name){ toast('Banka/kurum seçiniz'); return; }
  if(cardType!=='yemek'&&cardType!=='hediye'&&!body.limit_){ toast('Limit giriniz'); return; }
  xhr('/api/cards', body, function(r){
    if(r.ok){
      toast('Kart kaydedildi ✓');
      xhr('/api/cards',null,function(list){
        if(list) _allCards=list;
        loadCards(); loadCardsDropdown(); loadDashboard();
      });
      ['card-name','card-limit','card-used','card-owner'].forEach(function(id){
        var el=document.getElementById(id); if(el) el.value='';
      });
    }
  });
}

function loadCards(){
  xhr('/api/cards', null, function(list){
    var el = document.getElementById('card-list');
    if(!list.length){ el.innerHTML='<div class="empty-state"><div class="icon">💳</div>Henüz kart eklenmedi</div>'; document.getElementById('card-totals').style.display='none'; return; }
    var totalLimit=0, totalUsed=0;
    var today = new Date().getDate();
    var _ctypeIco={'kredi':'💳','banka':'🏧','yemek':'🍽️','hediye':'🎁'};
    var _ctypeGroups=[
      {key:'kredi', label:'💳 Kredi Kartları'},
      {key:'banka', label:'🏧 Banka Kartları'},
      {key:'yemek', label:'🍽️ Yemek Kartları'},
      {key:'hediye',label:'🎁 Hediye Kartları'},
    ];
    var grouped={};
    list.forEach(function(c){
      var t=c.card_type||'kredi';
      if(!grouped[t]) grouped[t]=[];
      grouped[t].push(c);
      totalLimit+=(c.limit_||0); totalUsed+=(c.used_||0);
    });
    var html='';
    _ctypeGroups.forEach(function(g){
      var grpList=grouped[g.key]||[];
      if(!grpList.length) return;
      html+='<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--txt2);margin:8px 0 6px;padding:0 2px">'+g.label+'</div>';
      html+=grpList.map(function(c){
      var ctype   = c.card_type||'kredi';
      var ico     = _ctypeIco[ctype]||'💳';
      var avail   = (c.limit_||0) - (c.used_||0);
      var usePct  = c.limit_>0 ? Math.min(100, Math.round((c.used_||0) / c.limit_ * 100)) : 0;
      var isKredi = ctype==='kredi';
      var minPay  = isKredi ? Math.round((c.used_||0) * (c.min_pct||25) / 100) : 0;
      var color   = usePct>80 ? 'var(--r)' : usePct>50 ? 'var(--y)' : 'var(--g)';
      var daysLeft = c.due_day >= today ? c.due_day - today : 30 - today + c.due_day;
      totalLimit += (c.limit_||0); totalUsed += (c.used_||0);
      var isYemek = ctype==='yemek'; var isHediye = ctype==='hediye';
      var cJson=JSON.stringify({id:c.id,bank_name:c.bank_name,card_name:c.card_name,owner:c.owner,limit_:c.limit_,used_:c.used_,due_day:c.due_day,statement_day:c.statement_day,min_pct:c.min_pct,card_type:ctype}).replace(/"/g,'&quot;');
      return '<div style="background:var(--bg2);border-radius:14px;border:1px solid var(--border);padding:15px 16px;margin-bottom:10px" data-card-id="'+c.id+'" data-card="'+cJson+'">'+
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">'+
          _bankLogo(c.bank_name)+
          '<div style="min-width:0;flex:1">'+
            '<div style="font-weight:700;font-size:.92rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+c.bank_name+(c.card_name?' · '+c.card_name:'')+'</div>'+
            '<div style="display:flex;align-items:center;gap:6px;margin-top:3px">'+
              '<span style="font-size:.68rem;color:var(--txt2);background:var(--bg3);padding:1px 7px;border-radius:5px">'+
                (isYemek?'🍽️ Yemek':isHediye?'🎁 Hediye':ctype==='banka'?'🏧 Banka':'💳 Kredi')+'</span>'+
              (c.owner?'<span style="font-size:.68rem;color:var(--b2)">👤 '+c.owner+'</span>':'')+
            '</div>'+
          '</div>'+
          '<button class="del-row" onclick="delCard('+c.id+')">✕</button>'+
        '</div>'+
        '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-size:.78rem;margin-bottom:12px">'+
          '<div><div style="color:var(--txt2)">Limit</div><div style="font-weight:700">'+fmt(c.limit_||0)+'</div></div>'+
          '<div><div style="color:var(--txt2)">'+(isYemek||isHediye?'Kullanılan':'Borç')+'</div><div style="font-weight:700;color:var(--r)">'+fmt(c.used_||0)+'</div></div>'+
          '<div><div style="color:var(--txt2)">Kullanılabilir</div><div style="font-weight:700;color:'+(avail<0?'var(--r)':'var(--g)')+'">'+fmt(avail)+'</div></div>'+
        '</div>'+
        (c.limit_>0?'<div class="prog-bg" style="margin-bottom:10px"><div class="prog-fill" style="width:'+usePct+'%;background:'+color+'"></div></div>':'')+
        (isKredi?
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
          '</div>':'')+
        '<div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">'+
          '<button class="btn btn-primary" style="flex:1;min-width:120px;font-size:.82rem" onclick="openCardPayModal('+c.id+',\''+c.bank_name+(c.card_name?' '+c.card_name:'')+'\','+c.used_+','+minPay+','+(c.limit_||0)+')">'+ico+' Ödeme Yap</button>'+
          '<button class="btn btn-ghost" style="font-size:.78rem;padding:8px 12px" onclick="openCardEdit({id:'+c.id+',bank_name:\''+c.bank_name+'\',card_name:\''+(c.card_name||'')+'\',owner:\''+(c.owner||'')+'\',limit_:'+(c.limit_||0)+',used_:'+(c.used_||0)+',due_day:'+(c.due_day||15)+',statement_day:'+(c.statement_day||20)+',min_pct:'+(c.min_pct||25)+',card_type:\''+(ctype||'kredi')+'\'})">✏️ Düzenle</button>'+
        '</div>'+
      '</div>';
      }).join('');
    });
    el.innerHTML=html;
    document.getElementById('card-totals').style.display='block';
    document.getElementById('ct-limit').textContent = fmt(totalLimit);
    document.getElementById('ct-used').textContent  = fmt(totalUsed);
    document.getElementById('ct-avail').textContent = fmt(totalLimit-totalUsed);
  });
}

// ── KART ÖDEME MODALI ────────────────────────────────────────────────────────
var _payCardId=0;
function openCardPayModal(id, name, debt, minPay, limit){
  _payCardId=id;
  var m=document.getElementById('card-pay-modal'); if(!m) return;
  document.getElementById('cpay-name').textContent=name;
  document.getElementById('cpay-debt').textContent=fmt(debt);
  document.getElementById('cpay-min').textContent=fmt(minPay);
  document.getElementById('cpay-avail').textContent=fmt(limit-debt);
  document.getElementById('cpay-amount').value='';
  document.getElementById('cpay-asgari-val').textContent=fmt(minPay);
  document.getElementById('cpay-tam-val').textContent=fmt(debt);
  // Vadesiz hesap dropdown'unu doldur
  var accSel=document.getElementById('cpay-account');
  if(accSel){
    // Kredi kartı ödemesi sadece vadesiz veya KMH ile yapılabilir
    function _fillCpayAccounts(list){
      accSel.innerHTML='<option value="">— Nakit (Hesap Seçme) —</option>';
      (list||[]).filter(function(a){return a.type==='vadesiz'||a.type==='kmh';}).forEach(function(a){
        var opt=document.createElement('option');
        opt.value=a.id;
        var ico=a.type==='kmh'?'🔄':'🏦';
        opt.textContent=ico+' '+(a.bank?a.bank+' · ':'')+a.name;
        accSel.appendChild(opt);
      });
    }
    if(_allAccounts.length){ _fillCpayAccounts(_allAccounts); }
    else { xhr('/api/accounts',null,function(list){ _allAccounts=list||[]; _fillCpayAccounts(_allAccounts); }); }
  }
  m.style.display='flex';
}
function closeCardPayModal(){ var m=document.getElementById('card-pay-modal'); if(m) m.style.display='none'; }
function setCardPayAmount(val){ document.getElementById('cpay-amount').value=val; }
function confirmCardPay(){
  var amount=parseFloat((document.getElementById('cpay-amount').value||'').replace(',','.'));
  if(!amount||amount<=0){toast('Tutar giriniz','#ef4444');return;}
  var accSel=document.getElementById('cpay-account');
  var accId=accSel&&accSel.value?parseInt(accSel.value):null;
  xhr('/api/cards/'+_payCardId+'/pay',{amount:amount,account_id:accId},function(r){
    if(r.ok){
      closeCardPayModal();
      toast('✅ Ödeme kaydedildi — '+fmt(r.paid)+' ödendi, kalan borç: '+fmt(r.new_debt),'#22c55e');
      loadCards(); loadDashboard();
    } else { toast(r.error||'Hata','#ef4444'); }
  });
}

var _editCardId=0;
function openCardEdit(c){
  _editCardId=c.id;
  var m=document.getElementById('card-edit-modal'); if(!m) return;
  document.getElementById('ce-bank').value=c.bank_name||'';
  document.getElementById('ce-name').value=c.card_name||'';
  document.getElementById('ce-owner').value=c.owner||'';
  document.getElementById('ce-limit').value=(c.limit_||0).toString();
  document.getElementById('ce-used').value=(c.used_||0).toString();
  document.getElementById('ce-due').value=(c.due_day||15).toString();
  document.getElementById('ce-stmt').value=(c.statement_day||20).toString();
  document.getElementById('ce-minpct').value=(c.min_pct||25).toString();
  // Kart türü
  document.querySelectorAll('#ce-ctype-chips .acc-type-chip').forEach(function(b){
    b.classList.toggle('active',b.dataset.ctype===(c.card_type||'kredi'));
  });
  m.style.display='flex';
}
function saveCardEdit(){
  var body={
    bank_name:document.getElementById('ce-bank').value,
    card_name:document.getElementById('ce-name').value,
    owner:document.getElementById('ce-owner').value,
    limit_:parseFloat(document.getElementById('ce-limit').value)||0,
    used_:parseFloat(document.getElementById('ce-used').value)||0,
    due_day:parseInt(document.getElementById('ce-due').value)||15,
    statement_day:parseInt(document.getElementById('ce-stmt').value)||20,
    min_pct:parseFloat(document.getElementById('ce-minpct').value)||25,
    card_type:(document.querySelector('#ce-ctype-chips .acc-type-chip.active')||{}).dataset&&document.querySelector('#ce-ctype-chips .acc-type-chip.active').dataset.ctype||'kredi',
  };
  xhr('/api/cards/'+_editCardId,body,function(r){
    if(r&&r.ok){toast('Güncellendi ✓');document.getElementById('card-edit-modal').style.display='none';loadCards();}
  },true);
}
function openCardUpdateModal(id, currentDebt){
  // Eski yöntem — doğrudan borç güncelle
  var c={}; try{ c=JSON.parse(document.querySelector('[data-card-id="'+id+'"]').dataset.card); }catch(e){}
  openCardEdit(Object.assign({id:id,used_:currentDebt},c));
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
function exportPDF(year, month){
  var fromEl = document.getElementById('f-date-from');
  var toEl   = document.getElementById('f-date-to');
  var from   = fromEl && fromEl.value;
  var to     = toEl   && toEl.value;
  var url;
  if(from && to){
    url = '/api/export/pdf?start='+from+'&end='+to;
  } else {
    var y = year  || curYear;
    var m = month || curMonth;
    url = '/api/export/pdf?year='+y+'&month='+m;
  }
  window.open(url, '_blank');
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

<!-- trial banner kaldırıldı — abonelik bilgisi profil dropdown'da gösterilmektedir -->

<!-- PREMIUM REQUIRED MODAL -->
<div id="premium-modal" style="display:none;position:fixed;inset:0;z-index:9200;background:rgba(0,0,0,.75);align-items:center;justify-content:center">
  <div style="background:#111318;border:1px solid #1e2233;border-radius:20px;padding:36px 32px;max-width:380px;width:90%;text-align:center">
    <div style="font-size:2.5rem;margin-bottom:12px">🔒</div>
    <div style="font-size:1.1rem;font-weight:800;color:#e2e8f0;margin-bottom:8px">Premium Özellik</div>
    <div id="premium-modal-text" style="font-size:.85rem;color:#64748b;margin-bottom:24px;line-height:1.6">Bu özellik Premium üyelik gerektirir.</div>
    <div style="display:flex;gap:10px">
      <a href="/premium" style="flex:1;padding:12px;background:linear-gradient(135deg,#6366f1,#a855f7);color:#fff;border-radius:10px;text-decoration:none;font-weight:700;font-size:.88rem">Premium'a Geç →</a>
      <button onclick="closePremiumModal()" style="flex:1;padding:12px;background:#1e2233;color:#94a3b8;border:none;border-radius:10px;font-size:.88rem;cursor:pointer">Kapat</button>
    </div>
  </div>
</div>

<script>
// ── ABONELİK DURUMU ──────────────────────────────────────────────────────────
var _kirpiSub = null;

function loadSubStatus() {
  fetch('/api/me').then(r => r.json()).then(d => {
    if (!d.subscription) return;
    _kirpiSub = d.subscription;
    _renderDropdownSubRow();
    applyPremiumLocks();
  }).catch(function(){});
}

function _renderDropdownSubRow() {
  var el = document.getElementById('udrop-sub-row');
  if (!el || !_kirpiSub) return;
  var s = _kirpiSub;
  if (s.status === 'premium') {
    el.innerHTML = '<div style="display:flex;align-items:center;gap:8px;padding:6px 10px;background:#22c55e12;border-radius:8px">'
      + '<span style="font-size:.85rem">⭐</span>'
      + '<div><div style="font-size:.78rem;font-weight:700;color:#22c55e">Premium Üye</div>'
      + '<div style="font-size:.68rem;color:var(--txt2)">' + s.days_left + ' gün kaldı</div></div></div>';
  } else if (s.status === 'trial') {
    el.innerHTML = '<a href="/premium" style="display:flex;align-items:center;gap:8px;padding:6px 10px;background:#6366f112;border-radius:8px;text-decoration:none">'
      + '<span style="font-size:.85rem">🎁</span>'
      + '<div><div style="font-size:.78rem;font-weight:700;color:#818cf8">Deneme — ' + s.days_left + ' gün</div>'
      + '<div style="font-size:.68rem;color:var(--txt2)">Premium\'a geç →</div></div></a>';
  } else {
    el.innerHTML = '<a href="/premium" style="display:flex;align-items:center;gap:8px;padding:8px 10px;background:linear-gradient(135deg,#6366f1,#a855f7);border-radius:8px;text-decoration:none">'
      + '<span style="font-size:.9rem">🚀</span>'
      + '<div><div style="font-size:.8rem;font-weight:800;color:#fff">Premium\'a Geç</div>'
      + '<div style="font-size:.68rem;color:rgba(255,255,255,.75)">₺49/ay · Tüm özellikler</div></div></a>';
  }
}

function isPremium() {
  return _kirpiSub && _kirpiSub.is_premium;
}

function showPremiumModal(msg) {
  var m = document.getElementById('premium-modal');
  var t = document.getElementById('premium-modal-text');
  if (t) t.textContent = msg || 'Bu özellik Premium üyelik gerektirir. İlk 30 gün ücretsiz deniyebilirsiniz.';
  if (m) m.style.display = 'flex';
}

function closePremiumModal() {
  var m = document.getElementById('premium-modal');
  if (m) m.style.display = 'none';
}

function guardPremium(msg, callback) {
  if (isPremium()) { callback(); return; }
  showPremiumModal(msg);
}

function applyPremiumLocks() {
  if (isPremium()) return;
  // Sidebar menü öğelerine kilit ikonu ekle
  var premiumMenuIds = ['nav-investments','nav-assets','nav-suppliers'];
  premiumMenuIds.forEach(function(id) {
    var el = document.getElementById(id);
    if (el && !el.querySelector('.lock-icon')) {
      var lock = document.createElement('span');
      lock.className = 'lock-icon';
      lock.textContent = ' 🔒';
      lock.style.cssText = 'font-size:.7rem;opacity:.6';
      el.appendChild(lock);
    }
  });
}

document.addEventListener('DOMContentLoaded', loadSubStatus);

// ── İŞLEM DETAY (dashboard today kartı) ──────────────────────────────────────
function showTxDayDetail(t){
  var isG=t.type==='gelir'; var col=isG?'#22c55e':'#ef4444';
  var m=document.getElementById('tx-detail-modal'); if(!m) return;
  document.getElementById('txd-type').textContent=isG?'Gelir':'Gider';
  document.getElementById('txd-type').style.color=col;
  document.getElementById('txd-amount').textContent=(isG?'+':'-')+fmt(t.amount);
  document.getElementById('txd-amount').style.color=col;
  document.getElementById('txd-category').textContent=t.category||'—';
  document.getElementById('txd-desc').textContent=t.description||'Açıklama yok';
  document.getElementById('txd-date').textContent=fmtDate(t.date||'');
  document.getElementById('txd-edit-btn').onclick=function(){ closeTxDetail(); if(t.id) openTxEdit(t.id); };
  document.getElementById('txd-del-btn').onclick=function(){ closeTxDetail(); if(t.id) delTx(t.id); };
  m.style.display='flex';
}

// ── NET LİKİDİTE DETAYI ───────────────────────────────────────────────────────
function showLiquidityDetail(){
  var m=document.getElementById('liquidity-detail-modal'); if(!m) return;
  var d=window._lastInsightData||{};
  document.getElementById('lqd-balance').textContent='₺'+(d.total_balance||0).toLocaleString('tr-TR');
  document.getElementById('lqd-card').textContent='−₺'+(d.card_debt||0).toLocaleString('tr-TR');
  document.getElementById('lqd-net').textContent=(d.net_liquidity>=0?'+':'−')+'₺'+Math.abs(d.net_liquidity||0).toLocaleString('tr-TR');
  document.getElementById('lqd-net').style.color=(d.net_liquidity||0)>=0?'#4ade80':'#f87171';
  m.style.display='flex';
}
function closeLiquidityDetail(){ var m=document.getElementById('liquidity-detail-modal'); if(m) m.style.display='none'; }

function showAvailableLimitModal(){
  var m=document.getElementById('avail-limit-modal');
  var list=document.getElementById('avail-limit-list');
  if(!m||!list) return;
  var cards=_allCards||[];
  var available=cards.filter(function(c){ return (c.card_type==='kredi'||c.card_type==='banka')&&c.limit_>0&&(c.limit_-c.used_)>0; });
  if(!available.length){
    list.innerHTML='<div style="text-align:center;padding:20px;color:var(--txt2);font-size:.86rem">Kullanılabilir limitli kart yok.</div>';
  } else {
    list.innerHTML=available.map(function(c){
      var avail=Math.round(c.limit_-c.used_);
      var pct=Math.round((c.used_/c.limit_)*100);
      var barColor=pct>80?'var(--r)':pct>50?'var(--y)':'var(--g)';
      return '<div style="background:var(--bg3);border-radius:14px;padding:14px 16px">'
        +'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">'
        +'<div style="font-size:.86rem;font-weight:700;color:var(--txt)">💳 '+c.bank_name+(c.card_name?' · '+c.card_name:'')+'</div>'
        +'<div style="font-size:.9rem;font-weight:800;color:var(--g)">₺'+avail.toLocaleString('tr-TR')+'</div>'
        +'</div>'
        +'<div style="background:var(--bg);border-radius:4px;height:6px;overflow:hidden;margin-bottom:6px">'
        +'<div style="width:'+pct+'%;height:100%;background:'+barColor+';border-radius:4px;transition:width .5s"></div>'
        +'</div>'
        +'<div style="display:flex;justify-content:space-between;font-size:.72rem;color:var(--txt2)">'
        +'<span>Kullanılan: ₺'+Math.round(c.used_).toLocaleString('tr-TR')+'</span>'
        +'<span>Limit: ₺'+Math.round(c.limit_).toLocaleString('tr-TR')+'</span>'
        +'</div>'
        +'</div>';
    }).join('');
  }
  m.style.display='flex';
}
function closeAvailLimitModal(){ var m=document.getElementById('avail-limit-modal'); if(m) m.style.display='none'; }
</script>

<!-- KART ÖDEME MODALI -->
<div id="card-pay-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:9999;align-items:flex-end;justify-content:center" onclick="if(event.target===this)closeCardPayModal()">
  <div style="background:var(--bg2);border-radius:20px 20px 0 0;width:100%;max-width:480px;padding:28px 24px 40px;border-top:1px solid var(--border)">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
      <div style="font-size:1rem;font-weight:800;color:var(--txt)">💳 Ödeme Yap</div>
      <button onclick="closeCardPayModal()" style="width:32px;height:32px;border-radius:50%;border:1px solid var(--border2);background:var(--bg3);color:var(--txt2);cursor:pointer">✕</button>
    </div>
    <div id="cpay-name" style="font-size:.85rem;color:var(--b2);font-weight:600;margin-bottom:16px"></div>

    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:20px">
      <div style="background:var(--bg3);border-radius:10px;padding:10px;text-align:center">
        <div style="font-size:.65rem;color:var(--txt2);margin-bottom:3px">Mevcut Borç</div>
        <div id="cpay-debt" style="font-size:.9rem;font-weight:800;color:var(--r)"></div>
      </div>
      <div style="background:var(--bg3);border-radius:10px;padding:10px;text-align:center">
        <div style="font-size:.65rem;color:var(--txt2);margin-bottom:3px">Asgari Ödeme</div>
        <div id="cpay-min" style="font-size:.9rem;font-weight:800;color:var(--y)"></div>
      </div>
      <div style="background:var(--bg3);border-radius:10px;padding:10px;text-align:center">
        <div style="font-size:.65rem;color:var(--txt2);margin-bottom:3px">Kullanılabilir</div>
        <div id="cpay-avail" style="font-size:.9rem;font-weight:800;color:var(--g)"></div>
      </div>
    </div>

    <div style="display:flex;gap:8px;margin-bottom:14px">
      <button onclick="setCardPayAmount(document.getElementById('cpay-asgari-val').textContent.replace(/[₺.]/g,'').replace(',','.'))" class="btn btn-ghost" style="flex:1;font-size:.78rem">
        Asgari Öde<br><span id="cpay-asgari-val" style="font-weight:700;color:var(--y)"></span>
      </button>
      <button onclick="setCardPayAmount(document.getElementById('cpay-tam-val').textContent.replace(/[₺.]/g,'').replace(',','.'))" class="btn btn-ghost" style="flex:1;font-size:.78rem">
        Tamamını Öde<br><span id="cpay-tam-val" style="font-weight:700;color:var(--r)"></span>
      </button>
    </div>

    <label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:6px">Ödeme Tutarı (₺)</label>
    <input type="number" id="cpay-amount" class="f-input" step="0.01" placeholder="0,00" style="margin-bottom:12px">
    <label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:6px">🏦 Hangi Hesaptan Ödeniyor? <span style="opacity:.5">(opsiyonel)</span></label>
    <select id="cpay-account" class="f-input" style="margin-bottom:16px">
      <option value="">— Hesap Belirtme —</option>
    </select>
    <button onclick="confirmCardPay()" class="btn btn-primary" style="width:100%;padding:13px;font-size:.92rem">Ödemeyi Kaydet</button>
    <div style="font-size:.72rem;color:var(--txt2);text-align:center;margin-top:10px">Ödeme gider olarak kaydedilir, kart borcunuzdan düşülür.</div>
  </div>
</div>

<!-- İŞLEM DETAY MODALI -->
<div id="tx-detail-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:9999;align-items:flex-end;justify-content:center;padding:0" onclick="if(event.target===this)closeTxDetail()">
  <div style="background:var(--bg2);border-radius:20px 20px 0 0;width:100%;max-width:480px;padding:28px 24px 40px;border-top:1px solid var(--border)">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
      <div>
        <div id="txd-type" style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px">—</div>
        <div id="txd-amount" style="font-size:2rem;font-weight:900">—</div>
      </div>
      <button onclick="closeTxDetail()" style="width:32px;height:32px;border-radius:50%;border:1px solid var(--border2);background:var(--bg3);color:var(--txt2);cursor:pointer;font-size:.9rem">✕</button>
    </div>
    <div style="display:flex;flex-direction:column;gap:12px;margin-bottom:24px">
      <div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--border)">
        <span style="font-size:.8rem;color:var(--txt2)">Kategori</span>
        <span id="txd-category" style="font-size:.85rem;font-weight:600;color:var(--txt)">—</span>
      </div>
      <div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--border)">
        <span style="font-size:.8rem;color:var(--txt2)">Tarih</span>
        <span id="txd-date" style="font-size:.85rem;color:var(--txt)">—</span>
      </div>
      <div style="padding:10px 0">
        <div style="font-size:.8rem;color:var(--txt2);margin-bottom:6px">Açıklama</div>
        <div id="txd-desc" style="font-size:.88rem;color:var(--txt);line-height:1.5">—</div>
      </div>
    </div>
    <div style="display:flex;gap:10px">
      <button id="txd-edit-btn" style="flex:1;padding:12px;background:var(--bg3);color:var(--txt);border:1px solid var(--border2);border-radius:10px;font-size:.88rem;font-weight:600;cursor:pointer">✏️ Düzenle</button>
      <button id="txd-del-btn" style="flex:1;padding:12px;background:#ef444415;color:#f87171;border:1px solid #ef444430;border-radius:10px;font-size:.88rem;font-weight:600;cursor:pointer">🗑 Sil</button>
    </div>
  </div>
</div>

<!-- İŞLEM DÜZENLEME MODALI -->
<div id="tx-edit-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:9999;align-items:flex-end;justify-content:center" onclick="if(event.target===this)closeTxEdit()">
  <div style="background:var(--bg2);border-radius:20px 20px 0 0;width:100%;max-width:480px;padding:28px 24px 40px;border-top:1px solid var(--border)">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
      <div style="font-size:1rem;font-weight:800;color:var(--txt)">✏️ İşlemi Düzenle</div>
      <button onclick="closeTxEdit()" style="width:32px;height:32px;border-radius:50%;border:1px solid var(--border2);background:var(--bg3);color:var(--txt2);cursor:pointer;font-size:.9rem">✕</button>
    </div>
    <input type="hidden" id="txe-id">
    <label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:5px">Tarih</label>
    <input type="date" id="txe-date" class="f-input" style="margin-bottom:12px">
    <label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:5px">Kategori</label>
    <select id="txe-category" class="f-input" style="margin-bottom:12px"></select>
    <label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:5px">Tutar</label>
    <input type="number" id="txe-amount" class="f-input" step="0.01" style="margin-bottom:12px">
    <label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:5px">Açıklama</label>
    <input type="text" id="txe-desc" class="f-input" style="margin-bottom:12px">
    <!-- Ödeme Türü — gider için -->
    <div id="txe-pay-section" style="margin-bottom:12px">
      <label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:6px">Ödeme Türü</label>
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px" id="txe-pay-chips">
        <button type="button" class="pay-chip active" data-eptype="nakit" onclick="txeSelectPayType(this)">💵 Nakit</button>
        <button type="button" class="pay-chip" data-eptype="banka" onclick="txeSelectPayType(this)">🏧 Banka</button>
        <button type="button" class="pay-chip" data-eptype="kredi" onclick="txeSelectPayType(this)">💳 Kredi Kartı</button>
        <button type="button" class="pay-chip" data-eptype="yemek" onclick="txeSelectPayType(this)">🍽️ Yemek Kartı</button>
      </div>
      <div id="txe-acc-row" style="display:none">
        <select id="txe-account" class="f-input"><option value="">— Hesap seçin —</option></select>
      </div>
      <div id="txe-card-row" style="display:none">
        <select id="txe-card" class="f-input"><option value="">— Kart seçin —</option></select>
      </div>
    </div>
    <!-- Gelir için hesap -->
    <div id="txe-income-acc" style="display:none;margin-bottom:20px">
      <label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:5px">🏦 Hangi Hesaba Geldi?</label>
      <select id="txe-income-account" class="f-input"><option value="">— Belirtme (Nakit) —</option></select>
    </div>
    <button onclick="saveTxEdit()" style="width:100%;padding:13px;background:var(--b);color:#fff;border:none;border-radius:10px;font-size:.92rem;font-weight:700;cursor:pointer">Kaydet</button>
  </div>
</div>

<!-- KART DÜZENLEME MODALI -->
<div id="card-edit-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:9999;align-items:flex-end;justify-content:center" onclick="if(event.target===this)this.style.display='none'">
  <div style="background:var(--bg2);border-radius:20px 20px 0 0;width:100%;max-width:520px;padding:24px 20px 36px;border-top:1px solid var(--border);max-height:90vh;overflow-y:auto">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
      <div style="font-size:1rem;font-weight:800">✏️ Kartı Düzenle</div>
      <button onclick="document.getElementById('card-edit-modal').style.display='none'" style="width:32px;height:32px;border-radius:50%;border:1px solid var(--border2);background:var(--bg3);cursor:pointer">✕</button>
    </div>
    <div style="margin-bottom:12px">
      <div class="acc-type-chips" id="ce-ctype-chips">
        <button type="button" class="acc-type-chip active" data-ctype="kredi" onclick="this.parentElement.querySelectorAll('.acc-type-chip').forEach(function(b){b.classList.remove('active')});this.classList.add('active')">💳 Kredi</button>
        <button type="button" class="acc-type-chip" data-ctype="banka" onclick="this.parentElement.querySelectorAll('.acc-type-chip').forEach(function(b){b.classList.remove('active')});this.classList.add('active')">🏧 Banka</button>
        <button type="button" class="acc-type-chip" data-ctype="yemek" onclick="this.parentElement.querySelectorAll('.acc-type-chip').forEach(function(b){b.classList.remove('active')});this.classList.add('active')">🍽️ Yemek</button>
        <button type="button" class="acc-type-chip" data-ctype="hediye" onclick="this.parentElement.querySelectorAll('.acc-type-chip').forEach(function(b){b.classList.remove('active')});this.classList.add('active')">🎁 Hediye</button>
      </div>
    </div>
    <label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:4px">Banka / Kurum</label>
    <input class="f-input" id="ce-bank" placeholder="Garanti BBVA" style="margin-bottom:10px">
    <label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:4px">Kart Adı</label>
    <input class="f-input" id="ce-name" placeholder="Bonus, Miles & Smiles…" style="margin-bottom:10px">
    <label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:4px">Ad Soyad (Kart Sahibi)</label>
    <input class="f-input" id="ce-owner" placeholder="ör. Ali Yılmaz" style="margin-bottom:10px">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px">
      <div><label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:4px">Limit (₺)</label><input class="f-input" type="number" id="ce-limit" placeholder="50000"></div>
      <div><label style="font-size:.78rem;color:var(--txt2);display:block;margin-bottom:4px">Borç (₺)</label><input class="f-input" type="number" id="ce-used" placeholder="0"></div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:14px">
      <div><label style="font-size:.72rem;color:var(--txt2);display:block;margin-bottom:4px">Son Ödeme Günü</label><input class="f-input" type="number" id="ce-due" min="1" max="31"></div>
      <div><label style="font-size:.72rem;color:var(--txt2);display:block;margin-bottom:4px">Ekstre Günü</label><input class="f-input" type="number" id="ce-stmt" min="1" max="31"></div>
      <div><label style="font-size:.72rem;color:var(--txt2);display:block;margin-bottom:4px">Asgari %</label><input class="f-input" type="number" id="ce-minpct" min="0" max="100"></div>
    </div>
    <button onclick="saveCardEdit()" class="btn btn-primary" style="width:100%;padding:12px">Kaydet</button>
  </div>
</div>

<!-- NET LİKİDİTE DETAY MODALI -->
<div id="liquidity-detail-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:9999;align-items:flex-end;justify-content:center" onclick="if(event.target===this)closeLiquidityDetail()">
  <div style="background:var(--bg2);border-radius:20px 20px 0 0;width:100%;max-width:480px;padding:28px 24px 40px;border-top:1px solid var(--border)">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
      <div style="font-size:1rem;font-weight:800;color:var(--txt)">💧 Net Likidite Detayı</div>
      <button onclick="closeLiquidityDetail()" style="width:32px;height:32px;border-radius:50%;border:1px solid var(--border2);background:var(--bg3);color:var(--txt2);cursor:pointer">✕</button>
    </div>
    <div style="font-size:.8rem;color:var(--txt2);margin-bottom:16px;line-height:1.6">
      Hesaplarınızın toplam bakiyesinden kredi kartı borçlarınız düşülerek hesaplanır.
    </div>
    <div style="display:flex;flex-direction:column;gap:0">
      <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--border)">
        <span style="font-size:.85rem;color:var(--txt2)">🏦 Hesap Bakiyeleri</span>
        <span id="lqd-balance" style="font-size:.9rem;font-weight:700;color:var(--g)">—</span>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--border)">
        <span style="font-size:.85rem;color:var(--txt2)">💳 Kredi Kartı Borcu</span>
        <span id="lqd-card" style="font-size:.9rem;font-weight:700;color:var(--r)">—</span>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;padding:14px 0">
        <span style="font-size:.88rem;font-weight:700;color:var(--txt)">Net Likidite</span>
        <span id="lqd-net" style="font-size:1.1rem;font-weight:900">—</span>
      </div>
    </div>
    <div style="margin-top:16px;padding:12px 14px;background:var(--bg3);border-radius:10px;font-size:.76rem;color:var(--txt2);line-height:1.6">
      💡 Hesap bakiyesi = Hesapların başlangıç bakiyesi + Bugüne kadar kaydedilen gelir/gider işlemleri
    </div>
  </div>
</div>

<!-- KULLANILABİLİR LİMİT MODALI -->
<div id="avail-limit-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:9999;align-items:flex-end;justify-content:center" onclick="if(event.target===this)closeAvailLimitModal()">
  <div style="background:var(--bg2);border-radius:20px 20px 0 0;width:100%;max-width:480px;padding:28px 24px 40px;border-top:1px solid var(--border)">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
      <div style="font-size:1rem;font-weight:800;color:var(--txt)">🟢 Kullanılabilir Limitler</div>
      <button onclick="closeAvailLimitModal()" style="width:32px;height:32px;border-radius:50%;border:1px solid var(--border2);background:var(--bg3);color:var(--txt2);cursor:pointer">✕</button>
    </div>
    <div id="avail-limit-list" style="display:flex;flex-direction:column;gap:10px"></div>
  </div>
</div>

</body>
</html>"""

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
