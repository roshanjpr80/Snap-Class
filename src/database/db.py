"""
SnapClass — Database operations (Supabase).

NOTE ON IMPORT PATH: this expects a `supabase` client object importable
from `src.database.config` (the singleton built via get_supabase_client()
in the Supabase client setup file). If you saved that file under a
different path/name, update the import below to match.
"""

from datetime import datetime
import secrets
import string

import bcrypt

from src.database.config import supabase


# ERRORS
class DuplicateEntryError(Exception):
    """Raised when a unique constraint (username, subject_code, enrollment)
    is violated, so calling UI code can show a specific, friendly message
    instead of letting a raw Postgrest/database exception bubble up."""
    pass


# PASSWORD HELPERS
def hash_pass(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()


def check_pass(pwd: str, hashed: str) -> bool:
    return bcrypt.checkpw(pwd.encode(), hashed.encode())


#TEACHER AUTH
def check_teacher_exists(username: str) -> bool:
    """Returns True if the username is already taken."""
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0


def create_teacher(username: str, password: str, name: str, email: str | None = None) -> dict:
    if check_teacher_exists(username):
        raise DuplicateEntryError(f"Username '{username}' is already taken.")

    data = {
        "username": username,
        "password_hash": hash_pass(password),   # matches schema's `password_hash` column
        "name": name,
        "email": email,
    }
    response = supabase.table("teachers").insert(data).execute()
    return response.data


def teacher_login(username: str, password: str) -> dict | None:
    response = supabase.table("teachers").select("*").eq("username", username).execute()
    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher["password_hash"]):
            return teacher
    return None


# STUDENT AUTH
def check_student_exists(username: str) -> bool:
    """Returns True if the username is already taken."""
    response = supabase.table("students").select("username").eq("username", username).execute()
    return len(response.data) > 0


def create_student(
    name: str,
    username: str | None = None,
    password: str | None = None,
    email: str | None = None,
    roll_number: str | None = None,
    face_embedding=None,
    voice_embedding=None,
) -> dict:
    """
    Creates a student account. FaceID is the PRIMARY login method —
    username/password are an OPTIONAL backup credential. If provided, both
    must be provided together.
    """
    if bool(username) != bool(password):
        raise ValueError("Provide both a username and password together, or neither.")

    if username and check_student_exists(username):
        raise DuplicateEntryError(f"Username '{username}' is already taken.")

    data = {
        "name": name,
        "username": username,
        "password_hash": hash_pass(password) if password else None,
        "email": email,
        "roll_number": roll_number,
        "face_embedding": face_embedding,
        "voice_embedding": voice_embedding,
    }
    response = supabase.table("students").insert(data).execute()
    return response.data


def student_login(username: str, password: str) -> dict | None:
    """Backup login path — most students will use FaceID instead. Guards
    against students who never set a password_hash (None), rather than
    crashing on check_pass(password, None)."""
    response = supabase.table("students").select("*").eq("username", username).execute()
    if response.data:
        student = response.data[0]
        if student.get("password_hash") and check_pass(password, student["password_hash"]):
            return student
    return None


def get_student_by_id(student_id: int) -> dict | None:
    """Direct single-row lookup by ID — avoids fetching the entire students
    table just to find one row (previously done client-side in the FaceID
    login flow)."""
    response = supabase.table("students").select("*").eq("student_id", student_id).execute()
    return response.data[0] if response.data else None


def get_all_students() -> list:
    response = supabase.table("students").select("*").execute()
    return response.data


def update_student_embeddings(student_id: int, face_embedding=None, voice_embedding=None) -> dict:
    """Call this after enrollment (face/voice capture) to attach biometric
    data to an already-created student account."""
    data = {}
    if face_embedding is not None:
        data["face_embedding"] = face_embedding
    if voice_embedding is not None:
        data["voice_embedding"] = voice_embedding
    if not data:
        return {}
    response = supabase.table("students").update(data).eq("student_id", student_id).execute()
    return response.data


# SUBJECTS / CLASSES
def generate_subject_code(length: int = 6) -> str:
    """Generates a short, unique-ish, human-typeable join code (e.g. for a
    QR code or shareable link) — uppercase letters + digits, avoiding
    easily-confused characters like 0/O and 1/I."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def check_subject_code_exists(subject_code: str) -> bool:
    response = supabase.table("subjects").select("subject_code").eq("subject_code", subject_code).execute()
    return len(response.data) > 0


def create_subject(name: str, section: str, teacher_id: int, subject_code: str | None = None) -> dict:
    """If subject_code isn't provided, generates one automatically and
    retries on the rare chance of a collision."""
    if subject_code is None:
        subject_code = generate_subject_code()
        while check_subject_code_exists(subject_code):
            subject_code = generate_subject_code()
    elif check_subject_code_exists(subject_code):
        raise DuplicateEntryError(f"Subject code '{subject_code}' is already in use.")

    data = {
        "subject_code": subject_code,
        "name": name,
        "section": section,
        "teacher_id": teacher_id,
    }
    response = supabase.table("subjects").insert(data).execute()
    return response.data


def get_enrolled_students_with_details(subject_id: int) -> list:
    """Returns enrollment rows with full nested student details (name,
    face_embedding, voice_embedding, etc.) for a subject. Shared by both
    the face and voice attendance-taking flows, instead of each writing
    its own identical raw Supabase query."""
    response = (
        supabase.table('subject_students')
        .select("*, students(*)")
        .eq('subject_id', subject_id)
        .execute()
    )
    return response.data


def is_student_enrolled(student_id: int, subject_id: int) -> bool:
    """Quick membership check, used for upfront UI checks (e.g. showing
    'already enrolled' immediately) — separate from the duplicate-guard
    inside enroll_student_to_subject(), which protects against race
    conditions between this check and the actual insert."""
    response = (
        supabase.table("subject_students")
        .select("student_id")
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .execute()
    )
    return len(response.data) > 0


def get_subject_by_code(subject_code: str) -> dict | None:
    """Looks up a subject by its join code (case-insensitive, whitespace-
    tolerant — matches how codes are generated/stored as uppercase)."""
    response = (
        supabase.table("subjects")
        .select("subject_id, name, subject_code")
        .eq("subject_code", subject_code.strip().upper())
        .execute()
    )
    return response.data[0] if response.data else None


def get_teacher_subjects(teacher_id: int) -> list:
    response = (
        supabase.table("subjects")
        .select("*, subject_students(count), attendance_logs(logged_at)")
        .eq("teacher_id", teacher_id)
        .execute()
    )
    subjects = response.data

    for sub in subjects:
        sub["total_students"] = (
            sub.get("subject_students", [{}])[0].get("count", 0) if sub.get("subject_students") else 0
        )

        attendance = sub.get("attendance_logs", [])
        # Group by DATE rather than exact timestamp — two students checking
        # into the same class period will almost never share the exact same
        # second, so grouping by full timestamp wildly overcounts "sessions".
        # (Still an approximation — a dedicated class_sessions table would
        # be the fully correct fix if you add one later.)
        unique_session_dates = {
            _parse_date(log["logged_at"]) for log in attendance if log.get("logged_at")
        }
        sub["total_classes"] = len(unique_session_dates)

        sub.pop("subject_students", None)   # fixed typo: was 'subject_student' (missing 's'), so this never actually removed anything before
        sub.pop("attendance_logs", None)

    return subjects


def _parse_date(timestamp_str: str):
    """Best-effort date-only parse, tolerant of the couple of ISO timestamp
    formats Postgres/PostgREST commonly return."""
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.strptime(timestamp_str, fmt).date()
        except ValueError:
            continue
    return timestamp_str[:10]  # fallback: first 10 chars ("YYYY-MM-DD")


# ENROLLMENT
def enroll_student_to_subject(student_id: int, subject_id: int) -> dict:
    existing = (
        supabase.table("subject_students")
        .select("student_id")
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .execute()
    )
    if existing.data:
        raise DuplicateEntryError("This student is already enrolled in this subject.")

    data = {"student_id": student_id, "subject_id": subject_id}
    response = supabase.table("subject_students").insert(data).execute()
    return response.data


def unenroll_student_to_subject(student_id: int, subject_id: int) -> dict:
    response = (
        supabase.table("subject_students")
        .delete()
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .execute()
    )
    return response.data


def get_student_subjects(student_id: int) -> list:
    response = (
        supabase.table("subject_students")
        .select("*, subjects(*)")
        .eq("student_id", student_id)
        .execute()
    )
    return response.data


# ATTENDANCE
def get_student_attendance(student_id: int) -> list:
    response = (
        supabase.table("attendance_logs")
        .select("*, subjects(*)")
        .eq("student_id", student_id)
        .order("logged_at", desc=True)
        .execute()
    )
    return response.data


def create_attendance(logs) -> list:
    """Bulk insert. `logs` can be a single dict or a list of dicts, each
    matching the attendance_logs schema (subject_id, student_id, is_present,
    method, confidence_score)."""
    response = supabase.table("attendance_logs").insert(logs).execute()
    return response.data


def mark_attendance(
    student_id: int,
    subject_id: int,
    is_present: bool = True,
    method: str = "face",
    confidence_score: float | None = None,
) -> dict:
    """Convenience wrapper for a single check-in event, so calling code
    doesn't have to hand-build the dict every time."""
    log = {
        "student_id": student_id,
        "subject_id": subject_id,
        "is_present": is_present,
        "method": method,
        "confidence_score": confidence_score,
    }
    return create_attendance(log)


def get_attendance_for_teacher(teacher_id: int) -> list:
    response = (
        supabase.table("attendance_logs")
        .select("*, subjects!inner(*)")
        .eq("subjects.teacher_id", teacher_id)
        .order("logged_at", desc=True)
        .execute()
    )
    return response.data