import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.db import get_db

db = get_db()

def setup_db():
    print("Ensuring user exists...")
    users = db.table('users').select('id').limit(1).execute()
    if not users.data:
        print("Inserting user...")
        res = db.table('users').insert({"name": "Student", "email": "student@studyos.com"}).execute()
        user_id = res.data[0]['id']
    else:
        user_id = users.data[0]['id']
        
    print(f"User ID: {user_id}")

    print("Inserting subjects...")
    subjects_data = [
        {"user_id": user_id, "name": "Mathematics", "color_hex": "#3b82f6"},
        {"user_id": user_id, "name": "Physics", "color_hex": "#eab308"},
        {"user_id": user_id, "name": "Chemistry", "color_hex": "#ef4444"},
        {"user_id": user_id, "name": "Biology", "color_hex": "#22c55e"},
        {"user_id": user_id, "name": "SST", "color_hex": "#f97316"},
        {"user_id": user_id, "name": "English", "color_hex": "#8b5cf6"},
        {"user_id": user_id, "name": "Hindi", "color_hex": "#ec4899"},
    ]
    
    # We will insert one by one to avoid breaking if one exists
    sub_map = {}
    for sub in subjects_data:
        existing = db.table('subjects').select('id').eq('name', sub['name']).eq('user_id', user_id).execute()
        if existing.data:
            sub_map[sub['name']] = existing.data[0]['id']
        else:
            inserted = db.table('subjects').insert(sub).execute()
            sub_map[sub['name']] = inserted.data[0]['id']
            
    print(f"Subjects map: {sub_map}")

    chapters_data = {
        "Physics": ['Light - Reflection and Refraction', 'The Human Eye and the Colourful World', 'Electricity', 'Magnetic Effects of Electric Current'],
        "Chemistry": ['Chemical Reactions and Equations', 'Acids, Bases and Salts', 'Metals and Non-metals', 'Carbon and its Compounds'],
        "Biology": ['Life Processes', 'Control and Coordination', 'How do Organisms Reproduce?', 'Heredity', 'Our Environment'],
        "Mathematics": ['Real Numbers', 'Polynomials', 'Pair of Linear Equations in Two Variables', 'Quadratic Equations', 'Arithmetic Progressions', 'Triangles', 'Coordinate Geometry', 'Introduction to Trigonometry', 'Some Applications of Trigonometry', 'Circles', 'Areas Related to Circles', 'Surface Areas and Volumes', 'Statistics', 'Probability']
    }

    print("Inserting chapters...")
    for sub_name, chaps in chapters_data.items():
        sub_id = sub_map[sub_name]
        for chap_name in chaps:
            existing_chap = db.table('chapters').select('id').eq('name', chap_name).eq('subject_id', sub_id).execute()
            if not existing_chap.data:
                db.table('chapters').insert({"subject_id": sub_id, "name": chap_name, "status": "not_started"}).execute()
                print(f"Inserted: {chap_name}")

    print("Done!")

if __name__ == "__main__":
    setup_db()
