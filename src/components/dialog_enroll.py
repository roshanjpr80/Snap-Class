import time

import streamlit as st

from src.database.db import enroll_student_to_subject, get_subject_by_code, DuplicateEntryError


@st.dialog("Enroll in Subject")
def enroll_dialog():
    st.write('Enter the subject code provided by your teacher to enroll')
    join_code = st.text_input('Subject Code', placeholder='Eg. CS101')

    if st.button('Enroll now', type='primary', width='stretch'):
        cleaned_code = join_code.strip()
        if not cleaned_code:
            st.warning('Please enter a subject code')
            return

        subject = get_subject_by_code(cleaned_code)
        if not subject:
            # Previously: nothing happened at all here. A mistyped code
            # gave the student zero feedback.
            st.error(f"No class found with code '{cleaned_code.upper()}'. Please check and try again.")
            return

        student_id = st.session_state.student_data['student_id']

        try:
            enroll_student_to_subject(student_id, subject['subject_id'])
            st.success(f"Successfully enrolled in {subject['name']}!")
            time.sleep(1)
            st.rerun()
        except DuplicateEntryError:
            # Relying on db.py's own duplicate check instead of a separate
            # manual pre-check here — one less DB round-trip, and no race
            # condition between "check" and "insert" being two steps.
            st.warning(f"You're already enrolled in {subject['name']}.")
        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")