import pandas as pd
from unittest.mock import patch

from data.fetcher import fetch_stock, fetch_commodity, fetch_forex, fetch_any


def _make_mock_df():
    return pd.DataFrame({
        "Open":   [100.0, 101.0],
        "High":   [102.0, 103.0],
        "Low":    [99.0,  100.0],
        "Close":  [101.0, 102.0],
        "Volume": [1000,  2000],
    }, index=pd.date_range("2024-01-01", periods=2, freq="5min"))


@patch("data.fetcher.yf.download")
def test_fetch_stock_returns_dataframe(mock_dl):
    mock_dl.return_value = _make_mock_df()
    result = fetch_stock("RELIANCE.NS")
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    mock_dl.assert_called_once_with(
        "RELIANCE.NS", period="5d", interval="5m", progress=False, auto_adjust=True
    )


@patch("data.fetcher.yf.download")
def test_fetch_commodity_calls_download(mock_dl):
    mock_dl.return_value = _make_mock_df()
    result = fetch_commodity("GC=F")
    assert isinstance(result, pd.DataFrame)
    mock_dl.assert_called_once_with(
        "GC=F", period="5d", interval="5m", progress=False, auto_adjust=True
    )


@patch("data.fetcher.yf.download")
def test_fetch_forex_calls_download(mock_dl):
    mock_dl.return_value = _make_mock_df()
    result = fetch_forex("USDINR=X")
    assert isinstance(result, pd.DataFrame)
    mock_dl.assert_called_once_with(
        "USDINR=X", period="5d", interval="5m", progress=False, auto_adjust=True
    )


@patch("data.fetcher.yf.download")
def test_fetch_stock_custom_period(mock_dl):
    mock_dl.return_value = _make_mock_df()
    fetch_stock("TCS.NS", period="1mo", interval="15m")
    mock_dl.assert_called_once_with(
        "TCS.NS", period="1mo", interval="15m", progress=False, auto_adjust=True
    )


@patch("data.fetcher.yf.download")
def test_fetch_any_picks_interval_from_period(mock_dl):
    mock_dl.return_value = _make_mock_df()
    fetch_any("INFY.NS", "3mo")
    mock_dl.assert_called_once_with(
        "INFY.NS", period="3mo", interval="1d", progress=False, auto_adjust=True
    )


@patch("data.fetcher.yf.download")
def test_multiindex_columns_are_flattened(mock_dl):
    df = _make_mock_df()
    df.columns = pd.MultiIndex.from_product([df.columns, ["RELIANCE.NS"]])
    mock_dl.return_value = df
    result = fetch_stock("RELIANCE.NS")
    assert list(result.columns) == ["Open", "High", "Low", "Close", "Volume"]
