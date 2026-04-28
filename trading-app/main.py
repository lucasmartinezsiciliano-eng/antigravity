"""
FastAPI webhook receiver + dashboard.
Validates API key, queues signal to Redis, returns immediately.
Dashboard at /dashboard — live view of trades and analytics.
"""

import json
import logging
import os
from pathlib import Path

import redis
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from models import Signal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="IFVG Trading Bot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

LOG_FILE = Path(os.getenv("LOG_FILE", "trades.jsonl"))

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    return _redis


# ── Webhook ───────────────────────────────────────────────────────────────────

@app.post("/webhook")
async def receive_signal(signal: Signal, x_api_key: str = Header(None)):
    expected_key = os.getenv("WEBHOOK_API_KEY")
    if expected_key and x_api_key != expected_key:
        raise HTTPException(status_code=403, detail="Unauthorized")

    payload = signal.model_dump()
    get_redis().publish("signals", json.dumps(payload))
    log.info(f"[WEBHOOK] Queued: {signal.action} {signal.symbol} @ {signal.close}")
    return {"status": "queued", "action": signal.action, "symbol": signal.symbol}


# ── Status API ────────────────────────────────────────────────────────────────

@app.get("/status")
async def status():
    try:
        get_redis().ping()
        redis_ok = True
    except Exception:
        redis_ok = False
    return {"status": "online", "redis": "ok" if redis_ok else "error", "version": "1.0.0"}


@app.get("/api/trades")
async def get_trades(limit: int = 50):
    trades = []
    if LOG_FILE.exists():
        with open(LOG_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    trades.append(json.loads(line.strip()))
                except Exception:
                    pass
    return {"trades": trades[-limit:], "total": len(trades)}


@app.get("/api/analytics")
async def get_analytics():
    """Inline analytics — no subprocess needed."""
    trades = []
    if LOG_FILE.exists():
        with open(LOG_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    trades.append(json.loads(line.strip()))
                except Exception:
                    pass

    closed = [t for t in trades if t.get("event") == "trade_closed"]
    orders = [t for t in trades if t.get("event") == "order_placed"]
    skips  = [t for t in trades if t.get("event") == "skip"]

    wins   = [t for t in closed if t.get("pnl", 0) > 0]
    losses = [t for t in closed if t.get("pnl", 0) <= 0]

    total_w = sum(t.get("pnl", 0) for t in wins)
    total_l = abs(sum(t.get("pnl", 0) for t in losses))
    pf = round(total_w / total_l, 2) if total_l > 0 else None
    wr = round(len(wins) / len(closed), 3) if closed else None
    avg_w = round(total_w / len(wins), 2) if wins else 0
    avg_l = round(total_l / len(losses), 2) if losses else 0
    rr    = round(avg_w / avg_l, 2) if avg_l > 0 else None

    return {
        "orders_placed": len(orders),
        "trades_closed": len(closed),
        "signals_skipped": len(skips),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": wr,
        "profit_factor": pf,
        "avg_rr": rr,
        "total_pnl": round(total_w - total_l, 2),
    }


# ── Dashboard HTML ────────────────────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IFVG Trading Bot</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0d1117; color: #c9d1d9; font-family: 'SF Mono', 'Consolas', monospace; font-size: 14px; }
  .header { background: #161b22; border-bottom: 1px solid #30363d; padding: 16px 24px; display: flex; align-items: center; gap: 12px; }
  .header h1 { font-size: 18px; color: #e6edf3; font-weight: 600; }
  .dot { width: 10px; height: 10px; border-radius: 50%; background: #3fb950; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; padding: 20px 24px; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
  .card-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
  .card-value { font-size: 28px; font-weight: 700; color: #e6edf3; }
  .card-value.green { color: #3fb950; }
  .card-value.yellow { color: #d29922; }
  .card-value.red { color: #f85149; }
  .section { padding: 0 24px 20px; }
  .section-title { font-size: 13px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #21262d; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 11px; color: #8b949e; padding: 6px 10px; text-transform: uppercase; }
  td { padding: 8px 10px; border-top: 1px solid #21262d; font-size: 13px; }
  tr:hover td { background: #1c2128; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .badge-order { background: #1f3a5f; color: #58a6ff; }
  .badge-skip { background: #2d2d2d; color: #8b949e; }
  .badge-close-win { background: #1a3a2a; color: #3fb950; }
  .badge-close-loss { background: #3a1a1a; color: #f85149; }
  .badge-buy { background: #1a3a2a; color: #3fb950; }
  .badge-sell { background: #3a1a1a; color: #f85149; }
  .refresh-btn { margin-left: auto; background: #21262d; border: 1px solid #30363d; color: #c9d1d9; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; }
  .refresh-btn:hover { background: #30363d; }
  .threshold { font-size: 11px; color: #8b949e; margin-top: 4px; }
  .status-bar { background: #1c2128; padding: 8px 24px; font-size: 12px; color: #8b949e; border-top: 1px solid #21262d; display: flex; gap: 20px; }
</style>
</head>
<body>
<div class="header">
  <div class="dot" id="status-dot"></div>
  <h1>IFVG Trading Bot — Beta</h1>
  <button class="refresh-btn" onclick="refresh()">⟳ Refresh</button>
</div>

<div class="grid" id="metrics">
  <div class="card"><div class="card-label">Status</div><div class="card-value" id="m-status">...</div></div>
  <div class="card"><div class="card-label">Win Rate</div><div class="card-value" id="m-wr">—</div><div class="threshold">target ≥50%</div></div>
  <div class="card"><div class="card-label">Profit Factor</div><div class="card-value" id="m-pf">—</div><div class="threshold">target ≥1.5</div></div>
  <div class="card"><div class="card-label">Avg RR</div><div class="card-value" id="m-rr">—</div><div class="threshold">target ≥2:1</div></div>
  <div class="card"><div class="card-label">Total PnL</div><div class="card-value" id="m-pnl">—</div></div>
  <div class="card"><div class="card-label">Trades Today</div><div class="card-value" id="m-trades">—</div></div>
  <div class="card"><div class="card-label">Skipped</div><div class="card-value" id="m-skips">—</div></div>
  <div class="card"><div class="card-label">W / L</div><div class="card-value" id="m-wl">—</div></div>
</div>

<div class="section">
  <div class="section-title">Recent Events</div>
  <table>
    <thead><tr><th>Time</th><th>Event</th><th>Symbol</th><th>Side</th><th>Detail</th></tr></thead>
    <tbody id="trades-body"><tr><td colspan="5" style="color:#8b949e;padding:20px;text-align:center">Loading...</td></tr></tbody>
  </table>
</div>

<div class="status-bar">
  <span>Mode: <b style="color:#d29922">PAPER</b></span>
  <span id="redis-status">Redis: checking...</span>
  <span id="last-update">Last update: —</span>
  <span style="margin-left:auto">Webhook: <code>http://localhost:8000/webhook</code></span>
</div>

<script>
async function refresh() {
  // Status
  try {
    const s = await fetch('/status').then(r => r.json());
    document.getElementById('m-status').textContent = s.status === 'online' ? 'ONLINE' : 'OFFLINE';
    document.getElementById('m-status').className = 'card-value ' + (s.status === 'online' ? 'green' : 'red');
    document.getElementById('redis-status').textContent = 'Redis: ' + s.redis;
    document.getElementById('status-dot').style.background = s.status === 'online' ? '#3fb950' : '#f85149';
  } catch(e) {
    document.getElementById('m-status').textContent = 'OFFLINE';
    document.getElementById('m-status').className = 'card-value red';
  }

  // Analytics
  try {
    const a = await fetch('/api/analytics').then(r => r.json());
    const wr = a.win_rate;
    const pf = a.profit_factor;
    const rr = a.avg_rr;
    const pnl = a.total_pnl;

    document.getElementById('m-wr').textContent = wr !== null ? (wr*100).toFixed(0)+'%' : '—';
    document.getElementById('m-wr').className = 'card-value ' + (wr === null ? '' : wr >= 0.5 ? 'green' : wr >= 0.4 ? 'yellow' : 'red');

    document.getElementById('m-pf').textContent = pf !== null ? pf.toFixed(2) : '—';
    document.getElementById('m-pf').className = 'card-value ' + (pf === null ? '' : pf >= 2 ? 'green' : pf >= 1.5 ? 'yellow' : 'red');

    document.getElementById('m-rr').textContent = rr !== null ? rr.toFixed(1)+':1' : '—';
    document.getElementById('m-rr').className = 'card-value ' + (rr === null ? '' : rr >= 2 ? 'green' : 'yellow');

    document.getElementById('m-pnl').textContent = pnl !== 0 ? (pnl > 0 ? '+' : '') + '$' + pnl.toFixed(0) : '—';
    document.getElementById('m-pnl').className = 'card-value ' + (pnl > 0 ? 'green' : pnl < 0 ? 'red' : '');

    document.getElementById('m-trades').textContent = a.orders_placed || '0';
    document.getElementById('m-skips').textContent = a.signals_skipped || '0';
    document.getElementById('m-wl').textContent = a.wins + ' / ' + a.losses;
  } catch(e) {}

  // Trades log
  try {
    const t = await fetch('/api/trades?limit=30').then(r => r.json());
    const rows = t.trades.slice().reverse().map(ev => {
      const ts = new Date(ev.ts).toLocaleTimeString('es', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
      let badge = '', sym = ev.symbol || '—', side = '—', detail = '';

      if (ev.event === 'order_placed') {
        badge = '<span class="badge badge-order">ORDER</span>';
        side = `<span class="badge badge-${(ev.action||'').toLowerCase()}">${ev.action||''}</span>`;
        detail = `Entry ${ev.entry} | SL ${ev.sl} | TP ${ev.tp} | ${ev.qty}x | RR ${ev.rr}`;
      } else if (ev.event === 'trade_closed') {
        const win = ev.pnl > 0;
        badge = `<span class="badge ${win ? 'badge-close-win' : 'badge-close-loss'}">${win ? 'WIN' : 'LOSS'}</span>`;
        detail = `PnL: ${ev.pnl > 0 ? '+' : ''}$${(ev.pnl||0).toFixed(2)}`;
      } else if (ev.event === 'skip') {
        badge = '<span class="badge badge-skip">SKIP</span>';
        detail = ev.reason || '';
        sym = ev.signal?.symbol || '—';
      } else {
        badge = `<span class="badge badge-skip">${ev.event}</span>`;
        detail = ev.msg || '';
      }
      return `<tr><td>${ts}</td><td>${badge}</td><td>${sym}</td><td>${side}</td><td style="color:#8b949e">${detail}</td></tr>`;
    }).join('');

    document.getElementById('trades-body').innerHTML = rows ||
      '<tr><td colspan="5" style="color:#8b949e;padding:20px;text-align:center">No trades yet — send a test signal</td></tr>';
  } catch(e) {}

  document.getElementById('last-update').textContent = 'Last update: ' + new Date().toLocaleTimeString('es');
}

refresh();
setInterval(refresh, 5000);  // auto-refresh every 5 seconds
</script>
</body>
</html>"""


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML


@app.get("/")
async def root():
    return HTMLResponse(
        '<meta http-equiv="refresh" content="0; url=/dashboard">',
        status_code=302
    )
