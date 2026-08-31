import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.db import get_db

try:
    db = get_db()
    users = db.table('users').select('*').execute().data
    print(f"USERS: {users}")
    
    subjects = db.table('subjects').select('*').execute().data
    print(f"SUBJECTS: {subjects}")
except Exception as e:
    print(f"ERROR: {e}")
