"""
StudyOS - Dashboard (The Hub)
Phase 1 MVP: Daily checklist, focus timer, and AI doubt solver.
"""

import time
import streamlit as st

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudyOS | Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark study theme */
    .main { background-color: #0f0f1a; }
    .stApp { background-color: #0f0f1a; color: #e2e8f0; }

    /* Card style */
    .study-card {
        background: linear-gradient(135deg, #1e1e3a 0%, #16213e 100%);
        border: 1px solid #2d2d5e;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }

    /* Timer display */
    .timer-display {
        font-size: 4.5rem;
        font-weight: 700;
        text-align: center;
        color: #818cf8;
        font-family: 'Courier New', monospace;
        letter-spacing: 6px;
    }

    /* Subject pill */
    .subject-pill {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
    }

    /* Progress bar override */
    .stProgress > div > div { background-color: #818cf8; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #12122a; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar Navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=60)
    st.title("StudyOS")
    st.caption("CBSE Class 10 · 2026")
    st.divider()
    st.markdown("**📍 Navigation**")
    st.page_link("pages/1_Dashboard.py",      label="Dashboard",       icon="🏠")
    st.page_link("pages/2_Curriculum.py",     label="Curriculum Vault",icon="📘")
    st.page_link("pages/6_Saved_Notes.py",    label="My Saved Notes",  icon="📚")
    st.page_link("pages/7_PDF_Notes.py",      label="PDF Vault",       icon="📁")
    st.divider()
    st.caption("v0.1.0 · Phase 1 MVP")


# ── Header ─────────────────────────────────────────────────────────────────────
col_title, col_date = st.columns([4, 1])
with col_title:
    st.title("🎓 StudyOS Command Center")
with col_date:
    from datetime import date
    st.metric("Today", date.today().strftime("%d %b %Y"))

st.divider()

# ── Midterm Marathon ───────────────────────────────────────────────────────────
with st.expander("🔥 Midterm Marathon Timetable (Sep 5 - 16)", expanded=True):
    st.markdown("""
| Date | Subject Focus | Chapters / Goals |
| :--- | :--- | :--- |
| **Sep 5-6** | 📐 Maths | Ch 7, 14, 6 (PYQ Practice) |
| **Sep 7** | 📊 Economics | Ch 1, 2 |
| **Sep 8** | 🧬 Biology | Whole Biology Revision |
| **Sep 9** | 🌍 Geography | Whole Geography Revision |
| **Sep 10** | 🏛️ Civics & 📐 Maths | Civics Ch 3 + Start Trigonometry |
| **Sep 11** | 📐 Maths | Trigonometry |
| **Sep 12-13** | 🏛️ Civics & 📐 Maths | Civics Ch 1, 2, 3 and Maths Ch 1, 2, 3 |
| **Sep 14-15** | 🧪 Chem & 📜 History | Chem Ch 1, 2 and History Ch 1, 2 |
| **Sep 16** | ⚡ Physics | Ch 1, 2 |
    """)

# ── Initialize session state ───────────────────────────────────────────────────
if "timer_running"    not in st.session_state: st.session_state.timer_running    = False
if "timer_seconds"    not in st.session_state: st.session_state.timer_seconds    = 25 * 60
if "timer_start"      not in st.session_state: st.session_state.timer_start      = None
if "selected_subject" not in st.session_state: st.session_state.selected_subject = "Mathematics"

# ── Layout: 2 columns ─────────────────────────────────────────────────────────
col_left, col_right = st.columns([5, 4], gap="large")


# ──────────────────────────────────────────────────────────────────────────────
# LEFT COLUMN: Today's Study Plan
# ──────────────────────────────────────────────────────────────────────────────
with col_left:
    st.subheader("📋 Today's Study Plan")
    st.markdown("Your active chapters for today:")
    
    try:
        from services.db import get_db
        db = get_db()
        
        # 1. Show only 'in_progress' chapters
        active_chaps = db.table("chapters").select("*, subjects(name, color_hex)").eq("status", "in_progress").execute()
        
        if not active_chaps.data:
            st.success("Your plan is empty! Search below to add chapters.")
        else:
            total = len(active_chaps.data)
            completed = 0
            st.progress(0, text=f"Daily Progress: 0/{total} tasks done")
            st.markdown("")
            
            for chap in active_chaps.data:
                col_check, col_info, col_del = st.columns([1, 6, 1])
                with col_check:
                    is_done = st.checkbox("", key=f"chap_{chap['id']}", label_visibility="collapsed")
                with col_info:
                    subject_name = chap["subjects"]["name"] if chap.get("subjects") else "General"
                    subject_color = chap["subjects"]["color_hex"] if chap.get("subjects") else "#818cf8"
                    subject_style = f'background-color:{subject_color}22; color:{subject_color}; border:1px solid {subject_color}55'
                    st.markdown(
                        f'<span class="subject-pill" style="{subject_style}">{subject_name}</span> {chap["name"]}',
                        unsafe_allow_html=True,
                    )
                with col_del:
                    if st.button("❌", key=f"del_{chap['id']}", help="Remove from today"):
                        db.table("chapters").update({"status": "not_started"}).eq("id", chap["id"]).execute()
                        st.rerun()
                
                if is_done and chap['status'] != 'completed':
                    db.table("chapters").update({"status": "completed"}).eq("id", chap["id"]).execute()
                    st.rerun()

        st.markdown("---")
        st.subheader("🔍 Search & Add")
        search_q = st.text_input("Find chapters (e.g. '#physics light')", placeholder="#science, #history, or chapter name...")
        
        if search_q.strip():
            # Fetch all incomplete chapters
            all_chaps = db.table("chapters").select("*, subjects(name, color_hex)").eq("status", "not_started").execute()
            results = []
            
            query_lower = search_q.lower()
            # Extract hashtags if any
            tags = [word[1:] for word in query_lower.split() if word.startswith('#')]
            keywords = [word for word in query_lower.split() if not word.startswith('#')]
            
            for c in all_chaps.data:
                s_name = c["subjects"]["name"].lower() if c.get("subjects") else ""
                c_name = c["name"].lower()
                
                # Check tags (must match subject)
                if tags and not any(t in s_name for t in tags):
                    continue
                # Check keywords (must match chapter name)
                if keywords and not any(k in c_name for k in keywords):
                    continue
                results.append(c)
                
            if not results:
                st.caption("No CBSE chapters found.")
            else:
                for res in results[:5]:  # Show top 5 results
                    c1, c2 = st.columns([5, 1])
                    sub_color = res["subjects"]["color_hex"] if res.get("subjects") else "#ffffff"
                    c1.markdown(f"<span style='color:{sub_color}'>**{res['subjects']['name']}**</span>: {res['name']}", unsafe_allow_html=True)
                    if c2.button("➕ Add", key=f"add_{res['id']}"):
                        db.table("chapters").update({"status": "in_progress"}).eq("id", res["id"]).execute()
                        st.rerun()
            
        st.markdown("---")
        st.markdown("---")
        st.markdown("**Add Custom Topic & Schedule**")
        
        custom_q = st.text_input("Custom Topic", label_visibility="collapsed", placeholder="e.g. Calculus Basics, Mitochondria")
        col_date, col_time = st.columns(2)
        with col_date:
            sched_date = st.date_input("Date")
        with col_time:
            sched_time = st.time_input("Time", value=None)
            
        if st.button("➕ Create & Add to Plan", use_container_width=True):
            if custom_q.strip():
                uid = db.table("users").select("id").limit(1).execute().data[0]['id']
                subs = db.table("subjects").select("id").eq("name", "Custom Topics").execute()
                if subs.data:
                    sub_id = subs.data[0]['id']
                else:
                    res = db.table("subjects").insert({"name": "Custom Topics", "user_id": uid, "color_hex": "#9ca3af"}).execute()
                    sub_id = res.data[0]['id']
                
                # We save it. Assuming the user has added 'scheduled_for' in Supabase!
                try:
                    dt_str = f"{sched_date}T{sched_time if sched_time else '00:00:00'}"
                    db.table("chapters").insert({
                        "subject_id": sub_id, 
                        "name": custom_q.strip(), 
                        "status": "in_progress",
                        "scheduled_for": dt_str
                    }).execute()
                except:
                    # Fallback if they haven't run the SQL migration yet
                    db.table("chapters").insert({"subject_id": sub_id, "name": custom_q.strip(), "status": "in_progress"}).execute()
                
                # Generate Google Calendar link
                import urllib.parse
                text = urllib.parse.quote(custom_q.strip())
                if sched_time:
                    # Formatting for GCal: YYYYMMDDTHHMMSSZ
                    d1 = sched_date.strftime("%Y%m%d")
                    t1 = sched_time.strftime("%H%M%S")
                    dates = f"{d1}T{t1}/{d1}T{t1}"
                    gcal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={text}&dates={dates}"
                    st.success(f"Added! [Click here to add to Google Calendar]({gcal_url})")
                else:
                    st.success("Added to your Study Plan!")
                
                time.sleep(2)
                st.rerun()
            
    except Exception as e:
        st.error(f"Could not load plan: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# RIGHT COLUMN: Focus Timer (Pomodoro)
# ──────────────────────────────────────────────────────────────────────────────
with col_right:
    st.subheader("⏱️ Focus Timer")

    # Timer preset selection
    preset_col1, preset_col2, preset_col3 = st.columns(3)
    with preset_col1:
        if st.button("🍅 25 min", use_container_width=True):
            st.session_state.timer_seconds = 25 * 60
            st.session_state.timer_running = False
    with preset_col2:
        if st.button("📖 45 min", use_container_width=True):
            st.session_state.timer_seconds = 45 * 60
            st.session_state.timer_running = False
    with preset_col3:
        if st.button("☕ 5 min", use_container_width=True):
            st.session_state.timer_seconds = 5 * 60
            st.session_state.timer_running = False

    # Subject selector for the session
    st.session_state.selected_subject = st.selectbox(
        "Studying:", ["Mathematics", "Science", "SST", "English", "Hindi"],
        index=0, key="subject_select"
    )

    # Timer display
    secs = st.session_state.timer_seconds
    mins_display = secs // 60
    secs_display = secs % 60
    timer_placeholder = st.empty()
    timer_placeholder.markdown(
        f'<div class="timer-display">{mins_display:02d}:{secs_display:02d}</div>',
        unsafe_allow_html=True,
    )

    # Ring progress
    pct = 1 - (secs / (25 * 60))   # rough progress for default 25 min
    st.progress(min(pct, 1.0), text="Session progress")

    # Controls
    ctrl1, ctrl2, ctrl3 = st.columns(3)
    with ctrl1:
        if st.button("▶ Start", use_container_width=True, type="primary"):
            st.session_state.timer_running = True
            st.session_state.timer_start   = time.time()
    with ctrl2:
        if st.button("⏸ Pause", use_container_width=True):
            st.session_state.timer_running = False
    with ctrl3:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.timer_running = False
            st.session_state.timer_seconds = 25 * 60

    # Countdown tick (re-runs every second while timer is active)
    if st.session_state.timer_running and st.session_state.timer_seconds > 0:
        time.sleep(1)
        st.session_state.timer_seconds -= 1
        st.rerun()
    elif st.session_state.timer_running and st.session_state.timer_seconds == 0:
        st.session_state.timer_running = False
        st.balloons()
        st.success(f"🎉 Session complete! Great work on **{st.session_state.selected_subject}**.")

    st.markdown("---")
