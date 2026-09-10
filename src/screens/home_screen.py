import streamlit as st

from src.components.header import header_home
from src.components.footer import footer_home

from src.ui.base_layout import style_base_layout, style_background_home


def home_screen():
    style_base_layout()
    style_background_home()
    _inject_home_specific_css()
    header_home()

    st.markdown(
        '<h2 class="sc-hero-title">Who\'s logging in today?</h2>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sc-hero-subtitle">Choose your role to continue — attendance takes just a snap.</p>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<h3 class="sc-portal-title">🎓 I\'m Student</h3>', unsafe_allow_html=True)
        _image_slot("https://i.ibb.co/844D9Lrt/mascot-student.png", alt="Student mascot")
        st.markdown(
            "<p style='text-align:center; color:#444;'>"
            "Check in instantly with your face — no queues, no paperwork."
            "</p>",
            unsafe_allow_html=True,
        )
        if st.button(
            "Student Portal",
            type="primary",
            icon=":material/arrow_outward:",
            icon_position="right",
            use_container_width=True,
        ):
            st.session_state["login_type"] = "student"
            st.rerun()

    with col2:
        st.markdown('<h3 class="sc-portal-title">🧑\u200d🏫 I\'m Teacher</h3>', unsafe_allow_html=True)
        _image_slot("https://i.ibb.co/CsmQQV6X/mascot-prof.png", alt="Teacher mascot")
        st.markdown(
            "<p style='text-align:center; color:#444;'>"
            "Track every class in real time with live attendance analytics."
            "</p>",
            unsafe_allow_html=True,
        )
        if st.button(
            "Teacher Portal",
            type="secondary",
            icon=":material/arrow_outward:",
            icon_position="right",
            use_container_width=True,
        ):
            st.session_state["login_type"] = "teacher"
            st.rerun()

    _trust_strip()
    footer_home()


def _inject_home_specific_css():
    """
    Styles scoped to the home screen's two custom heading classes.

    IMPORTANT: style_base_layout() declares a *global* `h2 { ... !important }`
    rule (font-family/size/line-height). An inline style="" on a bare <h2>
    CANNOT beat that !important rule — inline styles lose to !important
    stylesheet rules regardless of the order they're written in. That's why
    the previous version's inline Poppins/font-size/line-height silently had
    no effect. Using dedicated classes with their own !important here is
    what actually lets us override the global heading rule on purpose.

    We also stick to 'Climate Crisis' / 'Outfit' — the two fonts already
    @import-ed in style_base_layout() — instead of introducing a third
    font ('Poppins') that's never loaded anywhere and would render as a
    default sans-serif regardless of the specificity issue.
    """
    st.markdown(
        """
        <style>
        .sc-hero-title {
            font-family: 'Climate Crisis', sans-serif !important;
            text-align: center !important;
            color: #1a1a1a !important;
            font-size: 2.2rem !important;
            line-height: 1.1 !important;
            margin: 0 0 4px 0 !important;
        }
        .sc-hero-subtitle {
            text-align: center;
            font-family: 'Outfit', sans-serif;
            color: #9AA0C3;
            font-size: 0.95rem;
            font-weight: 400;
            line-height: 1.5;
            letter-spacing: 0.01em;
            margin: 6px 0 28px 0;
        }
        .sc-portal-title {
            font-family: 'Outfit', sans-serif !important;
            text-align: center !important;
            color: #1a1a1a !important;
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            line-height: 1.3 !important;
            margin: 0 0 12px 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _image_slot(image_url: str, alt: str, height_px: int = 150):
    """Fixed-height, centered image wrapper so mascots of different aspect
    ratios don't push the two columns' buttons out of alignment."""
    st.markdown(
        f"""
        <div style="height:{height_px}px; display:flex; align-items:center;
                    justify-content:center; margin-bottom:0.5rem;">
            <img src="{image_url}" alt="{alt}" style="max-height:{height_px}px; max-width:100%;" />
        </div>
        """,
        unsafe_allow_html=True,
    )


def _trust_strip():
    """Small feature-highlight row to build trust on a public landing page."""
    st.markdown(
        """
        <div style="display:flex; justify-content:center; gap:28px; flex-wrap:wrap;
                    margin-top:2.5rem; opacity:0.9;">
            <span style="color:#E0E3FF; font-family:'Outfit', sans-serif; font-size:0.85rem;">
                🔒 Secure biometric login
            </span>
            <span style="color:#E0E3FF; font-family:'Outfit', sans-serif; font-size:0.85rem;">
                ⚡ Instant check-in
            </span>
            <span style="color:#E0E3FF; font-family:'Outfit', sans-serif; font-size:0.85rem;">
                📊 Real-time analytics
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )