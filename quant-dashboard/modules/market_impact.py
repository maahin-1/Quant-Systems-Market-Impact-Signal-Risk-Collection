import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State

import data.cache as cache
from config import SYMBOL_OPTIONS, PERIOD_OPTIONS, WATCHLIST
from data.fetcher import fetch_any
from llm.client import query_llm
from llm.prompts import interpret_market_impact

_METRICS = ["returns", "volatility", "coverage", "activity"]
_DEFAULT_SYMBOLS = [WATCHLIST["stocks"][0]]
_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#bcbd22", "#17becf", "#aec7e8",
]


def _get_data(symbol: str, period: str) -> pd.DataFrame:
    if period == "5d":
        df = cache.get(symbol)
        if not df.empty:
            return df
    try:
        return fetch_any(symbol, period)
    except Exception:
        return pd.DataFrame()


_VOL_WINDOW = 20
_ACT_WINDOW = 20

_METRIC_LABELS = {
    "returns":    "Cumulative Log Returns (%)",
    "volatility": f"Rolling Volatility ({_VOL_WINDOW}-bar std)",
    "coverage":   "Relative Volume (x mean)",
    "activity":   f"Rolling Activity ({_ACT_WINDOW}-bar mean |r|)",
}


def _compute_metrics(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < _VOL_WINDOW + 2:
        return {}
    close = df["Close"].squeeze().values.astype(float)
    n = len(close)
    distance = np.arange(n, dtype=float)
    log_close = np.log(np.clip(close, 1e-9, None))
    raw_returns = np.diff(log_close, prepend=log_close[0])

    cum_returns = (np.cumsum(raw_returns)) * 100.0  # percent
    volatility = pd.Series(raw_returns).rolling(_VOL_WINDOW).std().bfill().values * 100.0
    activity = pd.Series(np.abs(raw_returns)).rolling(_ACT_WINDOW).mean().bfill().values * 100.0

    if "Volume" in df.columns:
        volume = df["Volume"].squeeze().values.astype(float)
    else:
        volume = np.ones(n)
    mean_vol = volume.mean() or 1.0
    coverage = volume / mean_vol

    return {
        "distance":   distance,
        "returns":    cum_returns,
        "volatility": volatility,
        "coverage":   coverage,
        "activity":   activity,
    }


def _build_figure(symbol_metrics: dict, metric: str) -> go.Figure:
    fig = go.Figure()
    if not symbol_metrics:
        fig.update_layout(
            title="Select symbols and click Load Symbols",
            template="plotly_dark",
            height=500,
        )
        return fig
    for i, (sym, m) in enumerate(symbol_metrics.items()):
        color = _COLORS[i % len(_COLORS)]
        fig.add_trace(go.Scatter(
            x=m["distance"], y=m[metric], mode="lines",
            line=dict(color=color, width=2),
            name=sym,
        ))
    if metric == "returns":
        fig.add_hline(y=0, line_dash="dot", line_color="#555")
    fig.update_layout(
        title=f"Market Impact — {_METRIC_LABELS.get(metric, metric.capitalize())}",
        xaxis_title="Bar Index (time)",
        yaxis_title=_METRIC_LABELS.get(metric, metric.capitalize()),
        template="plotly_dark",
        height=500,
        legend=dict(orientation="h", y=-0.18),
        hovermode="x unified",
    )
    fig.update_yaxes(autorange=True)
    return fig


def layout() -> html.Div:
    return html.Div([
        html.Div([
            html.Label("Symbols", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="mi-symbols",
                options=SYMBOL_OPTIONS,
                value=_DEFAULT_SYMBOLS,
                multi=True,
                searchable=True,
                placeholder="Select one or more symbols…",
                style={"marginBottom": "8px"},
            ),
            html.Button("Load Symbols", id="mi-load-btn", n_clicks=0, className="load-btn"),

            html.Div(style={"height": "12px"}),

            html.Label("Metric", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="mi-metric",
                options=[{"label": m.capitalize(), "value": m} for m in _METRICS],
                value="returns",
                clearable=False,
                style={"marginBottom": "12px"},
            ),

            html.Label("Time Period", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="mi-period",
                options=PERIOD_OPTIONS,
                value="5d",
                clearable=False,
                style={"marginBottom": "16px"},
            ),

            html.Button(
                "Ask LLM", id="mi-ask-llm", n_clicks=0,
                style={"width": "100%", "padding": "10px", "cursor": "pointer"},
            ),
            html.Div(id="mi-anomaly-badge", style={"marginTop": "12px", "color": "orange"}),
        ], style={"width": "23%", "padding": "16px", "display": "inline-block", "verticalAlign": "top"}),

        html.Div([
            dcc.Graph(id="mi-chart"),
        ], style={"width": "54%", "display": "inline-block", "verticalAlign": "top"}),

        html.Div([
            html.H4("LLM Analysis", style={"borderBottom": "1px solid #444", "paddingBottom": "8px"}),
            html.Div(
                id="mi-llm-output",
                style={"whiteSpace": "pre-wrap", "fontSize": "13px", "lineHeight": "1.5"},
            ),
        ], style={"width": "21%", "padding": "16px", "display": "inline-block", "verticalAlign": "top"}),
    ], style={"width": "100%"})


def register_callbacks(app) -> None:
    @app.callback(
        Output("mi-chart", "figure"),
        Output("mi-anomaly-badge", "children"),
        Input("mi-load-btn", "n_clicks"),
        Input("mi-metric", "value"),
        Input("mi-period", "value"),
        State("mi-symbols", "value"),
    )
    def update_chart(_n, metric, period, symbols):
        if not symbols:
            return _build_figure({}, metric), "Select symbols then click Load Symbols"
        sym_metrics = {}
        for sym in symbols:
            df = _get_data(sym, period)
            m = _compute_metrics(df)
            if m:
                sym_metrics[sym] = m
        if not sym_metrics:
            return _build_figure({}, metric), "No data for selected symbols"
        fig = _build_figure(sym_metrics, metric)
        badge = "⚠ Anomaly detected" if cache.get_anomaly_flag("market_impact") else f"Loaded {len(sym_metrics)} symbol(s)"
        return fig, badge

    @app.callback(
        Output("mi-llm-output", "children"),
        Input("mi-ask-llm", "n_clicks"),
        State("mi-symbols", "value"),
        State("mi-metric", "value"),
        State("mi-period", "value"),
        prevent_initial_call=True,
    )
    def ask_llm(_n, symbols, metric, period):
        if not symbols:
            return "Select symbols first."
        lines = []
        for sym in symbols:
            df = _get_data(sym, period)
            m = _compute_metrics(df)
            if not m:
                lines.append(f"[{sym}] No data.")
                continue
            y = m[metric]
            x = m["distance"]
            mean = float(np.mean(y))
            slope = float(np.polyfit(x, y, 1)[0])
            prompt = interpret_market_impact(sym, metric, mean, slope)
            try:
                lines.append(f"=== {sym} ===\n{query_llm(prompt)}")
            except Exception as exc:
                msg = str(exc)
                if "429" in msg:
                    lines.append(f"[{sym}] Rate limited (free tier). Wait 30s and retry.")
                else:
                    lines.append(f"[{sym}] LLM error: {msg}")
        return "\n\n".join(lines)
