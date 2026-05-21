import streamlit as st
import yfinance as yf
import pandas as pd
import string
import time

from utils.styles import load_css
from utils.nse_data import get_full_nse_data

# =========================================================
# LOAD CONFIG & STYLES
# =========================================================
load_css()

# Track independent tables inside the Streamlit session state
if 'c1_results' not in st.session_state:
    st.session_state.c1_results = []
if 'c2_results' not in st.session_state:
    st.session_state.c2_results = []
if 'c3_results' not in st.session_state:
    st.session_state.c3_results = []

st.title("🦅 Three-Stage Institutional Reversal Dashboard")
st.caption("Table 1: Base Breakouts | Table 2: Downtrend Floor Breakouts | Table 3: Pre-Breakout Coils Ready to Pop")

# =========================================================
# NIFTY 50 & DATA LISTS
# =========================================================
NIFTY_50 = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO",
    "BAJFINANCE", "BAJAJFINSV", "BPCL", "BHARTIARTL", "BRITANNIA", "CIPLA",
    "COALINDIA", "DIVISLAB", "DRREDDY", "EICHERMOT", "GRASIM", "HCLTECH",
    "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK",
    "ITC", "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK", "LTIM",
    "LT", "M&M", "MARUTI", "NTPC", "NESTLEIND", "ONGC",
    "POWERGRID", "RELIANCE", "SBILIFE", "SBIN", "SUNPHARMA", "TCS",
    "TATACONSUM", "TATAMOTORS", "TATASTEEL", "TECHM", "TITAN", "ULTRACEMCO",
    "UPL", "WIPRO"
]

all_data = get_full_nse_data()

# =========================================================
# FILTERS INTERFACE
# =========================================================
col_sc1, col_sc2, col_sc3 = st.columns([1, 1, 1])

with col_sc1:
    scan_mode = st.selectbox("Scan Group", ["Nifty 50", "All Stocks", "Alphabetical/Numeric"])

with col_sc2:
    if scan_mode == "All Stocks":
        scan_list = all_data[all_data['SERIES'] == 'EQ']['SYMBOL'].tolist()
    elif scan_mode == "Alphabetical/Numeric":
        s_alpha = st.selectbox("Select Initial", ["0-9"] + list(string.ascii_uppercase), key="sc_alpha")
        if s_alpha == "0-9":
            scan_list = all_data[all_data['SYMBOL'].str[0].str.isdigit()]['SYMBOL'].tolist()
        else:
            scan_list = all_data[all_data['SYMBOL'].str.startswith(s_alpha)]['SYMBOL'].tolist()
    else:
        scan_list = NIFTY_50
    st.info(f"Targeting {len(scan_list)} Stocks")

with col_sc3:
    price_range = st.selectbox("Price Range", ["All", "0 - 100", "100 - 500", "500 - 1000", "1000 - 5000"])

# =========================================================
# CORE SCANNING ENGINE
# =========================================================
if st.button(f"🚀 Run Triple-Engine Lifecycle Scan"):
    c1_temp_results = []
    c2_temp_results = []
    c3_temp_results = []
    
    progress = st.progress(0)
    status_text = st.empty()

    for i, sym in enumerate(scan_list):
        try:
            status_text.text(f"Processing: {sym} ({i+1}/{len(scan_list)})")
            time.sleep(0.1)  # Safe rate limit delay

            # Fetch 50 days of daily data
            s_df = yf.download(f"{sym}.NS", period="50d", interval="1d", progress=False, auto_adjust=True)
            
            if len(s_df) < 35:
                continue

            if isinstance(s_df.columns, pd.MultiIndex):
                s_df.columns = s_df.columns.get_level_values(0)

            s_df = s_df.reset_index().dropna()
            s_df.columns = [c.capitalize() for c in s_df.columns]
            s_df['vol_ma'] = s_df['Volume'].rolling(20).mean()

            avg_vol = s_df['vol_ma'].iloc[-1]
            if pd.isna(avg_vol) or avg_vol == 0:
                avg_vol = 1.0

            # Price Filter Check upfront to minimize dictionary processing overhead
            curr_close_check = float(s_df['Close'].iloc[-1])
            price_passed = True
            if price_range != "All":
                min_p, max_p = map(int, price_range.split("-"))
                if not (min_p <= curr_close_check <= max_p):
                    price_passed = False
            
            if not price_passed:
                continue

            # -----------------------------------------------------
            # ENGINE 1 & 2 STRUCTURAL PREPARATION
            # -----------------------------------------------------
            block_8d = s_df.tail(8).copy()
            c1_matched = False
            absolute_low = 0.0
            max_structural_high = 0.0
            
            if len(block_8d) == 8:
                breakout_candle = block_8d.iloc[-1]
                pattern_window = block_8d.iloc[:-1]
                
                absolute_low = float(pattern_window['Low'].min())
                idx_absolute_low = pattern_window['Low'].idxmin()
                max_structural_high = float(pattern_window['High'].max())

                consolidation_after_sweep = pattern_window.loc[idx_absolute_low:]
                floor_buffer = absolute_low * 1.025
                is_valid_base = True
                
                for _, row in consolidation_after_sweep.iterrows():
                    if not (absolute_low <= float(row['Low']) <= floor_buffer):
                        is_valid_base = False
                        break

                current_close = float(breakout_candle['Close'])
                current_high = float(breakout_candle['High'])
                
                is_breakout_c1 = current_close >= max_structural_high or (current_high > max_structural_high and current_close > float(breakout_candle['Open']))

                # --- TABLE 1: CONDITION 1 MATCHED ---
                if is_valid_base and is_breakout_c1:
                    c1_matched = True
                    v_ratio = float(breakout_candle['Volume']) / avg_vol
                    c1_temp_results.append({
                        "Symbol": sym,
                        "LTP": round(current_close, 2),
                        "Breakout Barrier": round(max_structural_high, 2),
                        "Base Floor": round(absolute_low, 2),
                        "Vol Ratio": round(v_ratio, 2)
                    })

            # --- TABLE 2: CONDITION 2 MATCHED (TABLE 1 + DOWNTREND) ---
            trend_df = s_df.iloc[-25:-8]
            if len(trend_df) >= 12:
                is_downtrend = trend_df['High'].iloc[:4].mean() > trend_df['High'].iloc[-4:].mean()
                
                if is_downtrend and c1_matched:
                    v_ratio_c2 = float(block_8d.iloc[-1]['Volume']) / avg_vol
                    c2_temp_results.append({
                        "Symbol": sym,
                        "LTP": round(float(block_8d.iloc[-1]['Close']), 2),
                        "Breakout Barrier": round(max_structural_high, 2),
                        "Downtrend Base Floor": round(absolute_low, 2),
                        "Vol Ratio": round(v_ratio_c2, 2)
                    })

            # -----------------------------------------------------
            # ENGINE 3: CONDITION 3 PRE-BREAKOUT ANTICIPATION COIL
            # -----------------------------------------------------
            # Here, the last 7 days represent the base/sweep, and today is the coiled tracking candle.
            anticipation_window = s_df.tail(8).copy()
            if len(anticipation_window) == 8:
                current_candle = anticipation_window.iloc[-1]
                base_history = anticipation_window.iloc[:-1]
                
                c3_absolute_low = float(base_history['Low'].min())
                c3_idx_low = base_history['Low'].idxmin()
                c3_ceiling = float(base_history['High'].max())
                
                # Check for structural base validation
                c3_consolidation = base_history.loc[c3_idx_low:]
                c3_floor_buffer = c3_absolute_low * 1.025
                c3_base_valid = True
                
                for _, row in c3_consolidation.iterrows():
                    if not (c3_absolute_low <= float(row['Low']) <= c3_floor_buffer):
                        c3_base_valid = False
                        break
                        
                if c3_base_valid:
                    c3_close = float(current_candle['Close'])
                    c3_high = float(current_candle['High'])
                    
                    # ANTICIPATION MATH:
                    # 1. Price has NOT broken out yet (Close is still below or equal to the structural ceiling)
                    # 2. Price is knocking on the door: trading within 1.5% of the ceiling (fully compressed coiled spring)
                    is_not_broken_yet = c3_close <= c3_ceiling
                    is_knocking_on_door = c3_close >= (c3_ceiling * 0.985)
                    
                    # Verify trend backdrop context for quality tracking
                    c3_trend_check = s_df.iloc[-25:-8]
                    c3_is_downtrend = c3_trend_check['High'].iloc[:4].mean() > c3_trend_check['High'].iloc[-4:].mean()
                    
                    if is_not_broken_yet and is_knocking_on_door and c3_is_downtrend:
                        v_ratio_c3 = float(current_candle['Volume']) / avg_vol
                        c3_temp_results.append({
                            "Symbol": sym,
                            "LTP": round(c3_close, 2),
                            "Ceiling Target": round(c3_ceiling, 2),
                            "Risk Low Floor": round(c3_absolute_low, 2),
                            "Distance to Pop (%)": round(((c3_ceiling - c3_close) / c3_close) * 100, 2),
                            "Vol Ratio": round(v_ratio_c3, 2)
                        })

        except Exception:
            pass

        progress.progress((i + 1) / len(scan_list))

    # Save to Streamlit state parameters
    st.session_state.c1_results = c1_temp_results
    st.session_state.c2_results = c2_temp_results
    st.session_state.c3_results = c3_temp_results
    
    status_text.empty()
    st.success("Lifecycle parsing across all 3 conditions completed!")

# =========================================================
# DISPLAY SEPARATE RESULTS TABLES
# =========================================================

# TABLE 1: CONDITION 1
st.markdown("## 📊 Table 1: Standard 8-Day Base-Compression Breakouts (Condition 1)")
if st.session_state.c1_results:
    df1 = pd.DataFrame(st.session_state.c1_results).sort_values(by="Vol Ratio", ascending=False)
    st.dataframe(df1, use_container_width=True, hide_index=True)
else:
    st.info("No stocks currently matching the standard Condition 1 compression structure.")

st.markdown("---")

# TABLE 2: CONDITION 2
st.markdown("## 📉 Table 2: Deep Downtrend Floor Reversal Breakouts (Condition 2)")
if st.session_state.c2_results:
    df2 = pd.DataFrame(st.session_state.c2_results).sort_values(by="Vol Ratio", ascending=False)
    st.dataframe(df2, use_container_width=True, hide_index=True)
else:
    st.info("No confirmed post-downtrend breakout anomalies printed right now.")

st.markdown("---")

# TABLE 3: CONDITION 3 (THE ANTICIPATION WATCHLIST)
st.markdown("## 🔥 Table 3: Squeeze Watchlist (Coiling Under Resistance, Ready to Break!)")
if st.session_state.c3_results:
    # Sort by closest proximity to breaking out (Lowest Distance to Pop)
    df3 = pd.DataFrame(st.session_state.c3_results).sort_values(by="Distance to Pop (%)", ascending=True)
    st.dataframe(df3, use_container_width=True, hide_index=True)
else:
    st.info("No setups currently coiling inside the critical tight pre-breakout sweet spot.")