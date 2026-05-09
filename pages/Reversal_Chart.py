import streamlit as st
import yfinance as yf
import pandas as pd
import string
import time
from streamlit_lightweight_charts import renderLightweightCharts

# =========================================================
# PAGE CONFIG & STYLES
# =========================================================
st.set_page_config(page_title="NSE Reversal Chart", layout="wide")

# Fallback CSS if utils.styles is not available
try:
    from utils.styles import load_css
    load_css()
except ImportError:
    st.markdown("""
        <style>
        .main { background-color: #f5f7f9; }
        stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# DATA FETCHING (NSE MASTER)
# =========================================================
try:
    from utils.nse_data import get_full_nse_data
    all_data = get_full_nse_data()
except ImportError:
    # Minimal fallback list if utils is missing
    all_data = pd.DataFrame({'SYMBOL': ['RELIANCE', 'TCS', 'INFY', 'TATAMOTORS', 'LTIM'], 'SERIES': ['EQ']*5})

# =========================================================
# SIDEBAR / FILTER PANEL
# =========================================================
st.sidebar.header("🛠 Filter Stocks")

alpha_options = ["SHOW ALL", "0-9"] + list(string.ascii_uppercase)
alpha = st.sidebar.selectbox("Initial Letter", alpha_options)

working_df = all_data[all_data['SERIES'] == 'EQ']

if alpha == "0-9":
    working_df = working_df[working_df['SYMBOL'].str[0].str.isdigit()]
elif alpha != "SHOW ALL":
    working_df = working_df[working_df['SYMBOL'].str.startswith(alpha)]

search = st.sidebar.text_input("🔍 Quick Search", "").upper()
filtered_list = working_df['SYMBOL'].tolist()

if search:
    filtered_list = [s for s in filtered_list if search in s]

selected_stock = st.sidebar.selectbox("Pick Stock", filtered_list if filtered_list else ["TATAMOTORS"])
timeframe = st.sidebar.radio("Timeframe", ("1d", "1wk"))

# =========================================================
# MAIN CHART LOGIC
# =========================================================
st.title(f"📊 Reversal Analysis: {selected_stock}")

ticker = f"{selected_stock}.NS"

try:
    # 1. Download Data with auto_adjust
    df = yf.download(ticker, period="1y", interval=timeframe, progress=False, auto_adjust=True)
    
    if df.empty:
        st.error(f"No data found for {ticker}. It might be temporarily rate-limited by Yahoo.")
        st.stop()

    # 2. Multi-Index Header Fix (Critical for yfinance 2024+)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index().dropna()
    df.columns = [c.lower() for c in df.columns]

    # 3. DYNAMIC SUPPORT LOGIC (The 60-Day Lookback)
    # This keeps support relevant even if the stock is in a long-term uptrend
    lookback = 60
    df_recent = df.iloc[-lookback:] if len(df) > lookback else df
    
    # Find recent bottom index
    bottom_idx_recent = df_recent['low'].idxmin()
    abs_low = round(float(df.loc[bottom_idx_recent, 'low']), 2)

    # 4. LH TARGET LOGIC
    # Look for the high just before that recent bottom to find the 'breakout' trigger
    if bottom_idx_recent > 0:
        lh_target = round(float(df.loc[bottom_idx_recent - 1, 'high']), 2)
    else:
        lh_target = round(float(df.loc[bottom_idx_recent, 'high']), 2)

    # 5. TECHNICAL CALCULATIONS
    ltp = round(float(df['close'].iloc[-1]), 2)
    df['vol_ma'] = df['volume'].rolling(20).mean()
    curr_vol = float(df['volume'].iloc[-1])
    avg_vol = float(df['vol_ma'].iloc[-1]) if pd.notna(df['vol_ma'].iloc[-1]) else 1
    vol_ratio = curr_vol / avg_vol
    distance_pct = round(((lh_target - ltp) / ltp) * 100, 2)

    # 6. SIGNAL CLASSIFICATION
    status = "WAITING"
    if ltp > lh_target:
        status = "✅ ALREADY BROKEN OUT"
    elif 0 <= distance_pct <= 1 and vol_ratio > 1.2:
        status = "🔥 VERY CLOSE"
    elif 0 <= distance_pct <= 3:
        status = "⏳ READY"
    elif ltp > abs_low and distance_pct <= 8:
        status = "⚡ EARLY REVERSAL"

    # 7. METRICS DISPLAY
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("LTP", f"₹{ltp}")
    m2.metric("LH Target", f"₹{lh_target}", delta=f"{distance_pct}%", delta_color="inverse")
    m3.metric("Recent Support", f"₹{abs_low}")
    m4.metric("Vol Ratio", f"{vol_ratio:.1f}x")
    m5.metric("Status", status.split()[-1])

    # 8. LIGHTWEIGHT CHART DATA
    df['time'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    chart_data = df[['time', 'open', 'high', 'low', 'close']].to_dict('records')

    # 9. RENDER CHART
    renderLightweightCharts([
        {
            "chart": {
                "layout": {"background": {"color": "#ffffff"}, "textColor": "#333"},
                "grid": {"vertLines": {"visible": False}, "horzLines": {"visible": False}},
                "height": 450,
            },
            "series": [
                {
                    "type": "Candlestick",
                    "data": chart_data,
                    "options": {
                        "upColor": "#26a69a", "downColor": "#ef5350",
                        "borderVisible": False, "wickUpColor": "#26a69a", "wickDownColor": "#ef5350"
                    }
                }
            ]
        }
    ], key=f"chart_{ticker}")

    # 10. ACTIONABLE INSIGHTS
    if status == "🔥 VERY CLOSE":
        st.warning(f"**Alert:** Price is within 1% of the LH Target (₹{lh_target}). High volume ({vol_ratio:.1f}x) suggests a breakout attempt.")
    elif status == "✅ ALREADY ABOVE LH":
        st.success(f"**Trend Confirmed:** Stock is trading above the structural LH resistance of ₹{lh_target}.")

except Exception as e:
    st.error(f"Technical Error analyzing {selected_stock}: {str(e)}")
    st.info("Try refreshing the page or checking if the symbol name is correct on Yahoo Finance.")