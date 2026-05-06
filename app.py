import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import io
import string
from streamlit_lightweight_charts import renderLightweightCharts

# --- Configuration & Styling ---
st.set_page_config(page_title="NSE Pro Reversal Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #131722; }
    .stMetric { background-color: #f8f9fb; border-radius: 8px; padding: 15px; border: 1px solid #e0e3eb; }
    [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 700; color: #131722; }
    .section-header { font-size: 20px; font-weight: 700; margin-top: 20px; margin-bottom: 10px; }
    .stDataFrame { border: 1px solid #e0e3eb; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- Session State ---
if 'selected_stock' not in st.session_state: st.session_state.selected_stock = "RELIANCE"
if 'scan_results' not in st.session_state: st.session_state.scan_results = []

# --- Data Fetching ---
@st.cache_data
def get_full_nse_data():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        df = pd.read_csv(io.StringIO(response.text))
        df.columns = df.columns.str.strip()
        return df[['SYMBOL', 'NAME OF COMPANY', 'SERIES', 'DATE OF LISTING', 'FACE VALUE']]
    except:
        return pd.DataFrame({'SYMBOL': ['RELIANCE', 'TCS'], 'NAME OF COMPANY': ['Reliance Industries', 'Tata Consultancy Services'], 'SERIES': ['EQ', 'EQ']})

NIFTY_50 = ["ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BPCL", "BHARTIARTL", "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY", "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK", "ITC", "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK", "LTIM", "LT", "M&M", "MARUTI", "NTPC", "NESTLEIND", "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN", "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS", "TATASTEEL", "TECHM", "TITAN", "ULTRACEMCO", "UPL", "WIPRO"]

all_data = get_full_nse_data()

# --- TAB DEFINITION ---
tab1, tab2, tab3 = st.tabs(["📊 Reversal Chart", "🔍 Volume-Confirmed Scanner", "📋 Full NSE List"])

# --- TAB 1: CHART ---
with tab1:
    col_watch, col_chart = st.columns([1, 4])
    
    with col_watch:
        st.write("### 🛠 Filter Stocks")
        alpha_options = ["SHOW ALL", "0-9"] + list(string.ascii_uppercase)
        alpha = st.selectbox("Initial", alpha_options)
        
        working_df = all_data[all_data['SERIES'] == 'EQ']
        if alpha == "0-9":
            working_df = working_df[working_df['SYMBOL'].str[0].str.isdigit()]
        elif alpha != "SHOW ALL":
            working_df = working_df[working_df['SYMBOL'].str.startswith(alpha)]
            
        search = st.text_input("🔍 Quick Search", "")
        filtered_list = working_df['SYMBOL'].tolist()
        if search:
            filtered_list = [s for s in filtered_list if search.upper() in s]
            
        if filtered_list:
            if st.session_state.selected_stock not in filtered_list:
                st.session_state.selected_stock = filtered_list[0]
            st.session_state.selected_stock = st.selectbox("Pick Stock", filtered_list, index=filtered_list.index(st.session_state.selected_stock))
            ticker_sym = st.session_state.selected_stock
        else:
            ticker_sym = "RELIANCE"

        ticker = f"{ticker_sym}.NS"
        tf = st.radio("Timeframe", ("1d", "1wk"))

    with col_chart:
        df = yf.download(ticker, period="1y", interval=tf, progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df.reset_index().rename(columns=str.lower)
            
            df['vol_ma'] = df['volume'].rolling(20).mean()
            bottom_idx = df['low'].idxmin()
            abs_low = df.loc[bottom_idx, 'low']
            lh_level = df.loc[bottom_idx - 1, 'high'] if bottom_idx > 0 else df.loc[bottom_idx, 'high']
            
            ltp = df['close'].iloc[-1]
            curr_vol = df['volume'].iloc[-1]
            avg_vol = df['vol_ma'].iloc[-1]
            vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 0
            
            df['time'] = df['date'].dt.strftime('%Y-%m-%d')
            chart_data = df[['time', 'open', 'high', 'low', 'close']].to_dict('records')
            renderLightweightCharts([{"chart": {"layout": {"background": {"color": "#ffffff"}}}, 
                                     "series": [{"type": "Candlestick", "data": chart_data}]}], key=f"chart_{ticker}_{tf}")
            
            m1, m2, m3 = st.columns(3)
            m1.metric(f"{ticker_sym}", f"₹{ltp:.2f}")
            m2.metric("LH Target", f"₹{lh_level:.2f}")
            m3.metric("Vol / 20MA", f"{vol_ratio:.1f}x", delta="Strong" if vol_ratio > 1.2 else "Weak", delta_color="normal")
            
            if ltp > lh_level:
                st.success(f"🔥 BREAKOUT: Price above LH (₹{lh_level:.2f})")
            else:
                st.info(f"⏳ Target: ₹{lh_level:.2f}")

# --- TAB 2: SCANNER ---
with tab2:
    st.subheader("🔍 Volume-Confirmed Scanner")
    col_sc1, col_sc2 = st.columns([1, 1])
    with col_sc1:
        scan_mode = st.selectbox("Scan Group", ["Nifty 50", "Alphabetical/Numeric"])
    with col_sc2:
        if scan_mode == "Alphabetical/Numeric":
            s_alpha = st.selectbox("Select Initial", ["0-9"] + list(string.ascii_uppercase), key="sc_alpha")
            scan_list = all_data[all_data['SYMBOL'].str[0].str.isdigit()]['SYMBOL'].tolist() if s_alpha == "0-9" else all_data[all_data['SYMBOL'].str.startswith(s_alpha)]['SYMBOL'].tolist()
        else:
            scan_list = NIFTY_50

    if st.button(f"🚀 Start Scanning {len(scan_list)} Stocks"):
        results = []
        progress = st.progress(0)
        for i, sym in enumerate(scan_list):
            try:
                s_df = yf.download(f"{sym}.NS", period="100d", interval="1d", progress=False)
                if len(s_df) < 30: continue
                if isinstance(s_df.columns, pd.MultiIndex): s_df.columns = s_df.columns.get_level_values(0)
                s_df = s_df.reset_index()
                s_df['vol_ma'] = s_df['Volume'].rolling(20).mean()
                b_idx = s_df['Low'].idxmin()
                if 0 < b_idx < (len(s_df) - 1):
                    lh_val = s_df.loc[b_idx - 1, 'High']
                    curr = s_df['Close'].iloc[-1]
                    v_ratio = s_df['Volume'].iloc[-1] / s_df['vol_ma'].iloc[-1]
                    dist = ((lh_val - curr) / curr) * 100
                    status = "🔥 STRONG" if (curr > lh_val and v_ratio > 1.2) else "⚠️ WEAK" if curr > lh_val else "⏳ READY" if dist < 3 else None
                    if status:
                        results.append({"Status": status, "Symbol": sym, "LTP": round(curr, 2), "LH": round(lh_val, 2), "Vol Ratio": f"{v_ratio:.1f}x", "Dist %": f"{dist:.1f}%"})
            except: pass
            progress.progress((i + 1) / len(scan_list))
        st.session_state.scan_results = results

    if st.session_state.scan_results:
        res_df = pd.DataFrame(st.session_state.scan_results)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='section-header'>✅ Breakouts</div>", unsafe_allow_html=True)
            st.dataframe(res_df[res_df['Status'].str.contains("STRONG|WEAK")], use_container_width=True, hide_index=True)
        with c2:
            st.markdown("<div class='section-header'>⏳ Watchlist</div>", unsafe_allow_html=True)
            st.dataframe(res_df[res_df['Status'] == "⏳ READY"], use_container_width=True, hide_index=True)

# --- TAB 3: FULL NSE LIST ---
with tab3:
    st.subheader("📋 Official NSE Equity List")
    st.write(f"Total Stocks Listed: **{len(all_data)}**")
    
    # Filtering for the table
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        f_series = st.multiselect("Filter by Series", options=all_data['SERIES'].unique(), default=['EQ', 'BE'])
    with col_f2:
        f_search = st.text_input("Search Company or Symbol", "").upper()
    with col_f3:
        # Download Button
        csv = all_data.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Full List (CSV)", data=csv, file_name="NSE_All_Stocks.csv", mime='text/csv')

    # Apply Filters
    display_df = all_data.copy()
    if f_series:
        display_df = display_df[display_df['SERIES'].isin(f_series)]
    if f_search:
        display_df = display_df[(display_df['SYMBOL'].str.contains(f_search)) | (display_df['NAME OF COMPANY'].str.contains(f_search))]

    # Table Display
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Selection logic to jump back to Chart
    st.divider()
    st.write("### ⚡ Quick Action")
    selected_from_list = st.selectbox("Select a stock from this list to view its chart:", display_df['SYMBOL'].unique())
    if st.button("📈 View Chart for Selected Stock"):
        st.session_state.selected_stock = selected_from_list
        st.rerun()