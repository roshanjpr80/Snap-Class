import io
import urllib.parse

import segno
import streamlit as st


@st.dialog("Share Class Link")
def share_subject_dialog(subject_name, subject_code):
    # Configurable via .streamlit/secrets.toml (or your deployment's Secrets
    # panel) as APP_BASE_URL. Falls back to the deployed app URL below if
    # unset — update this if your deployed URL ever changes.
    app_domain = st.secrets.get("APP_BASE_URL", "https://snap-class-attendance-ai-v2.streamlit.app")
    # Safety net: if APP_BASE_URL ever gets set in secrets.toml without a
    # scheme (e.g. just "snapclass-main.streamlit.app"), the resulting join
    # link/QR code would be a schema-less string — inconsistently handled by
    # browsers (some treat it as a search query, not a URL to navigate to)
    # rather than a reliable clickable/scannable link.
    if not app_domain.startswith(("http://", "https://")):
        app_domain = f"https://{app_domain}"
    app_domain = app_domain.rstrip("/")
    join_url = f"{app_domain}/?join-code={subject_code}"

    st.header(f"Share “{subject_name}”")
    st.caption("Students who open this link or scan this code join automatically.")

    try:
        qr = segno.make(join_url)
        out = io.BytesIO()
        qr.save(out, kind='png', scale=10, border=1)
        qr_bytes = out.getvalue()
    except Exception:
        qr_bytes = None
        st.error("Couldn't generate a QR code for this link, but the link below still works.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('### Copy Link')
        st.code(join_url, language="text")
        st.code(subject_code, language="text")
        st.info('Copy this link to share on WhatsApp or Email')

        whatsapp_text = urllib.parse.quote(f"Join {subject_name} on SnapClass: {join_url}")
        email_subject = urllib.parse.quote(f"Join {subject_name} on SnapClass")
        email_body = urllib.parse.quote(f"Use this link to join {subject_name}: {join_url}")

        st.link_button(
            "Share on WhatsApp",
            f"https://wa.me/?text={whatsapp_text}",
            width='stretch',
            icon=":material/chat:",
        )
        st.link_button(
            "Share via Email",
            f"mailto:?subject={email_subject}&body={email_body}",
            width='stretch',
            icon=":material/mail:",
        )

    with col2:
        st.markdown('### Scan to Join')
        if qr_bytes:
            st.image(qr_bytes, caption='QR code for class joining')
            st.download_button(
                "Download QR code",
                data=qr_bytes,
                file_name=f"{subject_code}_join_qr.png",
                mime="image/png",
                width='stretch',
                icon=":material/download:",
            )