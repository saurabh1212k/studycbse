import os
import sys

# Ensure we can import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.db import get_db

db = get_db()

# Create a test subject if none exists
print("Fetching/Creating subject...")
users = db.table("users").select("id").limit(1).execute()
if not users.data:
    user_res = db.table("users").insert({"name": "Test User", "email": "test@studyos.com"}).execute()
    user_id = user_res.data[0]["id"]
else:
    user_id = users.data[0]["id"]

subs = db.table("subjects").select("id").eq("name", "Science").execute()
if not subs.data:
    sub_res = db.table("subjects").insert({"user_id": user_id, "name": "Science", "color_hex": "#22c55e"}).execute()
    sub_id = sub_res.data[0]["id"]
else:
    sub_id = subs.data[0]["id"]

# Sample PYQs
sample_pyqs = [
    {
        "subject_id": sub_id,
        "year": 2023,
        "marks": 3,
        "question_type": "SAQ",
        "difficulty": "medium",
        "question_text": "A student added a few pieces of aluminium metal to two test tubes A and B containing aqueous solutions of iron sulphate and copper sulphate respectively. In the second part of her experiment, she added iron metal to another test tube C containing an aqueous solution of aluminium sulphate. \n(a) State the colour change in test tubes A and B.\n(b) In which test tube will no reaction occur? Give reason.",
        "answer_text": "(a) In test tube A, the pale green colour of iron sulphate fades and turns colourless. In test tube B, the blue colour of copper sulphate fades and turns colourless. Brown/grey solid deposits are formed in both.\n(b) No reaction occurs in test tube C. This is because iron is less reactive than aluminium, so it cannot displace aluminium from aluminium sulphate solution."
    },
    {
        "subject_id": sub_id,
        "year": 2020,
        "marks": 5,
        "question_type": "LAQ",
        "difficulty": "hard",
        "question_text": "Draw a neat labelled diagram of human respiratory system. Explain the mechanism of breathing in human beings.",
        "answer_text": "(Diagram of human respiratory system showing trachea, lungs, bronchi, alveoli, diaphragm - 2 marks)\nMechanism of breathing:\nInhalation: When we breathe in, our ribs are lifted up and outwards, and the diaphragm becomes flattened. The volume of the chest cavity increases, pressure decreases, and air rushes into the lungs. (1.5 marks)\nExhalation: When we breathe out, the ribs move downwards and inwards, and the diaphragm relaxes and arches upwards. The volume of the chest cavity decreases, pressure increases, and air is pushed out of the lungs. (1.5 marks)"
    }
]

print("Inserting PYQs...")
for pyq in sample_pyqs:
    db.table("pyqs").insert(pyq).execute()
    
print("Successfully seeded PYQs!")
