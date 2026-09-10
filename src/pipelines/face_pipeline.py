"""
SnapClass — Face recognition pipeline (InsightFace / ArcFace).

ARCHITECTURE CHANGE from the previous dlib-based version:
1. Engine: dlib + face_recognition_models -> insightface (ArcFace, 512-d
   embeddings), matching what's actually in requirements.txt. dlib-bin is
   Windows-only and breaks Linux/Docker/cloud deployment.
2. Matching strategy: trained SVC classifier -> direct nearest-neighbor
   cosine-similarity comparison. Your data model stores exactly ONE face
   embedding per student (a single JSONB column), and an SVM trained with
   one sample per class has no real within-class variance to learn from.
   Nearest-neighbor matching has no training step to fail, needs no
   retraining when a student is added, and is naturally scoped to just the
   students you pass in — rather than a single global model trained on
   your entire student database regardless of which class is being
   checked.

OPERATIONAL NOTE: the first time load_face_model() runs, insightface
downloads the 'buffalo_l' model pack (~300MB) from the internet. Make sure
your deployment target has internet access on first run, or pre-bake the
model weights into your deployment image if you're on a locked-down host.
"""

import numpy as np
import streamlit as st
from insightface.app import FaceAnalysis

from src.database.db import get_all_students

# Cosine similarity threshold for "same person" — higher = more confident.
# This is a reasonable starting point for the buffalo_l model pack; tune it
# against your own real classroom photos. Raise it if you see false
# positives (wrong student marked present), lower it if real students are
# being marked absent.
MATCH_THRESHOLD = 0.45


@st.cache_resource
def load_face_model() -> FaceAnalysis:
    """Loads the InsightFace model pack once per app process.

    CPU-only (providers=['CPUExecutionProvider'], ctx_id=-1) to match the
    CPU-only onnxruntime pinned in requirements.txt. If you later deploy
    with a GPU, switch to providers=['CUDAExecutionProvider'] and ctx_id=0,
    and swap requirements.txt's onnxruntime for onnxruntime-gpu.
    """
    try:
        app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        app.prepare(ctx_id=-1, det_size=(640, 640))
        return app
    except Exception as exc:
        st.error(
            "Couldn't load the face recognition model. If this is the "
            "first run, it needs internet access to download the model "
            "pack (~300MB)."
        )
        raise RuntimeError("Failed to load InsightFace model") from exc


def get_face_embeddings(image_np: np.ndarray) -> list[np.ndarray]:
    """Detects every face in an image and returns their 512-d, L2-normalized
    ArcFace embeddings (already normalized, so cosine similarity between two
    of these is just their dot product)."""
    app = load_face_model()
    faces = app.get(image_np)
    return [face.normed_embedding for face in faces]


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def get_enrolled_embeddings(enrolled_student_ids: tuple) -> list[dict]:
    """Fetches (student_id, embedding) pairs for the given students only —
    scoping recognition to the class actually being checked, rather than
    your entire student database.

    `enrolled_student_ids` must be a tuple (hashable), not a list.
    """
    all_students = get_all_students()
    id_set = set(enrolled_student_ids)
    known = []
    for student in all_students:
        if student["student_id"] not in id_set:
            continue
        embedding = student.get("face_embedding")
        if embedding:
            known.append({
                "student_id": student["student_id"],
                "embedding": np.array(embedding),
            })
    return known


def train_classifier(*args, **kwargs) -> bool:
    """No-op, kept for backward compatibility.

    The SVC-based classifier this used to (re)train was replaced with
    direct nearest-neighbor matching (see module docstring) — newly
    enrolled students are recognized immediately, with no retraining step.
    Safe to leave existing calls to this in place, or remove them.
    """
    return True


def predict_attendance(class_image_np: np.ndarray, enrolled_student_ids: tuple = None):
    """
    Detects every face in `class_image_np` and matches each against the
    enrolled students' stored embeddings via nearest-neighbor cosine
    similarity.

    Args:
        class_image_np: the classroom photo as a numpy array.
        enrolled_student_ids: tuple of student_ids enrolled in the subject
            being checked, e.g.
                tuple(node['students']['student_id'] for node in enrolled_students)
            in teacher_screen.py. Scopes matching to just that class —
            much faster and more accurate than comparing against every
            student in the whole database. If omitted, falls back to
            matching against every student (only use this if you haven't
            wired up the enrolled-student list at the call site).

    Returns:
        detected_students: dict[int, float] — student_id -> confidence
            score (cosine similarity, higher = more confident) for every
            face that matched an enrolled student above MATCH_THRESHOLD.
            (Same dict-with-truthy-values shape as before, so existing code
            checking `.keys()` or `if detected:` keeps working unchanged.)
        known_student_ids: list[int] — enrolled students who had a usable
            stored embedding to compare against.
        num_faces_detected: int — total faces found in the photo, whether
            or not they matched anyone.
    """
    encodings = get_face_embeddings(class_image_np)

    if enrolled_student_ids is None:
        all_students = get_all_students()
        enrolled_student_ids = tuple(s["student_id"] for s in all_students)

    known = get_enrolled_embeddings(enrolled_student_ids)
    known_student_ids = [k["student_id"] for k in known]

    detected_students = {}
    if not known:
        return detected_students, known_student_ids, len(encodings)

    for encoding in encodings:
        best_student_id = None
        best_score = -1.0
        for entry in known:
            score = _cosine_similarity(encoding, entry["embedding"])
            if score > best_score:
                best_score = score
                best_student_id = entry["student_id"]

        if best_student_id is not None and best_score >= MATCH_THRESHOLD:
            # If two detected faces both best-match the same student
            # (shouldn't normally happen, but photos can be messy), keep
            # whichever match was more confident.
            existing = detected_students.get(best_student_id)
            if existing is None or best_score > existing:
                detected_students[best_student_id] = best_score

    return detected_students, known_student_ids, len(encodings)