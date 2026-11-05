import numpy as np
import pandas as pd
import plotly.graph_objects as go


def _make_df(n=80):
    np.random.seed(7)
    prices = 100 + np.cumsum(np.random.randn(n))
    return pd.DataFrame(
        {"Close": prices, "Volume": np.random.randint(1000, 5000, n)},
        index=pd.date_range("2024-01-01", periods=n, freq="5min"),
    )


from modules.signal_decay import _compute_decay, _build_figure


def test_compute_decay_returns_required_keys():
    result = _compute_decay(_make_df())
    assert "lags" in result
    assert "correlation" in result
    assert "half_life" in result


def test_compute_decay_empty_returns_empty():
    assert _compute_decay(pd.DataFrame()) == {}


def test_compute_decay_short_returns_empty():
    assert _compute_decay(_make_df(5)) == {}


def test_build_decay_figure_returns_go_figure():
    metrics = _compute_decay(_make_df())
    fig = _build_figure({"AAA.NS": metrics, "BBB.NS": metrics})
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2


def test_build_decay_figure_empty_returns_empty_figure():
    fig = _build_figure({})
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0


def test_half_life_is_positive_float():
    result = _compute_decay(_make_df())
    assert isinstance(result["half_life"], float)
    assert result["half_life"] > 0
