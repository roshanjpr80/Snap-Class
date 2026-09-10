import streamlit as st

import streamlit.components.v1 as components


def back_to_top_button() -> None:
    """Renders a floating 'back to top' button.

    NOTE: this renders inside an isolated `components.html` iframe, which
    has its own document — it does NOT inherit the main app's fonts or the
    CSS variables (:root tokens) defined in styles.py. That's why the font
    is @import-ed again here and the brand color is hardcoded as rgba()
    rather than referencing var(--sc-primary): those variables simply don't
    exist in this iframe's document.
    """
    components.html(
        """
        <button
            type="button"
            id="snapclass-top-btn"
            class="footer-top-button"
            onclick="snapClassScrollToTop()"
            aria-label="Back to top"
        >
            ↑ Back to top
        </button>

        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600&display=swap');

            .footer-top-button {
                display: inline-flex;
                align-items: center;
                justify-content: center;

                margin-top: 12px;
                padding: 8px 16px;

                border: 1px solid rgba(88, 101, 242, 0.35);
                border-radius: 10px;

                background: rgba(88, 101, 242, 0.10);
                color: #1a1a1a !important;

                font-family: 'Outfit', sans-serif;
                font-size: 0.78rem;
                font-weight: 600;

                cursor: pointer;
                transition: background 0.2s ease, transform 0.2s ease, opacity 0.25s ease;

                /* Hidden until the user actually scrolls down (see script below) */
                opacity: 0;
                pointer-events: none;
            }

            .footer-top-button.is-visible {
                opacity: 1;
                pointer-events: auto;
            }

            .footer-top-button:hover {
                background: rgba(88, 101, 242, 0.18);
                transform: translateY(-1px);
            }

            .footer-top-button:active {
                transform: translateY(0);
            }
        </style>

        <script>
            function snapClassScrollToTop() {
                const doc = window.parent.document;

                // data-testid names change across Streamlit versions, so try
                // the known candidates first...
                const known = [
                    doc.querySelector('[data-testid="stAppViewContainer"]'),
                    doc.querySelector('[data-testid="stMain"]'),
                    doc.querySelector('section.main'),
                    doc.querySelector('.main'),
                    doc.scrollingElement,
                    doc.documentElement,
                    doc.body,
                ].filter(Boolean);

                let scrolledAny = false;
                for (const el of known) {
                    if (el.scrollTop > 0) {
                        el.scrollTo({ top: 0, behavior: 'smooth' });
                        scrolledAny = true;
                    }
                }

                // ...then fall back to scanning every element for whichever
                // one is actually holding the scroll position right now.
                if (!scrolledAny) {
                    const all = doc.querySelectorAll('*');
                    for (const el of all) {
                        if (el.scrollTop > 0) {
                            el.scrollTo({ top: 0, behavior: 'smooth' });
                            scrolledAny = true;
                        }
                    }
                }

                window.parent.scrollTo({ top: 0, behavior: 'smooth' });
            }

            // Show the button only after the user has scrolled down a bit.
            // We poll (instead of addEventListener('scroll')) because
            // Streamlit reruns can replace the parent's scroll container
            // with a new DOM node on every rerun, which would silently
            // detach any listener bound to the old node.
            (function initScrollWatcher() {
                const doc = window.parent.document;
                const btn = document.getElementById('snapclass-top-btn');
                const SHOW_AFTER_PX = 300;

                function currentScrollTop() {
                    const candidates = [
                        doc.querySelector('[data-testid="stAppViewContainer"]'),
                        doc.querySelector('[data-testid="stMain"]'),
                        doc.scrollingElement,
                        doc.documentElement,
                    ].filter(Boolean);

                    let max = 0;
                    for (const el of candidates) {
                        if (el.scrollTop > max) max = el.scrollTop;
                    }
                    return max;
                }

                function updateVisibility() {
                    if (!btn) return;
                    if (currentScrollTop() > SHOW_AFTER_PX) {
                        btn.classList.add('is-visible');
                    } else {
                        btn.classList.remove('is-visible');
                    }
                }

                setInterval(updateVisibility, 400);
                updateVisibility();
            })();
        </script>
        """,
        height=55,
    )