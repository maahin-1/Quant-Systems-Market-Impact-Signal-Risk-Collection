from __future__ import annotations

import pandas as pd

from config import SUPABASE_URL, SUPABASE_KEY

_client = None


def _get_client():
    global _client
    if _client is None:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def upsert_ohlcv(symbol: str, df: pd.DataFrame) -> None:
    if df.empty:
        return
    records = []
    for ts, row in df.iterrows():
        ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        records.append({
            "symbol": symbol,
            "timestamp": ts_str,
            "open":   float(row.get("Open",   0) or 0),
            "high":   float(row.get("High",   0) or 0),
            "low":    float(row.get("Low",    0) or 0),
            "close":  float(row.get("Close",  0) or 0),
            "volume": float(row.get("Volume", 0) or 0),
        })
    try:
        _get_client().table("ohlcv").upsert(records, on_conflict="symbol,timestamp").execute()
    except Exception as exc:
        print(f"[supabase] upsert failed for {symbol}: {exc}")


def fetch_ohlcv(symbol: str, limit: int = 500) -> pd.DataFrame:
    try:
        resp = (
            _get_client()
            .table("ohlcv")
            .select("timestamp,open,high,low,close,volume")
            .eq("symbol", symbol)
            .order("timestamp", desc=False)
            .limit(limit)
            .execute()
        )
        rows = resp.data
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.set_index("timestamp").rename(columns={
            "open": "Open", "high": "High", "low": "Low",
            "close": "Close", "volume": "Volume",
        })
        return df
    except Exception as exc:
        print(f"[supabase] fetch failed for {symbol}: {exc}")
        return pd.DataFrame()
