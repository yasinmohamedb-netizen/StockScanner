import streamlit as st

def load_css():

    st.markdown("""
        <style>

        .stApp {
            background-color: #ffffff;
            color: #131722;
        }

        .stMetric {
            background-color: #f8f9fb;
            border-radius: 8px;
            padding: 15px;
            border: 1px solid #e0e3eb;
        }

        [data-testid="stMetricValue"] {
            font-size: 26px !important;
            font-weight: 700;
            color: #131722;
        }

        .section-header {
            font-size: 20px;
            font-weight: 700;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        </style>
    """, unsafe_allow_html=True)