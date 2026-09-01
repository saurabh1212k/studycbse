"""
StudyOS - Curriculum Tracker (Phase 7)
"""

import streamlit as st
import pandas as pd
from services.db import get_db

st.set_page_config(page_title="StudyOS | Curriculum", page_icon="📘", layout="wide")

st.title("📘 Curriculum Tracker")
st.caption("Your master syllabus tracker. Check the boxes to update your progress.")
st.divider()

db = get_db()

# 1. Sidebar - Select Subject
try:
    subs_res = db.table("subjects").select("id, name, color_hex").execute()
    if not subs_res.data:
        st.warning("No subjects found. Use the Ingestion Engine to create subjects.")
        st.stop()
        
    subject_names = {s["name"]: s for s in subs_res.data}
    selected_sub_name = st.sidebar.selectbox("Select Subject", list(subject_names.keys()))
    selected_sub = subject_names[selected_sub_name]
    
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

st.markdown(f"### <span style='color:{selected_sub['color_hex']}'>{selected_sub_name}</span> Chapters", unsafe_allow_html=True)

# 2. Fetch Chapters
chaps_res = db.table("chapters").select("id, name, status").eq("subject_id", selected_sub["id"]).order("id").execute()

if not chaps_res.data:
    st.info("No chapters found for this subject.")
else:
    # Build the dataframe
    data = []
    for c in chaps_res.data:
        data.append({
            "_id": c["id"],
            "Chapter Name": c["name"],
            "Not Done": c["status"] == "not_started",
            "Nearly Done": c["status"] == "in_progress",
            "Completed": c["status"] == "completed"
        })
        
    df = pd.DataFrame(data)
    
    # Store original state to detect exactly which box was clicked
    if "prev_df" not in st.session_state or st.session_state.get("last_sub") != selected_sub["id"]:
        st.session_state.prev_df = df.copy()
        st.session_state.last_sub = selected_sub["id"]
        
    # 3. Render Data Editor with Checkboxes
    edited_df = st.data_editor(
        df[["Chapter Name", "Not Done", "Nearly Done", "Completed"]],
        column_config={
            "Chapter Name": st.column_config.TextColumn(disabled=True, width="large"),
            "Not Done": st.column_config.CheckboxColumn("Not Done", default=False),
            "Nearly Done": st.column_config.CheckboxColumn("Nearly Done", default=False),
            "Completed": st.column_config.CheckboxColumn("Completed", default=False),
        },
        hide_index=True,
        use_container_width=True,
        key=f"editor_{selected_sub['id']}"
    )
    
    # 4. Detect Checkbox Changes
    changed = False
    for i in range(len(edited_df)):
        orig_row = st.session_state.prev_df.iloc[i]
        new_row = edited_df.iloc[i]
        chap_id = df.iloc[i]["_id"]
        
        # If user checked 'Not Done'
        if new_row["Not Done"] and not orig_row["Not Done"]:
            db.table("chapters").update({"status": "not_started"}).eq("id", chap_id).execute()
            changed = True
        # If user checked 'Nearly Done'
        elif new_row["Nearly Done"] and not orig_row["Nearly Done"]:
            db.table("chapters").update({"status": "in_progress"}).eq("id", chap_id).execute()
            changed = True
        # If user checked 'Completed'
        elif new_row["Completed"] and not orig_row["Completed"]:
            db.table("chapters").update({"status": "completed"}).eq("id", chap_id).execute()
            changed = True
            
    if changed:
        # Update session state and rerun to reflect mutually exclusive radio-like behavior
        st.session_state.prev_df = df.copy()
        st.rerun()

# 5. Legend Box
st.markdown("---")
st.markdown("""
<div style="background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155;">
    <h4>📋 Tracker Guide</h4>
    <ul style="list-style-type: none; padding-left: 0;">
        <li>✅ <b>Completed:</b> PYQs + Total chapter revision done.</li>
        <li>⏳ <b>Nearly Done:</b> Chapter done, PYQs left.</li>
        <li>❌ <b>Not Done:</b> Nothing done.</li>
    </ul>
</div>
""", unsafe_allow_html=True)
