"""
SnapClass — Voice recognition pipeline (Resemblyzer-based speaker verification).

Used as a secondary/backup verification factor alongside face recognition,
and for the standalone voice-attendance flow.

SECURITY NOTE: like the face pipeline, there's no anti-spoofing check here —
a played-back recording of a student's voice would currently pass
verification. Worth addressing alongside the face-liveness work.
"""

import io

import librosa
import numpy as np
import streamlit as st
import structlog
from resemblyzer import VoiceEncoder, preprocess_wav

logger = structlog.get_logger(__name__)

TARGET_SR = 16000
MIN_SEGMENT_SECONDS = 0.5

# Cosine similarity threshold for "same speaker" — higher = more confident.
# Voice is generally noisier than face matching (background noise, mic
# quality), so treat this as a starting point and tune it against real
# recordings from your actual deployment environment.
DEFAULT_MATCH_THRESHOLD = 0.65


@st.cache_resource
def load_voice_encoder() -> VoiceEncoder:
    return VoiceEncoder()


def _cosine_similarity(a, b) -> float:
    """Explicit cosine similarity rather than a raw dot product.
    Resemblyzer's embed_utterance() already returns L2-normalized
    embeddings (so a plain dot product ≈ cosine similarity today), but
    computing it explicitly protects against a future Resemblyzer version
    changing that, or an embedding drifting from unit norm after a DB
    round-trip — cheap insurance, same pattern used in face_pipeline.py."""
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def get_voice_embedding(audio_bytes: bytes):
    """Extracts a single voice embedding from one audio clip — used for
    enrollment (a student recording their passphrase) and single-shot
    identification. Returns a plain list (JSON/JSONB-storable), or None on
    failure."""
    try:
        encoder = load_voice_encoder()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=TARGET_SR)

        if len(audio) < sr * MIN_SEGMENT_SECONDS:
            st.error("Recording is too short — please record at least half a second of clear speech.")
            return None

        wav = preprocess_wav(audio, source_sr=sr)
        embedding = encoder.embed_utterance(wav)
        return embedding.tolist()

    except Exception as exc:
        logger.error("voice_embedding_failed", error=str(exc))
        st.error("Couldn't process that recording — please try again with a clearer clip.")
        return None


def identify_speaker(new_embedding, candidates_dict: dict, threshold: float = DEFAULT_MATCH_THRESHOLD):
    """Matches one embedding against {student_id: stored_embedding}.
    Returns (student_id, confidence) if above threshold, else
    (None, best_score_found) so callers can still see how close the
    nearest (rejected) match was — useful for debugging borderline cases."""
    if new_embedding is None or not candidates_dict:
        return None, 0.0

    best_sid = None
    best_score = -1.0
    for sid, stored_embedding in candidates_dict.items():
        if not stored_embedding:
            continue
        similarity = _cosine_similarity(new_embedding, stored_embedding)
        if similarity > best_score:
            best_score = similarity
            best_sid = sid

    if best_score >= threshold:
        return best_sid, best_score

    return None, best_score


def process_bulk_audio(audio_bytes: bytes, candidates_dict: dict, threshold: float = DEFAULT_MATCH_THRESHOLD):
    """Splits one longer recording (e.g. a class saying their names in turn)
    into speech segments and identifies the speaker of each.

    Returns:
        identified_results: dict[student_id, confidence] — best match per
            student found across all segments.
        usable_segments: int — how many speech segments were long enough to
            process, regardless of whether they matched anyone. Lets the
            caller distinguish "no one spoke" (0 segments) from "people
            spoke but didn't match anyone enrolled" (segments > 0, empty
            results).

    NOTE: this is a changed return signature — previously returned just
    identified_results. Any caller must be updated to unpack two values.
    """
    try:
        encoder = load_voice_encoder()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=TARGET_SR)
        segments = librosa.effects.split(audio, top_db=30)

        identified_results = {}
        usable_segments = 0

        for start, end in segments:
            if (end - start) < sr * MIN_SEGMENT_SECONDS:
                continue
            usable_segments += 1

            segment_audio = audio[start:end]
            wav = preprocess_wav(segment_audio, source_sr=sr)
            embedding = encoder.embed_utterance(wav)
            sid, score = identify_speaker(embedding, candidates_dict, threshold)

            if sid:
                if sid not in identified_results or score > identified_results[sid]:
                    identified_results[sid] = score

        return identified_results, usable_segments

    except Exception as exc:
        logger.error("bulk_voice_processing_failed", error=str(exc))
        st.error("Couldn't process that recording — please try again.")
        return {}, 0