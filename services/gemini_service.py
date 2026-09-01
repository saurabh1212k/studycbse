import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

_flash_model = genai.GenerativeModel("gemini-1.5-flash")

def ask_doubt(question: str, subject: str = "General") -> str:
    """Answers a student's doubt in a step-by-step, CBSE-friendly way."""
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
    response = _flash_model.generate_content(prompt)
    return response.text
