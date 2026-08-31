import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.db import get_db

db = get_db()

def split_sst():
    print("Fetching user...")
    users = db.table('users').select('id').limit(1).execute()
    if not users.data:
        print("No users found.")
        return
    user_id = users.data[0]['id']

    # 1. Delete the old "SST" subject (and its chapters via ON DELETE CASCADE)
    print("Removing old SST umbrella subject...")
    db.table('subjects').delete().eq('name', 'SST').execute()

    # 2. Add the 4 new SST subjects with distinct colors
    new_subjects = {
        "History": "#f43f5e",      # Rose
        "Geography": "#10b981",    # Emerald
        "Civics": "#0ea5e9",       # Sky Blue
        "Economics": "#f59e0b"     # Amber
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
    sst_curriculum = {
        "History": [
            "The Rise of Nationalism in Europe",
            "Nationalism in India",
            "The Making of a Global World",
            "The Age of Industrialisation",
            "Print Culture and the Modern World"
        ],
        "Geography": [
            "Resources and Development",
            "Forest and Wildlife Resources",
            "Water Resources",
            "Agriculture",
            "Minerals and Energy Resources",
            "Manufacturing Industries",
            "Lifelines of National Economy"
        ],
        "Civics": [
            "Power Sharing",
            "Federalism",
            "Gender, Religion and Caste",
            "Political Parties",
            "Outcomes of Democracy"
        ],
        "Economics": [
            "Development",
            "Sectors of the Indian Economy",
            "Money and Credit",
            "Globalisation and the Indian Economy",
            "Consumer Rights"
        ]
    }

    print("Injecting new 4-part curriculum...")
    for sub_name, chap_list in sst_curriculum.items():
        sub_id = sub_map[sub_name]
        for chap_name in chap_list:
            existing_chap = db.table('chapters').select('id').eq('name', chap_name).eq('subject_id', sub_id).execute()
            if not existing_chap.data:
                db.table('chapters').insert({
                    "subject_id": sub_id, 
                    "name": chap_name, 
                    "status": "not_started"
                }).execute()

    print("SST split complete!")

if __name__ == "__main__":
    split_sst()
