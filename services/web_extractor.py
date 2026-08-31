import requests
from bs4 import BeautifulSoup
import markdownify
from services.gemini_service import _pro_model

def scrape_notes_from_url(url: str) -> str:
    """Scrapes an educational URL and returns clean markdown notes."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Strip out unwanted elements like nav, scripts, footers, sidebars
        for tag in soup(["script", "style", "nav", "footer", "aside", "header", "iframe"]):
            tag.decompose()
            
        # Target the main content area (heuristics for WordPress / educational sites)
        main_content = soup.find("main") or soup.find("article") or soup.find("div", class_="entry-content") or soup.body
        
        if not main_content:
            return "Could not find main content on this page."
            
        # Convert the remaining HTML to markdown
        md = markdownify.markdownify(str(main_content), heading_style="ATX")
        
        # Clean up excessive newlines
        clean_md = "\n".join([line for line in md.splitlines() if line.strip() != ""])
        return clean_md
        
    except Exception as e:
        return f"Error scraping {url}: {e}"

def generate_extra_questions(context_md: str) -> str:
    """Uses Gemini Pro to generate extra questions based ONLY on the scraped context."""
    prompt = f"""You are a CBSE Class 10 Examiner. 
Based ONLY on the provided study notes below, generate 5 challenging "Extra Questions" (a mix of short and long answer types).
Provide the question first, followed by a detailed answer key.

Study Notes Context:
{context_md[:15000]}  # Limiting to avoid context bloat if page is huge

Format output purely in Markdown.
"""
    try:
        res = _pro_model.generate_content(prompt)
        return res.text
    except Exception as e:
        return f"Error generating questions: {e}"
