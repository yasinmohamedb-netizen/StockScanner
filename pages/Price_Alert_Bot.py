import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import threading
import time

from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Price Alert Bot",
    layout="wide"
)

# =========================================================
# TELEGRAM CONFIG
# =========================================================

TELEGRAM_TOKEN = st.secrets[
    "TELEGRAM_TOKEN"
]

CHAT_IDS = st.secrets[
    "CHAT_IDS"
]

# =========================================================
# INDEX LIST
# =========================================================

INDICES = {

    "NIFTY 50": "^NSEI",

    "BANK NIFTY": "^NSEBANK",

    "FIN NIFTY": "NIFTY_FIN_SERVICE.NS",

    "NIFTY IT": "^CNXIT",

    "NIFTY AUTO": "^CNXAUTO",

    "NIFTY PHARMA": "^CNXPHARMA",

    "MIDCAP": "^NSEMDCP50",

    "SMALLCAP": "^CNXSC"

}

# =========================================================
# SESSION STATE
# =========================================================

if "stock_alerts" not in st.session_state:

    st.session_state.stock_alerts = []

if "index_alerts" not in st.session_state:

    st.session_state.index_alerts = []

if "alert_engine_started" not in st.session_state:

    st.session_state.alert_engine_started = False

# =========================================================
# TITLE
# =========================================================

st.title(
    "🚨 Price Alert Bot"
)

st.info(
    "Stock Price Alerts + Index Zone Alerts"
)

# =========================================================
# TELEGRAM FUNCTION
# =========================================================

def send_telegram(message):

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_TOKEN}/sendMessage"
    )

    success = False

    for chat_id in CHAT_IDS:

        payload = {

            "chat_id": chat_id,

            "text": message

        }

        try:

            response = requests.post(

                url,

                json=payload,

                timeout=10

            )

            if response.status_code == 200:

                success = True

        except:

            pass

    return success

# =========================================================
# STOCK LTP
# =========================================================

def get_stock_ltp(symbol):

    try:

        symbol = symbol.upper().strip()

        ticker = yf.Ticker(
            f"{symbol}.NS"
        )

        data = ticker.history(
            period="1d",
            interval="1m"
        )

        if data.empty:

            return None

        return round(

            float(
                data['Close'].iloc[-1]
            ),

            2

        )

    except:

        return None

# =========================================================
# INDEX LTP
# =========================================================

def get_index_ltp(ticker):

    try:

        data = yf.Ticker(
            ticker
        ).history(
            period="1d",
            interval="1m"
        )

        if data.empty:

            return None

        return round(

            float(
                data['Close'].iloc[-1]
            ),

            2

        )

    except:

        return None

# =========================================================
# STOCK ALERT SECTION
# =========================================================

st.subheader(
    "📈 Stock Alerts"
)

c1, c2, c3 = st.columns(3)

with c1:

    stock_symbol = st.text_input(
        "Stock Symbol",
        placeholder="Example: RELIANCE"
    ).upper()

with c2:

    stock_condition = st.selectbox(

        "Condition",

        [
            "Above",
            "Below",
            "Touch"
        ]

    )

with c3:

    stock_price = st.number_input(

        "Target Price",

        min_value=0.0,

        step=1.0

    )

if st.button(
    "➕ Add Stock Alert"
):

    if stock_symbol != "":

        st.session_state.stock_alerts.append({

            "symbol": stock_symbol,

            "condition": stock_condition,

            "price": stock_price,

            "triggered": False,

            "created_at": datetime.now().strftime(
                "%d-%b-%Y %I:%M %p"
            ),

            "triggered_at": ""

        })

        st.success(
            "Stock Alert Added"
        )

# =========================================================
# INDEX ALERT SECTION
# =========================================================

st.subheader(
    "📊 Index Zone Alerts"
)

i1, i2, i3 = st.columns(3)

with i1:

    selected_index = st.selectbox(

        "Select Index",

        list(INDICES.keys())

    )

with i2:

    zone_start = st.number_input(

        "Zone Start",

        min_value=0.0,

        step=1.0

    )

with i3:

    zone_end = st.number_input(

        "Zone End",

        min_value=0.0,

        step=1.0

    )

if st.button(
    "➕ Add Index Alert"
):

    st.session_state.index_alerts.append({

        "index": selected_index,

        "ticker": INDICES[selected_index],

        "start": zone_start,

        "end": zone_end,

        "triggered": False,

        "created_at": datetime.now().strftime(
            "%d-%b-%Y %I:%M %p"
        ),

        "triggered_at": ""

    })

    st.success(
        "Index Alert Added"
    )

# =========================================================
# ACTIVE STOCK ALERTS
# =========================================================

st.subheader(
    "📋 Active Stock Alerts"
)

if len(
    st.session_state.stock_alerts
) > 0:

    for alert in st.session_state.stock_alerts:

        alert["current_ltp"] = get_stock_ltp(
            alert["symbol"]
        )

    stock_df = pd.DataFrame(
        st.session_state.stock_alerts
    )

    st.dataframe(

        stock_df,

        width="stretch",

        hide_index=True

    )

else:

    st.warning(
        "No Stock Alerts"
    )

# =========================================================
# ACTIVE INDEX ALERTS
# =========================================================

st.subheader(
    "📋 Active Index Alerts"
)

if len(
    st.session_state.index_alerts
) > 0:

    for alert in st.session_state.index_alerts:

        alert["current_ltp"] = get_index_ltp(
            alert["ticker"]
        )

    index_df = pd.DataFrame(
        st.session_state.index_alerts
    )

    st.dataframe(

        index_df,

        width="stretch",

        hide_index=True

    )

else:

    st.warning(
        "No Index Alerts"
    )

# =========================================================
# TEST TELEGRAM
# =========================================================

if st.button(
    "📨 Test Telegram"
):

    ok = send_telegram(
        "Telegram Working ✅"
    )

    if ok:

        st.success(
            "Telegram Sent Successfully"
        )

    else:

        st.error(
            "Telegram Failed"
        )

# =========================================================
# ALERT ENGINE
# =========================================================

def check_alerts(stock_alerts, index_alerts):

    while True:

        # =================================================
        # STOCK ALERTS
        # =================================================

        for alert in stock_alerts:

            try:

                if alert['triggered']:

                    continue

                ltp = get_stock_ltp(
                    alert['symbol']
                )

                if ltp is None:

                    continue

                triggered = False

                # =========================================
                # CONDITIONS
                # =========================================

                if alert['condition'] == "Above":

                    triggered = (
                        ltp >= alert['price']
                    )

                elif alert['condition'] == "Below":

                    triggered = (
                        ltp <= alert['price']
                    )

                elif alert['condition'] == "Touch":

                    triggered = (

                        abs(
                            ltp
                            -
                            alert['price']
                        ) <= 0.5

                    )

                # =========================================
                # SEND TELEGRAM
                # =========================================

                if triggered:

                    now = datetime.now().strftime(
                        "%d-%b-%Y %I:%M:%S %p"
                    )

                    message = f"""
🚨 STOCK ALERT

Stock:
{alert['symbol']}

Condition:
{alert['condition']}

Target:
₹{alert['price']}

Current Price:
₹{ltp}

Triggered At:
{now}
"""

                    ok = send_telegram(
                        message
                    )

                    if ok:

                        alert['triggered'] = True

                        alert['triggered_at'] = now

            except Exception as e:

                print(e)

        # =================================================
        # INDEX ALERTS
        # =================================================

        for alert in index_alerts:

            try:

                if alert['triggered']:

                    continue

                ltp = get_index_ltp(
                    alert['ticker']
                )

                if ltp is None:

                    continue

                triggered = (

                    alert['start']
                    <= ltp
                    <= alert['end']

                )

                if triggered:

                    now = datetime.now().strftime(
                        "%d-%b-%Y %I:%M:%S %p"
                    )

                    message = f"""
🚨 INDEX ALERT

Index:
{alert['index']}

Zone:
₹{alert['start']} - ₹{alert['end']}

Current Price:
₹{ltp}

Triggered At:
{now}
"""

                    ok = send_telegram(
                        message
                    )

                    if ok:

                        alert['triggered'] = True

                        alert['triggered_at'] = now

            except Exception as e:

                print(e)

        time.sleep(60)

# =========================================================
# START ENGINE
# =========================================================

if not st.session_state.alert_engine_started:

    thread = threading.Thread(

        target=check_alerts,

        args=(

            st.session_state.stock_alerts,

            st.session_state.index_alerts

        ),

        daemon=True

    )

    thread.start()

    st.session_state.alert_engine_started = True

# =========================================================
# STATUS
# =========================================================

st.success(
    "✅ Alert Engine Running Every 60 Seconds"
)