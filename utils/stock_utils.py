import yfinance as yf
import streamlit as st

@st.cache_data(ttl=300)
def get_stock_price(symbol):

    try:

        ticker = yf.Ticker(f"{symbol}.NS")

        hist = ticker.history(period="1d")

        if hist.empty:
            return None

        return round(
            float(hist['Close'].iloc[-1]),
            2
        )

    except Exception:
        return None