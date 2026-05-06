import os
import sys

# =========================================================
# VERCEL HANDLER
# =========================================================

def handler(request=None):

    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        "app.py",
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ]

    stcli.main()

# =========================================================
# REQUIRED FOR VERCEL
# =========================================================

app = handler

# =========================================================
# STREAMLIT APP
# =========================================================

import streamlit as st

st.set_page_config(
    page_title="NSE Pro Reversal Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 NSE Pro Reversal Terminal")

st.info(
    "Use the sidebar to open the tools."
)

st.sidebar.title("📌 Navigation")

st.sidebar.markdown("""
- 📊 Reversal Chart
- 🔍 Volume Scanner
- 📋 Full NSE List
""")