import streamlit as st
import yfinance as yf
import pandas as pd
import string

from streamlit_lightweight_charts import renderLightweightCharts

from utils.styles import load_css
from utils.nse_data import get_full_nse_data

# =========================================================
# LOAD CSS
# =========================================================

load_css()

# =========================================================
# TITLE
# =========================================================

st.title("📊 Reversal Chart")

# =========================================================
# NSE DATA
# =========================================================

all_data = get_full_nse_data()

# =========================================================
# FILTER PANEL
# =========================================================

col_watch, col_chart = st.columns([1, 4])

# =========================================================
# LEFT PANEL
# =========================================================

with col_watch:

    st.write("### 🛠 Filter Stocks")

    alpha_options = [
        "SHOW ALL",
        "0-9"
    ] + list(string.ascii_uppercase)

    alpha = st.selectbox(
        "Initial",
        alpha_options
    )

    working_df = all_data[
        all_data['SERIES'] == 'EQ'
    ]

    # =====================================================
    # ALPHABET FILTER
    # =====================================================

    if alpha == "0-9":

        working_df = working_df[
            working_df['SYMBOL']
            .str[0]
            .str.isdigit()
        ]

    elif alpha != "SHOW ALL":

        working_df = working_df[
            working_df['SYMBOL']
            .str.startswith(alpha)
        ]

    # =====================================================
    # SEARCH
    # =====================================================

    search = st.text_input(
        "🔍 Quick Search",
        ""
    )

    filtered_list = working_df[
        'SYMBOL'
    ].tolist()

    if search:

        filtered_list = [
            s for s in filtered_list
            if search.upper() in s
        ]

    # =====================================================
    # STOCK SELECT
    # =====================================================

    selected_stock = st.selectbox(
        "Pick Stock",
        filtered_list
    )

    # =====================================================
    # TIMEFRAME
    # =====================================================

    timeframe = st.radio(
        "Timeframe",
        ("1d", "1wk")
    )

# =========================================================
# CHART PANEL
# =========================================================

with col_chart:

    ticker = f"{selected_stock}.NS"

    try:

        # =====================================================
        # DOWNLOAD DATA
        # =====================================================

        df = yf.download(
            ticker,
            period="1y",
            interval=timeframe,
            progress=False,
            auto_adjust=True
        )

        # =====================================================
        # MULTI INDEX FIX
        # =====================================================

        if isinstance(df.columns, pd.MultiIndex):

            df.columns = df.columns.get_level_values(0)

        # =====================================================
        # RESET INDEX
        # =====================================================

        df = df.reset_index()

        df.columns = [
            c.lower()
            for c in df.columns
        ]

        # =====================================================
        # REMOVE NaN
        # =====================================================

        df = df.dropna()

        # =====================================================
        # VOLUME MA
        # =====================================================

        df['vol_ma'] = (
            df['volume']
            .rolling(20)
            .mean()
        )

        # =====================================================
        # ORIGINAL REVERSAL LOGIC
        # =====================================================

        bottom_idx = df['low'].idxmin()

        # =====================================================
        # ABSOLUTE SUPPORT FLOOR
        # =====================================================

        abs_low = round(
            float(
                df.loc[
                    bottom_idx,
                    'low'
                ]
            ),
            2
        )

        # =====================================================
        # LH TARGET
        # =====================================================

        lh_target = round(
            float(
                df.loc[
                    bottom_idx - 1,
                    'high'
                ]
            ),
            2
        ) if bottom_idx > 0 else round(
            float(
                df.loc[
                    bottom_idx,
                    'high'
                ]
            ),
            2
        )

        # =====================================================
        # CURRENT PRICE
        # =====================================================

        ltp = round(
            float(
                df['close'].iloc[-1]
            ),
            2
        )

        # =====================================================
        # VOLUME RATIO
        # =====================================================

        curr_vol = float(
            df['volume'].iloc[-1]
        )

        avg_vol = (
            float(df['vol_ma'].iloc[-1])
            if pd.notna(df['vol_ma'].iloc[-1])
            else 0
        )

        vol_ratio = (
            curr_vol / avg_vol
            if avg_vol > 0
            else 0
        )

        # =====================================================
        # DISTANCE %
        # =====================================================

        distance_pct = round(
            (
                (lh_target - ltp)
                / ltp
            ) * 100,
            2
        )

        # =====================================================
        # WATCHLIST LOGIC
        # =====================================================

        status = None

        # =====================================================
        # VERY CLOSE
        # =====================================================

        if (
            ltp < lh_target
            and distance_pct >= 0
            and distance_pct <= 1
            and vol_ratio > 1.2
        ):

            status = "🔥 VERY CLOSE"

        # =====================================================
        # READY
        # =====================================================

        elif (
            ltp < lh_target
            and distance_pct >= 0
            and distance_pct <= 3
            and vol_ratio > 1
        ):

            status = "⏳ READY"

        # =====================================================
        # EARLY REVERSAL
        # =====================================================

        elif (
            ltp > abs_low
            and ltp < lh_target
            and distance_pct <= 8
            and vol_ratio > 1.2
        ):

            status = "⚡ EARLY REVERSAL"

        # =====================================================
        # ALREADY BROKEN OUT
        # =====================================================

        elif ltp > lh_target:

            status = "✅ ALREADY ABOVE LH"

        # =====================================================
        # CHART DATA
        # =====================================================

        df['time'] = pd.to_datetime(
            df['date']
        ).dt.strftime('%Y-%m-%d')

        chart_df = df[
            [
                'time',
                'open',
                'high',
                'low',
                'close'
            ]
        ].copy()

        chart_df = chart_df.fillna(0)

        chart_data = chart_df.to_dict('records')

        # =====================================================
        # RENDER CHART
        # =====================================================

        renderLightweightCharts(
            [
                {
                    "chart": {
                        "layout": {
                            "background": {
                                "color": "#ffffff"
                            },
                            "textColor": "#000000"
                        }
                    },
                    "series": [
                        {
                            "type": "Candlestick",
                            "data": chart_data
                        }
                    ]
                }
            ],
            key=f"{ticker}_{timeframe}"
        )

        # =====================================================
        # METRICS
        # =====================================================

        m1, m2, m3, m4, m5 = st.columns(5)

        m1.metric(
            "LTP",
            f"₹{ltp}"
        )

        m2.metric(
            "LH Target",
            f"₹{lh_target}"
        )

        m3.metric(
            "Support Floor",
            f"₹{abs_low}"
        )

        m4.metric(
            "Distance %",
            f"{distance_pct}%"
        )

        m5.metric(
            "Vol Ratio",
            f"{vol_ratio:.1f}x"
        )

        # =====================================================
        # SIGNAL
        # =====================================================

        if status == "🔥 VERY CLOSE":

            st.warning(
                f"{status} : Breakout likely soon above ₹{lh_target}"
            )

        elif status == "⏳ READY":

            st.info(
                f"{status} : Watching breakout above ₹{lh_target}"
            )

        elif status == "⚡ EARLY REVERSAL":

            st.success(
                f"{status} : Reversal structure forming"
            )

        elif status == "✅ ALREADY ABOVE LH":

            st.success(
                f"{status} : Stock already crossed LH ₹{lh_target}"
            )

        else:

            st.info(
                f"Waiting for proper setup near ₹{lh_target}"
            )

    except Exception as e:

        st.error(
            f"Error : {str(e)}"
        )