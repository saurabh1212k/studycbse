"""
StudyOS - Saved Notes Repository
View all AI-generated notes saved from PDFs and YouTube videos.
"""

import streamlit as st

st.set_page_config(page_title="StudyOS | Saved Notes", page_icon="📚", layout="wide")

st.title("📚 My Saved Notes")
st.caption("Access all your AI-generated summaries and study materials.")
st.divider()

try:
    from services.db import get_db
    db = get_db()
    
    # Fetch all chapters that have notes saved
    # We use .not_("notes_url", "is", "null") or just filter in python if postgrest syntax is tricky
    res = db.table("chapters").select("id, name, notes_url, subjects(name, color_hex)").execute()
    
    # Filter only chapters with actual notes
    chapters_with_notes = [c for c in res.data if c.get("notes_url") and str(c["notes_url"]).strip() != ""]
    
    if not chapters_with_notes:
        st.info("You haven't saved any notes yet! Go to the ⚡ Ingestion Engine to upload a PDF or YouTube link.")
    else:
        # Create a layout with a sidebar list and a main viewing area
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("Chapters")
            selected_chap_id = None
            
            # Group by subject visually
            subjects = {}
            for chap in chapters_with_notes:
                sub_name = chap["subjects"]["name"] if chap.get("subjects") else "Uncategorized"
                if sub_name not in subjects:
                    subjects[sub_name] = []
                subjects[sub_name].append(chap)
                
            # Create a selection menu
            for sub_name, chaps in subjects.items():
                st.markdown(f"**{sub_name}**")
                for chap in chaps:
                    if st.button(f"📄 {chap['name']}", key=f"btn_{chap['id']}", use_container_width=True):
                        st.session_state.viewing_note_id = chap['id']
                        
        with col2:
            st.subheader("Note Viewer")
            view_id = st.session_state.get("viewing_note_id")
            
            if not view_id:
                st.write("👈 Select a chapter from the left to view your notes.")
            else:
                # Find the selected chapter data
                selected_chap = next((c for c in chapters_with_notes if c["id"] == view_id), None)
                if selected_chap:
                    color = selected_chap["subjects"]["color_hex"] if selected_chap.get("subjects") else "#ffffff"
                    st.markdown(f"<h2 style='color: {color};'>{selected_chap['name']} Notes</h2>", unsafe_allow_html=True)
                    st.divider()
                    
                    # Display the markdown notes
                    st.markdown(selected_chap["notes_url"])
                
except Exception as e:
    st.error(f"Could not load notes: {e}")
