"""
Beta local — servidor standalone para Windows sin Docker ni Redis.
Simula ejecución de órdenes en memoria (paper trading simulado).
Ejecutar: python beta_local.py

Dashboard: http://localhost:8000/dashboard
"""

import json
import os
import sys
import webbrowser
import threading
import time
import random
from pathlib import Path
from datetime import datetime, timezone
from collections import deque

# ── Instalar dependencias si faltan ──────────────────────────────────────────
def install_if_missing():
    import importlib.util
    needed = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn[standard]",
        "pydantic": "pydantic",
        "requests": "requests",
    }
    missing = [pkg for mod, pkg in needed.items() if importlib.util.find_spec(mod) is None]
    if missing:
        print(f"Installing: {', '.join(missing)}")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "-q"])
        print("Done. Restarting...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

install_if_missing()

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# ── In-memory state ───────────────────────────────────────────────────────────
SIGNALS_QUEUE: deque = deque(maxlen=100)
TRADES_LOG: list = []
LOG_FILE = Path("trades.jsonl")

ACCOUNT = {"balance": 50_000.0, "start": 50_000.0}

def log_event(event: str, data: dict):
    record = {"ts": datetime.now(timezone.utc).isoformat() + "Z", "event": event, **data}
    TRADES_LOG.append(record)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record

# ── Simulated executor ────────────────────────────────────────────────────────
def simulated_executor():
    """Runs in background thread — processes signals and simulates fills."""
    while True:
        time.sleep(0.5)
        if not SIGNALS_QUEUE:
            continue
        signal = SIGNALS_QUEUE.popleft()

        # Filter: kill zone check (simplified — just check weekday)
        now = datetime.now()
        if now.weekday() >= 5:
            log_event("skip", {"reason": "Weekend — market closed", "signal": signal})
            continue

        # Simulate position size (1% risk, 10 tick SL)
        entry = signal["close"]
        action = signal["action"]
        stop_dist = entry * 0.005          # 0.5% SL
        rr = 2.0
        sl = round(entry - stop_dist, 4) if action == "BUY" else round(entry + stop_dist, 4)
        tp = round(entry + stop_dist * rr, 4) if action == "BUY" else round(entry - stop_dist * rr, 4)
        qty = max(1, int(ACCOUNT["balance"] * 0.01 / (stop_dist or 1)))

        log_event("order_placed", {
            "symbol": signal["symbol"],
            "action": action,
            "qty": qty,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "rr": rr,
            "risk_usd": round(ACCOUNT["balance"] * 0.01, 2),
            "reason": signal.get("reason", ""),
        })
        print(f"  [SIMULATED] {action} {qty}x {signal['symbol']} @ {entry} | SL {sl} TP {tp}")

        # Simulate random outcome (60% win for paper testing)
        time.sleep(random.uniform(1, 3))
        win = random.random() < 0.60
        pnl = round(stop_dist * qty * rr if win else -stop_dist * qty, 2)
        ACCOUNT["balance"] += pnl

        log_event("trade_closed", {
            "symbol": signal["symbol"],
            "pnl": pnl,
            "rr_achieved": rr if win else round(random.uniform(0.3, 0.8), 1),
            "result": "WIN" if win else "LOSS",
        })
        outcome = "WIN" if win else "LOSS"
        print(f"  [RESULT] {outcome} {signal['symbol']} PnL: ${pnl:+.2f} | Balance: ${ACCOUNT['balance']:,.0f}")

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="IFVG Trading Bot — Local Beta", version="1.0.0-beta")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Signal(BaseModel):
    action: str
    symbol: str
    timeframe: str = "1"
    close: float
    time: str = ""
    reason: str = "IFVG_manual"

@app.post("/webhook")
async def webhook(signal: Signal, x_api_key: str = Header(None)):
    api_key = os.getenv("WEBHOOK_API_KEY", "")
    if api_key and x_api_key != api_key:
        raise HTTPException(403, "Unauthorized")
    payload = signal.model_dump()
    SIGNALS_QUEUE.append(payload)
    print(f"  [WEBHOOK] Signal queued: {signal.action} {signal.symbol} @ {signal.close}")
    return {"status": "queued", "action": signal.action, "symbol": signal.symbol}

@app.get("/status")
async def status():
    return {"status": "online", "redis": "in-memory", "mode": "LOCAL BETA", "version": "1.0.0-beta"}

@app.get("/api/trades")
async def trades_api(limit: int = 50):
    return {"trades": TRADES_LOG[-limit:], "total": len(TRADES_LOG)}

@app.get("/api/analytics")
async def analytics_api():
    closed = [t for t in TRADES_LOG if t.get("event") == "trade_closed"]
    orders = [t for t in TRADES_LOG if t.get("event") == "order_placed"]
    skips  = [t for t in TRADES_LOG if t.get("event") == "skip"]
    wins   = [t for t in closed if t.get("pnl", 0) > 0]
    losses = [t for t in closed if t.get("pnl", 0) <= 0]
    total_w = sum(t.get("pnl", 0) for t in wins)
    total_l = abs(sum(t.get("pnl", 0) for t in losses))
    avg_w = total_w / len(wins) if wins else 0
    avg_l = total_l / len(losses) if losses else 0
    return {
        "orders_placed": len(orders),
        "trades_closed": len(closed),
        "signals_skipped": len(skips),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins)/len(closed), 3) if closed else None,
        "profit_factor": round(total_w/total_l, 2) if total_l > 0 else None,
        "avg_rr": round(avg_w/avg_l, 2) if avg_l > 0 else None,
        "total_pnl": round(total_w - total_l, 2),
        "balance": round(ACCOUNT["balance"], 2),
    }

@app.post("/api/test-signal")
async def test_signal(symbol: str = "NQ1!", action: str = "BUY", price: float = 19250.0):
    """Quick test signal without needing full webhook format."""
    sig = {"action": action, "symbol": symbol, "close": price,
           "timeframe": "1", "time": "", "reason": "IFVG_test"}
    SIGNALS_QUEUE.append(sig)
    return {"status": "queued", "signal": sig}

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IFVG Bot — Beta Local</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0d1117; color: #c9d1d9; font-family: 'SF Mono', 'Consolas', monospace; font-size: 14px; }
  .header { background: #161b22; border-bottom: 1px solid #30363d; padding: 16px 24px; display: flex; align-items: center; gap: 12px; }
  .header h1 { font-size: 18px; color: #e6edf3; font-weight: 600; }
  .mode-badge { background: #1a3a2a; color: #3fb950; border: 1px solid #2ea043; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; }
  .dot { width: 10px; height: 10px; border-radius: 50%; background: #3fb950; animation: pulse 2s infinite; flex-shrink: 0; }
  @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.4} }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; padding: 20px 24px; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
  .card-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
  .card-value { font-size: 26px; font-weight: 700; color: #e6edf3; }
  .card-value.green { color: #3fb950; }
  .card-value.yellow { color: #d29922; }
  .card-value.red { color: #f85149; }
  .threshold { font-size: 11px; color: #555; margin-top: 4px; }
  .section { padding: 0 24px 20px; }
  .section-title { font-size: 12px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #21262d; display: flex; justify-content: space-between; align-items: center; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 11px; color: #8b949e; padding: 6px 10px; text-transform: uppercase; }
  td { padding: 8px 10px; border-top: 1px solid #21262d; font-size: 13px; }
  tr:hover td { background: #1c2128; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .b-order { background:#1f3a5f;color:#58a6ff; }
  .b-skip { background:#2d2d2d;color:#8b949e; }
  .b-win { background:#1a3a2a;color:#3fb950; }
  .b-loss { background:#3a1a1a;color:#f85149; }
  .b-buy { background:#1a3a2a;color:#3fb950; }
  .b-sell { background:#3a1a1a;color:#f85149; }
  .controls { padding: 0 24px 20px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
  .btn { padding: 8px 16px; border-radius: 6px; border: 1px solid #30363d; background: #21262d; color: #c9d1d9; cursor: pointer; font-size: 13px; font-family: inherit; transition: background 0.15s; }
  .btn:hover { background: #30363d; }
  .btn.green { background: #1a3a2a; border-color: #2ea043; color: #3fb950; }
  .btn.green:hover { background: #2ea043; color: #fff; }
  .btn.red { background: #3a1a1a; border-color: #f85149; color: #f85149; }
  select { padding: 8px 12px; border-radius: 6px; border: 1px solid #30363d; background: #21262d; color: #c9d1d9; font-size: 13px; font-family: inherit; }
  .status-bar { background: #1c2128; padding: 8px 24px; font-size: 12px; color: #8b949e; border-top: 1px solid #21262d; display: flex; gap: 20px; flex-wrap: wrap; }
  .progress-bar { height: 4px; background: #21262d; border-radius: 2px; margin-top: 8px; overflow: hidden; }
  .progress-fill { height: 100%; border-radius: 2px; transition: width 0.5s, background 0.5s; }
</style>
</head>
<body>
<div class="header">
  <div class="dot" id="dot"></div>
  <h1>IFVG Trading Bot</h1>
  <span class="mode-badge">PAPER BETA</span>
</div>

<div class="grid">
  <div class="card">
    <div class="card-label">Balance</div>
    <div class="card-value green" id="m-balance">$50,000</div>
    <div class="progress-bar"><div class="progress-fill" id="pb-balance" style="width:100%;background:#3fb950"></div></div>
  </div>
  <div class="card">
    <div class="card-label">Win Rate</div>
    <div class="card-value" id="m-wr">—</div>
    <div class="threshold">target ≥50%</div>
  </div>
  <div class="card">
    <div class="card-label">Profit Factor</div>
    <div class="card-value" id="m-pf">—</div>
    <div class="threshold">target ≥1.5</div>
  </div>
  <div class="card">
    <div class="card-label">Avg RR</div>
    <div class="card-value" id="m-rr">—</div>
    <div class="threshold">target ≥2:1</div>
  </div>
  <div class="card">
    <div class="card-label">PnL Total</div>
    <div class="card-value" id="m-pnl">—</div>
  </div>
  <div class="card">
    <div class="card-label">Órdenes</div>
    <div class="card-value" id="m-orders">0</div>
  </div>
  <div class="card">
    <div class="card-label">Filtradas</div>
    <div class="card-value" id="m-skips">0</div>
  </div>
  <div class="card">
    <div class="card-label">W / L</div>
    <div class="card-value" id="m-wl">—</div>
  </div>
</div>

<div class="section">
  <div class="section-title">
    <span>Enviar señal de test</span>
  </div>
</div>
<div class="controls">
  <select id="sym">
    <option value="NQ1!">NQ (Nasdaq Futures)</option>
    <option value="ES1!">ES (S&P Futures)</option>
    <option value="AAPL">AAPL</option>
    <option value="MSFT">MSFT</option>
    <option value="NVDA">NVDA</option>
    <option value="TSLA">TSLA</option>
    <option value="EURUSD">EURUSD</option>
  </select>
  <select id="price-preset">
    <option value="19250">NQ @ 19,250</option>
    <option value="5300">ES @ 5,300</option>
    <option value="172.5">AAPL @ 172.5</option>
    <option value="415">MSFT @ 415</option>
    <option value="875">NVDA @ 875</option>
    <option value="180">TSLA @ 180</option>
    <option value="1.085">EURUSD @ 1.085</option>
  </select>
  <button class="btn green" onclick="sendSignal('BUY')">▲ LONG</button>
  <button class="btn red" onclick="sendSignal('SELL')">▼ SHORT</button>
  <span id="signal-status" style="color:#8b949e;font-size:13px"></span>
</div>

<div class="section">
  <div class="section-title">
    <span>Eventos recientes</span>
    <span id="last-update" style="font-size:11px;color:#555"></span>
  </div>
  <table>
    <thead><tr><th>Hora</th><th>Evento</th><th>Símbolo</th><th>Lado</th><th>Detalle</th></tr></thead>
    <tbody id="tbody">
      <tr><td colspan="5" style="color:#8b949e;padding:24px;text-align:center">
        Pulsa LONG o SHORT para simular una señal IFVG →
      </td></tr>
    </tbody>
  </table>
</div>

<div class="status-bar">
  <span id="s-mode">Modo: <b style="color:#d29922">LOCAL BETA</b> (simulación, sin IBKR real)</span>
  <span id="s-queue">Cola: 0 señales</span>
  <span style="margin-left:auto">Webhook: <code>POST http://localhost:8000/webhook</code></span>
</div>

<script>
let lastCount = 0;

async function sendSignal(action) {
  const sym = document.getElementById('sym').value;
  const price = parseFloat(document.getElementById('price-preset').value);
  const st = document.getElementById('signal-status');
  st.style.color = '#d29922';
  st.textContent = `Enviando ${action} ${sym}...`;
  try {
    const r = await fetch(`/api/test-signal?symbol=${sym}&action=${action}&price=${price}`, {method:'POST'});
    const d = await r.json();
    st.style.color = '#3fb950';
    st.textContent = `✓ ${d.status} — el executor procesará en ~1s`;
    setTimeout(() => { st.textContent = ''; }, 4000);
  } catch(e) {
    st.style.color = '#f85149';
    st.textContent = 'Error: ' + e.message;
  }
}

async function refresh() {
  try {
    const [a, t] = await Promise.all([
      fetch('/api/analytics').then(r=>r.json()),
      fetch('/api/trades?limit=30').then(r=>r.json())
    ]);

    // Metrics
    const wr = a.win_rate, pf = a.profit_factor, rr = a.avg_rr, pnl = a.total_pnl;
    const bal = a.balance || 50000;

    document.getElementById('m-balance').textContent = '$' + bal.toLocaleString('es', {maximumFractionDigits:0});
    const balPct = Math.max(0, Math.min(100, (bal / 50000) * 100));
    const balColor = bal >= 50000 ? '#3fb950' : bal >= 47500 ? '#d29922' : '#f85149';
    document.getElementById('m-balance').style.color = balColor;
    document.getElementById('pb-balance').style.cssText = `width:${balPct}%;background:${balColor}`;

    function setMetric(id, val, fmt, good, warn) {
      const el = document.getElementById(id);
      el.textContent = val === null ? '—' : fmt(val);
      el.className = 'card-value ' + (val === null ? '' : val >= good ? 'green' : val >= warn ? 'yellow' : 'red');
    }
    setMetric('m-wr', wr, v=>(v*100).toFixed(0)+'%', 0.5, 0.4);
    setMetric('m-pf', pf, v=>v.toFixed(2), 2.0, 1.5);
    setMetric('m-rr', rr, v=>v.toFixed(1)+':1', 2.0, 1.5);

    const pnlEl = document.getElementById('m-pnl');
    pnlEl.textContent = pnl !== 0 ? (pnl>0?'+':'')+'$'+pnl.toFixed(0) : '—';
    pnlEl.className = 'card-value ' + (pnl>0?'green':pnl<0?'red':'');

    document.getElementById('m-orders').textContent = a.orders_placed || '0';
    document.getElementById('m-skips').textContent = a.signals_skipped || '0';
    document.getElementById('m-wl').textContent = (a.wins||0) + ' / ' + (a.losses||0);

    // Trades table
    if (t.total !== lastCount) {
      lastCount = t.total;
      const rows = t.trades.slice().reverse().map(ev => {
        const ts = new Date(ev.ts).toLocaleTimeString('es', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
        let badge='', sym='—', side='—', detail='';
        if (ev.event === 'order_placed') {
          badge = '<span class="badge b-order">ORDEN</span>';
          sym = ev.symbol;
          side = `<span class="badge b-${(ev.action||'').toLowerCase()}">${ev.action}</span>`;
          detail = `Entry ${ev.entry} | SL ${ev.sl} | TP ${ev.tp} | x${ev.qty} | RR ${ev.rr}`;
        } else if (ev.event === 'trade_closed') {
          const w = ev.pnl > 0;
          badge = `<span class="badge ${w?'b-win':'b-loss'}">${w?'WIN':'LOSS'}</span>`;
          sym = ev.symbol;
          detail = `PnL: ${ev.pnl>0?'+':''}$${(ev.pnl||0).toFixed(2)} | RR conseguido: ${ev.rr_achieved}`;
        } else if (ev.event === 'skip') {
          badge = '<span class="badge b-skip">SKIP</span>';
          sym = ev.signal?.symbol || '—';
          detail = ev.reason || '';
        } else {
          badge = `<span class="badge b-skip">${ev.event}</span>`;
          detail = ev.msg || JSON.stringify(ev).slice(0,80);
        }
        return `<tr><td>${ts}</td><td>${badge}</td><td>${sym}</td><td>${side}</td><td style="color:#8b949e;font-size:12px">${detail}</td></tr>`;
      }).join('');
      document.getElementById('tbody').innerHTML = rows ||
        '<tr><td colspan="5" style="color:#8b949e;padding:24px;text-align:center">Pulsa LONG o SHORT para simular una señal IFVG →</td></tr>';
    }

    document.getElementById('last-update').textContent = 'Auto-refresh · ' + new Date().toLocaleTimeString('es');
  } catch(e) {
    document.getElementById('dot').style.background = '#f85149';
  }
}

refresh();
setInterval(refresh, 3000);
</script>
</body>
</html>"""

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse('<meta http-equiv="refresh" content="0; url=/dashboard">', 302)


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  IFVG Trading Bot — Beta Local")
    print("="*55)
    print("  Modo: PAPER (simulación sin IBKR real)")
    print("  Dashboard: http://localhost:8000/dashboard")
    print("  Webhook:   http://localhost:8000/webhook")
    print("  Ctrl+C para parar")
    print("="*55 + "\n")

    # Start simulated executor in background thread
    t = threading.Thread(target=simulated_executor, daemon=True)
    t.start()

    # Open browser after 1.5s
    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://localhost:8000/dashboard")
    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
