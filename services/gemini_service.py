"""
StudyOS - Gemini AI Service
Central module for all Gemini API interactions.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use the latest available models as recommended by the API
_flash_model = genai.GenerativeModel("gemini-1.5-flash") # Keep flash for fast, simple tasks like summarization
_pro_model   = genai.GenerativeModel("gemini-1.5-pro") # Upgrade to Pro for deep reasoning (Grading, Math doubts)


def ask_doubt(question: str, subject: str = "General") -> str:
    """
    Answers a student's doubt in a step-by-step, CBSE-friendly way.

    Args:
        question: The student's question text.
        subject:  e.g., 'Mathematics', 'Science', 'SST'

    Returns:
        AI-generated explanation as a string.
    """
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


def grade_subjective_answer(
    question: str,
    model_answer: str,
    student_answer: str,
    total_marks: int,
    subject: str = "SST",
) -> dict:
    """
    Step-marking grader for SST / English subjective answers.

    Returns a dict: { score, max_score, feedback, step_breakdown }
    """
    prompt = f"""You are a strict but fair CBSE Board examiner.
Subject: {subject}
Total Marks: {total_marks}

Question:
{question}

Official Model Answer:
{model_answer}

Student's Answer:
{student_answer}

Task: Grade the student's answer using CBSE step-marking rubric.
Respond ONLY as valid JSON in this exact format:
{{
  "score": <float>,
  "max_score": {total_marks},
  "step_breakdown": [
    {{"point": "<key point from model answer>", "awarded": <0 or 1>, "comment": "<brief comment>"}}
  ],
  "overall_feedback": "<1-2 sentence improvement tip>"
}}
"""
    response = _pro_model.generate_content(prompt)
    import json
    # Strip markdown code fences if Gemini wraps the JSON
    raw = response.text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(raw)


def summarize_content(raw_text: str, chapter_name: str) -> str:
    """
    Summarizes a YouTube transcript or PDF text into CBSE-style notes.

    Args:
        raw_text:     The raw transcript / PDF text.
        chapter_name: The chapter this content belongs to.

    Returns:
        Formatted markdown summary string.
    """
    prompt = f"""You are a CBSE Class 10 study note generator.
Chapter: {chapter_name}

Raw Content:
{raw_text[:8000]}  # Trim to avoid token limits

Task:
1. Write a structured summary with clear headings (##, ###).
2. Highlight important terms in **bold**.
3. Add a "Key Formulae / Dates / Facts" section at the end.
4. Use simple language suitable for a 15-year-old student.

Output as clean Markdown.
"""
    response = _flash_model.generate_content(prompt)
    return response.text


def generate_flashcards(summary: str, chapter_name: str, count: int = 10) -> list[dict]:
    """
    Generates flashcard Q&A pairs from a chapter summary.

    Returns a list of dicts: [{ "front": "...", "back": "..." }, ...]
    """
    prompt = f"""You are a CBSE Class 10 flashcard generator.
Chapter: {chapter_name}

Content:
{summary[:5000]}

Generate exactly {count} high-quality flashcard pairs covering key concepts, definitions, and formulae.
Respond ONLY as a valid JSON array of objects. Do not include any other text.
Format:
[
  {{"front": "<question or term>", "back": "<concise answer or definition>"}}
]
"""
    try:
        response = _flash_model.generate_content(prompt)
        import json
        
        # Clean the output string to ensure it's pure JSON
        raw = response.text.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        elif raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
            
        return json.loads(raw.strip())
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return []
