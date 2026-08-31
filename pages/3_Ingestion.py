"""
StudyOS - Ingestion Engine Page (Phase 2)
Drop a YouTube link or PDF → get AI notes + flashcards.
"""

import streamlit as st
from services.ingestion import process_youtube_video, process_pdf

st.set_page_config(page_title="StudyOS | Ingestion", page_icon="⚡", layout="wide")

st.title("⚡ Ingestion Engine")
st.caption("Drop a YouTube link or PDF → AI generates notes + flashcards automatically")
st.divider()

if "ingestion_result" not in st.session_state:
    st.session_state.ingestion_result = None

col1, col2 = st.columns(2)

with col1:
    st.subheader("📺 YouTube Ingestion")
    yt_url = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    chapter_name = st.text_input("Chapter Name", placeholder="e.g., Chemical Reactions & Equations", key="yt_chap")
    
    if st.button("⚡ Process Video", use_container_width=True, type="primary"):
        if not yt_url or not chapter_name:
            st.warning("Please provide both URL and Chapter Name.")
        else:
            with st.spinner("Downloading transcript and generating AI notes..."):
                try:
                    result = process_youtube_video(yt_url, chapter_name)
                    st.session_state.ingestion_result = result
                    st.session_state.last_chapter_name = chapter_name
                    st.success("Successfully generated notes and flashcards!")
                except Exception as e:
                    st.error(f"Error: {e}")

with col2:
    st.subheader("📄 PDF Ingestion")
    uploaded_file = st.file_uploader("Upload PDF File", type=["pdf"])
    chapter_name_pdf = st.text_input("Chapter Name", placeholder="e.g., Nationalism in India", key="pdf_chap")
    
    if st.button("⚡ Process PDF", use_container_width=True, type="primary"):
        if not uploaded_file or not chapter_name_pdf:
            st.warning("Please provide both a PDF and Chapter Name.")
        else:
            with st.spinner("Extracting text and generating AI notes..."):
                try:
                    result = process_pdf(uploaded_file, chapter_name_pdf)
                    st.session_state.ingestion_result = result
                    st.session_state.last_chapter_name = chapter_name_pdf
                    st.success("Successfully generated notes and flashcards!")
                except Exception as e:
                    st.error(f"Error: {e}")

st.divider()

if st.session_state.ingestion_result:
    res = st.session_state.ingestion_result
    st.subheader("📝 Generated Notes")
    st.markdown(res["summary"])
    st.divider()
    st.subheader("💾 Save to Database")
    
    try:
        from services.db import get_db
        db = get_db()
        subs_res = db.table("subjects").select("name").execute()
        sub_list = [s["name"] for s in subs_res.data] if subs_res.data else ["General"]
    except:
        sub_list = ["General"]
    
    save_subject = st.selectbox("Select Subject to save under:", sub_list)
    
    if st.button("Save Notes", type="primary"):
        with st.spinner("Saving to Supabase..."):
            try:
                from services.db import save_ingestion_to_db
                # Assume the chapter name was saved in session state when processing
                save_chap_name = st.session_state.get("last_chapter_name", "Untitled Chapter")
                
                save_ingestion_to_db(
                    subject_name=save_subject,
                    chapter_name=save_chap_name,
                    summary=res["summary"],
                    flashcards=[]
                )
                st.success("✅ Successfully saved to Supabase! You can now review these in your Curriculum Vault or Saved Notes.")
            except Exception as e:
                st.error(f"Database Error: {e}")
