import time

import streamlit as st

from src.database.db import create_subject, DuplicateEntryError


@st.dialog("Create New Subject")
def create_subject_dialog(teacher_id):
    st.write("Enter the details of the new subject")

    sub_name = st.text_input("Subject Name", placeholder="Introduction to Computer Science")
    sub_section = st.text_input("Section (optional)", placeholder="A")
    sub_code = st.text_input(
        "Custom join code (optional)",
        placeholder="Leave blank to auto-generate",
        help="Students use this code to join your class. Leave blank and "
             "we'll generate a short, unique one for you.",
    )

    if st.button("Create Subject Now", type='primary', width='stretch'):
        if not sub_name.strip():
            st.warning("Please enter a subject name.")
            return

        try:
            # NOTE: db.py's create_subject() signature is
            # (name, section, teacher_id, subject_code=None) — positional
            # order matters here, this previously didn't match and would
            # have silently scrambled fields.
            create_subject(
                name=sub_name.strip(),
                section=sub_section.strip() or "N/A",
                teacher_id=teacher_id,
                subject_code=sub_code.strip().upper() or None,
            )
            st.toast("Subject created successfully!", icon="✅")
            time.sleep(1)   # let the toast actually show before the dialog closes on rerun
            st.rerun()

        except DuplicateEntryError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")