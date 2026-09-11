import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")


def _gemini_rest_call(prompt: str, model: str = "gemini-2.0-flash", max_retries: int = 2) -> str:
    """
    Calls the Gemini REST API directly using the x-goog-api-key header.
    Works with standard AI Studio keys (AIza...) and avoids SDK auth quirks.
    """
    if not API_KEY:
        raise Exception(
            "Missing GEMINI_API_KEY. Add it to your .env file "
            "(get a free key at https://aistudio.google.com/apikey)"
        )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"x-goog-api-key": API_KEY.strip()}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    last_err = None
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 429 and attempt < max_retries:
                import time
                time.sleep(2 ** attempt)  # Backoff: 1s, 2s
                continue
            if resp.status_code == 401:
                raise Exception(
                    "Gemini API key is invalid or expired (401 UNAUTHENTICATED). "
                    "Generate a fresh key at https://aistudio.google.com/apikey "
                    "and update GEMINI_API_KEY in your .env file."
                )
            if resp.status_code == 404:
                raise Exception(f"Model '{model}' not found for this API key.")
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except requests.RequestException as e:
            last_err = e
            if attempt >= max_retries:
                break
            import time
            time.sleep(2 ** attempt)

    raise Exception(f"Gemini API request failed after retries: {last_err}")


def ask_doubt(question: str, subject: str = "General") -> str:
    """Answers a student's doubt via the Gemini REST API."""
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
    return _gemini_rest_call(prompt)


def summarize_content(raw_text: str, chapter_name: str) -> str:
    """Turns raw transcript/PDF text into structured markdown study notes."""
    prompt = f"""You are an expert CBSE Class 10 note-maker.
Create clean, exam-oriented markdown study notes for the chapter: {chapter_name}

Source material:
{raw_text[:28000]}

Structure the notes with:
- ## Chapter overview (2-3 lines)
- ## Key concepts (with short explanations)
- ## Important formulas / definitions (if any)
- ## Quick revision bullets

Use markdown headers, bold, and bullet points. Output ONLY the notes."""
    return _gemini_rest_call(prompt)


def generate_flashcards(summary: str, chapter_name: str, count: int = 10) -> list:
    """Generates flashcards as a list of {'front': str, 'back': str} dicts."""
    prompt = f"""Based on these study notes for "{chapter_name}", generate exactly {count} flashcards as a JSON array.
Each element: {{"front": "question", "back": "concise answer"}}.
Cover the most examinable facts. Output ONLY the JSON array, no markdown fences.

Notes:
{summary[:24000]}"""
    import json
    import re

    raw = _gemini_rest_call(prompt)
    # Strip potential markdown fences
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    try:
        cards = json.loads(cleaned)
        return [
            {"front": str(c.get("front", "")).strip(), "back": str(c.get("back", "")).strip()}
            for c in cards
            if isinstance(c, dict) and c.get("front") and c.get("back")
        ]
    except json.JSONDecodeError:
        raise Exception(f"Could not parse flashcards from AI response: {raw[:200]}")
