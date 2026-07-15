# Antigravity AI Email Assistant

A production-ready, feature-rich AI productivity application built with **Streamlit** and the **Google Gemini API**. This tool helps professionals compose, refine, rewrite, and organize email communication with premium styling, local SQLite-backed autosave draft capabilities, and versatile format exporters (TXT/PDF).

---

## Key Features

- 📝 **Compose Panel**: Input specific email details, tones, recipients, length requirements, and creativity scale to generate highly polished drafts.
- 🔄 **Refine & Rewrite**: Paste rough drafts to fix grammar, change tones, extract key action checklists, or customize layout structures immediately.
- 📚 **Template Library**: Select from pre-made templates (Formal resignation, Cold sales outreaches, Sick leaves, Application follow-ups) that pre-fill configurations instantly.
- 📜 **Generation History**: A persistent SQLite-backed log repository to view, delete, or load historical drafts back to Composer or Refiner.
- 📥 **Flexible Exporters**: Download polished text as plain TXT files or custom-styled professional PDF files with automatic Unicode cleanups.
- ⏱️ **Writing Analytics**: Live counters tracking input character counts, word counts, and estimated reading speeds.
- 🛡️ **Autosave Drafts**: Form states are automatically saved locally, ensuring no drafts are lost during browser reloads.

---

## Project Structure

```text
├── app.py                  # Streamlit entry point containing layout, custom styling, and routing
├── utils.py                # Database controllers, Gemini API, statistics, and PDF/TXT exporters
├── prompts.py              # Structured prompt system instructions and JSON schemas
├── requirements.txt        # Package dependencies list
└── README.md               # User documentation (this file)
```

---

## Installation

### Prerequisites
- Python 3.9 or higher installed.

### Setup Steps
1. Clone or download this project workspace directory.
2. Open your terminal in the directory.
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## How to Set Up the API Key

The assistant communicates with Google Generative AI models. You have two ways to supply your Gemini API key:

### Option A: Environment Variables (Recommended)
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```
The application will automatically detect this key on startup.

### Option B: Interactive UI Setting
Enter the key directly into the **Google Gemini API Key** input in the application sidebar. This key is stored securely in session state and is never shared outside your browser.

---

## How to Run the App

Start the Streamlit local dev server by running:
```bash
streamlit run app.py
```

The application will launch automatically in your default browser at `http://localhost:8501`.

---

## Screenshots Placeholder

*Visual representation of the Compose Dashboard:*
![Compose Panel Screenshot](https://raw.githubusercontent.com/google/gemini-cookbook/main/images/placeholder.png)

*Visual representation of the Rewrite & Polish View:*
![Rewrite View Screenshot](https://raw.githubusercontent.com/google/gemini-cookbook/main/images/placeholder.png)

---

## Future Improvements

1. **Multi-Model Support**: Integrate alternative model wrappers (e.g., OpenAI GPT-4, Anthropic Claude) through modular prompt configurations.
2. **Email Client Connectors**: Allow sending drafts directly through integrations with Microsoft Outlook, Gmail, or SMTP servers.
3. **Advanced Rich-Text Formatting**: Integrate rich-text components directly in inputs and output render windows.
4. **Shared Preset Libraries**: Create customizable templates that users can save to their own custom database library.
