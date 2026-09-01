import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

def ask_doubt(question: str, subject: str = "General") -> str:
    """Answers a student's doubt using the raw Gemini REST API."""
    if not API_KEY:
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

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    # Passing the key explicitly in the header fixes the SDK bug!
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY.strip()
    }
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"API Error {e.code}: {error_body}")
    except Exception as e:
        raise Exception(f"Request failed: {str(e)}")
