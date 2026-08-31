"""
StudyOS - Curriculum Vault (Phase 4)
Complete CBSE syllabus browser with web extraction for Notes, PYQs, and Extra Questions.
"""

import streamlit as st
from services.db import get_db
from services.web_extractor import scrape_notes_from_url, generate_extra_questions

st.set_page_config(page_title="StudyOS | Curriculum Vault", page_icon="📘", layout="wide")

st.title("📘 Curriculum Vault")
st.caption("Your complete CBSE Class 10 Syllabus, Notes, and PYQ Repository.")
st.divider()

db = get_db()

# 1. Fetch Subjects
try:
    subs_res = db.table("subjects").select("*").execute()
    subjects = subs_res.data
except Exception as e:
    st.error(f"Could not load database. Did you run the SQL migration? Error: {e}")
    st.stop()

if not subjects:
    st.info("No subjects found in the database. Please run the `phase4_migration.sql` script in Supabase.")
    st.stop()

# 2. UI Layout
col_sidebar, col_main = st.columns([1, 3])

with col_sidebar:
    st.subheader("📚 Subjects")
    selected_sub_name = st.selectbox("Select Subject", [s["name"] for s in subjects])
    selected_sub = next(s for s in subjects if s["name"] == selected_sub_name)
    
    st.markdown("---")
    st.subheader("📖 Chapters")
    
    # Fetch chapters for selected subject
    chaps_res = db.table("chapters").select("*").eq("subject_id", selected_sub["id"]).execute()
    chapters = chaps_res.data
    
    if not chapters:
        st.warning("No chapters found for this subject.")
        st.stop()
        
    selected_chap_name = st.radio("Select Chapter", [c["name"] for c in chapters])
    selected_chap = next(c for c in chapters if c["name"] == selected_chap_name)

# 3. Main Viewing Area (Tabs)
with col_main:
    st.markdown(f"## {selected_chap['name']}")
    
    # ── Chapter Content ──
    if selected_chap.get("notes_url"):
        st.subheader("📝 Saved Notes")
        st.markdown(selected_chap["notes_url"])
    else:
        st.info("No notes saved for this chapter yet. Use the Ingestion Engine to generate notes from YouTube videos or PDFs!")
