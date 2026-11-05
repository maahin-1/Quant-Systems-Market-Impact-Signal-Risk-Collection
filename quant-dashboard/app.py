import dash
from dash import dcc, html, Input, Output

import data.cache as cache
import modules.market_impact as market_impact
import modules.signal_decay as signal_decay
import modules.risk_surface as risk_surface

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Quant Dashboard — Indian Markets"

app.layout = html.Div([
    html.H2(
        "Quant Dashboard — Indian Markets",
        style={"padding": "16px 16px 0", "margin": 0},
    ),
    dcc.Tabs(
        id="tabs",
        value="market-impact",
        children=[
            dcc.Tab(label="Market Impact", value="market-impact"),
            dcc.Tab(label="Signal Decay",    value="signal-decay"),
            dcc.Tab(label="3D Risk Surface", value="risk-surface"),
        ],
        style={"margin": "8px 16px 0"},
    ),
    html.Div(id="tab-content", style={"marginTop": "8px"}),
    dcc.Interval(id="page-refresh", interval=300_000, n_intervals=0),
], style={
    "fontFamily": "sans-serif",
    "backgroundColor": "#1a1a2e",
    "color": "#eee",
    "minHeight": "100vh",
})

market_impact.register_callbacks(app)
signal_decay.register_callbacks(app)
risk_surface.register_callbacks(app)


@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value"),
)
def render_tab(tab: str):
    if tab == "market-impact":
        return market_impact.layout()
    if tab == "signal-decay":
        return signal_decay.layout()
    if tab == "risk-surface":
        return risk_surface.layout()
    return html.Div("Unknown tab.", style={"padding": "32px"})


if __name__ == "__main__":
    cache.start_background_refresh()
    app.run(debug=False, use_reloader=False, host="127.0.0.1", port=8050)
