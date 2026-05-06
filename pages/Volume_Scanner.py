import streamlit as st
import yfinance as yf
import pandas as pd
import string

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
        [
            "All Stocks",
            "Nifty 50",
            "Alphabetical/Numeric"
        ]
    )

# =========================================================
# STOCK LIST
# =========================================================

with col_sc2:

    # =====================================================
    # ALL STOCKS
    # =====================================================

    if scan_mode == "All Stocks":

        scan_list = all_data[
            all_data['SERIES'] == 'EQ'
        ]['SYMBOL'].tolist()

        st.info(
            f"Scanning {len(scan_list)} NSE EQ Stocks"
        )

    # =====================================================
    # ALPHABETICAL
    # =====================================================

    elif scan_mode == "Alphabetical/Numeric":

        s_alpha = st.selectbox(
            "Select Initial",
            ["0-9"] + list(string.ascii_uppercase),
            key="sc_alpha"
        )

        if s_alpha == "0-9":

            scan_list = all_data[
                all_data['SYMBOL']
                .str[0]
                .str.isdigit()
            ]['SYMBOL'].tolist()

        else:

            scan_list = all_data[
                all_data['SYMBOL']
                .str.startswith(s_alpha)
            ]['SYMBOL'].tolist()

    # =====================================================
    # NIFTY 50
    # =====================================================

    else:

        scan_list = NIFTY_50

# =========================================================
# PRICE FILTER
# =========================================================

with col_sc3:

    price_range = st.selectbox(
        "Price Range",
        [
            "All",
            "0 - 100",
            "100 - 500",
            "500 - 1000",
            "1000 - 5000",
            "5000 - 100000"
        ]
    )

# =========================================================
# START SCAN
# =========================================================

if st.button(
    f"🚀 Start Scanning {len(scan_list)} Stocks"
):

    results = []

    progress = st.progress(0)

    # =====================================================
    # LOOP
    # =====================================================

    for i, sym in enumerate(scan_list):

        try:

            # =================================================
            # DOWNLOAD DATA
            # =================================================

            s_df = yf.download(
                f"{sym}.NS",
                period="100d",
                interval="1d",
                progress=False,
                auto_adjust=True
            )

            if len(s_df) < 30:
                continue

            # =================================================
            # MULTI INDEX FIX
            # =================================================

            if isinstance(
                s_df.columns,
                pd.MultiIndex
            ):

                s_df.columns = (
                    s_df.columns
                    .get_level_values(0)
                )

            # =================================================
            # RESET INDEX
            # =================================================

            s_df = s_df.reset_index()

            # =================================================
            # REMOVE NaN
            # =================================================

            s_df = s_df.dropna()

            # =================================================
            # VOLUME MA
            # =================================================

            s_df['vol_ma'] = (
                s_df['Volume']
                .rolling(20)
                .mean()
            )

            # =================================================
            # ORIGINAL REVERSAL LOGIC
            # =================================================

            b_idx = s_df['Low'].idxmin()

            if 0 < b_idx < (len(s_df) - 1):

                # =============================================
                # SUPPORT FLOOR
                # =============================================

                abs_low = round(
                    float(
                        s_df.loc[
                            b_idx,
                            'Low'
                        ]
                    ),
                    2
                )

                # =============================================
                # LH TARGET
                # =============================================

                lh_val = round(
                    float(
                        s_df.loc[
                            b_idx - 1,
                            'High'
                        ]
                    ),
                    2
                )

                # =============================================
                # CURRENT PRICE
                # =============================================

                curr = round(
                    float(
                        s_df['Close'].iloc[-1]
                    ),
                    2
                )

                # =============================================
                # PRICE FILTER
                # =============================================

                if price_range != "All":

                    min_price = int(
                        price_range
                        .split("-")[0]
                        .strip()
                    )

                    max_price = int(
                        price_range
                        .split("-")[1]
                        .strip()
                    )

                    if not (
                        min_price
                        <= curr
                        <= max_price
                    ):
                        continue

                # =============================================
                # VOLUME RATIO
                # =============================================

                avg_vol = (
                    s_df['vol_ma']
                    .iloc[-1]
                )

                if (
                    pd.isna(avg_vol)
                    or avg_vol == 0
                ):
                    continue

                v_ratio = (
                    s_df['Volume']
                    .iloc[-1]
                    / avg_vol
                )

                # =============================================
                # DISTANCE %
                # =============================================

                dist = round(
                    (
                        (lh_val - curr)
                        / curr
                    ) * 100,
                    2
                )

                # =============================================
                # WATCHLIST LOGIC
                # =============================================

                status = None

                # =============================================
                # VERY CLOSE TO BREAKOUT
                # =============================================

                if (
                    curr < lh_val
                    and dist >= 0
                    and dist <= 1
                    and v_ratio > 1.2
                ):

                    status = "🔥 VERY CLOSE"

                # =============================================
                # READY TO BREAKOUT
                # =============================================

                elif (
                    curr < lh_val
                    and dist >= 0
                    and dist <= 3
                    and v_ratio > 1
                ):

                    status = "⏳ READY"

                # =============================================
                # EARLY REVERSAL
                # =============================================

                elif (
                    curr > abs_low
                    and curr < lh_val
                    and dist <= 8
                    and v_ratio > 1.2
                ):

                    status = "⚡ EARLY"

                # =============================================
                # STORE RESULTS
                # =============================================

                if status:

                    results.append({

                        "Status": status,

                        "Symbol": sym,

                        "LTP": curr,

                        "LH Target": lh_val,

                        "Support": abs_low,

                        "Distance %": dist,

                        "Vol Ratio": round(
                            v_ratio,
                            2
                        )

                    })

        except Exception:
            pass

        # =====================================================
        # PROGRESS
        # =====================================================

        progress.progress(
            (i + 1) / len(scan_list)
        )

    # =====================================================
    # STORE SESSION RESULTS
    # =====================================================

    st.session_state.scan_results = results

# =========================================================
# DISPLAY RESULTS
# =========================================================

if st.session_state.scan_results:

    res_df = pd.DataFrame(
        st.session_state.scan_results
    )

    # =====================================================
    # SORTING
    # =====================================================

    res_df = res_df.sort_values(
        by=[
            "Distance %",
            "Vol Ratio"
        ],
        ascending=[
            True,
            False
        ]
    )

    # =====================================================
    # READY TO BREAKOUT
    # =====================================================

    ready_df = res_df[
        res_df['Status']
        == "⏳ READY"
    ]

    if not ready_df.empty:

        st.markdown(
            "<div class='section-header'>⏳ Ready To Breakout</div>",
            unsafe_allow_html=True
        )

        st.dataframe(
            ready_df,
            use_container_width=True,
            hide_index=True
        )

    # =====================================================
    # VERY CLOSE TO BREAKOUT
    # =====================================================

    very_close_df = res_df[
        res_df['Status']
        == "🔥 VERY CLOSE"
    ]

    if not very_close_df.empty:

        st.markdown(
            "<div class='section-header'>🔥 Very Close To Breakout</div>",
            unsafe_allow_html=True
        )

        st.dataframe(
            very_close_df,
            use_container_width=True,
            hide_index=True
        )

    # =====================================================
    # EARLY REVERSAL
    # =====================================================

    early_df = res_df[
        res_df['Status']
        == "⚡ EARLY"
    ]

    if not early_df.empty:

        st.markdown(
            "<div class='section-header'>⚡ Early Reversal</div>",
            unsafe_allow_html=True
        )

        st.dataframe(
            early_df,
            use_container_width=True,
            hide_index=True
        )

else:

    st.info(
        "Run the scanner to view breakout watchlist stocks."
    )