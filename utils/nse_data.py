import pandas as pd
import requests
import io
import streamlit as st

@st.cache_data(ttl=3600)
def get_full_nse_data():

    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        df = pd.read_csv(
            io.StringIO(response.text)
        )

        df.columns = df.columns.str.strip()

        return df[
            [
                'SYMBOL',
                'NAME OF COMPANY',
                'SERIES',
                'DATE OF LISTING',
                'FACE VALUE'
            ]
        ]

    except Exception:

        return pd.DataFrame({
            'SYMBOL': ['RELIANCE', 'TCS'],
            'NAME OF COMPANY': [
                'Reliance Industries',
                'Tata Consultancy Services'
            ],
            'SERIES': ['EQ', 'EQ']
        })