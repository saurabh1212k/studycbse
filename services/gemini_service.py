import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    # The brand new Google GenAI SDK perfectly supports the new AQ. keys!
    client = genai.Client(api_key=API_KEY.strip())
else:
    client = None

def ask_doubt(question: str, subject: str = "General") -> str:
    """Answers a student's doubt using the new google-genai SDK."""
    if not client:
        raise Exception("Missing GEMINI_API_KEY")

    prompt = f"""You are StudyOS AI, a friendly and expert CBSE Class 10 tutor.
Subject: {subject}

Student's Question:
{question}

Instructions:
- Explain step-by-step in simple English.
- For Math/Science, show full working with formulas.
- Keep the answer concise but complete for a Class 10 board exam.
- End with a "Key Takeaway" in one sentence.
"""
    
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        raise Exception(f"API Request failed: {str(e)}")
