import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.db import get_db

db = get_db()

def fix_curriculum():
    print("Fetching user...")
    users = db.table('users').select('id').limit(1).execute()
    if not users.data:
        print("No users found.")
        return
    user_id = users.data[0]['id']

    # 1. Fetch all subjects
    subs = db.table('subjects').select('*').execute().data
    sub_map = {s['name']: s['id'] for s in subs}

    # Ensure all subjects exist
    required_subjects = {
        "Mathematics": "#3b82f6",
        "Physics": "#eab308",
        "Chemistry": "#ef4444",
        "Biology": "#22c55e",
        "SST": "#f97316",
        "English": "#8b5cf6",
        "Hindi": "#ec4899"
    }

    for sub_name, color in required_subjects.items():
        if sub_name not in sub_map:
            print(f"Adding missing subject: {sub_name}")
            res = db.table('subjects').insert({"user_id": user_id, "name": sub_name, "color_hex": color}).execute()
            sub_map[sub_name] = res.data[0]['id']

    # 2. Deduplicate chapters
    chaps = db.table('chapters').select('*').execute().data
    seen = set()
    duplicates_to_delete = []

    for chap in chaps:
        identifier = (chap['subject_id'], chap['name'])
        if identifier in seen:
            duplicates_to_delete.append(chap['id'])
        else:
            seen.add(identifier)

    if duplicates_to_delete:
        print(f"Deleting {len(duplicates_to_delete)} duplicate chapters...")
        for dup_id in duplicates_to_delete:
            db.table('chapters').delete().eq('id', dup_id).execute()

    # 3. Add missing curriculum
    full_curriculum = {
        "SST": [
            "The Rise of Nationalism in Europe",
            "Nationalism in India",
            "Resources and Development",
            "Agriculture",
            "Power Sharing",
            "Federalism",
            "Development",
            "Sectors of the Indian Economy"
        ],
        "English": [
            "A Letter to God",
            "Nelson Mandela: Long Walk to Freedom",
            "Two Stories about Flying",
            "The Diary of Anne Frank",
            "The Triumph of Surgery",
            "The Thief's Story"
        ],
        "Hindi": [
            "सूरदास के पद (Surdas ke Pad)",
            "राम-लक्ष्मण-परशुराम संवाद",
            "नेताजी का चश्मा (Netaji ka Chashma)",
            "बालगोबिन भगत (Balgobin Bhagat)"
        ],
        "Mathematics": [
            "Real Numbers", "Polynomials", "Pair of Linear Equations in Two Variables",
            "Quadratic Equations", "Arithmetic Progressions", "Triangles",
            "Coordinate Geometry", "Introduction to Trigonometry", "Some Applications of Trigonometry",
            "Circles", "Areas Related to Circles", "Surface Areas and Volumes", "Statistics", "Probability"
        ]
    }

    print("Adding missing chapters...")
    for sub_name, chap_list in full_curriculum.items():
        sub_id = sub_map[sub_name]
        for chap_name in chap_list:
            if (sub_id, chap_name) not in seen:
                db.table('chapters').insert({
                    "subject_id": sub_id, 
                    "name": chap_name, 
                    "status": "not_started"
                }).execute()
                seen.add((sub_id, chap_name))

    print("Curriculum fixed completely!")

if __name__ == "__main__":
    fix_curriculum()
