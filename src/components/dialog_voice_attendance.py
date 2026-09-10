from datetime import datetime

import pandas as pd
import streamlit as st

from src.components.dialog_attendance_results import show_attendance_result
from src.database.db import get_enrolled_students_with_details
from src.pipelines.voice_pipeline import process_bulk_audio


@st.dialog('Voice Attendance')
def voice_attendance_dialog(selected_subject_id):
    st.write('Record audio of students saying "I am present." Then AI will recognize the students.')

    audio_data = st.audio_input("Record classroom audio")

    if st.button('Analyze Audio', width='stretch', type='primary'):
        if not audio_data:
            st.warning('Please record some audio first.')
            return

        with st.spinner('Processing audio data...'):
            try:
                enrolled_students = get_enrolled_students_with_details(selected_subject_id)
            except Exception:
                st.error("Couldn't load enrolled students — please check your connection and try again.")
                return

            if not enrolled_students:
                st.warning('No students enrolled in this course')
                return

            candidates_dict = {
                s['students']['student_id']: s['students']['voice_embedding']
                for s in enrolled_students if s['students'].get('voice_embedding')
            }

            if not candidates_dict:
                st.error('No enrolled students have voice profiles registered')
                return

            audio_bytes = audio_data.read()

            # process_bulk_audio returns (results, segment_count) — lets us
            # tell "no one spoke" apart from "people spoke but weren't
            # recognized", instead of both looking like an empty result.
            detected_scores, usable_segments = process_bulk_audio(audio_bytes, candidates_dict)

            if usable_segments == 0:
                st.warning("No speech detected in that recording — please try again with clearer audio.")
                return

            results, attendance_to_log = [], []
            current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

            for node in enrolled_students:
                student = node['students']
                score = detected_scores.get(student['student_id'], 0.0)
                is_present = bool(score > 0)

                results.append({
                    "Name": student['name'],
                    "ID": student['student_id'],
                    "Confidence": f"{score:.0%}" if is_present else "-",
                    "Status": "✅ Present" if is_present else "❌ Absent"
                })

                attendance_to_log.append({
                    'student_id': student['student_id'],
                    'subject_id': selected_subject_id,
                    'logged_at': current_timestamp,        # was 'timestamp' — schema column is 'logged_at'
                    'is_present': bool(is_present),
                    'method': 'voice',                      # was missing — every entry defaulted to 'face' in the DB
                    'confidence_score': round(score, 4) if is_present else None,
                })

            if usable_segments < len(candidates_dict):
                st.info(
                    f"Detected {usable_segments} speech segment(s) for {len(candidates_dict)} "
                    "students with voice profiles — some students may not have spoken clearly enough to be picked up."
                )

            st.session_state.voice_attendance_results = (pd.DataFrame(results), attendance_to_log)

    if st.session_state.get('voice_attendance_results'):
        st.divider()
        df_results, logs = st.session_state.voice_attendance_results
        show_attendance_result(df_results, logs)