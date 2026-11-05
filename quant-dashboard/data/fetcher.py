import pandas as pd
import yfinance as yf

_PERIOD_INTERVALS = {
    "5d":  "5m",
    "1mo": "60m",
    "3mo": "1d",
    "6mo": "1d",
    "1y":  "1d",
}


def _fetch(symbol: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
    # yfinance 1.x returns MultiIndex columns for single-ticker downloads;
    # flatten to simple column names so downstream code works uniformly.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def fetch_stock(symbol: str, period: str = "5d", interval: str = "5m") -> pd.DataFrame:
    return _fetch(symbol, period, interval)


def fetch_commodity(symbol: str, period: str = "5d", interval: str = "5m") -> pd.DataFrame:
    return _fetch(symbol, period, interval)


def fetch_forex(symbol: str, period: str = "5d", interval: str = "5m") -> pd.DataFrame:
    return _fetch(symbol, period, interval)


def fetch_any(symbol: str, period: str = "5d") -> pd.DataFrame:
    interval = _PERIOD_INTERVALS.get(period, "5m")
    return _fetch(symbol, period, interval)
