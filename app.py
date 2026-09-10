"""
SnapClass — AI-Powered Attendance System
Main application entry point.
"""

import streamlit as st

from src.screens.home_screen import home_screen
from src.screens.teacher_screen import teacher_screen
from src.screens.student_screen import student_screen

from src.components.dialog_auto_enroll import auto_enroll_dialog


# GLOBAL STYLES
def _inject_global_css():
    """Inject shared CSS once per app load (status bar, layout polish)."""
    st.markdown(
        """
        <style>
        /* ---- Top status bar ---- */
        .snapclass-status {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.6rem 1rem;
            border-radius: 10px;
            font-size: 0.75rem;
            margin-bottom: 1.2rem;
            opacity:0.5; 
            margin-top:2rem;
            color: #9AA0C3;
        }
        .snapclass-status-left {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 600;
        }
        .snapclass-status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4ADE80;
            box-shadow: 0 0 6px #4ADE80;
            display: inline-block;
            animation: snapclass-pulse 2s infinite;
        }
        @keyframes snapclass-pulse {
            0% { opacity: 1; }
            50% { opacity: 0.4; }
            100% { opacity: 1; }
        }
        .snapclass-version {
            opacity: 0.9;
            font-size: 0.75rem;
        }

        /* ---- General app polish ---- */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_footer():
    """Display a small application status indicator at the top of every screen."""
    login_type = st.session_state.get("login_type")

    if login_type == "teacher":
        role_label = "Teacher workspace"
    elif login_type == "student":
        role_label = "Student workspace"
    else:
        role_label = "Welcome"

    st.markdown(
        f"""
        <div class="snapclass-status"; opacity:0.5; font-size:0.75rem; margin-top:2rem;>
            <div class="snapclass-status-left">
                <span class="snapclass-status-dot"></span>
                <span>SnapClass · AI-Powered Attendance System</span>
            </div>
            <span class="snapclass-version">{role_label} · v1.0</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# SESSION STATE
def _init_session_state():
    """Initialize every session_state key the app depends on, in one place,
    so no screen ever hits an inconsistent/missing default."""
    defaults = {
        "login_type": None,      # None | "teacher" | "student"
        "is_logged_in": False,
        "user_role": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# JOIN-CODE (DEEP LINK) HANDLING
def _handle_join_code():
    """
    Handle ?join-code=... deep links BEFORE the screen renders, to avoid
    flicker, and WITHOUT silently hijacking an already-logged-in session
    (e.g. a teacher who clicks a student join link by mistake).

    Returns True if a rerun was triggered (caller should stop rendering).
    """
    join_code = st.query_params.get("join-code")
    if not join_code:
        return False

    # Case 1: nobody logged in yet -> safe to route straight into student flow
    if st.session_state["login_type"] is None:
        st.session_state["login_type"] = "student"
        st.rerun()
        return True

    # Case 2: already logged in as a DIFFERENT role -> don't silently switch.
    # Ask for confirmation instead of wiping their session.
    if st.session_state["login_type"] != "student":
        st.warning(
            "This is a student join link, but you're currently signed in as a "
            f"**{st.session_state['login_type']}**. Switching will end your "
            "current session."
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Switch to student & join class", use_container_width=True):
                st.session_state.clear()
                st.session_state["login_type"] = "student"
                st.rerun()
        with col2:
            if st.button("Stay in current session", use_container_width=True):
                st.query_params.clear()
                st.rerun()
        return True

    # Case 3: already a logged-in student -> trigger enrollment dialog
    if st.session_state.get("is_logged_in") and st.session_state.get("user_role") == "student":
        auto_enroll_dialog(join_code)

    return False


# MAIN
def main():
    st.set_page_config(
        page_title="SnapClass - Making Attendance faster using AI",
        page_icon="https://i.ibb.co/YTYGn5qV/logo.png",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    _inject_global_css()
    _init_session_state()

    # Resolve any deep-link (?join-code=...) BEFORE picking a screen, so we
    # never paint the wrong screen and then rerun into the right one.
    if _handle_join_code():
        return

    try:
        match st.session_state["login_type"]:
            case "teacher":
                teacher_screen()
            case "student":
                student_screen()
            case _:
                # Covers None AND any unexpected/corrupted value, instead of
                # silently rendering a blank page.
                home_screen()
    except Exception as exc:
        # Never show a raw traceback to a public user.
        st.error(
            "Something went wrong loading this screen. Please refresh the page. "
            "If this keeps happening, contact your class administrator."
        )
        st.exception(exc)  # remove this line in production if you don't want details logged to the UI

    _render_footer()


if __name__ == "__main__":
    main()