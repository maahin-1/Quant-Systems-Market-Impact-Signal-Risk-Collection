import pandas as pd
import numpy as np


def _make_df(n=25, anomalous=False):
    prices = np.ones(n) * 100.0
    if anomalous:
        prices[-1] = 200.0  # spike forces |z| > 2
    return pd.DataFrame(
        {"Close": prices},
        index=pd.date_range("2024-01-01", periods=n, freq="5min"),
    )


def test_get_unknown_symbol_returns_empty():
    import data.cache as cache
    result = cache.get("FAKE_SYMBOL_XYZ")
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_check_anomalies_empty_df_returns_false():
    import data.cache as cache
    assert cache._check_anomalies("X", pd.DataFrame()) is False


def test_check_anomalies_short_df_returns_false():
    import data.cache as cache
    assert cache._check_anomalies("X", _make_df(5)) is False


def test_check_anomalies_normal_data_returns_false():
    import data.cache as cache
    # All prices identical → std=0 → returns False
    assert cache._check_anomalies("X", _make_df(25, anomalous=False)) is False


def test_check_anomalies_spike_returns_true():
    import data.cache as cache
    # Price spike to 200 while rest are 100 → |z| ≈ 4.25 > 2
    assert cache._check_anomalies("X", _make_df(25, anomalous=True)) is True


def test_get_anomaly_flag_unknown_module_returns_false():
    import data.cache as cache
    assert cache.get_anomaly_flag("nonexistent_module") is False
