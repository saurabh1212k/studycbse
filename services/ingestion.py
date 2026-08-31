"""
StudyOS - Ingestion Engine Service
Handles extracting text from YouTube and PDFs, and passing them to Gemini.
"""

from youtube_transcript_api import YouTubeTranscriptApi
import pdfplumber
from services.gemini_service import summarize_content, generate_flashcards

def extract_youtube_id(url: str) -> str:
    """Extracts the video ID from a YouTube URL."""
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return ""

def process_youtube_video(url: str, chapter_name: str) -> dict:
    """
    Downloads transcript, generates notes, and creates flashcards.
    Returns: {"summary": str, "flashcards": list}
    """
    video_id = extract_youtube_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL.")

    # 1. Download Transcript (Handle Hindi / Non-English videos)
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Grab the first available transcript (whether it's Hindi, English, etc.)
        for transcript in transcript_list:
            # Translate it to English using YouTube's built-in translation
            english_transcript = transcript.translate('en').fetch()
            raw_text = " ".join([t['text'] for t in english_transcript])
            break
            
    except Exception as e:
        raise ValueError(f"Could not download transcript. The video might not have any captions at all. Error: {e}")

    # 2. Generate Summary
    summary = summarize_content(raw_text, chapter_name)

    # 3. Generate Flashcards
    flashcards = generate_flashcards(summary, chapter_name, count=10)

    return {
        "summary": summary,
        "flashcards": flashcards,
        "raw_text_length": len(raw_text)
    }

def process_pdf(file_stream, chapter_name: str) -> dict:
    """
    Extracts text from PDF, generates notes, and creates flashcards.
    Returns: {"summary": str, "flashcards": list}
    """
    raw_text = ""
    try:
        with pdfplumber.open(file_stream) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    raw_text += text + "\n"
    except Exception as e:
        raise ValueError(f"Failed to read PDF file. Error: {e}")

    if not raw_text.strip():
        raise ValueError("No text could be extracted from this PDF. It might be an image-only scanned PDF.")

    # 2. Generate Summary
    summary = summarize_content(raw_text, chapter_name)

    # 3. Generate Flashcards
    flashcards = generate_flashcards(summary, chapter_name, count=10)

    return {
        "summary": summary,
        "flashcards": flashcards,
        "raw_text_length": len(raw_text)
    }
