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
if 'c4_results' not in st.session_state:
    st.session_state.c4_results = []

st.title("🦅 Four-Stage Institutional Reversal & Squeeze Dashboard")
st.caption("Table 1: Base Breakouts | Table 2: Deep Downtrend (5-Day Floor) Reversals | Table 3: Pre-Breakout Coils | Table 4: Silent Humming Squeezes")

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
if st.button(f"🚀 Run Quad-Engine Lifecycle Scan"):
    c1_temp_results = []
    c2_temp_results = []
    c3_temp_results = []
    c4_temp_results = []
    
    progress = st.progress(0)
    status_text = st.empty()

    for i, sym in enumerate(scan_list):
        try:
            status_text.text(f"Processing: {sym} ({i+1}/{len(scan_list)})")
            time.sleep(0.02)

            # Pull 60 days of data to guarantee room for back-trend calculations
            s_df = yf.download(f"{sym}.NS", period="60d", interval="1d", progress=False, auto_adjust=True)
            
            if len(s_df) < 40:
                continue

            if isinstance(s_df.columns, pd.MultiIndex):
                s_df.columns = s_df.columns.get_level_values(0)

            s_df = s_df.reset_index().dropna()
            s_df.columns = [c.capitalize() for c in s_df.columns]
            s_df['vol_ma'] = s_df['Volume'].rolling(20).mean()

            avg_vol = s_df['vol_ma'].iloc[-1]
            if pd.isna(avg_vol) or avg_vol == 0:
                avg_vol = 1.0

            # -----------------------------------------------------
            # CRITICAL MASTER VOLUME FILTER (2 LAKH / 200,000 SHARES)
            # Applies to all subsequent conditions automatically
            # -----------------------------------------------------
            if avg_vol < 200000:
                continue

            # Price Range Filter Upfront Check
            curr_close_check = float(s_df['Close'].iloc[-1])
            price_passed = True
            if price_range != "All":
                min_p, max_p = map(int, price_range.split("-"))
                if not (min_p <= curr_close_check <= max_p):
                    price_passed = False
            
            if not price_passed:
                continue

            # -----------------------------------------------------
            # ENGINE 1: STANDARD 8-DAY BASE BREAKOUT (CONDITION 1)
            # -----------------------------------------------------
            block_8d = s_df.tail(8).copy()
            c1_matched = False
            
            if len(block_8d) == 8:
                breakout_candle_c1 = block_8d.iloc[-1]
                pattern_window_c1 = block_8d.iloc[:-1]
                
                c1_absolute_low = float(pattern_window_c1['Low'].min())
                idx_c1_low = pattern_window_c1['Low'].idxmin()
                c1_max_high = float(pattern_window_c1['High'].max())

                consolidation_after_sweep_c1 = pattern_window_c1.loc[idx_c1_low:]
                floor_buffer_c1 = c1_absolute_low * 1.025
                is_valid_base_c1 = True
                
                for _, row in consolidation_after_sweep_c1.iterrows():
                    if not (c1_absolute_low <= float(row['Low']) <= floor_buffer_c1):
                        is_valid_base_c1 = False
                        break

                c1_current_close = float(breakout_candle_c1['Close'])
                c1_current_high = float(breakout_candle_c1['High'])
                
                is_breakout_c1 = c1_current_close >= c1_max_high or (c1_current_high > c1_max_high and c1_current_close > float(breakout_candle_c1['Open']))

                if is_valid_base_c1 and is_breakout_c1:
                    c1_matched = True
                    v_ratio_c1 = float(breakout_candle_c1['Volume']) / avg_vol
                    c1_temp_results.append({
                        "Symbol": sym,
                        "LTP": round(c1_current_close, 2),
                        "Breakout Barrier": round(c1_max_high, 2),
                        "Base Floor": round(c1_absolute_low, 2),
                        "Vol Ratio": round(v_ratio_c1, 2)
                    })

            # -----------------------------------------------------
            # ENGINE 2: COMPLETE DOWNTREND -> 5-DAY SUPPORT FLOOR -> BREAKOUT
            # -----------------------------------------------------
            block_6d = s_df.tail(6).copy()
            if len(block_6d) == 6:
                breakout_candle_c2 = block_6d.iloc[-1]
                floor_window_c2 = block_6d.iloc[:-1]
                
                c2_absolute_low = float(floor_window_c2['Low'].min())
                c2_max_high = float(floor_window_c2['High'].max())
                
                floor_buffer_c2 = c2_absolute_low * 1.025
                is_valid_5d_floor = True
                for _, row in floor_window_c2.iterrows():
                    if not (c2_absolute_low <= float(row['Low']) <= floor_buffer_c2):
                        is_valid_5d_floor = False
                        break
                
                c2_current_close = float(breakout_candle_c2['Close'])
                c2_current_high = float(breakout_candle_c2['High'])
                is_breakout_c2 = c2_current_close >= c2_max_high or (c2_current_high > c2_max_high and c2_current_close > float(breakout_candle_c2['Open']))
                
                if is_valid_5d_floor and is_breakout_c2:
                    trend_df_c2 = s_df.iloc[-21:-6]
                    if len(trend_df_c2) == 15:
                        first_half_high = trend_df_c2['High'].iloc[:7].mean()
                        second_half_high = trend_df_c2['High'].iloc[-7:].mean()
                        
                        is_downtrend_c2 = first_half_high > (second_half_high * 1.03)
                        peak_at_start = trend_df_c2['High'].idxmax() < trend_df_c2.index[7]
                        
                        if is_downtrend_c2 and peak_at_start:
                            v_ratio_c2 = float(breakout_candle_c2['Volume']) / avg_vol
                            c2_temp_results.append({
                                "Symbol": sym,
                                "LTP": round(c2_current_close, 2),
                                "Breakout Barrier": round(c2_max_high, 2),
                                "5-Day Floor Support": round(c2_absolute_low, 2),
                                "Vol Ratio": round(v_ratio_c2, 2)
                            })

            # -----------------------------------------------------
            # ENGINE 3: CONDITION 3 PRE-BREAKOUT ANTICIPATION COIL
            # -----------------------------------------------------
            anticipation_window = s_df.tail(8).copy()
            if len(anticipation_window) == 8:
                current_candle_c3 = anticipation_window.iloc[-1]
                base_history_c3 = anticipation_window.iloc[:-1]
                
                c3_absolute_low = float(base_history_c3['Low'].min())
                c3_idx_low = base_history_c3['Low'].idxmin()
                c3_ceiling = float(base_history_c3['High'].max())
                
                c3_consolidation = base_history_c3.loc[c3_idx_low:]
                c3_floor_buffer = c3_absolute_low * 1.025
                c3_base_valid = True
                
                for _, row in c3_consolidation.iterrows():
                    if not (c3_absolute_low <= float(row['Low']) <= c3_floor_buffer):
                        c3_base_valid = False
                        break
                        
                if c3_base_valid:
                    c3_close = float(current_candle_c3['Close'])
                    
                    is_not_broken_yet = c3_close <= c3_ceiling
                    is_knocking_on_door = c3_close >= (c3_ceiling * 0.985)
                    
                    c3_trend_check = s_df.iloc[-25:-8]
                    c3_is_downtrend = c3_trend_check['High'].iloc[:4].mean() > c3_trend_check['High'].iloc[-4:].mean()
                    
                    if is_not_broken_yet and is_knocking_on_door and c3_is_downtrend:
                        v_ratio_c3 = float(current_candle_c3['Volume']) / avg_vol
                        c3_temp_results.append({
                            "Symbol": sym,
                            "LTP": round(c3_close, 2),
                            "Ceiling Target": round(c3_ceiling, 2),
                            "Risk Low Floor": round(c3_absolute_low, 2),
                            "Distance to Pop (%)": round(((c3_ceiling - c3_close) / c3_close) * 100, 2),
                            "Vol Ratio": round(v_ratio_c3, 2)
                        })

            # -----------------------------------------------------
            # ENGINE 4: CONDITION 4 THE HUMMING SQUEEZE CLUSTER (NO BREAKOUT)
            # -----------------------------------------------------
            hum_block = s_df.tail(4).copy()
            if len(hum_block) == 4:
                block_high = float(hum_block['High'].max())
                block_low = float(hum_block['Low'].min())
                
                total_variance_pct = ((block_high - block_low) / block_low) * 100
                is_humming_range = total_variance_pct <= 2.5
                
                distance_to_pop = round(((block_high - curr_close_check) / curr_close_check) * 100, 2)
                is_primed_to_snap = distance_to_pop <= 0.6
                
                if is_humming_range and is_primed_to_snap:
                    v_ratio_c4 = float(hum_block['Volume'].iloc[-1]) / avg_vol
                    c4_temp_results.append({
                        "Symbol": sym,
                        "LTP": round(curr_close_check, 2),
                        "Humming Ceiling": round(block_high, 2),
                        "Humming Floor": round(block_low, 2),
                        "Cluster Tightness (%)": round(total_variance_pct, 2),
                        "Distance to Pop (%)": distance_to_pop,
                        "Vol Ratio": round(v_ratio_c4, 2)
                    })

        except Exception:
            pass

        progress.progress((i + 1) / len(scan_list))

    st.session_state.c1_results = c1_temp_results
    st.session_state.c2_results = c2_temp_results
    st.session_state.c3_results = c3_temp_results
    st.session_state.c4_results = c4_temp_results
    
    status_text.empty()
    st.success("Quad-Engine lifecycle scanning parsing completed with Liquidity Filters!")

# =========================================================
# DISPLAY SEPARATE RESULTS TABLES
# =========================================================

st.markdown("## 📊 Table 1: Standard 8-Day Base-Compression Breakouts (Condition 1)")
if st.session_state.c1_results:
    df1 = pd.DataFrame(st.session_state.c1_results).sort_values(by="Vol Ratio", ascending=False)
    st.dataframe(df1, use_container_width=True, hide_index=True)
else:
    st.info("No stocks currently matching the standard Condition 1 compression structure.")

st.markdown("---")

st.markdown("## 📉 Table 2: Deep Downtrend Floor Reversal Breakouts (Condition 2)")
if st.session_state.c2_results:
    df2 = pd.DataFrame(st.session_state.c2_results).sort_values(by="Vol Ratio", ascending=False)
    st.dataframe(df2, use_container_width=True, hide_index=True)
else:
    st.info("No confirmed post-downtrend breakout anomalies printed right now.")

st.markdown("---")

st.markdown("## 🌀 Table 3: Squeeze Watchlist (Coiling Under Resistance, Ready to Break!)")
if st.session_state.c3_results:
    df3 = pd.DataFrame(st.session_state.c3_results).sort_values(by="Distance to Pop (%)", ascending=True)
    st.dataframe(df3, use_container_width=True, hide_index=True)
else:
    st.info("No setups currently coiling inside the critical tight pre-breakout sweet spot.")

st.markdown("---")

st.markdown("## 🔥 Table 4: Silent Humming Watchlist (4-Day Ultra-Contraction Pattern)")
st.caption("No breakouts. These stocks are flatline coiling under 2.5% width—completely quiet before an institutional expansion.")
if st.session_state.c4_results:
    df4 = pd.DataFrame(st.session_state.c4_results).sort_values(by="Cluster Tightness (%)", ascending=True)
    st.dataframe(df4, use_container_width=True, hide_index=True)
else:
    st.info("No stocks currently humming inside the ultra-narrow 2.5% compression corridor.")