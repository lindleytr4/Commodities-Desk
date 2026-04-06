import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

from data_loader import (
    get_crude_prices, get_natgas_prices, get_metals_prices,
    get_agriculture_prices, get_eia_storage, get_eia_production,
    get_fred_macro, get_cftc_positioning
)
from config import COLORS, FONT, hex_to_rgba

st.set_page_config(
    page_title="COMMODITY DESK",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Inject CSS ──────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow+Condensed:wght@300;400;600;700&family=Barlow:wght@300;400;500&display=swap');

  :root {{
    --bg:        {COLORS['bg']};
    --surface:   {COLORS['surface']};
    --border:    {COLORS['border']};
    --accent:    {COLORS['accent']};
    --accent2:   {COLORS['accent2']};
    --text:      {COLORS['text']};
    --muted:     {COLORS['muted']};
    --up:        {COLORS['up']};
    --down:      {COLORS['down']};
    --mono:      'Share Tech Mono', monospace;
    --head:      'Barlow Condensed', sans-serif;
    --body:      'Barlow', sans-serif;
  }}

  html, body, [data-testid="stApp"] {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--body);
  }}

  /* Sidebar */
  [data-testid="stSidebar"] {{
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
  }}
  [data-testid="stSidebar"] * {{ color: var(--text) !important; }}

  /* Header bar */
  .desk-header {{
    display: flex;
    align-items: baseline;
    gap: 16px;
    padding: 8px 0 20px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
  }}
  .desk-title {{
    font-family: var(--head);
    font-size: 2.6rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    color: var(--text);
    line-height: 1;
  }}
  .desk-subtitle {{
    font-family: var(--mono);
    font-size: 0.72rem;
    color: var(--accent);
    letter-spacing: 0.12em;
  }}
  .desk-timestamp {{
    font-family: var(--mono);
    font-size: 0.68rem;
    color: var(--muted);
    margin-left: auto;
    letter-spacing: 0.06em;
  }}

  /* Ticker strip */
  .ticker-row {{
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    flex-wrap: wrap;
  }}
  .ticker-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 12px 18px;
    min-width: 140px;
    flex: 1;
    position: relative;
    overflow: hidden;
  }}
  .ticker-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent);
  }}
  .ticker-card.down::before {{ background: var(--down); }}
  .ticker-card.up::before {{ background: var(--up); }}
  .ticker-name {{
    font-family: var(--mono);
    font-size: 0.65rem;
    color: var(--muted);
    letter-spacing: 0.1em;
    margin-bottom: 4px;
  }}
  .ticker-price {{
    font-family: var(--mono);
    font-size: 1.5rem;
    font-weight: 400;
    color: var(--text);
    line-height: 1;
  }}
  .ticker-change {{
    font-family: var(--mono);
    font-size: 0.72rem;
    margin-top: 4px;
  }}
  .up {{ color: var(--up); }}
  .down {{ color: var(--down); }}

  /* Section labels */
  .section-label {{
    font-family: var(--head);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }}

  /* Chart container */
  .chart-wrap {{
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 16px;
    margin-bottom: 16px;
  }}

  /* Metric grid */
  .metric-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 10px;
    margin-bottom: 16px;
  }}
  .metric-cell {{
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 14px 16px;
  }}
  .metric-label {{
    font-family: var(--mono);
    font-size: 0.6rem;
    color: var(--muted);
    letter-spacing: 0.1em;
    margin-bottom: 6px;
  }}
  .metric-value {{
    font-family: var(--mono);
    font-size: 1.15rem;
    color: var(--text);
  }}

  /* Streamlit overrides */
  .stTabs [data-baseweb="tab-list"] {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    gap: 0;
  }}
  .stTabs [data-baseweb="tab"] {{
    font-family: var(--head) !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.15em !important;
    font-weight: 600 !important;
    color: var(--muted) !important;
    padding: 10px 22px !important;
    background: transparent !important;
    border: none !important;
    text-transform: uppercase;
  }}
  .stTabs [aria-selected="true"] {{
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
  }}
  div[data-testid="stMarkdownContainer"] p {{
    font-family: var(--body);
    color: var(--text);
  }}
  .stSelectbox label, .stSlider label, .stDateInput label,
  .stMultiSelect label, .stRadio label {{
    font-family: var(--mono) !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.1em !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
  }}
  .stSelectbox [data-baseweb="select"] {{
    background: var(--bg) !important;
    border-color: var(--border) !important;
  }}
  button[kind="primary"], .stButton button {{
    background: transparent !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-family: var(--mono) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    border-radius: 0 !important;
  }}
  .stAlert {{ border-radius: 0 !important; }}

  /* Hide Streamlit chrome */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding-top: 1.5rem !important; }}
</style>
""", unsafe_allow_html=True)


# ── Helpers ─────────────────────────────────────────────────────────────────
def make_chart(fig):
    fig.update_layout(
        plot_bgcolor=COLORS['bg'],
        paper_bgcolor=COLORS['surface'],
        font=dict(family=FONT['mono'], color=COLORS['text'], size=11),
        margin=dict(l=12, r=12, t=36, b=12),
        legend=dict(
            bgcolor=COLORS['surface'],
            bordercolor=COLORS['border'],
            borderwidth=1,
            font=dict(family=FONT['mono'], size=10)
        ),
        xaxis=dict(
            gridcolor=COLORS['grid'],
            linecolor=COLORS['border'],
            tickfont=dict(family=FONT['mono'], size=10),
        ),
        yaxis=dict(
            gridcolor=COLORS['grid'],
            linecolor=COLORS['border'],
            tickfont=dict(family=FONT['mono'], size=10),
        ),
    )
    return fig


def pct_change_label(val, prev):
    if prev and prev != 0:
        pct = (val - prev) / abs(prev) * 100
        arrow = "▲" if pct >= 0 else "▼"
        cls = "up" if pct >= 0 else "down"
        return f'<span class="{cls}">{arrow} {abs(pct):.2f}%</span>', cls
    return '<span class="muted">— n/a</span>', "neutral"


def ticker_card(name, price, unit, prev_price, fmt="{:.2f}"):
    price_str = fmt.format(price) if price else "—"
    chg_html, cls = pct_change_label(price, prev_price)
    return f"""
    <div class="ticker-card {cls}">
      <div class="ticker-name">{name}</div>
      <div class="ticker-price">{price_str}<span style="font-size:0.6rem;color:var(--muted);margin-left:4px">{unit}</span></div>
      <div class="ticker-change">{chg_html}</div>
    </div>"""


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-label">Configuration</div>', unsafe_allow_html=True)

    lookback = st.selectbox(
        "Lookback Window",
        ["3M", "6M", "1Y", "2Y", "5Y"],
        index=2
    )
    lookback_days = {"3M": 90, "6M": 180, "1Y": 365, "2Y": 730, "5Y": 1825}[lookback]
    start_date = (datetime.today() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end_date = datetime.today().strftime("%Y-%m-%d")

    st.markdown('<div class="section-label" style="margin-top:20px">API Keys</div>', unsafe_allow_html=True)
    eia_key = st.text_input("EIA API Key", type="password", placeholder="paste key here")
    fred_key = st.text_input("FRED API Key", type="password", placeholder="paste key here")

    st.markdown('<div class="section-label" style="margin-top:20px">Display</div>', unsafe_allow_html=True)
    show_ma = st.checkbox("Show Moving Averages", value=True)
    ma_window = st.slider("MA Window (days)", 10, 90, 30) if show_ma else 30
    normalize = st.checkbox("Normalize to 100 (multi-asset)", value=False)

    st.markdown(f"""
    <div style="margin-top:32px;font-family:var(--mono);font-size:0.6rem;color:var(--muted);line-height:1.8">
      PROVIDERS<br>
      <span style="color:var(--accent)">●</span> Yahoo Finance (free)<br>
      <span style="color:{'var(--up)' if eia_key else 'var(--border)'}">{'●' if eia_key else '○'}</span> EIA {'✓' if eia_key else '(no key)'}<br>
      <span style="color:{'var(--up)' if fred_key else 'var(--border)'}">{'●' if fred_key else '○'}</span> FRED {'✓' if fred_key else '(no key)'}
    </div>
    """, unsafe_allow_html=True)


# ── Header ───────────────────────────────────────────────────────────────────
now_str = datetime.utcnow().strftime("%Y-%m-%d  %H:%M UTC")
st.markdown(f"""
<div class="desk-header">
  <div>
    <div class="desk-title">COMMODITY DESK</div>
    <div class="desk-subtitle">GLOBAL MARKETS INTELLIGENCE</div>
  </div>
  <div class="desk-timestamp">{now_str}</div>
</div>
""", unsafe_allow_html=True)


# ── Load Data ────────────────────────────────────────────────────────────────
with st.spinner("Fetching market data..."):
    crude_df    = get_crude_prices(start_date, end_date)
    natgas_df   = get_natgas_prices(start_date, end_date)
    metals_df   = get_metals_prices(start_date, end_date)
    ag_df       = get_agriculture_prices(start_date, end_date)
    macro_df    = get_fred_macro(start_date, end_date, fred_key or None)
    storage_df  = get_eia_storage(start_date, end_date, eia_key or None)
    prod_df     = get_eia_production(start_date, end_date, eia_key or None)
    cftc_df     = get_cftc_positioning(start_date, end_date)


# ── Ticker Strip ─────────────────────────────────────────────────────────────
def last_two(df, col):
    s = df[col].dropna()
    if len(s) >= 2:
        return float(s.iloc[-1]), float(s.iloc[-2])
    elif len(s) == 1:
        return float(s.iloc[-1]), None
    return None, None

tickers_html = '<div class="ticker-row">'

if crude_df is not None and "WTI" in crude_df.columns:
    v, p = last_two(crude_df, "WTI")
    if v: tickers_html += ticker_card("WTI CRUDE", v, "$/bbl", p)

if crude_df is not None and "Brent" in crude_df.columns:
    v, p = last_two(crude_df, "Brent")
    if v: tickers_html += ticker_card("BRENT", v, "$/bbl", p)

if natgas_df is not None and "HenryHub" in natgas_df.columns:
    v, p = last_two(natgas_df, "HenryHub")
    if v: tickers_html += ticker_card("HENRY HUB", v, "$/MMBtu", p)

if metals_df is not None and "Gold" in metals_df.columns:
    v, p = last_two(metals_df, "Gold")
    if v: tickers_html += ticker_card("GOLD", v, "$/oz", p)

if metals_df is not None and "Copper" in metals_df.columns:
    v, p = last_two(metals_df, "Copper")
    if v: tickers_html += ticker_card("COPPER", v, "$/lb", p)

if ag_df is not None and "Corn" in ag_df.columns:
    v, p = last_two(ag_df, "Corn")
    if v: tickers_html += ticker_card("CORN", v, "¢/bu", p)

tickers_html += '</div>'
st.markdown(tickers_html, unsafe_allow_html=True)


# ── Tabs ─────────────────────────────────────────────────────────────────────
tabs = st.tabs(["ENERGY", "METALS", "AGRICULTURE", "MACRO CONTEXT", "POSITIONING"])


# ═══════════════════════════════════════════════════════════════
# TAB 1 — ENERGY
# ═══════════════════════════════════════════════════════════════
with tabs[0]:
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="section-label">Crude Oil Benchmarks</div>', unsafe_allow_html=True)
        if crude_df is not None:
            fig = go.Figure()
            colors_map = {"WTI": COLORS['accent'], "Brent": COLORS['accent2']}
            for col in ["WTI", "Brent"]:
                if col in crude_df.columns:
                    s = crude_df[col].dropna()
                    y = (s / s.iloc[0] * 100) if normalize else s
                    fig.add_trace(go.Scatter(
                        x=crude_df.index, y=y, name=col,
                        line=dict(color=colors_map[col], width=1.5),
                        hovertemplate=f"<b>{col}</b><br>%{{x|%b %d, %Y}}<br>${{y:.2f}}<extra></extra>"
                    ))
                    if show_ma:
                        ma = s.rolling(ma_window).mean()
                        if normalize: ma = ma / s.iloc[0] * 100
                        fig.add_trace(go.Scatter(
                            x=crude_df.index, y=ma, name=f"{col} {ma_window}d MA",
                            line=dict(color=colors_map[col], width=1, dash='dot'),
                            opacity=0.5
                        ))
            fig.update_layout(title=dict(text="WTI vs BRENT  ($/bbl)", font=dict(family=FONT['head'], size=13, color=COLORS['muted'])))
            st.plotly_chart(make_chart(fig), use_container_width=True)
        else:
            st.info("Crude data unavailable.")

    with col2:
        st.markdown('<div class="section-label">Natural Gas</div>', unsafe_allow_html=True)
        if natgas_df is not None and "HenryHub" in natgas_df.columns:
            s = natgas_df["HenryHub"].dropna()
            y = (s / s.iloc[0] * 100) if normalize else s
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=natgas_df.index, y=y, name="Henry Hub",
                line=dict(color=COLORS['accent3'], width=1.5),
                fill='tozeroy', fillcolor=hex_to_rgba(COLORS['accent3'], 0.08)
            ))
            if show_ma:
                ma = s.rolling(ma_window).mean()
                if normalize: ma = ma / s.iloc[0] * 100
                fig2.add_trace(go.Scatter(
                    x=natgas_df.index, y=ma, name=f"{ma_window}d MA",
                    line=dict(color=COLORS['accent3'], width=1, dash='dot'), opacity=0.5
                ))
            fig2.update_layout(title=dict(text="HENRY HUB  ($/MMBtu)", font=dict(family=FONT['head'], size=13, color=COLORS['muted'])))
            st.plotly_chart(make_chart(fig2), use_container_width=True)

    # EIA Deep-Dive
    st.markdown('<div class="section-label">EIA Energy Detail</div>', unsafe_allow_html=True)

    if eia_key:
        ecol1, ecol2 = st.columns(2)
        with ecol1:
            if storage_df is not None:
                fig3 = go.Figure()
                fig3.add_trace(go.Bar(
                    x=storage_df.index, y=storage_df.iloc[:, 0],
                    marker_color=COLORS['accent'],
                    name="Weekly Storage"
                ))
                fig3.update_layout(title=dict(text="US NAT GAS STORAGE  (Bcf)", font=dict(family=FONT['head'], size=13, color=COLORS['muted'])))
                st.plotly_chart(make_chart(fig3), use_container_width=True)
            else:
                st.info("Storage data unavailable — check EIA key.")

        with ecol2:
            if prod_df is not None:
                fig4 = go.Figure()
                for i, col in enumerate(prod_df.columns[:3]):
                    fig4.add_trace(go.Scatter(
                        x=prod_df.index, y=prod_df[col], name=col,
                        line=dict(color=[COLORS['accent'], COLORS['accent2'], COLORS['accent3']][i], width=1.5)
                    ))
                fig4.update_layout(title=dict(text="US CRUDE PRODUCTION  (Mb/d)", font=dict(family=FONT['head'], size=13, color=COLORS['muted'])))
                st.plotly_chart(make_chart(fig4), use_container_width=True)
            else:
                st.info("Production data unavailable — check EIA key.")
    else:
        st.markdown("""
        <div style="background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);padding:16px 20px;font-family:var(--mono);font-size:0.72rem;color:var(--muted);line-height:1.9">
          EIA KEY NOT CONFIGURED<br>
          <span style="color:var(--text)">Add your EIA API key in the sidebar to unlock:</span><br>
          · Weekly natural gas storage (EIA-914)<br>
          · US crude production by region (mb/d)<br>
          · Refinery utilization rates<br>
          · Import/export flows<br><br>
          Get a free key at <span style="color:var(--accent)">eia.gov/opendata</span>
        </div>
        """, unsafe_allow_html=True)

    # Crude spread
    if crude_df is not None and "WTI" in crude_df.columns and "Brent" in crude_df.columns:
        st.markdown('<div class="section-label" style="margin-top:16px">Brent-WTI Spread</div>', unsafe_allow_html=True)
        spread = (crude_df["Brent"] - crude_df["WTI"]).dropna()
        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(
            x=spread.index, y=spread,
            line=dict(color=COLORS['accent2'], width=1.5),
            fill='tozeroy', fillcolor=hex_to_rgba(COLORS['accent2'], 0.13),
            name="Brent-WTI"
        ))
        fig5.add_hline(y=0, line_dash="dot", line_color=COLORS['muted'], opacity=0.4)
        fig5.update_layout(title=dict(text="BRENT PREMIUM TO WTI  ($/bbl)", font=dict(family=FONT['head'], size=13, color=COLORS['muted'])))
        st.plotly_chart(make_chart(fig5), use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 2 — METALS
# ═══════════════════════════════════════════════════════════════
with tabs[1]:
    if metals_df is not None:
        col1, col2 = st.columns(2)
        metal_colors = {"Gold": COLORS['gold'], "Silver": COLORS['silver'], "Copper": COLORS['copper']}

        with col1:
            st.markdown('<div class="section-label">Gold & Silver</div>', unsafe_allow_html=True)
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            for metal, secondary in [("Gold", False), ("Silver", True)]:
                if metal in metals_df.columns:
                    s = metals_df[metal].dropna()
                    y = (s / s.iloc[0] * 100) if normalize else s
                    fig.add_trace(go.Scatter(
                        x=metals_df.index, y=y, name=metal,
                        line=dict(color=metal_colors[metal], width=1.5)
                    ), secondary_y=secondary)
                    if show_ma:
                        ma = s.rolling(ma_window).mean()
                        if normalize: ma = ma / s.iloc[0] * 100
                        fig.add_trace(go.Scatter(
                            x=metals_df.index, y=ma, name=f"{metal} MA",
                            line=dict(color=metal_colors[metal], width=1, dash='dot'), opacity=0.45
                        ), secondary_y=secondary)
            fig.update_layout(title=dict(text="GOLD ($/oz)  |  SILVER ($/oz)", font=dict(family=FONT['head'], size=13, color=COLORS['muted'])))
            fig.update_yaxes(gridcolor=COLORS['grid'], linecolor=COLORS['border'], tickfont=dict(family=FONT['mono'], size=10))
            st.plotly_chart(make_chart(fig), use_container_width=True)

        with col2:
            st.markdown('<div class="section-label">Copper (Dr. Copper)</div>', unsafe_allow_html=True)
            if "Copper" in metals_df.columns:
                s = metals_df["Copper"].dropna()
                y = (s / s.iloc[0] * 100) if normalize else s
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=metals_df.index, y=y, name="Copper",
                    line=dict(color=COLORS['copper'], width=1.5),
                    fill='tozeroy', fillcolor=hex_to_rgba(COLORS['copper'], 0.08)
                ))
                if show_ma:
                    ma = s.rolling(ma_window).mean()
                    if normalize: ma = ma / s.iloc[0] * 100
                    fig2.add_trace(go.Scatter(
                        x=metals_df.index, y=ma, name=f"{ma_window}d MA",
                        line=dict(color=COLORS['copper'], width=1, dash='dot'), opacity=0.5
                    ))
                fig2.update_layout(title=dict(text="COPPER  ($/lb)", font=dict(family=FONT['head'], size=13, color=COLORS['muted'])))
                st.plotly_chart(make_chart(fig2), use_container_width=True)

        # Gold/Copper ratio
        if "Gold" in metals_df.columns and "Copper" in metals_df.columns:
            st.markdown('<div class="section-label">Gold / Copper Ratio (Risk Sentiment)</div>', unsafe_allow_html=True)
            ratio = (metals_df["Gold"] / (metals_df["Copper"] * 100)).dropna()
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=ratio.index, y=ratio,
                line=dict(color=COLORS['gold'], width=1.5),
                name="Gold/Copper"
            ))
            fig3.add_hline(y=ratio.mean(), line_dash="dot", line_color=COLORS['muted'],
                           annotation_text="Mean", annotation_font=dict(family=FONT['mono'], size=10, color=COLORS['muted']))
            fig3.update_layout(title=dict(text="GOLD/COPPER RATIO  — elevated = risk-off", font=dict(family=FONT['head'], size=13, color=COLORS['muted'])))
            st.plotly_chart(make_chart(fig3), use_container_width=True)
    else:
        st.info("Metals data unavailable.")


# ═══════════════════════════════════════════════════════════════
# TAB 3 — AGRICULTURE
# ═══════════════════════════════════════════════════════════════
with tabs[2]:
    if ag_df is not None:
        st.markdown('<div class="section-label">Grain Benchmarks</div>', unsafe_allow_html=True)
        ag_colors = {"Corn": "#F5C518", "Soybeans": "#6DBE45", "Wheat": "#E8956D"}
        col1, col2 = st.columns(2)

        with col1:
            fig = go.Figure()
            for crop, color in ag_colors.items():
                if crop in ag_df.columns:
                    s = ag_df[crop].dropna()
                    y = (s / s.iloc[0] * 100) if normalize else s
                    fig.add_trace(go.Scatter(
                        x=ag_df.index, y=y, name=crop,
                        line=dict(color=color, width=1.5)
                    ))
            fig.update_layout(title=dict(text="CORN / SOYBEANS / WHEAT  (¢/bu)", font=dict(family=FONT['head'], size=13, color=COLORS['muted'])))
            st.plotly_chart(make_chart(fig), use_container_width=True)

        with col2:
            # Corn/Soy ratio as a crush proxy
            if "Corn" in ag_df.columns and "Soybeans" in ag_df.columns:
                ratio = (ag_df["Soybeans"] / ag_df["Corn"]).dropna()
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=ratio.index, y=ratio,
                    line=dict(color="#6DBE45", width=1.5),
                    fill='tozeroy', fillcolor=hex_to_rgba("#6DBE45", 0.08),
                    name="Soy/Corn"
                ))
                fig2.add_hline(y=ratio.mean(), line_dash="dot", line_color=COLORS['muted'])
                fig2.update_layout(title=dict(text="SOYBEAN / CORN RATIO", font=dict(family=FONT['head'], size=13, color=COLORS['muted'])))
                st.plotly_chart(make_chart(fig2), use_container_width=True)

        if "Wheat" in ag_df.columns:
            st.markdown('<div class="section-label">Wheat Detail</div>', unsafe_allow_html=True)
            s = ag_df["Wheat"].dropna()
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=s.index, y=s, name="Wheat",
                line=dict(color="#E8956D", width=1.5),
                fill='tozeroy', fillcolor=hex_to_rgba("#E8956D", 0.08)
            ))
            fig3.update_layout(title=dict(text="WHEAT  (¢/bu)", font=dict(family=FONT['head'], size=13, color=COLORS['muted'])))
            st.plotly_chart(make_chart(fig3), use_container_width=True)
    else:
        st.info("Agriculture data unavailable.")


# ═══════════════════════════════════════════════════════════════
# TAB 4 — MACRO CONTEXT
# ═══════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="section-label">Dollar & Rate Context</div>', unsafe_allow_html=True)

    if macro_df is not None and not macro_df.empty:
        col1, col2 = st.columns(2)
        macro_colors = {
            "DXY": COLORS['accent'],
            "10Y_Yield": COLORS['accent2'],
            "Fed_Funds": COLORS['accent3'],
            "TIPS_10Y": COLORS['gold'],
        }
        macro_labels = {
            "DXY": "US Dollar Index (DXY)",
            "10Y_Yield": "10Y Treasury Yield (%)",
            "Fed_Funds": "Fed Funds Rate (%)",
            "TIPS_10Y": "10Y Real Yield / TIPS (%)",
        }
        available = [c for c in macro_colors if c in macro_df.columns]
        half = len(available) // 2 + len(available) % 2
        left_cols = available[:half]
        right_cols = available[half:]

        with col1:
            for key in left_cols:
                s = macro_df[key].dropna()
                if s.empty: continue
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=s.index, y=s, name=macro_labels[key],
                    line=dict(color=macro_colors[key], width=1.5),
                    fill='tozeroy', fillcolor=hex_to_rgba(macro_colors[key], 0.08)
                ))
                fig.update_layout(title=dict(text=macro_labels[key].upper(), font=dict(family=FONT['head'], size=13, color=COLORS['muted'])), height=280)
                st.plotly_chart(make_chart(fig), use_container_width=True)

        with col2:
            for key in right_cols:
                s = macro_df[key].dropna()
                if s.empty: continue
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=s.index, y=s, name=macro_labels[key],
                    line=dict(color=macro_colors[key], width=1.5),
                    fill='tozeroy', fillcolor=hex_to_rgba(macro_colors[key], 0.08)
                ))
                fig.update_layout(title=dict(text=macro_labels[key].upper(), font=dict(family=FONT['head'], size=13, color=COLORS['muted'])), height=280)
                st.plotly_chart(make_chart(fig), use_container_width=True)
    else:
        st.markdown("""
        <div style="background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent2);padding:16px 20px;font-family:var(--mono);font-size:0.72rem;color:var(--muted);line-height:1.9">
          FRED KEY NOT CONFIGURED — using fallback data where available<br>
          <span style="color:var(--text)">Add your FRED API key to unlock:</span><br>
          · US Dollar Index (DXY)<br>
          · 10Y Treasury yield &amp; real yield (TIPS)<br>
          · Fed Funds effective rate<br>
          · CPI / PCE inflation series<br><br>
          Get a free key at <span style="color:var(--accent2)">fred.stlouisfed.org/docs/api</span>
        </div>
        """, unsafe_allow_html=True)

    # Correlation heatmap across all commodity series
    st.markdown('<div class="section-label" style="margin-top:16px">Cross-Asset Correlation</div>', unsafe_allow_html=True)
    frames = {}
    for label, df_, cols in [
        ("WTI", crude_df, ["WTI"]),
        ("Brent", crude_df, ["Brent"]),
        ("NatGas", natgas_df, ["HenryHub"]),
        ("Gold", metals_df, ["Gold"]),
        ("Silver", metals_df, ["Silver"]),
        ("Copper", metals_df, ["Copper"]),
        ("Corn", ag_df, ["Corn"]),
        ("Wheat", ag_df, ["Wheat"]),
        ("Soybeans", ag_df, ["Soybeans"]),
    ]:
        if df_ is not None:
            for c in cols:
                if c in df_.columns:
                    frames[label] = df_[c]

    if len(frames) >= 3:
        combined = pd.DataFrame(frames).dropna()
        corr = combined.pct_change().corr()
        fig_corr = go.Figure(go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.index,
            colorscale=[[0, COLORS['down']], [0.5, COLORS['bg']], [1, COLORS['up']]],
            zmin=-1, zmax=1,
            text=corr.round(2).values,
            texttemplate="%{text}",
            textfont=dict(family=FONT['mono'], size=10)
        ))
        fig_corr.update_layout(
            height=380,
            title=dict(text="RETURN CORRELATIONS (DAILY %Δ)", font=dict(family=FONT['head'], size=13, color=COLORS['muted']))
        )
        st.plotly_chart(make_chart(fig_corr), use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 5 — POSITIONING
# ═══════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown('<div class="section-label">CFTC Commitments of Traders</div>', unsafe_allow_html=True)

    if cftc_df is not None and not cftc_df.empty:
        commodity_options = cftc_df["commodity"].unique().tolist() if "commodity" in cftc_df.columns else []
        if commodity_options:
            selected = st.selectbox("Select Commodity", commodity_options)
            sub = cftc_df[cftc_df["commodity"] == selected]
            if not sub.empty and "net_position" in sub.columns:
                fig = go.Figure()
                pos = sub["net_position"]
                colors = [COLORS['up'] if v >= 0 else COLORS['down'] for v in pos]
                fig.add_trace(go.Bar(x=sub.index, y=pos, marker_color=colors, name="Net Speculative Position"))
                fig.add_hline(y=0, line_dash="dot", line_color=COLORS['muted'], opacity=0.5)
                fig.update_layout(title=dict(text=f"NET SPECULATIVE POSITIONING — {selected.upper()}", font=dict(family=FONT['head'], size=13, color=COLORS['muted'])))
                st.plotly_chart(make_chart(fig), use_container_width=True)
    else:
        st.markdown("""
        <div style="background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--muted);padding:16px 20px;font-family:var(--mono);font-size:0.72rem;color:var(--muted);line-height:1.9">
          CFTC positioning data loads via OpenBB's regulators router.<br>
          This requires the openbb-finra or openbb-cftc extension.<br>
          Run: <span style="color:var(--accent)">pip install openbb[all]</span> to enable.
        </div>
        """, unsafe_allow_html=True)
