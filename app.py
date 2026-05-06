import streamlit as st

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="NSE Pro Reversal Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# REDIRECT MESSAGE
# =========================================================

st.title("📈 NSE Pro Reversal Terminal")

st.info(
    "Use the sidebar to open the tools."
)

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("📌 Navigation")

st.sidebar.markdown("""
- 📊 Reversal Chart
- 🔍 Volume Scanner
- 📋 Full NSE List
""")