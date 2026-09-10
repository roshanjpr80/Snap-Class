import streamlit as st
from PIL import Image

MAX_PHOTOS = 20


@st.dialog("Capture or upload photos")
def add_photos_dialog():
    st.write('Add classroom photos to scan for attendance')

    if 'photo_tab' not in st.session_state:
        st.session_state.photo_tab = 'camera'
    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []
    # These version counters are the fix for the duplicate-photo bug: since
    # Streamlit widgets keep their value across reruns as long as the key
    # doesn't change, we rotate the key after each successful capture/
    # upload so the widget resets to empty on the next run, instead of
    # re-submitting the same photo(s) forever.
    if 'camera_widget_version' not in st.session_state:
        st.session_state.camera_widget_version = 0
    if 'upload_widget_version' not in st.session_state:
        st.session_state.upload_widget_version = 0

    t1, t2 = st.columns(2)

    with t1:
        type_camera = "primary" if st.session_state.photo_tab == 'camera' else 'tertiary'
        if st.button('Camera', type=type_camera, width='stretch'):
            st.session_state.photo_tab = 'camera'

    with t2:
        type_upload = "primary" if st.session_state.photo_tab == 'upload' else 'tertiary'
        if st.button('Upload photos', type=type_upload, width='stretch'):
            st.session_state.photo_tab = 'upload'

    if st.session_state.photo_tab == 'camera':
        cam_key = f'dialog_cam_{st.session_state.camera_widget_version}'
        cam_photo = st.camera_input('Take Snapshot', key=cam_key)

        if cam_photo:
            if len(st.session_state.attendance_images) >= MAX_PHOTOS:
                st.warning(f"You've reached the {MAX_PHOTOS}-photo limit for this session.")
            else:
                try:
                    st.session_state.attendance_images.append(Image.open(cam_photo))
                    st.toast('Photo captured!')
                except Exception:
                    st.error("Couldn't read that photo — please try capturing again.")

            st.session_state.camera_widget_version += 1   # rotates key -> fresh empty widget next run
            st.rerun()

    if st.session_state.photo_tab == 'upload':
        upload_key = f'dialog_upload_{st.session_state.upload_widget_version}'
        uploaded_files = st.file_uploader(
            'Choose image files',
            type=['jpg', 'png', 'jpeg'],
            accept_multiple_files=True,
            key=upload_key,
        )

        if uploaded_files:
            added, skipped = 0, 0
            for f in uploaded_files:
                if len(st.session_state.attendance_images) >= MAX_PHOTOS:
                    skipped += 1
                    continue
                try:
                    st.session_state.attendance_images.append(Image.open(f))
                    added += 1
                except Exception:
                    skipped += 1

            if added:
                st.toast(f'{added} photo(s) uploaded successfully')
            if skipped:
                st.warning(f"{skipped} file(s) were skipped (session limit reached, or unreadable).")

            st.session_state.upload_widget_version += 1   # rotates key -> fresh empty widget next run
            st.rerun()

    if st.session_state.attendance_images:
        st.divider()
        st.write(f"**{len(st.session_state.attendance_images)} photo(s) added**")

        thumb_cols = st.columns(4)
        for idx, img in enumerate(st.session_state.attendance_images):
            with thumb_cols[idx % 4]:
                st.image(img, width='stretch')
                if st.button('Remove', key=f'remove_photo_{idx}', width='stretch', icon=':material/close:'):
                    st.session_state.attendance_images.pop(idx)
                    st.rerun()

    st.divider()
    if st.button('Done', type='primary', width='stretch'):
        st.rerun()