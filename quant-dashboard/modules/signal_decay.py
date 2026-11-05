import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State

import data.cache as cache
from config import SYMBOL_OPTIONS, PERIOD_OPTIONS, WATCHLIST
from data.fetcher import fetch_any
from llm.client import query_llm
from llm.prompts import signal_decay_prompt

_DEFAULT_SYMBOLS = [WATCHLIST["stocks"][0]]
_MAX_LAG = 30
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


def _compute_decay(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 10:
        return {}
    close = df["Close"].squeeze().values.astype(float)
    returns = np.diff(np.log(np.clip(close, 1e-9, None)))
    n = len(returns)
    max_lag = min(_MAX_LAG, n // 2)
    lags = np.arange(1, max_lag + 1)
    correlations = np.array([
        float(np.corrcoef(returns[:-lag], returns[lag:])[0, 1])
        if len(returns[:-lag]) > 1 else 0.0
        for lag in lags
    ])
    peak = abs(correlations).max() or 1e-9
    below_half = np.where(abs(correlations) < 0.5 * peak)[0]
    half_life = float(lags[below_half[0]]) if len(below_half) > 0 else float(max_lag)
    return {"lags": lags, "correlation": correlations, "half_life": half_life}


def _build_figure(symbol_metrics: dict) -> go.Figure:
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
            x=m["lags"], y=m["correlation"],
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=5, color=color),
            name=f"{sym} (HL={m['half_life']:.1f})",
        ))
    fig.add_hline(y=0, line_dash="dot", line_color="#555")
    fig.update_layout(
        title="Signal Decay vs Performance (Multi-Symbol)",
        xaxis_title="Lag (bars)",
        yaxis_title="Autocorrelation",
        template="plotly_dark",
        height=500,
        legend=dict(orientation="h", y=-0.18),
    )
    return fig


def layout() -> html.Div:
    return html.Div([
        html.Div([
            html.Label("Symbols", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="sd-symbols",
                options=SYMBOL_OPTIONS,
                value=_DEFAULT_SYMBOLS,
                multi=True,
                searchable=True,
                placeholder="Select one or more symbols…",
                style={"marginBottom": "8px"},
            ),
            html.Button("Load Symbols", id="sd-load-btn", n_clicks=0, className="load-btn"),

            html.Div(style={"height": "12px"}),

            html.Label("Time Period", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="sd-period",
                options=PERIOD_OPTIONS,
                value="5d",
                clearable=False,
                style={"marginBottom": "16px"},
            ),

            html.Button(
                "Ask LLM", id="sd-ask-llm", n_clicks=0,
                style={"width": "100%", "padding": "10px", "cursor": "pointer"},
            ),
            html.Div(id="sd-halflife-display", style={"marginTop": "12px", "fontSize": "13px"}),
        ], style={"width": "23%", "padding": "16px", "display": "inline-block", "verticalAlign": "top"}),

        html.Div([
            dcc.Graph(id="sd-chart"),
        ], style={"width": "54%", "display": "inline-block", "verticalAlign": "top"}),

        html.Div([
            html.H4("LLM Analysis", style={"borderBottom": "1px solid #444", "paddingBottom": "8px"}),
            html.Div(
                id="sd-llm-output",
                style={"whiteSpace": "pre-wrap", "fontSize": "13px", "lineHeight": "1.5"},
            ),
        ], style={"width": "21%", "padding": "16px", "display": "inline-block", "verticalAlign": "top"}),
    ], style={"width": "100%"})


def register_callbacks(app) -> None:
    @app.callback(
        Output("sd-chart", "figure"),
        Output("sd-halflife-display", "children"),
        Input("sd-load-btn", "n_clicks"),
        Input("sd-period", "value"),
        State("sd-symbols", "value"),
    )
    def update_chart(_n, period, symbols):
        if not symbols:
            return _build_figure({}), "Select symbols then click Load Symbols"
        sym_metrics = {}
        for sym in symbols:
            df = _get_data(sym, period)
            m = _compute_decay(df)
            if m:
                sym_metrics[sym] = m
        fig = _build_figure(sym_metrics)
        if not sym_metrics:
            return fig, "No data for selected symbols"
        hl_lines = [f"{s}: {m['half_life']:.1f} bars" for s, m in sym_metrics.items()]
        return fig, html.Pre("\n".join(hl_lines), style={"fontSize": "12px"})

    @app.callback(
        Output("sd-llm-output", "children"),
        Input("sd-ask-llm", "n_clicks"),
        State("sd-symbols", "value"),
        State("sd-period", "value"),
        prevent_initial_call=True,
    )
    def ask_llm(_n, symbols, period):
        if not symbols:
            return "Select symbols first."
        lines = []
        for sym in symbols:
            df = _get_data(sym, period)
            m = _compute_decay(df)
            if not m:
                lines.append(f"[{sym}] No data.")
                continue
            half_life = m["half_life"]
            current_bar = int(np.argmax(np.abs(m["correlation"])))
            prompt = signal_decay_prompt(sym, half_life, current_bar)
            try:
                lines.append(f"=== {sym} ===\n{query_llm(prompt)}")
            except Exception as exc:
                msg = str(exc)
                if "429" in msg:
                    lines.append(f"[{sym}] Rate limited (free tier). Wait 30s and retry.")
                else:
                    lines.append(f"[{sym}] LLM error: {msg}")
        return "\n\n".join(lines)
