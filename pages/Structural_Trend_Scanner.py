import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import string
import time

from utils.styles import load_css
from utils.nse_data import get_full_nse_data

# =========================================================
# INITIALIZATION & STYLES
# =========================================================
load_css()

if 't1_bounces' not in st.session_state:
    st.session_state.t1_bounces = []
if 't2_breakouts' not in st.session_state:
    st.session_state.t2_breakouts = []
if 't3_horiz_support' not in st.session_state:
    st.session_state.t3_horiz_support = []
if 't4_horiz_resistance' not in st.session_state:
    st.session_state.t4_horiz_resistance = []

st.title("📐 Institutional Structural Trend Scanner")
st.caption("Advanced 1D Multi-Setup Engine with Multi-Touch Filter & Predictive Analysis Matrix.")

# =========================================================
# WATCHLIST COMPILATION (COMPLETE 180+ F&O LIST)
# =========================================================
FNO_WATCHLIST = [
    "AARTIIND", "ABB", "ABBOTINDIA", "ACC", "ADANIENT", "ADANIPORTS", "ADANIPOWER",
    "ABCAPITAL", "ALKEM", "AMBUJACEM", "APOLLOHOSP", "APOLLOTYRE", "ASHOKLEY", 
    "ASIANPAINT", "ASTRAL", "ATUL", "AUBANK", "AUROPHARMA", "AXISBANK", 
    "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BALKRISIND", "BALRAMCHIN", 
    "BANDHANBNK", "BANKBARODA", "BATAINDIA", "BERGEPAINT", "BEL", "BHARATFORG", 
    "BHEL", "BPCL", "BHARTIARTL", "BIOCON", "BSOFT", "BOSCHLTD", "BRITANNIA", 
    "CANFINHOME", "CANBK", "CHAMBLFERT", "CHOLAFIN", "CIPLA", "CUB", "COALINDIA", 
    "COFORGE", "COLPAL", "CONCOR", "COROMANDEL", "CROMPTON", "CUMMINSIND", 
    "DABUR", "DALBHARAT", "DEEPAKNTR", "DELTACORP", "DIVISLAB", "DIXON", "DLF", 
    "LALPATHLAB", "DRREDDY", "EICHERMOT", "ESCORTS", "EXIDEIND", "FEDERALBNK", 
    "GAIL", "GLENMARK", "GODREJCP", "GODREJPROP", "GRANULES", "GRASIM", "GUJGASLTD", 
    "GNFC", "HAVELLS", "HCLTECH", "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", 
    "HINDALCO", "HAL", "HPCL", "HINDUNILVR", "HINDZINC", "HYUNDAI", "ICICIBANK", 
    "ICICIGI", "ICICIPRULI", "IEX", "IOC", "IRCTC", "IRFC", "IGL", "INDUSINDBK", 
    "NAUKRI", "INFY", "INDIGO", "IPCALAB", "ITC", "JINDALSTEL", "JKCEMENT", 
    "JSWSTEEL", "JUBLFOOD", "KALYANKNIL", "KOTAKBANK", "LTF", "LTIM", "LT", 
    "LICI", "LUPIN", "M&MFIN", "M&M", "MANAPPURAM", "MARUTI", "MFSL", "MAXHEALTH", 
    "METROPOLIS", "MPHASIS", "MCX", "MUTHOOTFIN", "NATIONALUM", "NAVINFLUOR", 
    "NESTLEIND", "NMDC", "NTPC", "NUVAMA", "OBEROIRLTY", "ONGC", "OIL", "PAYTM", 
    "OFSS", "PEL", "POLYCAB", "PFC", "POWERGRID", "PNB", "RADICO", "RELIANCE", 
    "RECL", "RVNL", "SAIL", "SBICARD", "SBILIFE", "SBIN", "SHREECEM", "SHRIRAMFIN", 
    "SIEMENS", "SRF", "SUPREMEIND", "SUNPHARMA", "SUNTV", "SYNGENE", "TATACOMM", 
    "TATACHEM", "TATAELXSI", "TATAMOTORS", "TATAPOWER", "TATASTEEL", "TCS", 
    "TECHM", "TITAN", "TORNTPHARM", "TORNTPOWER", "TRENT", "TRIDENT", "TVSMOTOR", 
    "UBL", "ULTRACEMCO", "UNIONBANK", "UPL", "VBL", "VEDL", "VOLTAS", "WIPRO", 
    "ZOMATO", "ZYDUSLIFE"
]

all_data = get_full_nse_data()

# =========================================================
# FILTERS & WATCHLIST INTERFACE
# =========================================================
col_ui1, col_ui2, col_ui3 = st.columns([1, 1, 1])

with col_ui1:
    scan_group = st.selectbox("Select Target Group", ["F&O Heavyweights", "All NSE Equities", "Alphabetical Cluster"])

with col_ui2:
    if scan_group == "All NSE Equities":
        scan_list = all_data[all_data['SERIES'] == 'EQ']['SYMBOL'].tolist()
    elif scan_group == "Alphabetical Cluster":
        alpha_select = st.selectbox("Initial Letter", list(string.ascii_uppercase), key="struct_alpha")
        scan_list = all_data[all_data['SYMBOL'].str.startswith(alpha_select)]['SYMBOL'].tolist()
    else:
        scan_list = FNO_WATCHLIST

with col_ui3:
    price_filter = st.selectbox("Asset Price Range", ["All Prices", "0 - 100", "100 - 500", "500 - 1000", "1000 - 5000"])

with st.expander(f"📋 Master Watchlist Explorer (Total loaded: {len(scan_list)} Stocks)", expanded=True):
    search_term = st.text_input("🔍 Filter list or find specific stock ticker:", "").upper()
    filtered_display_list = [stock for stock in scan_list if search_term in stock]
    st.write(f"Showing **{len(filtered_display_list)}** matched assets:")
    st.caption(" | ".join([f"`{s}`" for s in filtered_display_list]))

# =========================================================
# MATHEMATICAL STRUCTURAL DETECTOR ENGINE (1D ENGINE)
# =========================================================
if st.button("🚀 Run Multi-Setup Structural Scan"):
    t1_temp, t2_temp, t3_temp, t4_temp = [], [], [], []
    
    progress_bar = st.progress(0)
    status_msg = st.empty()

    for index, sym in enumerate(scan_list):
        try:
            status_msg.text(f"Analyzing 1D Layout: {sym} ({index+1}/{len(scan_list)})")
            time.sleep(0.005)

            df = yf.download(f"{sym}.NS", period="50d", interval="1d", progress=False, auto_adjust=True)
            if len(df) < 35:
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df.reset_index().dropna()
            df.columns = [c.capitalize() for c in df.columns]
            
            curr_close = float(df['Close'].iloc[-1])
            curr_high = float(df['High'].iloc[-1])
            curr_low = float(df['Low'].iloc[-1])
            curr_open = float(df['Open'].iloc[-1])
            
            if price_filter != "All Prices":
                p_min, p_max = map(int, price_filter.split("-"))
                if not (p_min <= curr_close <= p_max):
                    continue

            # Volume Baseline Tracking
            df['vol_ma'] = df['Volume'].rolling(20).mean()
            avg_vol = df['vol_ma'].iloc[-1] if df['vol_ma'].iloc[-1] > 0 else 1.0
            vol_ratio = float(df['Volume'].iloc[-1]) / avg_vol

            # Define historical lookback window (Trailing 30 bars)
            window = df.iloc[-30:-1].copy()
            x_indices = np.arange(len(window))
            
            # Formulate dynamic standard polyfit regression vectors
            slope_high, intercept_high = np.polyfit(x_indices, window['High'].values, 1)
            slope_low, intercept_low = np.polyfit(x_indices, window['Low'].values, 1)

            # -----------------------------------------------------
            # ANTI-NOISE FILTER: STRUCTURAL TOUCH COUNTER ENGINE
            # -----------------------------------------------------
            fitted_high_line_values = (slope_high * x_indices) + intercept_high
            fitted_low_line_values = (slope_low * x_indices) + intercept_low

            # Verify that the trendlines have actual historical structural hits (within 1% threshold)
            high_line_touches = np.sum(np.abs(window['High'].values - fitted_high_line_values) / fitted_high_line_values <= 0.01)
            low_line_touches = np.sum(np.abs(window['Low'].values - fitted_low_line_values) / fitted_low_line_values <= 0.01)

            is_valid_ceiling = high_line_touches >= 2
            is_valid_floor = low_line_touches >= 2

            # Evaluate values mapped to today's index position
            today_x = len(window)
            calculated_ceiling_line = (slope_high * today_x) + intercept_high
            calculated_floor_line = (slope_low * today_x) + intercept_low

            hist_highest_high = float(window['High'].max())
            hist_lowest_low = float(window['Low'].min())

            # -----------------------------------------------------
            # PREDICTIVE MATRIX PROBABILITY ENGINE
            # -----------------------------------------------------
            if vol_ratio > 1.5 and curr_close > ((curr_high + curr_open) / 2):
                breakout_prob = "🔥 HIGH (Volume Expansion)"
                reversal_prob = "⚠️ LOW"
            elif vol_ratio < 0.75:
                breakout_prob = "⚠️ LOW (Dry Volume)"
                reversal_prob = "🛡️ HIGH (Exhaustion Pivot)"
            else:
                breakout_prob = "⚖️ MODERATE"
                reversal_prob = "⚖️ MODERATE"

            # -----------------------------------------------------
            # SETUP 1: SLOPING SUPPORT BOUNCES
            # -----------------------------------------------------
            if is_valid_floor:
                distance_to_sloping_floor = ((curr_close - calculated_floor_line) / calculated_floor_line) * 100
                if -0.5 <= distance_to_sloping_floor <= 1.2 and curr_close > curr_open:
                    t1_temp.append({
                        "Symbol": sym,
                        "LTP": round(curr_close, 2),
                        "Sloping Floor": round(calculated_floor_line, 2),
                        "Proximity (%)": round(abs(distance_to_sloping_floor), 2),
                        "Reversal Bounce Prob": reversal_prob,
                        "Breakdown Risk": breakout_prob
                    })

            # -----------------------------------------------------
            # SETUP 2: TRIANGLE & SLOPING RESISTANCE TRIGGERS
            # -----------------------------------------------------
            if is_valid_ceiling:
                distance_to_sloping_ceil = ((calculated_ceiling_line - curr_close) / curr_close) * 100
                
                if curr_close > calculated_ceiling_line:
                    t2_temp.append({
                        "Symbol": sym,
                        "LTP": round(curr_close, 2),
                        "Status": "🚀 BREAKOUT",
                        "Trendline Ceiling": round(calculated_ceiling_line, 2),
                        "Gap/Premium (%)": round(((curr_close - calculated_ceiling_line) / calculated_ceiling_line) * 100, 2),
                        "Reversal Failure": "⚠️ LOW",
                        "Sustained Break Prob": "🔥 HIGH"
                    })
                elif 0 <= distance_to_sloping_ceil <= 1.2:
                    t2_temp.append({
                        "Symbol": sym,
                        "LTP": round(curr_close, 2),
                        "Status": "🌀 TESTING LINE",
                        "Trendline Ceiling": round(calculated_ceiling_line, 2),
                        "Distance (%)": round(distance_to_sloping_ceil, 2),
                        "Reversal Probability": reversal_prob,
                        "Breakout Probability": breakout_prob
                    })

            # -----------------------------------------------------
            # SETUP 3: FIXED HORIZONTAL SUPPORT FLOORS
            # -----------------------------------------------------
            distance_to_horiz_floor = ((curr_close - hist_lowest_low) / hist_lowest_low) * 100
            if 0 <= distance_to_horiz_floor <= 0.8 and curr_close > curr_open:
                t3_temp.append({
                    "Symbol": sym,
                    "LTP": round(curr_close, 2),
                    "Horizontal Floor": round(hist_lowest_low, 2),
                    "Margin (%)": round(distance_to_horiz_floor, 2),
                    "Reversal Bounce Prob": reversal_prob,
                    "Breakdown Prob": breakout_prob
                })

            # -----------------------------------------------------
            # SETUP 4: HORIZONTAL RESISTANCE CEILING SQUEEZES
            # -----------------------------------------------------
            distance_to_horiz_ceil = ((hist_highest_high - curr_close) / curr_close) * 100
            if 0 < distance_to_horiz_ceil <= 1.0:
                t4_temp.append({
                    "Symbol": sym,
                    "LTP": round(curr_close, 2),
                    "Horizontal Ceiling": round(hist_highest_high, 2),
                    "Distance to Pop (%)": round(distance_to_horiz_ceil, 2),
                    "Reversal Drop Prob": reversal_prob,
                    "Breakout Burst Prob": breakout_prob
                })

        except Exception:
            pass
        
        progress_bar.progress((index + 1) / len(scan_list))

    st.session_state.t1_bounces = t1_temp
    st.session_state.t2_breakouts = t2_temp
    st.session_state.t3_horiz_support = t3_temp
    st.session_state.t4_horiz_resistance = t4_temp

    status_msg.empty()
    st.success("Structural matrix analysis complete! Noise-only setups have been dynamically filtered out.")

# =========================================================
# RENDERING OUTPUT INTERFACE TABLES
# =========================================================
st.markdown("### 📈 Table 1: Sloping Channel/Triangle Support Bounces")
if st.session_state.t1_bounces:
    st.dataframe(pd.DataFrame(st.session_state.t1_bounces).sort_values(by="Proximity (%)", ascending=True), use_container_width=True, hide_index=True)
else:
    st.info("No stocks currently testing validated lower sloping support boundaries.")

st.markdown("---")

st.markdown("### 🚀 Table 2: Triangle & Sloping Trendline Triggers")
if st.session_state.t2_breakouts:
    st.dataframe(pd.DataFrame(st.session_state.t2_breakouts).sort_values(by="Status", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("No confirmed structural triggers logged for today's session.")

st.markdown("---")

st.markdown("### 🧱 Table 3: Horizontal Support Floors (Major Pivot Key Rests)")
if st.session_state.t3_horiz_support:
    st.dataframe(pd.DataFrame(st.session_state.t3_horiz_support).sort_values(by="Margin (%)", ascending=True), use_container_width=True, hide_index=True)
else:
    st.info("No stocks currently testing flat horizontal 30-day pivot demand zones.")

st.markdown("---")

st.markdown("### 🌀 Table 4: Horizontal Resistance Squeezes (Coiling Below Flat Ceilings)")
if st.session_state.t4_horiz_resistance:
    st.dataframe(pd.DataFrame(st.session_state.t4_horiz_resistance).sort_values(by="Distance to Pop (%)", ascending=True), use_container_width=True, hide_index=True)
else:
    st.info("No stocks currently compressing tightly beneath flat major historical ceilings.")