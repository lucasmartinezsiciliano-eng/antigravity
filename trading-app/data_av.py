"""
data_av.py — Historical 5m data downloader (Twelvedata)
=========================================================
Descarga hasta 2 años de velas 5m de QQQ via Twelvedata API.
No requiere registro ni API key — funciona con la clave "demo".

Uso:
    python data_av.py                        # 2 años QQQ (demo key)
    python data_av.py --months 12            # 1 año
    python data_av.py --out mi_data.json     # archivo personalizado

Salida: JSON [{time, open, high, low, close}]
Compatible con backtest.py via --data-file

QQQ = ETF NASDAQ-100, correlación ~0.99 con NQ futures.
Para displacement filter: NQ ~20,000 / QQQ ~$480 → ratio ~42
  15 NQ pts ≈ 0.35 QQQ pts → usar --min-displacement 0.35 en backtest
"""

import io, sys, json, time, argparse, urllib.request
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = "https://api.twelvedata.com/time_series"

def fetch_chunk(symbol: str, start: str, end: str, apikey: str = "demo") -> list:
    """Descarga un bloque de velas 5m entre start y end (formato YYYY-MM-DD)."""
    url = (f"{BASE_URL}?symbol={symbol}&interval=5min&outputsize=5000"
           f"&start_date={start}&end_date={end}&apikey={apikey}&timezone=America/New_York")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"  [ERROR] {start}->{end}: {e}")
        return []

    if data.get("status") != "ok" or "values" not in data:
        msg = data.get("message", data.get("status", "unknown"))
        print(f"  [WARN] {start}->{end}: {msg}")
        return []

    candles = []
    import pytz
    ny = pytz.timezone("America/New_York")
    for v in data["values"]:
        try:
            dt = datetime.strptime(v["datetime"], "%Y-%m-%d %H:%M:%S")
            ts = int(ny.localize(dt).timestamp())
            candles.append({
                "time":   ts,
                "open":   float(v["open"]),
                "high":   float(v["high"]),
                "low":    float(v["low"]),
                "close":  float(v["close"]),
                "volume": int(v.get("volume", 0)),
            })
        except Exception:
            continue
    return candles


def download_history(symbol: str = "QQQ", months: int = 24,
                     apikey: str = "demo", out_file: str = None) -> list:
    """Descarga N meses en bloques trimestrales y combina."""
    end_dt   = datetime.now()
    start_dt = end_dt - timedelta(days=months * 30)

    # Dividir en bloques de ~90 días (caben ~5000 velas de 5m c/u)
    chunks, cur = [], start_dt
    while cur < end_dt:
        nxt = min(cur + timedelta(days=90), end_dt)
        chunks.append((cur.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")))
        cur = nxt + timedelta(days=1)  # noqa: F841 — used as loop counter above

    print(f"\n[TD] Descargando {symbol} | {months} meses | {len(chunks)} bloques")

    all_candles = []
    for i, (s, e) in enumerate(chunks, 1):
        print(f"  [{i:02}/{len(chunks)}] {s} → {e}...", end=" ", flush=True)
        c = fetch_chunk(symbol, s, e, apikey)
        print(f"{len(c)} velas")
        all_candles.extend(c)
        if i < len(chunks):
            time.sleep(2)   # pequeño delay para no saturar demo key

    # Dedup + orden cronológico
    seen, unique = set(), []
    for c in all_candles:
        if c["time"] not in seen:
            seen.add(c["time"]); unique.append(c)
    unique.sort(key=lambda c: c["time"])

    print(f"\n[TD] Total: {len(unique)} velas únicas")
    if unique:
        t0 = datetime.fromtimestamp(unique[0]["time"]).strftime("%Y-%m-%d")
        t1 = datetime.fromtimestamp(unique[-1]["time"]).strftime("%Y-%m-%d")
        print(f"[TD] Rango: {t0} → {t1}")

    out = out_file or f"{symbol.lower()}_{months}m_5m.json"
    Path(out).write_text(json.dumps(unique), encoding="utf-8")
    print(f"[TD] Guardado en {out}")
    return unique


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol",  default="QQQ")
    parser.add_argument("--months",  default=24,  type=int)
    parser.add_argument("--apikey",  default="demo")
    parser.add_argument("--out",     default=None)
    args = parser.parse_args()
    download_history(args.symbol, args.months, args.apikey, args.out)

if __name__ == "__main__":
    main()
