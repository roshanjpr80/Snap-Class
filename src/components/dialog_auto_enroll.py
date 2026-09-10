import time

import streamlit as st

from src.database.db import (
    enroll_student_to_subject,
    get_subject_by_code,
    is_student_enrolled,
    DuplicateEntryError,
)


@st.dialog("Quick Enrollment")
def auto_enroll_dialog(subject_code):
    student_id = st.session_state.student_data['student_id']

    subject = get_subject_by_code(subject_code)
    if not subject:
        st.error('Subject code not found!')
        if st.button('Close'):
            st.query_params.clear()
            st.rerun()
        return

    if is_student_enrolled(student_id, subject['subject_id']):
        st.info("You're already enrolled!")
        if st.button('Got it!'):
            st.query_params.clear()
            st.rerun()
        return

    st.markdown(f"Would you like to enroll in **{subject['name']}**?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button('No thanks'):
            st.query_params.clear()
            st.rerun()

    with col2:
        if st.button('Yes enroll now!', type='primary', width='stretch'):
            try:
                enroll_student_to_subject(student_id, subject['subject_id'])
                st.success('Joined successfully!')
                st.query_params.clear()
                time.sleep(2)
                st.rerun()
            except DuplicateEntryError:
                st.info("You're already enrolled!")
                st.query_params.clear()
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")