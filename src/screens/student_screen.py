import hashlib
import time

import numpy as np
import streamlit as st
from PIL import Image

from src.components.dialog_enroll import enroll_dialog
from src.components.footer import footer_dashboard
from src.components.header import header_dashboard
from src.components.subject_card import subject_card
from src.database.db import (
    create_student,
    get_student_attendance,
    get_student_by_id,
    get_student_subjects,
    student_login,
    unenroll_student_to_subject,
    DuplicateEntryError,
)
from src.pipelines.face_pipeline import get_face_embeddings, predict_attendance, train_classifier
from src.pipelines.voice_pipeline import get_voice_embedding
from src.ui.base_layout import style_background_dashboard, style_base_layout


def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data['student_id']
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        # Not passing user_name/role here — header_dashboard's own greeting
        # feature would otherwise show the student's name a second time,
        # right next to the custom-styled "Welcome" heading below.
        header_dashboard()
    with c2:
        st.markdown(f"""<h3 class='header'>Welcome, {student_data['name']} </h3>""", unsafe_allow_html=True)
        if st.button("Logout", type='secondary', key='student_logout_btn', shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            st.session_state['user_role'] = None
            st.session_state.pop('student_data', None)
            st.rerun()

    st.space()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<h2 class="enroll-title">Your Enrolled Subjects</h2>', unsafe_allow_html=True)
    with c2:
        if st.button('Enroll in Subject', type='primary', width='stretch'):
            enroll_dialog()

    st.divider()

    with st.spinner('Loading your enrolled subjects..'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}
    for log in logs:
        sid = log['subject_id']
        if sid not in stats_map:
            stats_map[sid] = {"total": 0, "attended": 0}
        stats_map[sid]['total'] += 1
        if log.get('is_present'):
            stats_map[sid]['attended'] += 1

    if not subjects:
        st.info("You're not enrolled in any subjects yet — use the button above to join one.")

    cols = st.columns(2)
    for i, sub_node in enumerate(subjects):
        sub = sub_node['subjects']
        sid = sub['subject_id']
        stats = stats_map.get(sid, {"total": 0, "attended": 0})

        def unenroll_button(sid=sid, sub=sub):
            if st.button("Unenroll from this course", type='tertiary', width='stretch', icon=':material/delete_forever:'):
                unenroll_student_to_subject(student_id, sid)
                st.toast(f"Unenrolled from {sub['name']} successfully!")
                st.rerun()

        with cols[i % 2]:
            subject_card(
                name=sub['name'],
                code=sub['subject_code'],
                section=sub['section'],
                stats=[
                    ('📅', 'Total', stats['total']),
                    ('✅', 'Attended', stats['attended']),
                ],
                footer_callback=unenroll_button
            )

    footer_dashboard()


def _photo_hash(photo_file) -> str:
    """Stable identity for a captured photo, used to detect whether this is
    a genuinely NEW capture or the same one Streamlit is still holding onto
    across an unrelated rerun (e.g. the user typing into the name field)."""
    return hashlib.md5(photo_file.getvalue()).hexdigest()


def student_screen():
    style_background_dashboard()
    style_base_layout()
    _inject_home_specific_css()

    if "student_data" in st.session_state:
        student_dashboard()
        return

    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='student_login_back_btn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.markdown('<h2 class="sc-title">Login using FaceID</h2>', unsafe_allow_html=True)
    st.space()
    st.space()

    show_registration = False
    img = None
    photo_source = st.camera_input("Position your face in the center")

    if photo_source:
        current_hash = _photo_hash(photo_source)

        if st.session_state.get('_login_photo_hash') != current_hash:
            img = np.array(Image.open(photo_source))
            with st.spinner('AI is scanning..'):
                detected, all_ids, num_faces = predict_attendance(img)
            st.session_state['_login_photo_hash'] = current_hash
            st.session_state['_login_scan_result'] = (detected, all_ids, num_faces)
        else:
            img = np.array(Image.open(photo_source))
            detected, all_ids, num_faces = st.session_state['_login_scan_result']

        if num_faces == 0:
            st.warning('Face not found!')
        elif num_faces > 1:
            st.warning('Multiple faces found')
        else:
            if detected:
                student_id = list(detected.keys())[0]
                student = get_student_by_id(student_id)

                if student:
                    st.session_state.is_logged_in = True
                    st.session_state.user_role = 'student'
                    st.session_state.student_data = student
                    st.toast(f"Welcome back, {student['name']}!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.info('Face not recognized! You might be a new student!')
                show_registration = True

    if show_registration:
        with st.container(border=True):
            st.markdown('<h2 class="sc-re-title">Register new Profile</h2>', unsafe_allow_html=True)
            new_name = st.text_input("Enter your name", placeholder='E.g. Roshan Kumar')

            st.markdown('<h3 class="sc-rg-title">Optional: Voice Enrollment</h3>', unsafe_allow_html=True)
            st.info("Enroll your voice for voice-only attendance")
            audio_data = st.audio_input('Record a short phrase like "I am present, my name is Roshan."')

            st.markdown('<h3 class="sc-rg-title">Optional: Backup Login</h3>', unsafe_allow_html=True)
            st.info(
                "FaceID is your main way to log in. Username and password are "
                "an optional backup for when a camera isn't available — "
                "email is just for contact and isn't required either way."
            )
            backup_col1, backup_col2, backup_col3 = st.columns(3)
            with backup_col1:
                backup_username = st.text_input("Choose a username (optional)", key="reg_backup_username")
            with backup_col2:
                backup_password = st.text_input("Choose a password (optional)", type='password', key="reg_backup_password")
            with backup_col3:
                backup_email = st.text_input("Email (optional)", key="reg_backup_useremail")

            if st.button('Create Account', type='primary'):
                if not new_name:
                    st.warning('Please enter your name!')
                elif bool(backup_username) != bool(backup_password):
                    # Fixed: was a chained comparison `a != b != c`, which in
                    # Python means (a != b) and (b != c) — NOT "all three
                    # should match." That silently let a username-only or
                    # email-only submission through undetected. Email is now
                    # independent of the username/password pairing, since it
                    # isn't used for authentication anywhere (student_login()
                    # only checks username/password).
                    st.warning('Please fill in both the username and password, or leave both blank.')
                else:
                    with st.spinner('Creating profile..'):
                        encodings = get_face_embeddings(img)
                        if encodings:
                            face_emb = encodings[0].tolist()

                            voice_emb = None
                            if audio_data:
                                voice_emb = get_voice_embedding(audio_data.read())

                            try:
                                response_data = create_student(
                                    name=new_name,
                                    username=backup_username or None,
                                    password=backup_password or None,
                                    email=backup_email or None,
                                    face_embedding=face_emb,
                                    voice_embedding=voice_emb,
                                )
                            except DuplicateEntryError as e:
                                st.error(str(e))
                                response_data = None
                            except Exception as e:
                                st.error(f"Couldn't create your profile: {str(e)}")
                                response_data = None

                            if response_data:
                                train_classifier()
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = 'student'
                                st.session_state.student_data = response_data[0]
                                st.toast(f'Profile created! Hi {new_name}!')
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error("Couldn't capture your facial features for registration — please retake the photo.")

    st.divider()
    with st.expander("Can't use a camera? Log in with username & password instead"):
        backup_login_username = st.text_input("Username", key="login_backup_username")
        backup_login_password = st.text_input("Password", type='password', key="login_backup_password")
        if st.button("Log in", key="backup_login_btn"):
            if not backup_login_username or not backup_login_password:
                st.warning("Please enter both your username and password.")
            else:
                student = student_login(backup_login_username, backup_login_password)
                if student:
                    st.session_state.is_logged_in = True
                    st.session_state.user_role = 'student'
                    st.session_state.student_data = student
                    st.toast(f"Welcome back, {student['name']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid username/password, or you haven't set up a backup login yet.")

    footer_dashboard()


def _inject_home_specific_css():
    st.markdown(
        """
        <style>
        .sc-title {
            text-align: center !important;
            color: #1a1a1a !important;
        }
        .stCameraInput label { color: #777; }
        .sc-re-title {
            text-align: left !important;
            color: #1a1a1a !important;
        }
        div[data-testid="stSpinner"] p { color: #777; }

        /* Removed the blanket .stTextInput input / .stAlert overrides that
           were here before — they dimmed text the user is actively typing
           (username, password, name) and flattened every alert type
           (error/warning/success/info) to the same gray, removing the
           color cues people rely on to notice an error at a glance. */

        .sc-rg-title {
            text-align: left !important;
            color: #1a1a1a !important;
        }
        .header {
            color: #1a1a1a !important;
        }
        .enroll-title {
            color: #1a1a1a !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )