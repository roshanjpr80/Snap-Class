import streamlit as st


def subject_card(name: str, code: str, section: str, stats: list | None = None, footer_callback=None):
    """
    Renders a styled subject/class card.

    stats: optional list of (icon, label, value) tuples shown as small pills
        under the header, e.g. [("🫂", "Students", 32), ("🕰️", "Classes", 12)].
    footer_callback: optional zero-arg function called immediately after the
        card renders (e.g. a "Share code" button). Note: since this is a
        native Streamlit element rendered separately from the raw HTML
        block above it, it appears directly below the card rather than
        visually inside its border — a Streamlit limitation, not a bug to
        chase further unless you want to invest in a custom component.
    """
    _inject_subject_card_css()

    html = f"""
        <div class="sc-subject-card">
            <h3 class="sc-subject-card-title">{name}</h3>
            <p class="sc-subject-card-meta">
                Code : <span class="sc-subject-card-code">{code}</span> | Section : {section}
            </p>
        """

    if stats:
        html += '<div class="sc-subject-card-stats">'
        for icon, label, value in stats:
            html += f'<div class="sc-subject-card-stat">{icon} <b>{value}</b> {label}</div>'
        html += "</div>"

    html += "</div>"   # closes .sc-subject-card — previously missing entirely

    st.markdown(html, unsafe_allow_html=True)

    if footer_callback:
        footer_callback()


def _inject_subject_card_css():
    st.markdown(
        """
        <style>
        .sc-subject-card {
            background: white;
            /* border-left THEN border (not the other way around) — border
               is shorthand for all four sides, so declaring it first and
               border-left after is what actually lets the accent stripe
               win instead of being silently overridden. */
            border: 1px solid rgba(0,0,0,0.08);
            border-left: 8px solid var(--sc-secondary, #EB459E);
            padding: 25px;
            border-radius: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
            transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
        }
        .sc-subject-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.10);
        }
        .sc-subject-card-title {
            margin: 0;
            color: #1a1a1a !important;
            font-size: 1.5rem;
        }
        .sc-subject-card-meta {
            color: #64748b;
            margin: 10px 0;
        }
        .sc-subject-card-code {
            background: var(--sc-bg-panel, #E0E3FF);
            color: var(--sc-primary, #5865F2);
            padding: 2px 8px;
            border-radius: 5px;
            font-weight: 600;
        }
        .sc-subject-card-stats {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .sc-subject-card-stat {
            background: color-mix(in srgb, var(--sc-secondary, #EB459E) 10%, white);
            padding: 5px 12px;
            border-radius: 12px;
            font-size: 0.9rem;
            color: #64748b
        }

        @media (max-width: 640px) {
            .sc-subject-card {
                padding: 16px;
            }
            .sc-subject-card-title {
                font-size: 1.2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )