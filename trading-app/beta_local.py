"""
Beta local — servidor standalone para Windows sin Docker ni Redis.
Ejecutar: python beta_local.py
Dashboard: http://localhost:8000/dashboard
"""

import json, os, sys, webbrowser, threading, time, random
from pathlib import Path
from datetime import datetime
from collections import deque

def install_if_missing():
    import importlib.util
    needed = {"fastapi": "fastapi", "uvicorn": "uvicorn[standard]",
              "pydantic": "pydantic", "requests": "requests"}
    missing = [pkg for mod, pkg in needed.items() if importlib.util.find_spec(mod) is None]
    if missing:
        print(f"Installing: {', '.join(missing)}")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "-q"])
        os.execv(sys.executable, [sys.executable] + sys.argv)

install_if_missing()

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# ── State ─────────────────────────────────────────────────────────────────────
SIGNALS_QUEUE: deque = deque(maxlen=100)
TRADES_LOG: list     = []
EQUITY_CURVE: list   = []          # [{ts, balance}]
LOG_FILE = Path("trades.jsonl")
ACCOUNT  = {"balance": 50_000.0, "start": 50_000.0, "peak": 50_000.0}

def _ts() -> str:
    # Plain UTC ISO — JS new Date() can parse this fine
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def log_event(event: str, data: dict):
    record = {"ts": _ts(), "event": event, **data}
    TRADES_LOG.append(record)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record

def push_equity():
    ACCOUNT["peak"] = max(ACCOUNT["peak"], ACCOUNT["balance"])
    dd = (ACCOUNT["peak"] - ACCOUNT["balance"]) / ACCOUNT["peak"] * 100
    EQUITY_CURVE.append({
        "ts": _ts(),
        "balance": round(ACCOUNT["balance"], 2),
        "drawdown_pct": round(dd, 2),
    })

# ── Kill zone helpers ─────────────────────────────────────────────────────────
import pytz

def _now_ny():
    return datetime.now(pytz.timezone("America/New_York"))

def kill_zone_status() -> dict:
    try:
        ny = _now_ny()
        t = ny.time()
        import datetime as dt
        in_kz = (ny.weekday() < 5 and
                 dt.time(8, 30) <= t <= dt.time(11, 0))
        # minutes until next kill zone open
        if in_kz:
            close_h, close_m = 11, 0
            mins_left = (close_h * 60 + close_m) - (t.hour * 60 + t.minute)
            next_msg = f"Closes in {mins_left}m"
        else:
            if ny.weekday() >= 5:
                next_msg = "Weekend — opens Monday 8:30 ET"
            elif t.hour < 8 or (t.hour == 8 and t.minute < 30):
                mins_until = (8 * 60 + 30) - (t.hour * 60 + t.minute)
                next_msg = f"Opens in {mins_until}m"
            else:
                next_msg = "Opens tomorrow 8:30 ET"
        return {
            "active": in_kz,
            "et_time": ny.strftime("%H:%M:%S ET"),
            "weekday": ny.strftime("%A"),
            "next": next_msg,
        }
    except Exception:
        return {"active": True, "et_time": "??:?? ET", "weekday": "?", "next": "pytz not installed"}

# ── Simulated executor ────────────────────────────────────────────────────────
def simulated_executor():
    while True:
        time.sleep(0.3)
        if not SIGNALS_QUEUE:
            continue
        signal = SIGNALS_QUEUE.popleft()

        kz = kill_zone_status()
        if not kz["active"]:
            log_event("skip", {"reason": f"Outside kill zone — {kz['next']}", "signal": signal})
            continue

        entry  = signal["close"]
        action = signal["action"]
        stop_d = entry * 0.005
        rr     = 2.0
        sl  = round(entry - stop_d, 4) if action == "BUY" else round(entry + stop_d, 4)
        tp  = round(entry + stop_d * rr, 4) if action == "BUY" else round(entry - stop_d * rr, 4)
        qty = max(1, int(ACCOUNT["balance"] * 0.01 / (stop_d or 1)))

        log_event("order_placed", {
            "symbol": signal["symbol"], "action": action,
            "qty": qty, "entry": entry, "sl": sl, "tp": tp, "rr": rr,
            "risk_usd": round(ACCOUNT["balance"] * 0.01, 2),
            "reason": signal.get("reason", ""),
        })
        print(f"  [ORDER] {action} {qty}x {signal['symbol']} @ {entry} | SL {sl} TP {tp}")

        time.sleep(random.uniform(1.5, 4))
        win = random.random() < 0.60
        pnl = round(stop_d * qty * rr if win else -stop_d * qty, 2)
        ACCOUNT["balance"] += pnl
        push_equity()

        rr_got = rr if win else round(random.uniform(0.3, 0.9), 1)
        log_event("trade_closed", {
            "symbol": signal["symbol"], "pnl": pnl,
            "rr_achieved": rr_got, "result": "WIN" if win else "LOSS",
            "balance_after": round(ACCOUNT["balance"], 2),
        })
        print(f"  [{'WIN ' if win else 'LOSS'}] {signal['symbol']} ${pnl:+.2f} | Balance ${ACCOUNT['balance']:,.0f}")

# ── FastAPI ───────────────────────────────────────────────────────────────────
app = FastAPI(title="IFVG Trading Bot", version="1.0.0-beta")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Signal(BaseModel):
    action: str; symbol: str; timeframe: str = "1"
    close: float; time: str = ""; reason: str = "IFVG_manual"

@app.post("/webhook")
async def webhook(signal: Signal, x_api_key: str = Header(None)):
    key = os.getenv("WEBHOOK_API_KEY", "")
    if key and x_api_key != key:
        raise HTTPException(403, "Unauthorized")
    SIGNALS_QUEUE.append(signal.model_dump())
    print(f"  [WEBHOOK] {signal.action} {signal.symbol} @ {signal.close}")
    return {"status": "queued", "action": signal.action, "symbol": signal.symbol}

@app.get("/status")
async def status():
    kz = kill_zone_status()
    return {"status": "online", "redis": "in-memory", "mode": "LOCAL BETA",
            "kill_zone": kz, "version": "1.0.0-beta"}

@app.get("/api/trades")
async def trades_api(limit: int = 60):
    return {"trades": TRADES_LOG[-limit:], "total": len(TRADES_LOG)}

@app.get("/api/equity")
async def equity_api():
    start = ACCOUNT["start"]
    peak  = ACCOUNT["peak"]
    dd    = (peak - ACCOUNT["balance"]) / peak * 100 if peak > 0 else 0
    return {
        "curve": EQUITY_CURVE[-100:],
        "balance": round(ACCOUNT["balance"], 2),
        "start": start,
        "peak": round(peak, 2),
        "max_drawdown_pct": round(dd, 2),
    }

@app.get("/api/analytics")
async def analytics_api():
    closed = [t for t in TRADES_LOG if t.get("event") == "trade_closed"]
    orders = [t for t in TRADES_LOG if t.get("event") == "order_placed"]
    skips  = [t for t in TRADES_LOG if t.get("event") == "skip"]
    wins   = [t for t in closed if t.get("pnl", 0) > 0]
    losses = [t for t in closed if t.get("pnl", 0) <= 0]
    tw = sum(t.get("pnl", 0) for t in wins)
    tl = abs(sum(t.get("pnl", 0) for t in losses))
    aw = tw / len(wins) if wins else 0
    al = tl / len(losses) if losses else 0
    peak = ACCOUNT["peak"]
    dd   = (peak - ACCOUNT["balance"]) / peak * 100 if peak > 0 else 0

    # Skip reason breakdown
    skip_reasons: dict[str, int] = {}
    for s in skips:
        r = s.get("reason", "unknown").split("—")[0].strip()
        skip_reasons[r] = skip_reasons.get(r, 0) + 1

    return {
        "orders_placed": len(orders), "trades_closed": len(closed),
        "signals_skipped": len(skips), "wins": len(wins), "losses": len(losses),
        "win_rate":      round(len(wins)/len(closed), 3) if closed else None,
        "profit_factor": round(tw/tl, 2) if tl > 0 else None,
        "avg_rr":        round(aw/al, 2) if al > 0 else None,
        "total_pnl":     round(tw - tl, 2),
        "balance":       round(ACCOUNT["balance"], 2),
        "max_drawdown_pct": round(dd, 2),
        "skip_reasons":  skip_reasons,
    }

@app.post("/api/test-signal")
async def test_signal(symbol: str = "NQ1!", action: str = "BUY", price: float = 19250.0):
    sig = {"action": action, "symbol": symbol, "close": price,
           "timeframe": "1", "time": "", "reason": "IFVG_test"}
    SIGNALS_QUEUE.append(sig)
    return {"status": "queued", "signal": sig}

@app.post("/api/reset")
async def reset():
    TRADES_LOG.clear(); EQUITY_CURVE.clear(); SIGNALS_QUEUE.clear()
    ACCOUNT["balance"] = ACCOUNT["start"]; ACCOUNT["peak"] = ACCOUNT["start"]
    if LOG_FILE.exists(): LOG_FILE.unlink()
    return {"status": "reset"}

# ── Dashboard ─────────────────────────────────────────────────────────────────
DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>IFVG Bot — Beta</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d1117;color:#c9d1d9;font-family:'SF Mono','Consolas',monospace;font-size:14px}
.header{background:#161b22;border-bottom:1px solid #30363d;padding:14px 24px;display:flex;align-items:center;gap:10px}
.header h1{font-size:17px;color:#e6edf3;font-weight:600;flex:1}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;letter-spacing:.5px}
.badge-paper{background:#1a3a2a;color:#3fb950;border:1px solid #2ea043}
.badge-kz-on{background:#1f3a5f;color:#58a6ff;border:1px solid #388bfd}
.badge-kz-off{background:#2d2d2d;color:#8b949e;border:1px solid #30363d}
.dot{width:9px;height:9px;border-radius:50%;background:#3fb950;animation:pulse 2s infinite;flex-shrink:0}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.et-clock{font-size:13px;color:#8b949e;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;padding:16px 24px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px}
.card-label{font-size:10px;color:#8b949e;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
.card-value{font-size:24px;font-weight:700;color:#e6edf3}
.card-value.g{color:#3fb950}.card-value.y{color:#d29922}.card-value.r{color:#f85149}
.sub{font-size:11px;color:#555;margin-top:3px}
.pb{height:3px;background:#21262d;border-radius:2px;margin-top:7px;overflow:hidden}
.pb-fill{height:100%;border-radius:2px;transition:width .6s,background .6s}
.chart-wrap{padding:0 24px 16px}
.chart-title{font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}
canvas{width:100%;border-radius:6px;background:#161b22;border:1px solid #21262d}
.section{padding:0 24px 16px}
.sec-head{font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;
  padding-bottom:7px;border-bottom:1px solid #21262d;display:flex;justify-content:space-between;align-items:center}
table{width:100%;border-collapse:collapse}
th{text-align:left;font-size:10px;color:#8b949e;padding:5px 10px;text-transform:uppercase}
td{padding:7px 10px;border-top:1px solid #21262d;font-size:12px;max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
tr:hover td{background:#1c2128}
.b{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}
.b-order{background:#1f3a5f;color:#58a6ff}.b-skip{background:#2d2d2d;color:#8b949e}
.b-win{background:#1a3a2a;color:#3fb950}.b-loss{background:#3a1a1a;color:#f85149}
.b-buy{background:#1a3a2a;color:#3fb950}.b-sell{background:#3a1a1a;color:#f85149}
.controls{padding:0 24px 14px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.btn{padding:7px 14px;border-radius:6px;border:1px solid #30363d;background:#21262d;color:#c9d1d9;
  cursor:pointer;font-size:13px;font-family:inherit;transition:background .15s}
.btn:hover{background:#30363d}
.btn-g{background:#1a3a2a;border-color:#2ea043;color:#3fb950}.btn-g:hover{background:#2ea043;color:#fff}
.btn-r{background:#3a1a1a;border-color:#f85149;color:#f85149}.btn-r:hover{background:#f85149;color:#fff}
.btn-dim{background:#161b22;border-color:#30363d;color:#555}.btn-dim:hover{background:#21262d;color:#8b949e}
select{padding:7px 12px;border-radius:6px;border:1px solid #30363d;background:#21262d;color:#c9d1d9;font-size:13px;font-family:inherit}
.skip-grid{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.skip-pill{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:3px 10px;font-size:11px;color:#8b949e}
.sbar{background:#161b22;padding:8px 24px;font-size:11px;color:#8b949e;border-top:1px solid #21262d;display:flex;gap:16px;flex-wrap:wrap}
.sig-fb{font-size:12px;transition:color .3s}
</style>
</head>
<body>
<div class="header">
  <div class="dot" id="dot"></div>
  <h1>IFVG Trading Bot</h1>
  <span class="badge badge-paper">PAPER BETA</span>&nbsp;
  <span class="badge badge-kz-off" id="kz-badge">KZ OFF</span>
  <span class="et-clock" id="et-clock" style="margin-left:8px">--:-- ET</span>
</div>

<!-- Metrics grid -->
<div class="grid">
  <div class="card">
    <div class="card-label">Balance</div>
    <div class="card-value g" id="m-bal">$50,000</div>
    <div class="pb"><div class="pb-fill" id="pb-bal" style="width:100%;background:#3fb950"></div></div>
  </div>
  <div class="card">
    <div class="card-label">Win Rate</div>
    <div class="card-value" id="m-wr">—</div>
    <div class="sub">target ≥50%</div>
  </div>
  <div class="card">
    <div class="card-label">Profit Factor</div>
    <div class="card-value" id="m-pf">—</div>
    <div class="sub">target ≥1.5</div>
  </div>
  <div class="card">
    <div class="card-label">Avg RR</div>
    <div class="card-value" id="m-rr">—</div>
    <div class="sub">target ≥2:1</div>
  </div>
  <div class="card">
    <div class="card-label">PnL Total</div>
    <div class="card-value" id="m-pnl">—</div>
    <div class="sub" id="m-dd">DD: 0%</div>
  </div>
  <div class="card">
    <div class="card-label">Órdenes</div>
    <div class="card-value" id="m-ord">0</div>
    <div class="sub" id="m-fil">Filtradas: 0</div>
  </div>
  <div class="card">
    <div class="card-label">W / L</div>
    <div class="card-value" id="m-wl">—</div>
  </div>
  <div class="card">
    <div class="card-label">Max DD</div>
    <div class="card-value" id="m-mdd">0%</div>
    <div class="sub">límite: 20%</div>
  </div>
</div>

<!-- Equity curve -->
<div class="chart-wrap">
  <div class="chart-title">Curva de equity</div>
  <canvas id="equity-chart" height="110"></canvas>
</div>

<!-- Send signal -->
<div class="section">
  <div class="sec-head"><span>Enviar señal de test</span><span class="sig-fb" id="sig-fb"></span></div>
</div>
<div class="controls">
  <select id="sym">
    <option value="NQ1!">NQ (Nasdaq Fut.)</option>
    <option value="ES1!">ES (S&P Fut.)</option>
    <option value="AAPL">AAPL</option>
    <option value="MSFT">MSFT</option>
    <option value="NVDA">NVDA</option>
    <option value="TSLA">TSLA</option>
    <option value="EURUSD">EURUSD</option>
  </select>
  <select id="px">
    <option value="19250">NQ @ 19,250</option>
    <option value="5300">ES @ 5,300</option>
    <option value="172.5">AAPL @ 172.5</option>
    <option value="415">MSFT @ 415</option>
    <option value="875">NVDA @ 875</option>
    <option value="180">TSLA @ 180</option>
    <option value="1.085">EURUSD @ 1.085</option>
  </select>
  <button class="btn btn-g" onclick="fire('BUY')">▲ LONG</button>
  <button class="btn btn-r" onclick="fire('SELL')">▼ SHORT</button>
  <button class="btn btn-dim" onclick="doReset()" title="Clear all trades and reset balance">↺ Reset</button>
</div>

<!-- Skip breakdown -->
<div class="section" id="skip-section" style="display:none">
  <div class="sec-head"><span>Señales filtradas</span></div>
  <div class="skip-grid" id="skip-pills"></div>
</div>

<!-- Events table -->
<div class="section">
  <div class="sec-head">
    <span>Eventos recientes</span>
    <span id="ts-note" style="font-size:11px;color:#555"></span>
  </div>
  <table>
    <thead><tr><th>Hora ET</th><th>Evento</th><th>Símbolo</th><th>Lado</th><th>Detalle</th></tr></thead>
    <tbody id="tbody">
      <tr><td colspan="5" style="color:#8b949e;padding:24px;text-align:center">
        Pulsa ▲ LONG o ▼ SHORT para simular una señal IFVG
      </td></tr>
    </tbody>
  </table>
</div>

<div class="sbar">
  <span>Modo: <b style="color:#d29922">LOCAL BETA</b> (sin IBKR real)</span>
  <span id="s-kz">Kill zone: —</span>
  <span id="s-queue">Cola: 0</span>
  <span style="margin-left:auto">Webhook: <code>POST http://localhost:8000/webhook</code></span>
</div>

<script>
// ── Equity chart ─────────────────────────────────────────────────────────────
const canvas = document.getElementById('equity-chart');
const ctx = canvas.getContext('2d');
let curveData = [];

function drawChart(points, start) {
  const W = canvas.offsetWidth; const H = 110;
  canvas.width = W; canvas.height = H;
  ctx.fillStyle = '#161b22'; ctx.fillRect(0, 0, W, H);
  if (points.length < 2) {
    ctx.fillStyle = '#8b949e'; ctx.font = '12px Consolas,monospace';
    ctx.textAlign = 'center';
    ctx.fillText('Envía señales para ver la curva de equity', W/2, H/2);
    return;
  }
  const vals = points.map(p => p.balance);
  const mn = Math.min(...vals, start * 0.97);
  const mx = Math.max(...vals, start * 1.03);
  const pad = {t:10,b:24,l:60,r:12};
  const cw = W - pad.l - pad.r, ch = H - pad.t - pad.b;
  const sx = i => pad.l + (i / (points.length-1)) * cw;
  const sy = v => pad.t + (1 - (v - mn) / (mx - mn)) * ch;

  // Zero line (start balance)
  const y0 = sy(start);
  ctx.strokeStyle='#30363d'; ctx.lineWidth=1; ctx.setLineDash([4,4]);
  ctx.beginPath(); ctx.moveTo(pad.l, y0); ctx.lineTo(W-pad.r, y0); ctx.stroke();
  ctx.setLineDash([]);

  // Gradient fill
  const grad = ctx.createLinearGradient(0, pad.t, 0, H-pad.b);
  const lastVal = vals[vals.length-1];
  const isUp = lastVal >= start;
  grad.addColorStop(0, isUp ? 'rgba(63,185,80,.35)' : 'rgba(248,81,73,.35)');
  grad.addColorStop(1, 'rgba(22,27,34,0)');
  ctx.beginPath();
  points.forEach((p, i) => i===0 ? ctx.moveTo(sx(i), sy(p.balance)) : ctx.lineTo(sx(i), sy(p.balance)));
  ctx.lineTo(sx(points.length-1), H-pad.b);
  ctx.lineTo(pad.l, H-pad.b);
  ctx.closePath(); ctx.fillStyle=grad; ctx.fill();

  // Line
  ctx.beginPath(); ctx.strokeStyle = isUp ? '#3fb950' : '#f85149'; ctx.lineWidth=2;
  points.forEach((p,i) => i===0 ? ctx.moveTo(sx(i),sy(p.balance)) : ctx.lineTo(sx(i),sy(p.balance)));
  ctx.stroke();

  // Y labels
  ctx.fillStyle='#555'; ctx.font='10px Consolas'; ctx.textAlign='right';
  [mn, (mn+mx)/2, mx].forEach(v => {
    const y = sy(v);
    ctx.fillText('$'+Math.round(v).toLocaleString('es'), pad.l-4, y+3);
  });
}

// ── Kill zone & clock ─────────────────────────────────────────────────────────
function updateKZ(kz) {
  const badge = document.getElementById('kz-badge');
  const clock = document.getElementById('et-clock');
  const sKz   = document.getElementById('s-kz');
  clock.textContent = kz.et_time || '--:-- ET';
  if (kz.active) {
    badge.textContent = 'KZ ACTIVA'; badge.className='badge badge-kz-on';
    sKz.innerHTML = `Kill zone: <b style="color:#58a6ff">ACTIVA</b> · ${kz.next}`;
  } else {
    badge.textContent = 'KZ OFF'; badge.className='badge badge-kz-off';
    sKz.innerHTML = `Kill zone: <span style="color:#8b949e">INACTIVA</span> · ${kz.next}`;
  }
}

// ── Metric helpers ────────────────────────────────────────────────────────────
function setMetric(id, val, fmt, good, warn) {
  const el = document.getElementById(id);
  el.textContent = val == null ? '—' : fmt(val);
  el.className = 'card-value ' + (val==null ? '' : val>=good?'g':val>=warn?'y':'r');
}

// ── Main refresh ──────────────────────────────────────────────────────────────
let lastCount = 0;

async function refresh() {
  try {
    const [s, a, eq, t] = await Promise.all([
      fetch('/status').then(r=>r.json()),
      fetch('/api/analytics').then(r=>r.json()),
      fetch('/api/equity').then(r=>r.json()),
      fetch('/api/trades?limit=40').then(r=>r.json()),
    ]);

    // Kill zone
    if (s.kill_zone) updateKZ(s.kill_zone);

    // Balance card
    const bal = eq.balance, start = eq.start;
    document.getElementById('m-bal').textContent = '$'+bal.toLocaleString('es',{maximumFractionDigits:0});
    const pct = Math.max(5, Math.min(100, (bal/start)*100));
    const bc = bal >= start ? '#3fb950' : bal >= start*0.95 ? '#d29922' : '#f85149';
    document.getElementById('m-bal').className = 'card-value ' + (bal>=start?'g':bal>=start*.95?'y':'r');
    document.getElementById('pb-bal').style.cssText = `width:${pct}%;background:${bc}`;

    // Metrics
    setMetric('m-wr', a.win_rate,      v=>(v*100).toFixed(0)+'%', 0.5, 0.4);
    setMetric('m-pf', a.profit_factor, v=>v.toFixed(2),            2.0, 1.5);
    setMetric('m-rr', a.avg_rr,        v=>v.toFixed(1)+':1',       2.0, 1.5);

    const pnl = a.total_pnl;
    const pnlEl = document.getElementById('m-pnl');
    pnlEl.textContent = pnl !== 0 ? (pnl>0?'+':'')+'$'+pnl.toFixed(0) : '—';
    pnlEl.className = 'card-value '+(pnl>0?'g':pnl<0?'r':'');

    document.getElementById('m-dd').textContent = `DD actual: ${(a.max_drawdown_pct||0).toFixed(1)}%`;
    document.getElementById('m-ord').textContent = a.orders_placed||'0';
    document.getElementById('m-fil').textContent = `Filtradas: ${a.signals_skipped||0}`;
    document.getElementById('m-wl').textContent = `${a.wins||0} / ${a.losses||0}`;

    const mdd = eq.max_drawdown_pct||0;
    const mddEl = document.getElementById('m-mdd');
    mddEl.textContent = mdd.toFixed(1)+'%';
    mddEl.className = 'card-value '+(mdd<10?'g':mdd<20?'y':'r');

    // Equity curve
    curveData = eq.curve || [];
    drawChart(curveData, start);

    // Skip breakdown
    const sr = a.skip_reasons||{};
    const skSec = document.getElementById('skip-section');
    const skPills = document.getElementById('skip-pills');
    if (Object.keys(sr).length > 0) {
      skSec.style.display = 'block';
      skPills.innerHTML = Object.entries(sr).map(([r,n])=>
        `<span class="skip-pill">${r}: <b>${n}</b></span>`).join('');
    }

    // Trades table
    if (t.total !== lastCount || t.total === 0) {
      lastCount = t.total;
      const rows = t.trades.slice().reverse().map(ev => {
        let tsStr = '—';
        try {
          const d = new Date(ev.ts);
          tsStr = isNaN(d) ? ev.ts.slice(11,19) :
            d.toLocaleTimeString('es', {timeZone:'America/New_York',
              hour:'2-digit', minute:'2-digit', second:'2-digit'}) + ' ET';
        } catch(_) {}

        let badge='', sym=ev.symbol||'—', side='—', detail='';
        if (ev.event==='order_placed') {
          badge=`<span class="b b-order">ORDEN</span>`;
          side=`<span class="b b-${(ev.action||'').toLowerCase()}">${ev.action||''}</span>`;
          detail=`Entry ${ev.entry} | SL ${ev.sl} | TP ${ev.tp} | x${ev.qty} | RR ${ev.rr}`;
        } else if (ev.event==='trade_closed') {
          const w=ev.pnl>0;
          badge=`<span class="b ${w?'b-win':'b-loss'}">${w?'WIN':'LOSS'}</span>`;
          const c=w?'#3fb950':'#f85149';
          const pnlStr=`<span style="color:${c}">${ev.pnl>0?'+':''}$${(ev.pnl||0).toFixed(2)}</span>`;
          detail=`PnL: ${pnlStr} | RR: ${ev.rr_achieved} | Balance: $${(ev.balance_after||0).toLocaleString('es',{maximumFractionDigits:0})}`;
        } else if (ev.event==='skip') {
          badge=`<span class="b b-skip">SKIP</span>`;
          sym=ev.signal?.symbol||'—'; detail=ev.reason||'';
        } else {
          badge=`<span class="b b-skip">${ev.event}</span>`;
          detail=ev.msg||'';
        }
        return `<tr><td>${tsStr}</td><td>${badge}</td><td>${sym}</td><td>${side}</td><td style="color:#8b949e">${detail}</td></tr>`;
      }).join('');
      document.getElementById('tbody').innerHTML = rows ||
        '<tr><td colspan="5" style="color:#8b949e;padding:24px;text-align:center">Pulsa ▲ LONG o ▼ SHORT para simular una señal IFVG</td></tr>';
    }

    document.getElementById('ts-note').textContent = 'Auto-refresh · '+new Date().toLocaleTimeString('es');
    document.getElementById('dot').style.background = '#3fb950';
    document.getElementById('s-queue').textContent = 'Cola: 0';
  } catch(e) {
    document.getElementById('dot').style.background = '#f85149';
    console.error(e);
  }
}

// ── Actions ───────────────────────────────────────────────────────────────────
async function fire(action) {
  const sym = document.getElementById('sym').value;
  const price = parseFloat(document.getElementById('px').value);
  const fb = document.getElementById('sig-fb');
  fb.style.color = '#d29922'; fb.textContent = `Enviando ${action} ${sym}...`;
  try {
    const r = await fetch(`/api/test-signal?symbol=${sym}&action=${action}&price=${price}`, {method:'POST'});
    const d = await r.json();
    fb.style.color = '#3fb950';
    fb.textContent = `✓ Señal en cola — el executor procesará en ~2s`;
    setTimeout(()=>{ fb.textContent=''; }, 5000);
    setTimeout(refresh, 500);
  } catch(e) {
    fb.style.color='#f85149'; fb.textContent='Error: '+e.message;
  }
}

async function doReset() {
  if (!confirm('¿Resetear todas las trades y el balance? (no se puede deshacer)')) return;
  await fetch('/api/reset', {method:'POST'});
  lastCount = 0;
  await refresh();
}

// ── Init ──────────────────────────────────────────────────────────────────────
refresh();
setInterval(refresh, 3000);
window.addEventListener('resize', () => drawChart(curveData, 50000));
</script>
</body>
</html>"""

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse('<meta http-equiv="refresh" content="0;url=/dashboard">', 302)

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  IFVG Trading Bot — Beta Local")
    print("  Dashboard: http://localhost:8000/dashboard")
    print("  Ctrl+C para parar")
    print("="*55 + "\n")
    threading.Thread(target=simulated_executor, daemon=True).start()
    threading.Thread(target=lambda: (time.sleep(1.5), webbrowser.open("http://localhost:8000/dashboard")), daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
