"""
StudyOS - Supabase Database Client
Singleton pattern: imports this module anywhere to get the same db client.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None


def get_db() -> Client:
    """Returns a singleton Supabase client instance."""
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise ValueError(
                "❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY in your .env file.\n"
                "Copy .env.example → .env and fill in your credentials."
            )
        _client = create_client(url, key)
    return _client

def save_ingestion_to_db(subject_name: str, chapter_name: str, summary: str, flashcards: list):
    """
    Saves the generated notes and flashcards to Supabase.
    Creates a dummy user/subject if they don't exist (since there's no login yet).
    """
    db = get_db()
    
    # 1. Get or create a User
    users = db.table("users").select("id").limit(1).execute()
    if not users.data:
        user_res = db.table("users").insert({"name": "Student", "email": "student@studyos.com"}).execute()
        user_id = user_res.data[0]["id"]
    else:
        user_id = users.data[0]["id"]

    # 2. Get or create the Subject
    subjects = db.table("subjects").select("id").eq("user_id", user_id).eq("name", subject_name).execute()
    if not subjects.data:
        sub_res = db.table("subjects").insert({
            "user_id": user_id, 
            "name": subject_name,
            "color_hex": "#818cf8"
        }).execute()
        subject_id = sub_res.data[0]["id"]
    else:
        subject_id = subjects.data[0]["id"]

    # 3. Get or create the Chapter and save the notes
    chapters = db.table("chapters").select("id").eq("subject_id", subject_id).eq("name", chapter_name).execute()
    if not chapters.data:
        chap_res = db.table("chapters").insert({
            "subject_id": subject_id,
            "name": chapter_name,
            "notes_url": summary  # Storing the raw markdown text here for Phase 2
        }).execute()
        chapter_id = chap_res.data[0]["id"]
    else:
        chapter_id = chapters.data[0]["id"]
        # Update existing chapter with new notes
        db.table("chapters").update({"notes_url": summary}).eq("id", chapter_id).execute()

    # 4. Save the Flashcards
    cards_to_insert = []
    for card in flashcards:
        cards_to_insert.append({
            "chapter_id": chapter_id,
            "front": card.get("front", ""),
            "back": card.get("back", ""),
            "source": "pdf" # or youtube, but we'll default to pdf for now
        })
    
    if cards_to_insert:
        db.table("flashcards").insert(cards_to_insert).execute()
        
    return True
