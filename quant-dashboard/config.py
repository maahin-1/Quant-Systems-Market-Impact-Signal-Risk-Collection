import os
from dotenv import load_dotenv

load_dotenv()

WATCHLIST = {
    "stocks":      ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"],
    "commodities": ["GC=F", "CL=F", "SI=F"],
    "forex":       ["USDINR=X", "EURINR=X", "GBPINR=X"],
}

# Comprehensive symbol list for autocomplete dropdown
NSE_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "TITAN.NS", "NESTLEIND.NS", "WIPRO.NS", "HCLTECH.NS", "POWERGRID.NS",
    "TECHM.NS", "ONGC.NS", "GRASIM.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS",
    "DIVISLAB.NS", "BPCL.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "JSWSTEEL.NS",
    "M&M.NS", "CIPLA.NS", "DRREDDY.NS", "INDUSINDBK.NS", "EICHERMOT.NS",
    "HDFCLIFE.NS", "BAJAJFINSV.NS", "APOLLOHOSP.NS", "ADANIPORTS.NS",
    "ADANIENT.NS", "NTPC.NS", "COALINDIA.NS", "HEROMOTOCO.NS",
    "BRITANNIA.NS", "VEDL.NS", "HINDALCO.NS", "UPL.NS",
    "PIDILITIND.NS", "SIEMENS.NS", "HAVELLS.NS", "BAJAJ-AUTO.NS",
    "SHREECEM.NS", "TORNTPHARM.NS", "BOSCHLTD.NS", "BERGEPAINT.NS",
    "COLPAL.NS", "GODREJCP.NS", "MARICO.NS", "CONCOR.NS",
    "HAL.NS", "BEL.NS", "IRCTC.NS", "ZOMATO.NS", "DMART.NS",
]

COMMODITIES = [
    "GC=F",   # Gold
    "CL=F",   # Crude Oil WTI
    "SI=F",   # Silver
    "HG=F",   # Copper
    "NG=F",   # Natural Gas
    "BZ=F",   # Brent Crude
    "PL=F",   # Platinum
    "ZC=F",   # Corn
    "ZW=F",   # Wheat
    "ZS=F",   # Soybeans
]

FOREX_PAIRS = [
    "USDINR=X", "EURINR=X", "GBPINR=X",
    "JPYINR=X", "CHFINR=X", "AUDINR=X",
    "CADINR=X", "SGDINR=X", "HKDINR=X",
]

SYMBOL_OPTIONS = [
    {"label": f"[NSE] {s}", "value": s} for s in NSE_STOCKS
] + [
    {"label": f"[CMD] {s}", "value": s} for s in COMMODITIES
] + [
    {"label": f"[FX]  {s}", "value": s} for s in FOREX_PAIRS
]

REFRESH_INTERVAL = 300
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
DEFAULT_MODEL = "qwen/qwen3-coder:free"

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

PERIOD_OPTIONS = [
    {"label": "5 Days  (5m bars)",  "value": "5d"},
    {"label": "1 Month (1h bars)",  "value": "1mo"},
    {"label": "3 Months (1d bars)", "value": "3mo"},
    {"label": "6 Months (1d bars)", "value": "6mo"},
    {"label": "1 Year   (1d bars)", "value": "1y"},
]
