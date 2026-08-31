import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.db import get_db

db = get_db()

def split_languages():
    print("Fetching user...")
    users = db.table('users').select('id').limit(1).execute()
    if not users.data:
        print("No users found.")
        return
    user_id = users.data[0]['id']

    # 1. Delete old umbrella subjects
    print("Removing old English and Hindi subjects...")
    db.table('subjects').delete().eq('name', 'English').execute()
    db.table('subjects').delete().eq('name', 'Hindi').execute()

    # 2. Add the new divided subjects with distinct colors
    new_subjects = {
        "Eng: First Flight": "#8b5cf6",          # Purple
        "Eng: Footprints Without Feet": "#a855f7", # Lighter Purple
        "Hindi: Kshitij": "#ec4899",             # Pink
        "Hindi: Kritika": "#f472b6"              # Lighter Pink
    }
    
    sub_map = {}
    for sub_name, color in new_subjects.items():
        existing = db.table('subjects').select('id').eq('name', sub_name).eq('user_id', user_id).execute()
        if existing.data:
            sub_map[sub_name] = existing.data[0]['id']
        else:
            res = db.table('subjects').insert({"user_id": user_id, "name": sub_name, "color_hex": color}).execute()
            sub_map[sub_name] = res.data[0]['id']

    # 3. Insert specific chapters for each
    lang_curriculum = {
        "Eng: First Flight": [
            "A Letter to God",
            "Nelson Mandela: Long Walk to Freedom",
            "Two Stories about Flying",
            "From the Diary of Anne Frank",
            "Glimpses of India",
            "Mijbil the Otter",
            "Madam Rides the Bus",
            "The Sermon at Benares",
            "The Proposal"
        ],
        "Eng: Footprints Without Feet": [
            "A Triumph of Surgery",
            "The Thief's Story",
            "The Midnight Visitor",
            "A Question of Trust",
            "Footprints without Feet",
            "The Making of a Scientist",
            "The Necklace",
            "Bholi",
            "The Book That Saved the Earth"
        ],
        "Hindi: Kshitij": [
            "सूरदास के पद (Surdas ke Pad)",
            "राम-लक्ष्मण-परशुराम संवाद",
            "उत्साह और अट नहीं रही है",
            "नेताजी का चश्मा (Netaji ka Chashma)",
            "बालगोबिन भगत (Balgobin Bhagat)",
            "लखनवी अंदाज़ (Lakhnavi Andaz)",
            "एक कहानी यह भी",
            "नौबतखाने में इबादत"
        ],
        "Hindi: Kritika": [
            "माता का अँचल (Mata ka Anchal)",
            "साना साना हाथ जोड़ि",
            "मैं क्यों लिखता हूँ"
        ]
    }

    print("Injecting new Language curriculum...")
    for sub_name, chap_list in lang_curriculum.items():
        sub_id = sub_map[sub_name]
        for chap_name in chap_list:
            existing_chap = db.table('chapters').select('id').eq('name', chap_name).eq('subject_id', sub_id).execute()
            if not existing_chap.data:
                db.table('chapters').insert({
                    "subject_id": sub_id, 
                    "name": chap_name, 
                    "status": "not_started"
                }).execute()

    print("Languages split complete!")

if __name__ == "__main__":
    split_languages()
