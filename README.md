# Commodity Desk — Setup Guide

A Streamlit-based commodities intelligence dashboard powered by OpenBB.

---

## 1. Prerequisites

- Python 3.10–3.13
- VS Code with the Python extension installed

---

## 2. Get Your API Keys (Free)

### EIA (Energy Information Administration)
1. Go to https://www.eia.gov/opendata/register.php
2. Register with your email — key arrives instantly
3. Unlocks: US crude production, natural gas storage, refinery data, import/export flows

### FRED (Federal Reserve Bank of St. Louis)
1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
2. Create a free account and request an API key
3. Unlocks: DXY, Treasury yields, real yields (TIPS), Fed Funds rate, CPI/PCE

Both are completely free, no credit card required.

---

## 3. Installation

Open a terminal in VS Code (`Ctrl+`` `) and run:

```bash
# Create a virtual environment (recommended)
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 4. Run the Dashboard

```bash
streamlit run app.py
```

The app opens at http://localhost:8501

---

## 5. Enter API Keys

Paste your EIA and FRED keys into the sidebar of the running app.
No need to hardcode them anywhere — they're session-only.

If you want keys to persist between sessions, create a `.env` file:

```
EIA_API_KEY=your_eia_key_here
FRED_API_KEY=your_fred_key_here
```

And add to the top of `app.py`:
```python
from dotenv import load_dotenv
import os
load_dotenv()
eia_key = os.getenv("EIA_API_KEY")
fred_key = os.getenv("FRED_API_KEY")
```
Then install: `pip install python-dotenv`

---

## 6. What's in the Dashboard

| Tab | What You Get |
|-----|-------------|
| **Energy** | WTI/Brent prices, Brent-WTI spread, Henry Hub gas, EIA storage & production (with key) |
| **Metals** | Gold, silver, copper prices; gold/copper ratio as risk-sentiment indicator |
| **Agriculture** | Corn, soybeans, wheat; soy/corn ratio |
| **Macro Context** | DXY, 10Y yield, TIPS real yield, Fed Funds; cross-asset correlation heatmap |
| **Positioning** | CFTC Commitments of Traders — net speculative positioning by commodity |

### Sidebar Controls
- **Lookback window**: 3M / 6M / 1Y / 2Y / 5Y
- **Moving averages**: toggle on/off, adjust window (10–90 days)
- **Normalize to 100**: compare price trajectories across assets on same scale

---

## 7. Data Sources

| Data | Provider | Key Required |
|------|----------|-------------|
| Commodity futures prices | Yahoo Finance (via OpenBB) | No |
| EIA storage & production | FRED public series | No (EIA key expands coverage) |
| Macro rates / DXY | FRED | No (free tier) |
| CFTC positioning | OpenBB regulators router | No |

---

## 8. Project Structure

```
commodities_dashboard/
├── app.py           # Main Streamlit application
├── data_loader.py   # All data fetching (OpenBB calls)
├── config.py        # Colors and fonts
├── requirements.txt # Python dependencies
└── README.md        # This file
```
