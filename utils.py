"""
Utility module for the AI Email Assistant.
Handles:
1. SQLite Database storage for history and autosave drafts.
2. Google Gemini API interface with JSON-mode parsing.
3. Live text analysis (word count, char count, reading time).
4. Export options (clean text and formatted PDFs via fpdf2).
"""

import os
import sqlite3
import json
from datetime import datetime
from google import genai
from google.genai import types
from fpdf import FPDF

DB_NAME = "email_assistant.db"

# ==========================================
# 1. DATABASE INITIALIZATION & OPERATIONS
# ==========================================

def init_db():
    """Initializes the SQLite database tables if they do not exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Store drafts (simple key-value store for app state)
    c.execute("""
        CREATE TABLE IF NOT EXISTS drafts (
            key TEXT PRIMARY KEY,
            val TEXT
        )
    """)
    
    # Store historical emails
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            email_type TEXT,
            subject TEXT,
            body TEXT,
            recipient TEXT,
            sender TEXT,
            category TEXT,
            tone TEXT,
            length TEXT,
            action_items TEXT,
            writing_tips TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def save_draft(key: str, data: dict):
    """Saves app draft state in SQLite as JSON."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    serialized = json.dumps(data)
    c.execute(
        "INSERT OR REPLACE INTO drafts (key, val) VALUES (?, ?)",
        (key, serialized)
    )
    conn.commit()
    conn.close()

def get_draft(key: str) -> dict:
    """Retrieves app draft state. Returns empty dict if not found."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT val FROM drafts WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row[0])
        except Exception:
            return {}
    return {}

def save_history(
    email_type: str,
    subject: str,
    body: str,
    recipient: str,
    sender: str,
    category: str,
    tone: str,
    length: str,
    action_items: list,
    writing_tips: list
):
    """Saves a successfully generated email record to the history log."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        """
        INSERT INTO history (
            timestamp, email_type, subject, body, recipient, sender, 
            category, tone, length, action_items, writing_tips
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            email_type,
            subject,
            body,
            recipient,
            sender,
            category,
            tone,
            length,
            json.dumps(action_items),
            json.dumps(writing_tips)
        )
    )
    conn.commit()
    conn.close()

def get_history(limit: int = 20) -> list:
    """Retrieves recent email generation logs."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    # Return as list of dictionaries
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    
    # Deserialize JSON fields
    for row in result:
        try:
            row["action_items"] = json.loads(row["action_items"])
        except Exception:
            row["action_items"] = []
        try:
            row["writing_tips"] = json.loads(row["writing_tips"])
        except Exception:
            row["writing_tips"] = []
    return result

def delete_history_item(item_id: int):
    """Deletes a specific history item by ID."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM history WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def clear_history():
    """Wipes all rows in history table."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM history")
    conn.commit()
    conn.close()


# ==========================================
# 2. GEMINI API CLIENT AND PARSING
# ==========================================

def _generate_mock_response(prompt: str) -> dict:
    """Generates realistic mock responses matching the structured JSON schemas."""
    # Default values
    subject = ""
    details = ""
    recipient = "Recipient"
    sender = "Sender"
    category = "Formal"
    tone = "Professional"
    length = "Medium"
    
    # Simple extraction of key parameters from prompt formatting
    for line in prompt.split("\n"):
        line_clean = line.strip()
        if "- Subject Line Idea/Topic:" in line_clean or "- Subject Line Idea:" in line_clean:
            subject = line_clean.split(":", 1)[1].strip()
        elif "- Details/Points to Include:" in line_clean or "- Details:" in line_clean:
            details = line_clean.split(":", 1)[1].strip()
        elif "- Recipient Name:" in line_clean:
            recipient = line_clean.split(":", 1)[1].strip()
        elif "- Sender Name:" in line_clean:
            sender = line_clean.split(":", 1)[1].strip()
        elif "- Category:" in line_clean:
            category = line_clean.split(":", 1)[1].strip()
            if " (" in category:
                category = category.split(" (")[0]
        elif "- Tone:" in line_clean:
            tone = line_clean.split(":", 1)[1].strip()
            if " (" in tone:
                tone = tone.split(" (")[0]
        elif "- Desired Length:" in line_clean:
            length = line_clean.split(":", 1)[1].strip()
            if " (" in length:
                length = length.split(" (")[0]

    # Check context (Compose vs Rewrite)
    is_rewrite = "rewriting an existing email" in prompt.lower() or "rewrite" in prompt.lower()
    
    if is_rewrite:
        # Extract the original email to rewrite if present
        original_email = ""
        if '"""' in prompt:
            parts = prompt.split('"""')
            if len(parts) >= 3:
                original_email = parts[1].strip()
        if not original_email:
            original_email = "Original draft email."
            
        body = (
            f"[Offline Mock Mode]\n\n"
            f"Dear {recipient if recipient and recipient != 'N/A' else 'Team'},\n\n"
            f"Thank you for reaching out. In response to your previous message, I wanted to "
            f"confirm that we have updated the details as requested. We are prioritizing "
            f"the next steps to align with your expectations.\n\n"
            f"Please let me know if you would like to adjust any further points.\n\n"
            f"Best regards,\n"
            f"{sender if sender and sender != 'N/A' else 'AI Assistant'}"
        )
        
        return {
            "subject": f"Polished: {subject}" if subject else "Polished Email Draft",
            "body": body,
            "action_items": [
                "Sender: Review the polished layout and tone",
                "Recipient: Confirm if the updated draft meets your expectations"
            ],
            "writing_tips": [
                f"The email tone was successfully polished to '{tone}'.",
                f"Formatting was structured to fit a '{length}' length standard."
            ]
        }
    else:
        # Compose Mode response matching GENERATE_EMAIL_PROMPT schema
        subj_final = subject if subject else f"Important Update Regarding {category}"
        body = (
            f"[Offline Mock Mode]\n\n"
            f"Dear {recipient if recipient else 'Recipient'},\n\n"
            f"I am writing to discuss {subject.lower() if subject else 'our upcoming plans'}. "
            f"Specifically, I want to ensure we address the following key aspects: "
            f"{details if details else 'our project deadlines and resource allocations'}.\n\n"
            f"Could you please review these details and let me know your thoughts? "
            f"I look forward to hearing from you.\n\n"
            f"Best regards,\n"
            f"{sender if sender else 'Sender'}"
        )
        
        return {
            "missing_info_warnings": [] if subject and details else ["Note: Adding more detailed key points or specific timeline dates would make this request stronger."],
            "subject": subj_final,
            "body": body,
            "alternatives": [
                {
                    "subject": f"Quick update: {subj_final}",
                    "body": f"[Offline Mock Mode - Alt 1]\n\nHi {recipient if recipient else 'Team'},\n\nJust wanted to send a quick note regarding {subject.lower() if subject else 'our update'}.\n\n{details if details else 'Please check the latest details when you get a chance.'}\n\nThanks,\n{sender if sender else 'Best'}"
                },
                {
                    "subject": f"Action Required: {subj_final}",
                    "body": f"[Offline Mock Mode - Alt 2]\n\nHello {recipient if recipient else 'there'},\n\nPlease find the details regarding {subject.lower() if subject else 'our update'} below.\n\n{details if details else 'Let me know if you have any questions or feedback.'}\n\nRegards,\n{sender if sender else 'Sender'}"
                },
                {
                    "subject": f"Draft proposal: {subj_final}",
                    "body": f"[Offline Mock Mode - Alt 3]\n\nDear {recipient if recipient else 'Colleagues'},\n\nI hope this message finds you well. I would like to propose the following details regarding {subject.lower() if subject else 'our update'}:\n\n{details if details else 'Let us sync on this at your earliest convenience.'}\n\nSincerely,\n{sender if sender else 'Sender'}"
                }
            ],
            "action_items": [
                f"Recipient: Review and confirm details for {subj_final}",
                f"Sender: Follow up with recipient regarding timeline"
            ],
            "writing_tips": [
                f"Since this is a {category.lower()} email, keeping the tone {tone.lower()} builds a solid professional impression.",
                f"A {length.lower()}-length format is selected to keep the recipient's attention focused on the action items."
            ]
        }


def call_gemini(
    api_key: str,
    model_name: str,
    system_instruction: str,
    prompt: str,
    creativity: float,
    mock_mode: bool = False
) -> dict:
    """
    Invokes the Google Gemini API with the given parameters using the new google-genai SDK.
    Enforces structured JSON response mode. Supports offline mock mode for testing.
    """
    if mock_mode:
        return _generate_mock_response(prompt)

    if not api_key:
        raise ValueError("Google Gemini API Key is missing. Please set it in the sidebar.")
    
    # Map creativity scale to temperature (0.0 to 2.0)
    temperature = max(0.0, min(creativity, 2.0))
    
    try:
        # Initialize client with specified key
        client = genai.Client(api_key=api_key)
        
        # Configure GenerateContentConfig
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            response_mime_type="application/json"
        )
        
        # Call modern endpoint
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        
        if not response.text:
            raise Exception("Empty response received from the AI model. Please try again.")
            
        # Parse output JSON
        data = json.loads(response.text)
        return data
        
    except json.JSONDecodeError as jde:
        # Fallback in case JSON mode returns slightly malformed JSON or markdown-wrapped JSON
        text = response.text.strip()
        # Strip potential markdown block syntax
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            raise Exception(f"Failed to parse structured JSON from AI model response. Raw text: {response.text[:200]}...")
            
    except Exception as e:
        # Re-raise standard exception with user-friendly error message
        raise Exception(f"Gemini API Error: {str(e)}")


# ==========================================
# 3. LIVE TEXT ANALYTICS
# ==========================================

def get_text_stats(text: str) -> dict:
    """Calculates word count, character count, and estimated reading time."""
    if not text:
        return {"words": 0, "chars": 0, "reading_time": "0s"}
    
    words = len(text.split())
    chars = len(text)
    
    # Average adult reading speed: ~200 WPM
    wpm = 200
    total_seconds = int((words / wpm) * 60)
    
    if total_seconds < 60:
        reading_time = f"{total_seconds}s"
    else:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        if seconds == 0:
            reading_time = f"{minutes} min"
        else:
            reading_time = f"{minutes} min {seconds}s"
            
    return {
        "words": words,
        "chars": chars,
        "reading_time": reading_time
    }


# ==========================================
# 4. EXPORT HANDLERS
# ==========================================

def clean_for_pdf(text: str) -> str:
    """
    Cleans Unicode characters to fit standard Latin-1/Helvetica encoding for PDF.
    This guarantees that the FPDF writer doesn't crash on standard typographic quotes.
    """
    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2022": "*",
        "\u2013": "-",
        "\u2014": "-",
        "\u2192": "->",
        "\u00a0": " ",
    }
    cleaned = text
    for original, replacement in replacements.items():
        cleaned = cleaned.replace(original, replacement)
    
    # Encode to latin-1, replace outliers with '?' to ensure no fpdf encoding crashes
    return cleaned.encode('latin-1', errors='replace').decode('latin-1')

def generate_pdf(subject: str, body: str, sender: str, recipient: str, category: str, tone: str) -> bytes:
    """Generates a beautiful formatted PDF of the email draft."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Set document properties
    pdf.set_title("AI Email Assistant - Draft Export")
    pdf.set_author(sender if sender else "AI Email Assistant")
    
    # Title Banner
    pdf.set_fill_color(30, 41, 59) # Slate 800
    pdf.rect(0, 0, 210, 40, 'F')
    
    # Title Text
    pdf.set_y(12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 8, clean_for_pdf("AI EMAIL ASSISTANT"), ln=1, align="C")
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 6, clean_for_pdf("Professional Draft Document"), ln=1, align="C")
    
    pdf.ln(15)
    pdf.set_text_color(51, 65, 85) # Slate 700
    
    # Metadata Box
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(248, 250, 252) # Slate 50
    pdf.set_draw_color(226, 232, 240) # Slate 200
    
    # Write metadata fields
    # Draw left border or outline
    pdf.rect(10, 45, 190, 40, 'FD')
    
    pdf.set_xy(15, 48)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(25, 6, clean_for_pdf("DATE:"), 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(60, 6, clean_for_pdf(datetime.now().strftime("%B %d, %Y")), 0, 0)
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(25, 6, clean_for_pdf("CATEGORY:"), 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(60, 6, clean_for_pdf(category.upper() if category else "GENERAL"), 0, 1)
    
    pdf.set_x(15)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(25, 6, clean_for_pdf("SENDER:"), 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(60, 6, clean_for_pdf(sender if sender else "N/A"), 0, 0)
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(25, 6, clean_for_pdf("TONE:"), 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(60, 6, clean_for_pdf(tone.upper() if tone else "PROFESSIONAL"), 0, 1)
    
    pdf.set_x(15)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(25, 6, clean_for_pdf("RECIPIENT:"), 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(60, 6, clean_for_pdf(recipient if recipient else "N/A"), 0, 1)
    
    pdf.ln(12)
    
    # Subject Line
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 23, 42) # Slate 900
    pdf.cell(25, 8, clean_for_pdf("Subject:"), 0, 0)
    pdf.set_font("Helvetica", "B", 12)
    pdf.multi_cell(0, 8, clean_for_pdf(subject if subject else "(No Subject Line)"))
    
    # Divider Line
    pdf.set_draw_color(148, 163, 184) # Slate 400
    pdf.line(10, pdf.get_y() + 3, 200, pdf.get_y() + 3)
    pdf.ln(8)
    
    # Email Body
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(30, 41, 59) # Slate 800
    
    # Multi_cell handles paragraph wrapping automatically
    pdf.multi_cell(0, 6.5, clean_for_pdf(body if body else "(No content)"))
    
    # Return PDF bytes
    return bytes(pdf.output())

def generate_txt(subject: str, body: str, sender: str, recipient: str, category: str, tone: str) -> bytes:
    """Generates simple plain text byte stream for downloading."""
    divider = "=" * 60
    txt_content = (
        f"AI EMAIL ASSISTANT - DRAFT EXPORT\n"
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Category: {category}\n"
        f"Tone: {tone}\n"
        f"Sender: {sender}\n"
        f"Recipient: {recipient}\n"
        f"{divider}\n"
        f"Subject: {subject}\n"
        f"{divider}\n\n"
        f"{body}\n"
    )
    return txt_content.encode("utf-8")
