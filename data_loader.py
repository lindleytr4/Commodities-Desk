"""
data_loader.py
All data fetching logic for the Commodity Desk dashboard.
Uses OpenBB as the primary source; falls back gracefully when keys are missing.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# ── OpenBB import ─────────────────────────────────────────────────────────────
try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False
    print("WARNING: openbb not installed. Run: pip install openbb[all]")


# ── Helpers ───────────────────────────────────────────────────────────────────
def _obb_to_df(result, value_col=None):
    """Convert OBBject to DataFrame, return None on failure."""
    try:
        df = result.to_dataframe()
        if df is None or df.empty:
            return None
        if "date" in df.columns:
            df = df.set_index("date")
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        if value_col and value_col in df.columns:
            return df[[value_col]]
        return df
    except Exception as e:
        print(f"  obb_to_df error: {e}")
        return None


def _fetch_price(ticker, start, end, provider="yfinance"):
    """Generic price fetch via OpenBB equity.price.historical."""
    if not OPENBB_AVAILABLE:
        return None
    try:
        result = obb.equity.price.historical(
            symbol=ticker,
            start_date=start,
            end_date=end,
            provider=provider
        )
        df = _obb_to_df(result)
        if df is not None and "close" in df.columns:
            return df["close"].rename(ticker)
        return None
    except Exception as e:
        print(f"  Price fetch failed [{ticker}]: {e}")
        return None


# ── Crude Oil ─────────────────────────────────────────────────────────────────
def get_crude_prices(start, end):
    """
    WTI: CL=F (NYMEX front-month proxy via yfinance)
    Brent: BZ=F
    """
    series = {}
    for label, ticker in [("WTI", "CL=F"), ("Brent", "BZ=F")]:
        s = _fetch_price(ticker, start, end)
        if s is not None:
            series[label] = s

    if not series:
        return None

    df = pd.DataFrame(series)
    df = df[~df.index.duplicated(keep='last')]
    return df


# ── Natural Gas ───────────────────────────────────────────────────────────────
def get_natgas_prices(start, end):
    """
    Henry Hub proxy: NG=F (NYMEX natural gas front-month)
    """
    s = _fetch_price("NG=F", start, end)
    if s is None:
        return None
    df = pd.DataFrame({"HenryHub": s})
    df = df[~df.index.duplicated(keep='last')]
    return df


# ── Metals ────────────────────────────────────────────────────────────────────
def get_metals_prices(start, end):
    """
    Gold:   GC=F (COMEX)
    Silver: SI=F
    Copper: HG=F ($/lb)
    """
    series = {}
    for label, ticker in [("Gold", "GC=F"), ("Silver", "SI=F"), ("Copper", "HG=F")]:
        s = _fetch_price(ticker, start, end)
        if s is not None:
            series[label] = s

    if not series:
        return None

    df = pd.DataFrame(series)
    df = df[~df.index.duplicated(keep='last')]
    return df


# ── Agriculture ───────────────────────────────────────────────────────────────
def get_agriculture_prices(start, end):
    """
    Corn:     ZC=F (CBOT, ¢/bu)
    Soybeans: ZS=F
    Wheat:    ZW=F
    """
    series = {}
    for label, ticker in [("Corn", "ZC=F"), ("Soybeans", "ZS=F"), ("Wheat", "ZW=F")]:
        s = _fetch_price(ticker, start, end)
        if s is not None:
            series[label] = s

    if not series:
        return None

    df = pd.DataFrame(series)
    df = df[~df.index.duplicated(keep='last')]
    return df


# ── EIA — Natural Gas Storage ─────────────────────────────────────────────────
def get_eia_storage(start, end, eia_key=None):
    """
    Weekly US natural gas storage via OpenBB commodity router (EIA).
    Requires EIA API key.
    """
    if not OPENBB_AVAILABLE or not eia_key:
        return None
    try:
        obb.user.credentials.eia_api_key = eia_key
        result = obb.commodity.price.spot(
            symbol="NG", provider="eia",
            start_date=start, end_date=end
        )
        return _obb_to_df(result)
    except Exception:
        pass

    # Fallback: try economy endpoint for nat gas storage series
    try:
        result = obb.economy.fred_series(
            symbol="NGCSCSTUS72",   # EIA Weekly Nat Gas Storage
            start_date=start, end_date=end,
            provider="fred"
        )
        df = _obb_to_df(result)
        if df is not None:
            df.columns = ["Storage_Bcf"]
        return df
    except Exception as e:
        print(f"  EIA storage fetch failed: {e}")
        return None


# ── EIA — Crude Production ────────────────────────────────────────────────────
def get_eia_production(start, end, eia_key=None):
    """
    US crude oil production (weekly, mb/d) via FRED/EIA series.
    FRED series WCRFPUS2 = US weekly crude production.
    """
    if not OPENBB_AVAILABLE:
        return None

    fred_series = {
        "US_Production_Mbpd": "WCRFPUS2",
    }

    series = {}
    for label, sym in fred_series.items():
        try:
            result = obb.economy.fred_series(
                symbol=sym, start_date=start, end_date=end
            )
            df = _obb_to_df(result)
            if df is not None:
                s = df.iloc[:, 0]
                series[label] = s
        except Exception as e:
            print(f"  Production series [{sym}] failed: {e}")

    if not series:
        return None
    return pd.DataFrame(series)


# ── FRED Macro ────────────────────────────────────────────────────────────────
def get_fred_macro(start, end, fred_key=None):
    """
    Key macro series via FRED:
      DXY:      DTWEXBGS  (Trade-weighted USD index)
      10Y_Yield: DGS10
      Fed_Funds: FEDFUNDS
      TIPS_10Y:  DFII10   (10Y real yield)
    Falls back to public FRED endpoint (no key needed for basic series).
    """
    if not OPENBB_AVAILABLE:
        return None

    if fred_key:
        try:
            obb.user.credentials.fred_api_key = fred_key
        except Exception:
            pass

    fred_map = {
        "DXY":       "DTWEXBGS",
        "10Y_Yield": "DGS10",
        "Fed_Funds": "FEDFUNDS",
        "TIPS_10Y":  "DFII10",
    }

    series = {}
    for label, sym in fred_map.items():
        try:
            result = obb.economy.fred_series(
                symbol=sym, start_date=start, end_date=end
            )
            df = _obb_to_df(result)
            if df is not None and not df.empty:
                series[label] = df.iloc[:, 0]
        except Exception as e:
            print(f"  FRED [{sym}] failed: {e}")

    if not series:
        return None

    out = pd.DataFrame(series)
    out = out[~out.index.duplicated(keep='last')]
    return out


# ── CFTC Positioning ──────────────────────────────────────────────────────────
def get_cftc_positioning(start, end):
    """
    CFTC Commitments of Traders — net speculative positioning.
    Uses OpenBB regulators.cftc router.
    """
    if not OPENBB_AVAILABLE:
        return None

    commodities = {
        "Crude Oil (WTI)":  "067651",
        "Natural Gas":      "023651",
        "Gold":             "088691",
        "Copper":           "085692",
        "Corn":             "002602",
        "Soybeans":         "005602",
        "Wheat (CBOT)":     "001602",
    }

    frames = []
    for name, code in commodities.items():
        try:
            result = obb.regulators.cftc.cot(
                id=code, start_date=start, end_date=end
            )
            df = _obb_to_df(result)
            if df is not None and not df.empty:
                # Calculate net speculative (non-commercial) position
                if "noncomm_positions_long_all" in df.columns and "noncomm_positions_short_all" in df.columns:
                    df["net_position"] = df["noncomm_positions_long_all"] - df["noncomm_positions_short_all"]
                    df["commodity"] = name
                    frames.append(df[["net_position", "commodity"]])
        except Exception as e:
            print(f"  CFTC [{name}] failed: {e}")

    if not frames:
        return None

    combined = pd.concat(frames)
    combined = combined[~combined.index.duplicated(keep='last')]
    return combined
