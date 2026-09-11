# Snap Class — AI-Powered Attendance System

**Live: [snap-class-attendance-ai-v2.streamlit.app](https://snap-class-attendance-ai-v2.streamlit.app/)**

Attendance in seconds, verified with AI face and voice recognition. Built for teachers and students who are tired of manual roll-calls and proxy attendance.

---

## Features

- **FaceID login for students** — no password needed day-to-day; show your face, you're in
- **Optional backup login** — username/password for when a camera isn't available, plus optional voice enrollment
- **AI attendance from classroom photos** — teachers snap or upload photos, InsightFace (ArcFace) matches every enrolled student via direct embedding comparison
- **Voice attendance** — students say "I am present," verified by speaker recognition (Resemblyzer)
- **Join-code enrollment** — a short code, a shareable link, or a QR code — teacher's choice
- **Teacher dashboard** — take attendance, manage subjects, review attendance history and stats
- **Student dashboard** — enrolled subjects, personal attendance record, one-tap unenroll
- **Auditable attendance logs** — every entry records _how_ it was marked (face / voice / manual) and the model's confidence score

---

## Tech Stack

| Layer             | Technology                                            |
| ----------------- | ----------------------------------------------------- |
| App / UI          | Streamlit                                             |
| Hosting           | Streamlit Community Cloud                             |
| Database          | Supabase (PostgreSQL)                                 |
| Face recognition  | InsightFace (ArcFace, 512-d embeddings) + onnxruntime |
| Voice recognition | Resemblyzer + librosa                                 |
| Auth              | bcrypt password hashing                               |
| QR codes          | segno                                                 |

Trimmed to exactly what the codebase imports — see [`requirements.txt`](./requirements.txt) for the full list, version pins, and notes on why each one's there.

**Python version: 3.11** — both locally and in the deployed app's settings. InsightFace doesn't ship prebuilt wheels past 3.12, and 3.13+ forces it to compile from source, which needs a full C++ toolchain. Keeping local and deployed versions identical avoids "works on my machine" surprises.

---

## Project Structure

```
snapclass/
├── app.py                     # Entry point — routing, session state, join-code deep links
├── requirements.txt
├── .gitignore
├── schema.sql                 # Supabase/PostgreSQL schema (run once in Supabase's SQL editor)
├── .streamlit/
│   └── secrets.toml            # Supabase URL/keys, APP_BASE_URL — never committed
│
├── src/
│   ├── database/
│   │   ├── config.py           # Supabase client setup (cached, reads st.secrets)
│   │   └── db.py                # Every database read/write goes through here
│   │
│   ├── ui/
│   │   └── base_layout.py      # Shared CSS: colors, fonts, buttons, cards (single source of design tokens)
│   │
│   ├── components/
│   │   ├── header.py            # Logo/title header (home + dashboard, with optional personalized greeting)
│   │   ├── footer.py            # Shared footer + credits
│   │   ├── dialog_to_top.py    # Floating "back to top" button (appears after scrolling)
│   │   ├── subject_card.py     # Subject/class card UI
│   │   ├── dialog_create_subject.py   # Create a subject, auto-generates a join code
│   │   ├── dialog_share_subject.py    # QR code + WhatsApp/email share links
│   │   ├── dialog_enroll.py           # Manual join-code entry
│   │   ├── dialog_auto_enroll.py      # One-tap enrollment via a deep link
│   │   ├── dialog_add_photo.py        # Camera/upload capture for attendance
│   │   ├── dialog_attendance_results.py  # Review + confirm before saving
│   │   └── dialog_voice_attendance.py
│   │
│   ├── screens/
│   │   ├── home_screen.py      # Landing page — choose Student or Teacher
│   │   ├── teacher_screen.py   # Login/register + full teacher dashboard
│   │   └── student_screen.py   # FaceID login/register + student dashboard
│   │
│   └── pipelines/
│       ├── face_pipeline.py    # Face detection + nearest-neighbor cosine-similarity matching
│       └── voice_pipeline.py   # Speaker embedding + verification
```

---

## Running It Yourself

### 1. Clone and set up a Python 3.11 environment

```bash
git clone <your-repo-url>
cd snapclass

py -3.11 -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate   # macOS/Linux
```

### 2. Windows only: install a C++ compiler first

`insightface` needs to compile part of its code from source on Windows. Before installing anything:

1. Download [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. In the installer, check **"Desktop development with C++"**
3. Restart your terminal after install finishes

### 3. Install dependencies

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### 4. Set up Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Open the SQL editor and run [`schema.sql`](./schema.sql)
3. Grab your project URL and **secret key** (Settings → API)

### 5. Configure secrets

Create `.streamlit/secrets.toml` (already in `.gitignore` — never commit this):

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_SECRET_KEY = "your-secret-key"
APP_BASE_URL = "http://localhost:8501"
```

### 6. Run it

```bash
streamlit run app.py
```

First run downloads the InsightFace model pack (~300MB) — make sure you have internet access.

---

## Deploying Your Own Copy

This project is live on Streamlit Community Cloud — here's how to deploy your own instance:

1. Push your repo to GitHub (`.streamlit/secrets.toml` must **not** be included — check `.gitignore`)
2. Sign in at [share.streamlit.io](https://share.streamlit.io) with GitHub
3. **Create app** → **"Yup, I have an app"** → fill in repo, branch, and `app.py` as the main file path
4. Choose an **App URL** subdomain — lowercase letters, numbers, and hyphens only, and it must be globally unique (add your name or a number if your first choice is taken)
5. In **Advanced settings**: set **Python version to 3.11**, and paste your `secrets.toml` contents into the Secrets box, with `APP_BASE_URL` matching the exact subdomain you just chose
6. Click **Deploy** — expect several minutes given the ML dependencies

**If the install fails:** click "Manage app" to view the full build log. A failure partway through can prevent _later_ packages in `requirements.txt` from installing too, even ones with nothing wrong with them individually — always check the first error in the log, not just the last one reported.

---

## Security Notes

- Row Level Security is enabled on every table in `schema.sql`, but the actual policies are placeholders — write real ones matching your auth flow before public use.
- Face/voice data is biometric data, likely belonging to minors — get real consent flows and a privacy policy in place before any public launch.
- **Liveness/anti-spoofing is not yet implemented**, for either face or voice. A printed photo or a played-back recording currently passes verification. This is the single highest-priority item before relying on this beyond a supervised classroom pilot.
- If any secret key was ever exposed somewhere it shouldn't have been, rotate it in Supabase's dashboard — treat it as compromised regardless of where it appeared.

---

## Known Limitations / Roadmap

- [ ] Liveness/anti-spoofing for face and voice
- [ ] Multiple face embeddings per student (currently one, limiting robustness across lighting/angles)
- [ ] Real RLS policies (currently enabled but unpopulated)
- [ ] A proper `class_sessions` table (attendance "sessions" are currently approximated by grouping on date)
- [ ] Multi-tenant isolation for scaling across many schools

See [`PROJECT_WALKTHROUGH.md`](./PROJECT_WALKTHROUGH.md) for a full explanation of how every file connects and why key design decisions were made.

---

## License

Add your license of choice here (MIT is a common default for a project like this).
