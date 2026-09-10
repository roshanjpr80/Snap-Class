"""
SnapClass — Shared header components (logo + title) for home and dashboard screens.
"""

from datetime import datetime

import streamlit as st

# TODO: move this into a shared src/config.py (or constants.py) once you have
# one, and import it everywhere (app.py's page_icon, this file, etc.) so the
# logo only ever needs to change in a single place.
LOGO_URL = "https://i.ibb.co/YTYGn5qV/logo.png"

# Also destined for that future config.py, alongside LOGO_URL.
COLOR_TEXT_DARK = "#1a1a1a"


def _get_greeting() -> str:
    """Returns a time-of-day-appropriate greeting."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    return "Good evening"


def header_home():
    """Large centered logo + title, used on the home/landing screen."""
    st.markdown(
        f"""
        <div class="sc-header-home" style="display:flex; flex-direction:column;
             align-items:center; justify-content:center; margin-bottom:30px; margin-top:30px;">
            <img src="{LOGO_URL}" alt="SnapClass logo" style="height:100px;" />
            <h1 style="text-align:center; color: var(--sc-bg-panel, #E0E3FF);">
                SNAP<br/>CLASS
            </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _inject_responsive_header_css()


def header_dashboard(
    user_name: str | None = None,
    role: str | None = None,
    show_clock: bool = True,
):
    """Compact horizontal logo + title, used on teacher/student dashboard screens.

    Optionally shows a personalized greeting + role badge + live clock on the
    right side. All existing calls with no arguments still work exactly as
    before — the greeting/clock area just renders empty.

    IMPORTANT: unlike the previous version, the greeting/clock strings are
    built as real Python logic *before* the HTML template runs, then dropped
    into the template as already-finished variables. Putting if/assignment
    statements directly inside an f-string's template body doesn't execute
    them as code — it's a NameError waiting to happen the moment the
    template tries to evaluate a `{variable}` that was never actually
    defined in this function's scope.
    """
    greeting_line = ""
    if user_name:
        role_badge_html = f'<span class="snap-role-badge">{role}</span>' if role else ""
        greeting_line = (
            f'<p class="snap-greeting">{_get_greeting()}, {user_name} {role_badge_html}</p>'
        )

    clock_line = ""
    if show_clock:
        now_str = datetime.now().strftime("%A, %d %b %Y  •  %I:%M %p")
        clock_line = f'<p class="snap-clock">{now_str}</p>'

    html = f'<div style="text-align:left;">{greeting_line}{clock_line}</div>'

    st.markdown(
        f"""
        <div class="sc-header-dashboard" style="display:flex; align-items:center;
             justify-content:space-between; gap:10px; flex-wrap:wrap; margin-bottom:1rem;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{LOGO_URL}" alt="SnapClass logo" style="height:85px;" />
                <h2 style="text-align:left; color: var(--sc-primary, #5865F2); margin:0;">
                    SNAP<br/>CLASS
                </h2>
            </div>
            {html}
        </div>
        """,
        unsafe_allow_html=True,
    )
    _inject_responsive_header_css()
    _inject_dashboard_greeting_css()


def _inject_responsive_header_css():
    """Shrinks the logo/title on small screens so the dashboard header doesn't
    dominate a phone screen. Safe to call multiple times (idempotent CSS)."""
    st.markdown(
        """
        <style>
        @media (max-width: 640px) {
            .sc-header-home img,
            .sc-header-dashboard img {
                height: 60px !important;
            }
            .sc-header-dashboard {
                justify-content: center !important;
                text-align: center !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _inject_dashboard_greeting_css():
    """Styles for the personalized greeting/role-badge/clock area.
    Uses 'Outfit' (already @import-ed by style_base_layout in styles.py)
    rather than 'Poppins', which is never loaded anywhere in this app."""
    st.markdown(
        f"""
        <style>
        .snap-greeting {{
            font-family: 'Outfit', sans-serif;
            color: {COLOR_TEXT_DARK};
            font-size: 1.05rem;
            font-weight: 600;
            margin: 0;
        }}
        .snap-role-badge {{
            display: inline-block;
            margin-left: 6px;
            padding: 2px 10px;
            border-radius: 999px;
            background: rgba(88, 101, 242, 0.12);
            color: var(--sc-primary, #5865F2);
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: capitalize;
            vertical-align: middle;
        }}
        .snap-clock {{
            font-family: 'Outfit', sans-serif;
            color: #777;
            font-size: 0.8rem;
            margin: 2px 0 0 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )