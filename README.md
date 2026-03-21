# AI Chatbot with Company Data Analysis

**Team 5 — Integration & Interface**

This branch contains the integration layer that connects all project modules into a single working application.

---

## What Team 5 Built

- `main_app.py` — application entry point integrating all modules
- `chatbot/chatbot_engine.py` — AI chatbot with stateful conversation memory
- `report_generator.py` — PDF and Excel report generation
- Full Streamlit UI with floating chatbot interface
- Sidebar filters connected to all dashboard components
- Startup loading screen and error handling

---

## Setup

```bash
git clone https://github.com/manunaik111/AI-Sales-Chatbot-System.git
cd AI-Sales-Chatbot-System
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m nltk.downloader punkt stopwords punkt_tab
```

Create `.streamlit/secrets.toml`:
```toml
AI_API_KEY = "your-groq-api-key"
```

```bash
streamlit run main_app.py
```

---

## Tech Stack

Python 3.11 · Streamlit · Groq API · Pandas · fpdf2 · openpyxl · streamlit-float
