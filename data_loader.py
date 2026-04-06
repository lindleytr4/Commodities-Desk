"""
data_loader.py
All data fetching for the Commodity Desk dashboard.
Uses yfinance, fredapi, and requests directly — no OpenBB dependency.
This makes the app compatible with Streamlit Cloud.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# ── yfinance ──────────────────────────────────────────────────────────────────
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# ── fredapi ───────────────────────────────────────────────────────────────────
try:
    from fredapi import Fred
    FREDAPI_AVAILABLE = True
except ImportError:
    FREDAPI_AVAILABLE = False

# ── requests (for EIA) ────────────────────────────────────────────────────────
import requests


# ── Generic yfinance price fetch ─────────────────────────────────────────────
def _yf_price(ticker, start, end):
    if not YFINANCE_AVAILABLE:
        return None
    try:
        df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
        if df is None or df.empty:
            return None
        s = df["Close"]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        s.index = pd.to_datetime(s.index)
        s = s.sort_index()
        s.name = ticker
        return s
    except Exception as e:
        print(f"  yfinance fetch failed [{ticker}]: {e}")
        return None


# ── Crude Oil ─────────────────────────────────────────────────────────────────
def get_crude_prices(start, end):
    series = {}
    for label, ticker in [("WTI", "CL=F"), ("Brent", "BZ=F")]:
        s = _yf_price(ticker, start, end)
        if s is not None:
            series[label] = s
    if not series:
        return None
    df = pd.DataFrame(series)
    return df[~df.index.duplicated(keep='last')]


# ── Natural Gas ───────────────────────────────────────────────────────────────
def get_natgas_prices(start, end):
    s = _yf_price("NG=F", start, end)
    if s is None:
        return None
    df = pd.DataFrame({"HenryHub": s})
    return df[~df.index.duplicated(keep='last')]


# ── Metals ────────────────────────────────────────────────────────────────────
def get_metals_prices(start, end):
    series = {}
    for label, ticker in [("Gold", "GC=F"), ("Silver", "SI=F"), ("Copper", "HG=F")]:
        s = _yf_price(ticker, start, end)
        if s is not None:
            series[label] = s
    if not series:
        return None
    df = pd.DataFrame(series)
    return df[~df.index.duplicated(keep='last')]


# ── Agriculture ───────────────────────────────────────────────────────────────
def get_agriculture_prices(start, end):
    series = {}
    for label, ticker in [("Corn", "ZC=F"), ("Soybeans", "ZS=F"), ("Wheat", "ZW=F")]:
        s = _yf_price(ticker, start, end)
        if s is not None:
            series[label] = s
    if not series:
        return None
    df = pd.DataFrame(series)
    return df[~df.index.duplicated(keep='last')]


# ── EIA — Natural Gas Storage ─────────────────────────────────────────────────
def get_eia_storage(start, end, eia_key=None):
    """
    Weekly US natural gas storage via EIA API v2.
    Series: NW2 (Lower 48 working gas in storage)
    """
    if not eia_key:
        return None
    try:
        url = "https://api.eia.gov/v2/natural-gas/stor/wkly/data/"
        params = {
            "api_key": eia_key,
            "frequency": "weekly",
            "data[0]": "value",
            "facets[series][]": "NW2",
            "start": start[:7],  # YYYY-MM
            "end": end[:7],
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "length": 500,
            "offset": 0,
        }
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        rows = data.get("response", {}).get("data", [])
        if not rows:
            return None
        df = pd.DataFrame(rows)
        df["period"] = pd.to_datetime(df["period"])
        df = df.set_index("period").sort_index()
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df[["value"]].rename(columns={"value": "Storage_Bcf"})
        return df
    except Exception as e:
        print(f"  EIA storage fetch failed: {e}")
        return None


# ── EIA — Crude Production ────────────────────────────────────────────────────
def get_eia_production(start, end, eia_key=None):
    """
    Weekly US crude oil production via EIA API v2.
    """
    if not eia_key:
        return None
    try:
        url = "https://api.eia.gov/v2/petroleum/sum/sndw/data/"
        params = {
            "api_key": eia_key,
            "frequency": "weekly",
            "data[0]": "value",
            "facets[series][]": "WCRFPUS2",
            "start": start[:7],
            "end": end[:7],
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "length": 500,
            "offset": 0,
        }
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        rows = data.get("response", {}).get("data", [])
        if not rows:
            return None
        df = pd.DataFrame(rows)
        df["period"] = pd.to_datetime(df["period"])
        df = df.set_index("period").sort_index()
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df[["value"]].rename(columns={"value": "US_Production_Mbpd"})
        return df
    except Exception as e:
        print(f"  EIA production fetch failed: {e}")
        return None


# ── FRED Macro ────────────────────────────────────────────────────────────────
def get_fred_macro(start, end, fred_key=None):
    """
    Key macro series via FRED:
      DXY:       DTWEXBGS  (Trade-weighted USD index)
      10Y_Yield: DGS10
      Fed_Funds: FEDFUNDS
      TIPS_10Y:  DFII10    (10Y real yield)
    """
    if not fred_key or not FREDAPI_AVAILABLE:
        return None

    fred_map = {
        "DXY":       "DTWEXBGS",
        "10Y_Yield": "DGS10",
        "Fed_Funds": "FEDFUNDS",
        "TIPS_10Y":  "DFII10",
    }

    try:
        fred = Fred(api_key=fred_key)
        series = {}
        for label, sym in fred_map.items():
            try:
                s = fred.get_series(sym, observation_start=start, observation_end=end)
                s.index = pd.to_datetime(s.index)
                s = s.dropna().sort_index()
                series[label] = s
            except Exception as e:
                print(f"  FRED [{sym}] failed: {e}")

        if not series:
            return None
        out = pd.DataFrame(series)
        return out[~out.index.duplicated(keep='last')]
    except Exception as e:
        print(f"  FRED init failed: {e}")
        return None


# ── CFTC Positioning ──────────────────────────────────────────────────────────
def get_cftc_positioning(start, end):
    """
    CFTC Commitments of Traders via CFTC public API.
    Returns net speculative (non-commercial) positioning.
    """
    commodities = {
        "Crude Oil (WTI)": "067651",
        "Natural Gas":     "023651",
        "Gold":            "088691",
        "Copper":          "085692",
        "Corn":            "002602",
        "Soybeans":        "005602",
        "Wheat (CBOT)":    "001602",
    }

    frames = []
    base_url = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"

    for name, code in commodities.items():
        try:
            params = {
                "$where": f"cftc_commodity_code='{code}' AND report_date_as_yyyy_mm_dd >= '{start}' AND report_date_as_yyyy_mm_dd <= '{end}'",
                "$limit": 500,
                "$order": "report_date_as_yyyy_mm_dd ASC",
            }
            r = requests.get(base_url, params=params, timeout=15)
            r.raise_for_status()
            rows = r.json()
            if not rows:
                continue
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["report_date_as_yyyy_mm_dd"])
            df = df.set_index("date").sort_index()
            long_col  = "noncomm_positions_long_all"
            short_col = "noncomm_positions_short_all"
            if long_col in df.columns and short_col in df.columns:
                df[long_col]  = pd.to_numeric(df[long_col],  errors="coerce")
                df[short_col] = pd.to_numeric(df[short_col], errors="coerce")
                df["net_position"] = df[long_col] - df[short_col]
                df["commodity"] = name
                frames.append(df[["net_position", "commodity"]])
        except Exception as e:
            print(f"  CFTC [{name}] failed: {e}")

    if not frames:
        return None
    combined = pd.concat(frames)
    return combined[~combined.index.duplicated(keep='last')]
