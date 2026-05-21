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
    all_data = pd.DataFrame({'SYMBOL': ['RELIANCE', 'TCS', 'INFY', 'TATAMOTORS', 'WIPRO'], 'SERIES': ['EQ']*5})

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
    # Fetch data history to calculate 20-day Volume MA and historical trendlines
    df = yf.download(ticker, period="60d", interval=timeframe, progress=False, auto_adjust=True)
    
    if df.empty:
        st.error(f"No data found for {ticker}. It might be temporarily rate-limited by Yahoo.")
        st.stop()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index().dropna()
    df.columns = [c.lower() for c in df.columns]

    if len(df) < 35:
        st.warning("Insufficient data available on this asset to run structural pattern checks.")
        st.stop()

    # Calculate indicators
    df['vol_ma'] = df['volume'].rolling(20).mean()
    ltp = round(float(df['close'].iloc[-1]), 2)
    avg_vol = float(df['vol_ma'].iloc[-1]) if pd.notna(df['vol_ma'].iloc[-1]) else 1.0
    vol_ratio = round(float(df['volume'].iloc[-1]) / avg_vol, 2)

    # =========================================================
    # EXACT COPIED ENGINE LOGIC FROM THE TRIPLE SCANNER
    # =========================================================
    
    # 1. Background Trend Check (-25 to -8 days lookback window)
    trend_df = df.iloc[-25:-8]
    is_downtrend = False
    if len(trend_df) >= 12:
        is_downtrend = trend_df['high'].iloc[:4].mean() > trend_df['high'].iloc[-4:].mean()

    # 2. Extract 8-day block windows for Condition 1 & 2
    block_8d = df.tail(8).copy()
    breakout_candle = block_8d.iloc[-1]
    pattern_window = block_8d.iloc[:-1]
    
    base_floor = round(float(pattern_window['low'].min()), 2)
    idx_absolute_low = pattern_window['low'].idxmin()
    breakout_barrier = round(float(pattern_window['high'].max()), 2)

    # 3. Structural Floor Compression Check
    consolidation_after_sweep = pattern_window.loc[idx_absolute_low:]
    floor_buffer = base_floor * 1.025
    is_valid_base = True
    
    for _, row in consolidation_after_sweep.iterrows():
        if not (base_floor <= float(row['low']) <= floor_buffer):
            is_valid_base = False
            break

    # 4. Trigger Breaks Check
    current_close = float(breakout_candle['close'])
    current_high = float(breakout_candle['high'])
    is_breakout_confirmed = current_close >= breakout_barrier or (current_high > breakout_barrier and current_close > float(breakout_candle['open']))

    # 5. Evaluate Condition 3 (Anticipation / Squeeze watchlists)
    is_not_broken_yet = ltp <= breakout_barrier
    is_knocking_on_door = ltp >= (breakout_barrier * 0.985)
    distance_to_pop = round(((breakout_barrier - ltp) / ltp) * 100, 2)

    # =========================================================
    # CLASSIFY STATUS MATCHES
    # =========================================================
    if is_valid_base and is_breakout_confirmed and is_downtrend:
        status = "🔥 C2: DOWNTREND BREAKOUT"
        target_display_pct = 0.0
    elif is_valid_base and is_breakout_confirmed:
        status = "✅ C1: BASE BREAKOUT"
        target_display_pct = 0.0
    elif is_valid_base and is_not_broken_yet and is_knocking_on_door and is_downtrend:
        status = "⏳ C3: WATCHLIST COIL"
        target_display_pct = distance_to_pop
    else:
        status = "❌ NO SETUP MATCHED"
        target_display_pct = round(((breakout_barrier - ltp) / ltp) * 100, 2)

    # =========================================================
    # METRICS DISPLAY
    # =========================================================
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("LTP", f"₹{ltp}")
    m2.metric("Breakout Barrier", f"₹{breakout_barrier}", delta=f"{target_display_pct}% to pop" if target_display_pct > 0 else "Triggered", delta_color="inverse" if target_display_pct > 0 else "normal")
    m3.metric("Pattern Base Floor", f"₹{base_floor}")
    m4.metric("Volume Ratio", f"{vol_ratio}x")
    m5.metric("System Phase Status", status.split()[-1])

    # =========================================================
    # LIGHTWEIGHT CHART CONFIGURATION
    # =========================================================
    df['time'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    chart_data = df[['time', 'open', 'high', 'low', 'close']].to_dict('records')

    # Inject horizontal lines directly onto your chart structure
    renderLightweightCharts([
        {
            "chart": {
                "layout": {"background": {"color": "#ffffff"}, "textColor": "#333"},
                "grid": {"vertLines": {"visible": False}, "horzLines": {"visible": False}},
                "height": 480,
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
    ], key=f"chart_{ticker}_{timeframe}")

    # =========================================================
    # ACTIONABLE INSIGHT LABELS
    # =========================================================
    st.markdown("### 📋 Market Structure Context Insights")
    st.write(f"* **Macro Downtrend Context Present:** {'Yes' if is_downtrend else 'No'}")
    st.write(f"* **8-Day Tight Floor Validated:** {'Yes' if is_valid_base else 'No'}")
    
    if "C3" in status:
        st.warning(f"🎯 **Watchlist Alert:** This asset is coiled tightly in a pre-breakout squeeze! It is sitting just **{distance_to_pop}%** below the critical barrier level (₹{breakout_barrier}).")
    elif "C2" in status:
        st.success(f"🚀 **Trend Reversal Confirmed:** Strong structural breakout confirmed at the bottom of a major macro downtrend floor.")
    elif "C1" in status:
        st.info(f"📊 **Base Breakout Confirmed:** Stock cleared compression resistance at ₹{breakout_barrier}.")

except Exception as e:
    st.error(f"Technical Error analyzing {selected_stock}: {str(e)}")