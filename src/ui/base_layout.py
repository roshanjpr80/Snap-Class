"""
SnapClass — Shared UI styling.
Centralized CSS so every screen (home, teacher, student) looks consistent.
"""

import streamlit as st


# BASE LAYOUT — call this once, on every screen, before anything else.
# Defines the CSS variables (single source of truth for colors),
# fonts, button styles, cards, and responsive rules.
def style_base_layout():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis:YEAR@1979&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');

        /* ---- Design tokens: change once here, applies everywhere ---- */
        :root {
            --sc-primary: #5865F2;
            --sc-secondary: #EB459E;
            --sc-dark: #000000;
            --sc-bg-home: #5865F2;
            --sc-bg-panel: #E0E3FF;
            --sc-bg-dashboard: #E0E3FF;
            --sc-text-on-primary: #ffffff;
            --sc-radius-lg: 5rem;
            --sc-radius-md: 1.5rem;
            --sc-radius-sm: 0.75rem;
        }

        /* ---- Hide Streamlit's default chrome ---- */
        #MainMenu, footer, header {
            visibility: hidden;
        }

        .block-container {
            padding-top: 1.5rem !important;
            animation: sc-fade-in 0.35s ease-out;
        }

        @keyframes sc-fade-in {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* ---- Typography ---- */
        h1 {
            font-family: 'Climate Crisis', sans-serif !important;
            font-size: 3.5rem !important;
            line-height: 1.1 !important;
            margin-bottom: 0rem !important;
        }

        h2 {
            font-family: 'Climate Crisis', sans-serif !important;
            font-size: 2rem !important;
            line-height: 0.9 !important;
            margin-bottom: 0rem !important;
        }

        h3, h4, p {
            font-family: 'Outfit', sans-serif;
        }

        /* Smaller headers on narrow/mobile screens */
        @media (max-width: 640px) {
            h1 { font-size: 2.2rem !important; }
            h2 { font-size: 1.4rem !important; }
        }

        /* ---- Buttons ----
           Scoped to Streamlit's actual button wrapper (not a bare `button`
           selector) so file-uploader, dataframe download, and webrtc camera
           control buttons don't inherit this styling by accident. */
        div[data-testid="stButton"] button,
        div[data-testid="stFormSubmitButton"] button {
            border-radius: var(--sc-radius-md) !important;
            background-color: var(--sc-primary) !important;
            color: var(--sc-text-on-primary) !important;
            padding: 10px 20px !important;
            border: none !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600 !important;
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out !important;
            box-shadow: 0 2px 6px rgba(88, 101, 242, 0.25) !important;
        }

        div[data-testid="stButton"] button[kind="secondary"] {
            background-color: var(--sc-secondary) !important;
            box-shadow: 0 2px 6px rgba(235, 69, 158, 0.25) !important;
        }

        div[data-testid="stButton"] button[kind="tertiary"] {
            background-color: var(--sc-dark) !important;
            box-shadow: none !important;
        }

        div[data-testid="stButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            transform: scale(1.05);
        }

        div[data-testid="stButton"] button:active {
            transform: scale(0.97);
        }

        /* ---- Reusable card, for dashboard sections/metrics/tables.
           Wrap any section with st.container() and give it this class
           via markdown, or apply directly to stColumn as home screen does. ---- */
        .snapclass-card {
            background-color: var(--sc-bg-panel);
            padding: 1.5rem;
            border-radius: var(--sc-radius-sm);
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        }

        /* ---- Themed alerts, so they match the brand instead of
           Streamlit's default red/green/yellow boxes ---- */
        div[data-testid="stAlert"] {
            border-radius: var(--sc-radius-sm) !important;
            font-family: 'Outfit', sans-serif !important;
        }

        /* ---- Metrics (st.metric) get card treatment for dashboards ---- */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            padding: 1rem;
            border-radius: var(--sc-radius-sm);
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# HOME SCREEN BACKGROUND
def style_background_home():
    st.markdown(
        """
        <style>
        .stApp {
            background: var(--sc-bg-home, #5865F2) !important;
        }
        .stApp div[data-testid="stColumn"] {
            background-color: var(--sc-bg-panel, #E0E3FF) !important;
            padding: 2.5rem !important;
            border-radius: var(--sc-radius-lg, 5rem) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# DASHBOARD BACKGROUND (teacher / student screens)
def style_background_dashboard():
    st.markdown(
        """
        <style>
        .stApp {
            background: var(--sc-bg-dashboard, #E0E3FF) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )