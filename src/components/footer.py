"""
SnapClass — Shared footer components for home and dashboard screens.
"""

from datetime import datetime

import streamlit as st

from src.components.dialog_to_top import back_to_top_button

# TODO: move these into a shared src/config.py alongside LOGO_URL (see
# header.py) so branding info lives in exactly one place.
AUTHOR_NAME = "Kr. Roshan"
APP_VERSION = "v1.0"

# Edit this list to add/remove footer links (GitHub, LinkedIn, email, etc.)
FOOTER_LINKS = [
    # ("label", "url"),
    ("GitHub", "https://github.com/roshanjpr80"),
    ("LinkedIn", "https://www.linkedin.com/in/roshan-kumar-7340aa386/"),
    # ("Contact", "mailto:you@example.com"),
]


def _build_links_html():
    """Turn FOOTER_LINKS into a row of styled links. Returns an empty string
    (renders nothing) if the list is empty, instead of crashing."""
    if not FOOTER_LINKS:
        return ""
    items = "".join(
        f'<a class="footer-link" href="{url}" target="_blank">{label}</a>'
        for label, url in FOOTER_LINKS
    )
    return f'<div class="footer-links-row">{items}</div>'


def _inject_footer_css():
    st.markdown(
        """
        <style>
        .snapclass-footer {
            margin-top: 3rem;
            padding: 1.5rem 1rem;
            text-align: center;
            border-top: 1px solid rgba(0,0,0,0.08);
        }
        .footer-credit-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            flex-wrap: wrap;
        }
        .footer-credit {
            font-weight: 600;
            color: #444;
            margin: 0;
        }
        .author-name {
            color: var(--sc-primary, #5865F2);
            margin: 0;
        }
        .footer-version {
            font-size: 0.8rem;
            color: #777;
            margin: 0.3rem 0 0 0;
        }
        .footer-copyright {
            font-size: 0.75rem;
            color: #999;
            margin: 0.2rem 0 0 0;
        }
        .footer-links-row {
            display: flex;
            gap: 14px;
            justify-content: center;
            margin-top: 0.6rem;
        }
        .footer-link {
            font-size: 0.8rem;
            color: var(--sc-primary, #5865F2);
            text-decoration: none;
            font-weight: 600;
            transition: opacity 0.2s ease-in-out;
        }
        .footer-link:hover {
            opacity: 0.7;
            text-decoration: underline;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def footer_home():
    """Full footer with credit, version, copyright, and links — used on the
    home/landing screen."""
    _inject_footer_css()
    year = datetime.now().year
    links_html = _build_links_html()

    st.markdown(
        f"""
        <div class="snapclass-footer">
            <div class="footer-credit-row">
                <p class="footer-credit">Created with ❤️ by</p>
                <h3 class="author-name">{AUTHOR_NAME}</h3>
            </div>
            <p class="footer-version">
                Snap Class {APP_VERSION} &bull; AI-Powered Attendance System
            </p>
            <p class="footer-copyright">
                &copy; {year} {AUTHOR_NAME}. All rights reserved.
            </p>
            {links_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
    back_to_top_button()


def footer_dashboard():
    """Compact footer for teacher/student dashboard screens."""
    _inject_footer_css()

    st.markdown(
        f"""
        <div style="margin-top:2rem; display:flex; gap:6px; justify-content:center; align-items:center;">
            <p style="font-weight:600; color:#444; margin:0;">Created with ❤️ by</p>
            <h3 class="author-name" style="margin:0; color: var(--sc-primary, #5865F2);">{AUTHOR_NAME}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    back_to_top_button()