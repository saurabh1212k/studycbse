# 🎓 StudyOS — CBSE Class 10 AI Study Ecosystem

> An all-in-one AI productivity hub powered by **Gemini**, **Supabase**, and **Streamlit**.

---

## 📦 Project Structure

```
studycbse/
├── app.py                   ← Main entry point
├── requirements.txt         ← All dependencies
├── .env.example             ← Copy → .env and fill your keys
├── supabase_schema.sql      ← Paste this in Supabase SQL Editor
├── PROJECT_STRUCTURE.md
├── .gitignore
│
├── services/
│   ├── db.py                ← Supabase client
│   ├── gemini_service.py    ← All AI calls (doubt, grading, summarization)
│   └── srs_engine.py        ← SM-2 Spaced Repetition Algorithm
│
└── pages/
    ├── 1_Dashboard.py       ← Hub: study plan, timer, doubts
    ├── 2_Flashcards.py      ← SM-2 flashcard review
    ├── 3_Ingestion.py       ← YouTube/PDF → notes (Phase 2)
    ├── 4_Testing_Ground.py  ← PYQ grader (Phase 3)
    └── 5_Analytics.py       ← Progress charts
```

---

## 🚀 First-Time Setup

### Step 1 — Install Python
If `python --version` doesn't work, download and install Python 3.11+ from:
👉 **https://www.python.org/downloads/**

> ⚠️ During installation, check **"Add Python to PATH"** — this is critical!

After installing, **close and reopen** PowerShell, then verify:
```powershell
python --version
# Expected: Python 3.11.x or higher
```

---

### Step 2 — Create & Activate Virtual Environment
```powershell
# Navigate to project folder
cd C:\Users\Saura\Downloads\studycbse

# Create virtual environment
python -m venv venv

# Activate it (do this every time you open a new terminal)
venv\Scripts\Activate.ps1
```

If you get a "running scripts is disabled" error, run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Step 3 — Install Dependencies
```powershell
pip install -r requirements.txt
```

This installs: Streamlit, Supabase, Gemini SDK, Plotly, and all other packages.

---

### Step 4 — Get Your API Keys

| Service | Where to get it | Free tier? |
|---|---|---|
| **Gemini API** | https://aistudio.google.com/apikey | ✅ Yes |
| **Supabase** | https://supabase.com → New Project | ✅ Yes (500MB) |

---

### Step 5 — Configure Environment
```powershell
# Copy the example file
copy .env.example .env
```

Open `.env` in Notepad and fill in your actual keys:
```
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
GEMINI_API_KEY=AIzaSy...
```

---

### Step 6 — Set Up Supabase Database
1. Go to your Supabase project → **SQL Editor** → **New Query**
2. Copy and paste the entire contents of [`supabase_schema.sql`](supabase_schema.sql)
3. Click **Run** — all 7 tables will be created

---

### Step 7 — Launch StudyOS! 🚀
```powershell
streamlit run app.py
```

Your browser will open automatically at **http://localhost:8501**

---

## 🛣️ Development Roadmap

| Phase | Features | Status |
|---|---|---|
| **Phase 1** (Weeks 1–3) | Dashboard, Focus Timer, Doubt Solver, Flashcards | ✅ Built |
| **Phase 2** (Weeks 4–6) | YouTube/PDF Ingestion, Auto-flashcard generation | 🔧 Next |
| **Phase 3** (Weeks 7–10) | PYQ Practice, Step-Marking Grader, SRS Analytics | 📋 Planned |
| **Phase 4** (Weeks 11–14) | n8n Automation, Google Calendar, Site Blocker | 📋 Planned |

---

## 🔑 Environment Variables Reference

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anonymous API key |
| `GEMINI_API_KEY` | Google Gemini API key |
| `N8N_WEBHOOK_URL` | n8n webhook URL (Phase 4 only) |

---

## ⚠️ Important Security Rules
1. **Never** commit your `.env` file to Git (it's in `.gitignore`)
2. **Never** share your API keys with anyone
3. Use Supabase Row Level Security (RLS) when you add multi-user support
