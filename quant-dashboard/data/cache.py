import threading
import time
from typing import Dict

import pandas as pd

from config import WATCHLIST, REFRESH_INTERVAL
from data.fetcher import fetch_stock, fetch_commodity, fetch_forex

_cache: Dict[str, pd.DataFrame] = {}
_anomaly_flags: Dict[str, bool] = {}
_lock = threading.Lock()


def get(symbol: str) -> pd.DataFrame:
    with _lock:
        df = _cache.get(symbol, pd.DataFrame())
    if not df.empty:
        return df
    # Supabase fallback — used when in-memory cache hasn't been populated yet
    try:
        from data.supabase_client import fetch_ohlcv
        return fetch_ohlcv(symbol)
    except Exception:
        return pd.DataFrame()


def get_anomaly_flag(module: str) -> bool:
    with _lock:
        return _anomaly_flags.get(module, False)


def _check_anomalies(symbol: str, df: pd.DataFrame) -> bool:
    if df.empty or len(df) < 20:
        return False
    close = df["Close"].squeeze()
    rolling_mean = close.rolling(20).mean()
    rolling_std = close.rolling(20).std()
    latest = float(close.iloc[-1])
    mean = float(rolling_mean.iloc[-1])
    std = float(rolling_std.iloc[-1])
    if std == 0:
        return False
    return abs(latest - mean) > 2 * std


def _refresh() -> None:
    fetcher_map = [
        (WATCHLIST["stocks"], fetch_stock),
        (WATCHLIST["commodities"], fetch_commodity),
        (WATCHLIST["forex"], fetch_forex),
    ]
    new_data: Dict[str, pd.DataFrame] = {}
    for symbols, fetcher in fetcher_map:
        for symbol in symbols:
            try:
                new_data[symbol] = fetcher(symbol)
            except Exception:
                pass

    anomaly = any(_check_anomalies(sym, df) for sym, df in new_data.items())

    with _lock:
        _cache.update(new_data)
        _anomaly_flags["market_impact"] = anomaly

    # Persist to Supabase in background (non-blocking)
    try:
        from data.supabase_client import upsert_ohlcv
        for sym, df in new_data.items():
            upsert_ohlcv(sym, df)
    except Exception as exc:
        print(f"[cache] Supabase sync error: {exc}")


def start_background_refresh() -> None:
    _refresh()

    def _loop() -> None:
        while True:
            time.sleep(REFRESH_INTERVAL)
            _refresh()

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
