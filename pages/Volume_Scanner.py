import streamlit as st
import yfinance as yf
import pandas as pd
import string
import time  # Added for rate limiting

from utils.styles import load_css
from utils.nse_data import get_full_nse_data

# =========================================================
# LOAD CSS
# =========================================================
load_css()

# =========================================================
# SESSION STATE
# =========================================================
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = []

# =========================================================
# TITLE
# =========================================================
st.title("🔍 Volume-Confirmed Scanner")

# =========================================================
# NIFTY 50
# =========================================================
NIFTY_50 = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP",
    "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO",
    "BAJFINANCE", "BAJAJFINSV", "BPCL",
    "BHARTIARTL", "BRITANNIA", "CIPLA",
    "COALINDIA", "DIVISLAB", "DRREDDY",
    "EICHERMOT", "GRASIM", "HCLTECH",
    "HDFCBANK", "HDFCLIFE", "HEROMOTOCO",
    "HINDALCO", "HINDUNILVR", "ICICIBANK",
    "ITC", "INDUSINDBK", "INFY",
    "JSWSTEEL", "KOTAKBANK", "LTIM",
    "LT", "M&M", "MARUTI",
    "NTPC", "NESTLEIND", "ONGC",
    "POWERGRID", "RELIANCE", "SBILIFE",
    "SBIN", "SUNPHARMA", "TCS",
    "TATACONSUM", "TATAMOTORS", "TATASTEEL",
    "TECHM", "TITAN", "ULTRACEMCO",
    "UPL", "WIPRO"
]

# =========================================================
# NSE DATA
# =========================================================
all_data = get_full_nse_data()

# =========================================================
# FILTERS
# =========================================================
col_sc1, col_sc2, col_sc3 = st.columns([1, 1, 1])

# =========================================================
# SCAN MODE
# =========================================================
with col_sc1:
    scan_mode = st.selectbox(
        "Scan Group",
        ["All Stocks", "Nifty 50", "Alphabetical/Numeric"]
    )

# =========================================================
# STOCK LIST
# =========================================================
with col_sc2:
    if scan_mode == "All Stocks":
        scan_list = all_data[all_data['SERIES'] == 'EQ']['SYMBOL'].tolist()
        st.info(f"Scanning {len(scan_list)} NSE EQ Stocks")
    elif scan_mode == "Alphabetical/Numeric":
        s_alpha = st.selectbox(
            "Select Initial",
            ["0-9"] + list(string.ascii_uppercase),
            key="sc_alpha"
        )
        if s_alpha == "0-9":
            scan_list = all_data[all_data['SYMBOL'].str[0].str.isdigit()]['SYMBOL'].tolist()
        else:
            scan_list = all_data[all_data['SYMBOL'].str.startswith(s_alpha)]['SYMBOL'].tolist()
    else:
        scan_list = NIFTY_50

# =========================================================
# PRICE FILTER
# =========================================================
with col_sc3:
    price_range = st.selectbox(
        "Price Range",
        ["All", "0 - 100", "100 - 500", "500 - 1000", "1000 - 5000", "5000 - 100000"]
    )

# =========================================================
# START SCAN
# =========================================================
if st.button(f"🚀 Start Scanning {len(scan_list)} Stocks"):
    results = []
    progress = st.progress(0)
    status_text = st.empty()  # To show which stock is being processed

    for i, sym in enumerate(scan_list):
        try:
            status_text.text(f"Processing: {sym} ({i+1}/{len(scan_list)})")
            
            # RATE LIMITING: Small sleep to prevent Yahoo Finance from blocking IP
            time.sleep(0.2)

            s_df = yf.download(
                f"{sym}.NS",
                period="100d",
                interval="1d",
                progress=False,
                auto_adjust=True
            )

            if len(s_df) < 30:
                continue

            if isinstance(s_df.columns, pd.MultiIndex):
                s_df.columns = s_df.columns.get_level_values(0)

            s_df = s_df.reset_index().dropna()
            
            # Normalize column names for consistency
            s_df.columns = [c.capitalize() for c in s_df.columns]

            s_df['vol_ma'] = s_df['Volume'].rolling(20).mean()

            b_idx = s_df['Low'].idxmin()

            if 0 < b_idx < (len(s_df) - 1):
                abs_low = round(float(s_df.loc[b_idx, 'Low']), 2)
                lh_val = round(float(s_df.loc[b_idx - 1, 'High']), 2)
                curr = round(float(s_df['Close'].iloc[-1]), 2)

                # Price Range Filter Logic
                if price_range != "All":
                    prices = price_range.split("-")
                    min_p = int(prices[0].strip())
                    max_p = int(prices[1].strip())
                    if not (min_p <= curr <= max_p):
                        continue

                avg_vol = s_df['vol_ma'].iloc[-1]
                if pd.isna(avg_vol) or avg_vol == 0:
                    continue

                v_ratio = s_df['Volume'].iloc[-1] / avg_vol
                dist = round(((lh_val - curr) / curr) * 100, 2)

                status = None
                if curr < lh_val and 0 <= dist <= 1 and v_ratio > 1.2:
                    status = "🔥 VERY CLOSE"
                elif curr < lh_val and 0 <= dist <= 3 and v_ratio > 1:
                    status = "⏳ READY"
                elif curr > abs_low and curr < lh_val and dist <= 8 and v_ratio > 1.2:
                    status = "⚡ EARLY"

                if status:
                    results.append({
                        "Status": status,
                        "Symbol": sym,
                        "LTP": curr,
                        "LH Target": lh_val,
                        "Support": abs_low,
                        "Distance %": dist,
                        "Vol Ratio": round(v_ratio, 2)
                    })

        except Exception:
            pass

        progress.progress((i + 1) / len(scan_list))

    st.session_state.scan_results = results
    status_text.empty()
    st.success("Scan Complete!")

# =========================================================
# DISPLAY RESULTS
# =========================================================
if st.session_state.scan_results:
    res_df = pd.DataFrame(st.session_state.scan_results)
    res_df = res_df.sort_values(by=["Distance %", "Vol Ratio"], ascending=[True, False])

    categories = [
        ("⏳ READY", "⏳ Ready To Breakout"),
        ("🔥 VERY CLOSE", "🔥 Very Close To Breakout"),
        ("⚡ EARLY", "⚡ Early Reversal")
    ]

    for status_key, header in categories:
        subset = res_df[res_df['Status'] == status_key]
        if not subset.empty:
            st.markdown(f"<div class='section-header'>{header}</div>", unsafe_allow_html=True)
            st.dataframe(subset, use_container_width=True, hide_index=True)
else:
    st.info("Run the scanner to view breakout watchlist stocks.")