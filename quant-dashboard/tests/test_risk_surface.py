import numpy as np
import pandas as pd
import plotly.graph_objects as go


def _seed_cache(symbols):
    import data.cache as cache_mod
    np.random.seed(1)
    for sym in symbols:
        prices = 100 + np.cumsum(np.random.randn(50))
        df = pd.DataFrame(
            {"Close": prices, "Volume": np.random.randint(1000, 5000, 50)},
            index=pd.date_range("2024-01-01", periods=50, freq="5min"),
        )
        with cache_mod._lock:
            cache_mod._cache[sym] = df


from modules.risk_surface import _compute_surface, _build_figure


def test_compute_surface_returns_correct_keys():
    _seed_cache(["RELIANCE.NS", "TCS.NS"])
    result = _compute_surface(["RELIANCE.NS", "TCS.NS"])
    assert set(result.keys()) == {"symbols", "lags", "z_matrix"}


def test_compute_surface_matrix_shape():
    _seed_cache(["RELIANCE.NS", "TCS.NS"])
    result = _compute_surface(["RELIANCE.NS", "TCS.NS"])
    assert result["z_matrix"].shape == (len(result["lags"]), 2)


def test_compute_surface_empty_symbols_returns_empty():
    assert _compute_surface([]) == {}


def test_build_surface_figure_returns_go_figure():
    _seed_cache(["RELIANCE.NS", "TCS.NS"])
    surface = _compute_surface(["RELIANCE.NS", "TCS.NS"])
    fig = _build_figure(surface)
    assert isinstance(fig, go.Figure)


def test_build_surface_figure_empty_returns_empty():
    fig = _build_figure({})
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0
