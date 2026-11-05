import numpy as np
import pandas as pd
import plotly.graph_objects as go


def _make_df(n=50):
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(n))
    volume = np.random.randint(1000, 5000, n)
    return pd.DataFrame(
        {"Close": prices, "Volume": volume},
        index=pd.date_range("2024-01-01", periods=n, freq="5min"),
    )


from modules.market_impact import _compute_metrics, _build_figure


def test_compute_metrics_returns_all_keys():
    result = _compute_metrics(_make_df())
    assert set(result.keys()) == {"distance", "returns", "volatility", "coverage", "activity"}


def test_compute_metrics_arrays_same_length():
    result = _compute_metrics(_make_df(50))
    lengths = {len(v) for v in result.values()}
    assert len(lengths) == 1


def test_compute_metrics_empty_returns_empty_dict():
    assert _compute_metrics(pd.DataFrame()) == {}


def test_compute_metrics_too_short_returns_empty_dict():
    assert _compute_metrics(_make_df(4)) == {}


def test_compute_metrics_cumulative_return_starts_at_zero():
    result = _compute_metrics(_make_df())
    assert result["returns"][0] == 0.0


def test_compute_metrics_relative_volume_averages_one():
    result = _compute_metrics(_make_df())
    assert abs(result["coverage"].mean() - 1.0) < 1e-9


def test_build_figure_draws_one_trace_per_symbol():
    metrics = _compute_metrics(_make_df())
    fig = _build_figure({"AAA.NS": metrics, "BBB.NS": metrics}, "returns")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert {t.name for t in fig.data} == {"AAA.NS", "BBB.NS"}


def test_build_figure_empty_metrics_returns_empty_figure():
    fig = _build_figure({}, "returns")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0
