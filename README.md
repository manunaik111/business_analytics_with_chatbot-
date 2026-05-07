<div align="center">

# ⚡ Zero Click AI

### AI-Powered Data Analytics Platform

*Built by 11 interns at Genesis Training — Python & AI Internship Program*

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_70B-F55036?style=flat-square)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## What Is Zero Click AI?

Zero Click AI is a full-stack AI analytics platform that lets you upload any dataset — sales, medical, financial, or otherwise — and instantly get dashboards, AI-generated insights, natural language chat, predictive forecasts, automated reports, and more. No data science expertise required.

The platform was designed and built from scratch by a team of 11 interns across 5 specialised modules, integrating a FastAPI backend, a dark glassmorphism frontend, Groq LLM (LLaMA 3.3 70B), NLP pipelines, machine learning forecasting, and an email scheduler into a single deployable application.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Modules](#modules)
- [AI Chatbot](#ai-chatbot)
- [API Reference](#api-reference)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [Deployment](#deployment)
- [Role-Based Access Control](#role-based-access-control)
- [Dataset Compatibility](#dataset-compatibility)
- [The Team](#the-team)

---

## Features

### Core Platform
- **Role-based authentication** — JWT-secured login, registration, self-service password change, and per-role permission enforcement
- **Universal file upload** — CSV, Excel (.xlsx, .xls), and JSON with automatic schema detection
- **Per-user dataset isolation** — each user's uploaded data is stored and served independently
- **Adaptive dashboard** — KPIs, charts, and insights that automatically adjust to any dataset type
- **Dark glassmorphism UI** — responsive, accessible frontend with no external UI framework dependency

### AI & Intelligence
- **Groq AI Chatbot** — powered by LLaMA 3.3 70B; 3-tier response system (zero-token instant → light Groq → full code-gen) with conversation memory, follow-up context awareness, and token-efficient prompt design
- **AI Insights** — auto-generated business insights from KPI data using the analytics engine
- **Smart Recommendations** — actionable recommendations derived from dataset patterns
- **Predictive Analytics** — linear + SES ensemble forecasting with seasonality adjustment and confidence bands

### Data Management
- **Dataset Profiling** — row/column counts, data types, null rates, cardinality, and statistical summaries
- **Data Quality Checks** — missing value detection, duplicate identification, outlier analysis, inconsistency flagging, and a composite quality score
- **Schema Mapping** — automatic column detection for sales, date, region, category, and item fields across any dataset structure

### NLP Pipeline
- **Intent Classification** — TF-IDF + scikit-learn classifier trained on sales query patterns
- **Entity Extraction** — product name, region, category, and metric entity recognition with fuzzy column matching
- **Query Execution** — structured query execution against the active DataFrame with categorical groupby fallback
- **Voice Input** — browser Web Speech API with MediaRecorder fallback to backend transcription
- **Voice Output** — browser SpeechSynthesis with UK English female voice preference; gTTS backend fallback

### Reporting & Scheduling
- **PDF Reports** — ReportLab-generated reports with KPIs, charts, and insights
- **Excel Reports** — openpyxl-generated multi-sheet workbooks
- **Email Scheduler** — APScheduler-powered recurring report delivery via SMTP (Daily / Weekly / Monthly)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Frontend)                        │
│  dashboard.html · analytics.html · profiling.html · team.html   │
│  Vanilla JS · Chart.js · SheetJS · Web Speech API               │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP / REST
┌────────────────────────────▼────────────────────────────────────┐
│                     FastAPI Backend (api.py)                     │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │   Auth   │  │Dashboard │  │  NLP /   │  │   Analytics    │  │
│  │  JWT +   │  │ Metrics  │  │ Chatbot  │  │  Prediction    │  │
│  │  RBAC    │  │  Charts  │  │  Groq AI │  │  Insights      │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │  Upload  │  │Profiling │  │ Quality  │  │    Reports     │  │
│  │  Store   │  │  Engine  │  │  Checks  │  │  PDF / Excel   │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Email Scheduler (APScheduler)               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   ┌──────────┐       ┌──────────┐       ┌──────────────┐
   │  SQLite  │       │  Groq    │       │  File Store  │
   │  users   │       │  API     │       │  data/       │
   │  .db     │       │  LLaMA   │       │  uploads/    │
   └──────────┘       └──────────┘       └──────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI 0.115 + Uvicorn |
| Language | Python 3.11 |
| AI / LLM | Groq API — LLaMA 3.3 70B Versatile |
| LLM orchestration | LangChain + LangChain-Groq |
| NLP | NLTK, spaCy, scikit-learn (TF-IDF) |
| Data processing | pandas 2.2, NumPy 1.26 |
| Machine learning | scikit-learn 1.5, statsmodels 0.14 |
| Visualisation | Chart.js (frontend), Plotly / Matplotlib (backend) |
| Authentication | python-jose (JWT), passlib + bcrypt |
| Report generation | ReportLab (PDF), openpyxl (Excel) |
| Email scheduling | APScheduler 3.10 |
| Voice I/O | SpeechRecognition, gTTS, Web Speech API |
| Frontend | Vanilla JS, HTML5, CSS3 (glassmorphism) |
| Database | SQLite (users + scheduler) |
| Environment | python-dotenv |

---

## Project Structure

```
zero-click-ai/
│
├── api.py                      # Main FastAPI application — all routes
├── main_app.py                 # Streamlit reference version (legacy)
├── report_generator.py         # PDF and Excel report generation
├── requirements.txt
├── .env.example
│
├── frontend/                   # Static frontend (served by FastAPI at /app/)
│   ├── index.html              # Entry redirect
│   ├── landing.html            # Marketing landing page
│   ├── login.html              # Authentication
│   ├── register.html           # Registration
│   ├── dashboard.html          # Main analytics dashboard
│   ├── analytics.html          # Deep analytics view
│   ├── profiling.html          # Dataset profiling
│   ├── quality.html            # Data quality report
│   ├── team.html               # Team showcase
│   ├── users.html              # User management (Admin only)
│   ├── dashboard.js            # Dashboard logic + AI chat + voice
│   ├── app.js                  # Auth, routing, API client
│   └── styles.css              # Design system (CSS variables + components)
│
├── auth/                       # Authentication module (Streamlit version)
│   ├── auth_manager.py
│   ├── login_page.py
│   ├── register_page.py
│   ├── user_management.py
│   ├── roles.py
│   └── users.db
│
├── analytics/                  # Module 3 — Analytics & Prediction
│   ├── analysis.py             # RetailDataAnalyzer — KPIs, category, regional, product analysis
│   ├── insights.py             # AI insight generation from KPI data
│   ├── my_recommendations.py   # Smart recommendation engine
│   └── predictive_engine.py    # SalesPredictiveEngine — linear + SES ensemble forecasting
│
├── nlp/                        # Module 2 — NLP & Chatbot
│   ├── nlp_processor.py        # Query parsing entry point + fuzzy column matching
│   ├── data_processor.py       # Query execution with categorical groupby fallback
│   ├── response_generator.py   # Template response generation
│   ├── intent_classifier.py    # TF-IDF intent classification
│   ├── entity_extractor.py     # Named entity extraction
│   ├── preprocessing.py        # Text normalisation
│   ├── parse_query.py          # Query structure parsing
│   ├── voice_input.py          # Speech-to-text (SpeechRecognition)
│   ├── voice_output.py         # Text-to-speech (gTTS, UK English female)
│   ├── training_data.py        # Intent classifier training data
│   ├── intent_classifier.pkl   # Trained classifier (serialised)
│   └── tfidf_vectorizer.pkl    # Trained TF-IDF vectorizer (serialised)
│
├── dashboard/                  # Module 4 — Dashboard & Visualisation
│   ├── data_ingestion.py       # File loading
│   ├── data_cleaning.py        # Automated cleaning pipeline
│   ├── data_analysis.py        # Column type detection, correlations, stats
│   ├── kpi_generator.py        # Adaptive KPI card generation
│   ├── visualization.py        # Auto chart generation
│   └── insights.py             # Dashboard-level insight generation
│
├── data_management/            # Module 1 — Data Management
│   ├── file_upload.py          # Upload validation, parsing, normalisation
│   ├── dataset_profiling.py    # Full dataset profile generation
│   ├── data_quality.py         # Quality checks and scoring
│   ├── schema_mapper.py        # Column detection and mapping
│   └── upload_store.py         # Per-user upload persistence
│
├── chatbot/                    # Module 5 — Chatbot (Streamlit version)
│   └── chatbot_engine.py       # Groq-powered chat with memory
│
├── email_scheduler/            # Email scheduling module
│   ├── db_manager.py           # SQLite schedule storage
│   ├── job_scheduler.py        # APScheduler job management
│   ├── smtp_client.py          # SMTP email delivery
│   └── pdf_generator.py        # Scheduled report PDF generation
│
├── data/
│   ├── SALES_DATA_SETT.csv     # Default sales dataset
│   └── uploads/                # Per-user uploaded datasets (git-ignored)
│
└── database/
    └── scheduler.db            # Email schedule SQLite database
```

---

## Modules

The project was built across five specialised modules, each owned by a sub-team.

### Module 1 — Data Management
Handles all file ingestion, validation, profiling, and quality assessment.

- **File Upload** (`data_management/file_upload.py`) — validates file type and size, parses CSV/Excel/JSON into DataFrames, normalises column names, auto-parses date columns
- **Dataset Profiling** (`data_management/dataset_profiling.py`) — generates row/column counts, per-column type detection, null rates, cardinality, min/max/mean/std for numeric columns
- **Data Quality** (`data_management/data_quality.py`) — checks for missing values, duplicates, outliers (IQR method), type inconsistencies; computes a composite quality score (0–100); generates human-readable warnings
- **Schema Mapper** (`data_management/schema_mapper.py`) — detects dataset type (sales vs generic), maps columns to standard roles (date, target, region, category, item), generates chatbot suggestions
- **Upload Store** (`data_management/upload_store.py`) — persists per-user uploads to `data/uploads/` as `.pkl` + `.json` metadata; loads on subsequent requests

### Module 2 — NLP & Chatbot
Processes natural language queries and generates responses.

- **NLP Processor** (`nlp/nlp_processor.py`) — entry point; orchestrates preprocessing → intent classification → entity extraction → query parsing. Includes fuzzy partial-word column matching and expanded metric aliases (income, earnings, margin, units, etc.)
- **Intent Classifier** (`nlp/intent_classifier.py`) — TF-IDF vectorizer + scikit-learn classifier trained on sales query patterns
- **Entity Extractor** (`nlp/entity_extractor.py`) — extracts product names, regions, categories, metrics, and time references from query text
- **Data Processor** (`nlp/data_processor.py`) — executes structured queries against the active pandas DataFrame; includes a categorical groupby fallback so "highest category" correctly groups and aggregates instead of erroring on text columns
- **Response Generator** (`nlp/response_generator.py`) — converts query results into natural language template responses
- **Voice Input** (`nlp/voice_input.py`) — microphone transcription via SpeechRecognition (Google backend)
- **Voice Output** (`nlp/voice_output.py`) — gTTS text-to-speech with UK English female voice (`tld='co.uk'`)

### Module 3 — Analytics & Prediction
Performs deep analysis and machine learning forecasting.

- **RetailDataAnalyzer** (`analytics/analysis.py`) — comprehensive analysis class covering KPIs, category analysis, product ranking, customer segmentation, regional breakdown, shipping analysis, discount impact, and profitability margins
- **Insights Engine** (`analytics/insights.py`) — generates AI-written business insights from KPI dictionaries
- **Recommendations Engine** (`analytics/my_recommendations.py`) — produces actionable recommendations based on dataset patterns
- **Predictive Engine** (`analytics/predictive_engine.py`) — `SalesPredictiveEngine` class implementing a linear regression + simple exponential smoothing (SES) ensemble with calendar-month seasonality factors, confidence bands, and R² fit quality reporting

### Module 4 — Dashboard & Visualisation
Builds the adaptive analytics dashboard.

- **Data Analysis** (`dashboard/data_analysis.py`) — detects column types (numeric, categorical, datetime), computes correlations, and generates statistical summaries
- **KPI Generator** (`dashboard/kpi_generator.py`) — produces up to 12 adaptive KPI cards from any dataset
- **Visualisation** (`dashboard/visualization.py`) — auto-generates charts (line, bar, doughnut, scatter, heatmap) based on detected column types
- **Data Cleaning** (`dashboard/data_cleaning.py`) — automated cleaning pipeline with imputation and deduplication

### Module 5 — Integration & Interface
Integrates all modules and builds the user-facing interface.

- **FastAPI Backend** (`api.py`) — 2,600+ line unified API with 30+ endpoints covering auth, upload, dashboard, profiling, quality, chatbot, analytics, prediction, reports, voice, and email scheduling
- **Frontend** (`frontend/`) — 13 HTML pages with a shared CSS design system; vanilla JS with no framework dependency
- **Groq AI Chat** — token-optimised 3-tier chatbot pipeline (see [AI Chatbot](#ai-chatbot) section)
- **Chatbot Engine** (`chatbot/chatbot_engine.py`) — Streamlit-compatible Groq chatbot with `st.cache_resource` memory management

---

## AI Chatbot

The chatbot uses a 3-tier response architecture designed to maximise answer quality while minimising Groq API token consumption.

### Tier 1 — Instant (Zero Groq tokens)
Handled entirely in Python with no API call. Covers:

| Question type | Examples |
|---|---|
| Greetings | "hi", "hello", "good morning" |
| Identity / help | "who are you", "what can you do", "introduce yourself" |
| Thanks / Goodbye | "thanks", "bye", "see you" |
| KPIs | "total sales", "total profit", "profit margin", "total orders" |
| Counts | "how many rows", "how many customers", "unique customers" |
| Averages | "average sales", "avg discount", "mean profit" |
| Min / Max | "minimum profit", "highest sales value" |
| Top / Bottom N | "top 5 products by sales", "bottom 3 categories", "worst region" |
| Comparisons | "compare sales by category", "breakdown by region" |
| Sub-categories | "top sub-categories by profit" |
| Trends | "monthly sales trend" → full chronological list + peak month |
| Yearly | "yearly revenue breakdown" |
| Shipping | "average shipping delay", "days to ship" |
| Specific values | "profit for Technology", "sales in West region" |
| Follow-ups | "what about East?", "and for 2023?" → context-aware filter |
| Schema | "what columns are there?", "show me the schema" |
| Data quality | "any missing values?", "show duplicates" |

### Tier 2 — Light Groq call (~500–800 tokens)
No code generation. Groq answers using a compact KPI summary. Used when question has analytical intent but no precise query can be constructed.

### Tier 3 — Full pipeline (~1,500–2,000 tokens)
For complex analytical questions:
1. **Code-gen call** — Groq writes a pandas expression from the capped schema (max 20 columns)
2. **Execution** — expression is run safely against the real DataFrame in a sandboxed environment
3. **Answer call** — Groq explains the actual result naturally, with only the last 4 history messages as context

If Groq responds `CANNOT_ANSWER` in step 1, the pipeline returns a helpful static suggestion instead of firing step 3.

### Token savings summary

| Scenario | Before | After |
|---|---|---|
| "Who are you?" | ~4,000 tokens | **0 tokens** |
| "Total sales?" | ~3,500 tokens | **0 tokens** |
| "Top 5 products by profit?" | ~4,500 tokens | **~1,500 tokens** |
| "Compare region performance monthly?" | ~5,000 tokens | **~2,000 tokens** |

---

## API Reference

All endpoints require a `Bearer` JWT token in the `Authorization` header unless noted.

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/login` | Public | Login — returns JWT token |
| `POST` | `/api/auth/register` | Public | Register new user (role defaults to Viewer) |
| `GET` | `/api/auth/me` | Required | Get current user profile + permissions |
| `POST` | `/api/auth/change-password` | Required | Change own password (non-admin users only) |
| `GET` | `/api/users` | Admin only | List all users |
| `PUT` | `/api/users/role` | Admin only | Update user role |
| `DELETE` | `/api/users/{email}` | Admin only | Delete user |

### Dashboard & Data

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/metrics` | KPIs, charts, insights, recommendations |
| `GET` | `/api/dashboard/stream` | Server-sent events stream (30s refresh) |
| `POST` | `/api/dashboard/upload` | Upload dataset (CSV / Excel / JSON) |
| `GET` | `/api/profiling` | Full dataset profile |
| `GET` | `/api/quality` | Data quality report and score |
| `GET` | `/api/analytics` | Deep analytics (category, region, product) |
| `GET` | `/api/predict` | Sales / value forecast with confidence bands |

### Chatbot

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat/message` | Send message — 3-tier AI response |
| `DELETE` | `/api/chat/history` | Clear conversation history |
| `GET` | `/api/chat/status` | Debug — confirms Groq connection status |

### Reports

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/reports/pdf` | Generate and download PDF report |
| `POST` | `/api/reports/excel` | Generate and download Excel report |

### Voice

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/voice/transcribe` | Transcribe uploaded audio to text |
| `POST` | `/api/voice/speak` | Convert text to speech (gTTS audio) |

### Email Scheduler

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/email/status` | Check if email is configured |
| `GET` | `/api/email/schedules` | List active schedules |
| `POST` | `/api/email/schedules` | Create recurring report schedule |
| `DELETE` | `/api/email/schedules/{id}` | Remove a schedule |

---

## Setup & Installation

### Prerequisites

- Python 3.11.x
- pip

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd zero-click-ai
```

### 2. Create a virtual environment

```bash
# Windows
py -3.11 -m venv venv
venv\Scripts\activate

# macOS / Linux
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download spaCy model

```bash
python -m spacy download en_core_web_sm
```

### 5. Configure environment

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` and fill in the required values (see [Environment Variables](#environment-variables)).

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `JWT_SECRET` | ✅ | Long random string for JWT signing |
| `GROQ_API_KEY` | ✅ | Groq API key — get one free at [console.groq.com](https://console.groq.com) |
| `ALLOWED_ORIGINS` | ✅ | Comma-separated CORS origins (e.g. `http://localhost:8000`) |
| `EMAIL_PROVIDER` | Optional | `smtp`, `resend`, or `auto` (default `smtp`) |
| `RESEND_API_KEY` | Optional | Resend API key for API-based email sending |
| `RESEND_API_BASE` | Optional | Resend API base URL (default `https://api.resend.com`) |
| `SMTP_HOST` | Optional | SMTP server hostname (e.g. `smtp.gmail.com`) |
| `SMTP_PORT` | Optional | SMTP port (default `587`) |
| `SMTP_USER` | Optional | SMTP username / sender email |
| `SMTP_PASSWORD` | Optional | SMTP app password |
| `SMTP_USE_TLS` | Optional | `true` or `false` (default `true`) |
| `SENDER_EMAIL` | Optional | From address for scheduled emails |
| `SENDER_NAME` | Optional | Display name for scheduled emails |
| `DATABASE_URL` | Optional | SQLite path (default `database/scheduler.db`) |
| `USER_DB_PATH` | Optional | User-account SQLite path. Defaults to `DATABASE_URL` when unset |

> **Note:** Email scheduling is fully optional. If neither `RESEND_API_KEY` + `SENDER_EMAIL` nor SMTP credentials are set, all email endpoints return a clear "disabled" message and the rest of the app continues normally.

---

## Running the App

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Then open:

```
http://localhost:8000/
```

The root URL redirects to the frontend at `/app/`. The default admin account is created automatically on first run:

```
Email:    admin@sales.com
Password: Admin@1234
```

> **Note:** The `admin@sales.com` system account is protected — its password cannot be changed via the UI. All other users can change their password from the sidebar after logging in.

---

## Deployment

### Start command

```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

### Platform notes

- Set all environment variables in your hosting platform's dashboard — do not upload `.env` to production
- The `data/uploads/` directory is git-ignored; configure persistent storage if your platform uses ephemeral filesystems
- Point `DATABASE_URL` (and optionally `USER_DB_PATH`) to persistent storage in production
- Email scheduler is optional — the app runs fully without SMTP credentials
- Voice features degrade gracefully if browser audio or backend voice dependencies are unavailable
- Rotate any credentials that were ever committed or exposed before deploying

### Pre-deployment checklist

- [ ] `JWT_SECRET` is a long, random, unique string
- [ ] `GROQ_API_KEY` is set and valid
- [ ] `ALLOWED_ORIGINS` includes your production domain
- [ ] Default admin password has been changed
- [ ] No real secrets in `.env` committed to git

---

## Role-Based Access Control

| Permission | Admin | Sales Manager | Analyst | Executive | Viewer |
|---|:---:|:---:|:---:|:---:|:---:|
| Upload dataset | ✅ | ✅ | ✅ | — | — |
| Download reports | ✅ | ✅ | ✅ | ✅ | — |
| Use chatbot | ✅ | ✅ | ✅ | ✅ | ✅ |
| View raw data | ✅ | ✅ | ✅ | — | — |
| AI insights | ✅ | ✅ | ✅ | ✅ | — |
| All charts | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dataset profiling | ✅ | ✅ | ✅ | — | — |
| Data quality | ✅ | ✅ | ✅ | — | — |
| Predictive analytics | ✅ | ✅ | ✅ | — | — |
| Schedule email | ✅ | — | — | — | — |
| Manage users | ✅ | — | — | — | — |
| **Change own password** | — | ✅ | ✅ | ✅ | ✅ |

> **Note:** The `admin@sales.com` system account cannot change its password via the UI. All other roles can update their password from the sidebar after login. The new password is saved as a bcrypt hash in `database/users.db`.

---

## Dataset Compatibility

Zero Click AI adapts to any tabular dataset. The platform detects the dataset type automatically and adjusts its behaviour accordingly.

### Sales-compatible datasets
Datasets with `Sales`, `Revenue`, or `Profit` columns unlock the full feature set:
- Financial KPIs (total sales, profit margin, avg order value, avg discount)
- Category, regional, product, and customer analysis
- Sales forecasting with confidence bands
- AI insights and smart recommendations

### Generic datasets
Any other tabular dataset gets:
- Adaptive KPI cards based on detected numeric columns
- Column type detection and statistical summaries
- Dataset profiling and data quality scoring
- Natural language chat powered by Groq AI
- Trend charts based on detected date columns
- Correlation analysis

> The platform never fabricates sales meaning for non-sales data. If a feature requires columns that are not present, it returns a clear message rather than inventing numbers.

---

## The Team

Built by 11 interns at **Genesis Training** — Python & AI Internship Program.

| Name | Role | Module |
|---|---|---|
| Naheen Kauser *(Team Lead)* | Team Lead | Module 4 — Dashboard |
| Manu Naik | Systems Engineer | Module 5 — Integration |
| Dhaval Shah | NLP Engineer | Module 2 — Chatbot |
| Mohammed Ammar | Data Engineer | Module 1 — Data Mgmt |
| Yusuf Chonche | UI Developer | Module 4 — Dashboard |
| Vaishnavi Metri | Analytics Engineer | Module 3 — Analytics |
| Anoosha Kembhavi | Systems Engineer | Module 5 — Integration |
| Snehal Kamble | Data Engineer | Module 1 — Data Mgmt |
| Nazhat Naikwadi | Data Engineer | Module 1 — Data Mgmt |
| Keerti Gadigeppagoudar | Analytics Engineer | Module 3 — Analytics |
| Samruddhi Patil | NLP Engineer | Module 2 — Chatbot |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the branching strategy, commit conventions, and pull request workflow.

---

<div align="center">

**Zero Click AI** &nbsp;·&nbsp; Genesis Training &nbsp;·&nbsp; Python & AI Internship &nbsp;·&nbsp; Powered by Groq AI

</div>
