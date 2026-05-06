import streamlit as st
import pandas as pd

from utils.styles import load_css
from utils.nse_data import get_full_nse_data

# =========================================================
# LOAD CSS
# =========================================================

load_css()

# =========================================================
# TITLE
# =========================================================

st.title("📋 Full NSE List")

# =========================================================
# LIVE INDEX URLS
# =========================================================

INDEX_URLS = {

    "All Stocks": None,

    "NIFTY 50":
    "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",

    "NEXT NIFTY 50":
    "https://www.niftyindices.com/IndexConstituent/ind_niftynext50list.csv",

    "NIFTY 100":
    "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv",

    "BANK NIFTY":
    "https://www.niftyindices.com/IndexConstituent/ind_niftybanklist.csv",

    "FIN NIFTY":
    "https://www.niftyindices.com/IndexConstituent/ind_niftyfinancelist.csv",

    "MIDCAP":
    "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap100list.csv",

    "SMALLCAP":
    "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap100list.csv"
}

# =========================================================
# LOAD NSE MASTER DATA
# =========================================================

all_data = get_full_nse_data()

display_df = all_data.copy()

# =========================================================
# FILTERS
# =========================================================

col1, col2, col3, col4 = st.columns(4)

# =========================================================
# INDEX FILTER
# =========================================================

with col1:

    selected_index = st.selectbox(
        "Index",
        list(INDEX_URLS.keys())
    )

# =========================================================
# SERIES FILTER
# =========================================================

with col2:

    series_filter = st.multiselect(
        "Series",
        options=display_df['SERIES'].unique(),
        default=['EQ']
    )

# =========================================================
# SEARCH
# =========================================================

with col3:

    search = st.text_input(
        "Search"
    ).upper()

# =========================================================
# PRICE FILTER
# =========================================================

with col4:

    price_filter = st.selectbox(
        "Price Filter",
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
# LIVE INDEX FILTER
# =========================================================

if selected_index != "All Stocks":

    try:

        live_df = pd.read_csv(
            INDEX_URLS[selected_index]
        )

        live_symbols = live_df[
            'Symbol'
        ].tolist()

        display_df = display_df[
            display_df['SYMBOL']
            .isin(live_symbols)
        ]

    except Exception:

        st.warning(
            "Unable to fetch live index data."
        )

# =========================================================
# SERIES FILTER
# =========================================================

if series_filter:

    display_df = display_df[
        display_df['SERIES']
        .isin(series_filter)
    ]

# =========================================================
# SEARCH FILTER
# =========================================================

if search:

    display_df = display_df[
        (
            display_df['SYMBOL']
            .str.contains(
                search,
                case=False,
                na=False
            )
        )
        |
        (
            display_df['NAME OF COMPANY']
            .str.contains(
                search,
                case=False,
                na=False
            )
        )
    ]

# =========================================================
# REMOVE PRICE FILTER LOGIC
# =========================================================

# Keeping dropdown only for future use
# No live price loading

# =========================================================
# SORT
# =========================================================

display_df = display_df.sort_values(
    by="SYMBOL",
    ascending=True
)

# =========================================================
# DISPLAY
# =========================================================

st.success(
    f"Showing {len(display_df)} Stocks"
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# DOWNLOAD CSV
# =========================================================

csv = display_df.to_csv(
    index=False
).encode('utf-8')

st.download_button(
    "📥 Download CSV",
    data=csv,
    file_name="NSE_Stocks.csv",
    mime='text/csv'
)