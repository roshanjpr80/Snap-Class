import time

import streamlit as st
import structlog

from src.database.db import create_attendance

logger = structlog.get_logger(__name__)


def show_attendance_result(df, logs):
    total = len(logs)
    present = sum(1 for entry in logs if entry.get('is_present'))
    absent = total - present

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Students", total)
    m2.metric("Present", present)
    m3.metric("Absent", absent)

    st.write('Please review attendance before confirming.')
    st.dataframe(df, hide_index=True, width='stretch')

    if 'confirm_discard_attendance' not in st.session_state:
        st.session_state.confirm_discard_attendance = False

    if st.session_state.confirm_discard_attendance:
        st.warning('This will discard all captured photos and results. Are you sure?')
        dc1, dc2 = st.columns(2)
        with dc1:
            if st.button('Cancel', width='stretch'):
                st.session_state.confirm_discard_attendance = False
                st.rerun()
        with dc2:
            if st.button('Yes, discard', width='stretch', type='primary'):
                st.session_state.voice_attendance_results = None
                st.session_state.attendance_images = []
                st.session_state.confirm_discard_attendance = False
                st.rerun()
        return

    col1, col2 = st.columns(2)

    with col1:
        if st.button('Discard', width='stretch'):
            st.session_state.confirm_discard_attendance = True
            st.rerun()

    with col2:
        if st.button('Confirm & Save', width='stretch', type='primary'):
            with st.spinner('Saving attendance...'):
                try:
                    create_attendance(logs)
                except Exception as exc:
                    logger.error("attendance_save_failed", error=str(exc), student_count=total)
                    st.error("Couldn't save attendance — please check your connection and try again.")
                    return

            st.toast(f"Attendance saved for {total} student(s) — {present} present, {absent} absent")
            st.session_state.attendance_images = []
            st.session_state.voice_attendance_results = None
            time.sleep(1)
            st.rerun()


@st.dialog("Attendance Reports")
def attendance_result_dialog(df, logs):
    show_attendance_result(df, logs)