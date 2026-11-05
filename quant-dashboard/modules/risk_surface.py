from typing import List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State

import data.cache as cache
from config import WATCHLIST, PERIOD_OPTIONS, SYMBOL_OPTIONS
from data.fetcher import fetch_any

_ALL_SYMBOLS = WATCHLIST["stocks"] + WATCHLIST["commodities"] + WATCHLIST["forex"]
_LAGS = list(range(1, 21))
_DEFAULT_SYMBOLS = WATCHLIST["stocks"][:3]


def _get_data(symbol: str, period: str) -> pd.DataFrame:
    if period == "5d":
        df = cache.get(symbol)
        if not df.empty:
            return df
    try:
        return fetch_any(symbol, period)
    except Exception:
        return pd.DataFrame()


def _rolling_vol(close: np.ndarray, lag: int) -> float:
    if len(close) < lag + 1:
        return 0.0
    returns = np.diff(np.log(np.clip(close, 1e-9, None)))
    return float(np.std(returns[-lag:]))


def _compute_surface(symbols: List[str], period: str = "5d") -> dict:
    if not symbols:
        return {}
    z_matrix = np.zeros((len(_LAGS), len(symbols)))
    for col_idx, sym in enumerate(symbols):
        df = _get_data(sym, period)
        if df.empty:
            continue
        close = df["Close"].squeeze().values.astype(float)
        for row_idx, lag in enumerate(_LAGS):
            z_matrix[row_idx, col_idx] = _rolling_vol(close, lag)
    return {"symbols": symbols, "lags": _LAGS, "z_matrix": z_matrix}


def _build_figure(surface: dict) -> go.Figure:
    if not surface:
        return go.Figure()
    fig = go.Figure(data=[go.Surface(
        z=surface["z_matrix"],
        x=surface["symbols"],
        y=surface["lags"],
        colorscale="Viridis",
        colorbar=dict(title="Volatility"),
    )])
    fig.update_layout(
        title="Multi-Asset 3D Risk Surface",
        scene=dict(
            xaxis_title="Asset",
            yaxis_title="Lag (bars)",
            zaxis_title="Rolling Volatility",
        ),
        template="plotly_dark",
        height=600,
    )
    return fig


def layout() -> html.Div:
    return html.Div([
        html.Div([
            html.Label("Asset Class (quick pick)", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="rs-asset-class",
                options=[
                    {"label": "—",           "value": "none"},
                    {"label": "All",         "value": "all"},
                    {"label": "Stocks",      "value": "stocks"},
                    {"label": "Commodities", "value": "commodities"},
                    {"label": "Forex",       "value": "forex"},
                ],
                value="none",
                clearable=False,
                style={"marginBottom": "12px"},
            ),

            html.Label("Symbols", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="rs-symbols",
                options=SYMBOL_OPTIONS,
                value=_DEFAULT_SYMBOLS,
                multi=True,
                searchable=True,
                placeholder="Select symbols…",
                style={"marginBottom": "8px"},
            ),
            html.Button("Load Symbols", id="rs-load-btn", n_clicks=0, className="load-btn"),

            html.Div(style={"height": "12px"}),

            html.Label("Time Period", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="rs-period",
                options=PERIOD_OPTIONS,
                value="5d",
                clearable=False,
                style={"marginBottom": "16px"},
            ),
            html.Div(id="rs-status", style={"fontSize": "12px", "color": "#aaa"}),
        ], style={"width": "23%", "padding": "16px", "display": "inline-block", "verticalAlign": "top"}),

        html.Div([
            dcc.Graph(id="rs-chart"),
        ], style={"width": "75%", "display": "inline-block", "verticalAlign": "top"}),
    ], style={"width": "100%"})


def register_callbacks(app) -> None:
    @app.callback(
        Output("rs-symbols", "value"),
        Input("rs-asset-class", "value"),
        State("rs-symbols", "value"),
        prevent_initial_call=True,
    )
    def quick_pick(asset_class: str, current):
        if asset_class == "none":
            return current
        if asset_class == "all":
            return _ALL_SYMBOLS
        return WATCHLIST.get(asset_class, current)

    @app.callback(
        Output("rs-chart", "figure"),
        Output("rs-status", "children"),
        Input("rs-load-btn", "n_clicks"),
        Input("rs-period", "value"),
        State("rs-symbols", "value"),
    )
    def update_surface(_n, period, symbols):
        if not symbols:
            return go.Figure(), "Select symbols then click Load Symbols"
        surface = _compute_surface(symbols, period)
        return _build_figure(surface), f"Loaded {len(symbols)} symbol(s)"
