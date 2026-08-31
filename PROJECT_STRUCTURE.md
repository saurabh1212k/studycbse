# StudyOS Project Structure
studycbse/
│
├── app.py                   # Main Streamlit entry point
├── requirements.txt
├── .env.example             # Copy to .env and add your keys
├── .gitignore
│
├── services/                # Backend logic modules
│   ├── __init__.py
│   ├── db.py                # Supabase client singleton
│   ├── gemini_service.py    # All Gemini API calls
│   ├── srs_engine.py        # SM-2 Spaced Repetition
│   └── ingestion.py         # YouTube + PDF pipeline (Phase 2)
│
└── pages/                   # Streamlit multi-page app
    ├── 1_Dashboard.py       # Hub: daily plan + timer
    ├── 2_Flashcards.py      # SRS flashcard review
    ├── 3_Ingestion.py       # Drop YouTube / PDF (Phase 2)
    ├── 4_Testing_Ground.py  # PYQ practice + grader (Phase 3)
    └── 5_Analytics.py       # Progress charts (Phase 3)
