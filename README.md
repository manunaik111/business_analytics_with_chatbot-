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
- **Role-based authentication** — JWT-secured login, registration, and per-role permission enforcement
- **Universal file upload** — CSV, Excel (.xlsx, .xls), and JSON with automatic schema detection
- **Per-user dataset isolation** — each user's uploaded data is stored and served independently
- **Adaptive dashboard** — KPIs, charts, and insights that automatically adjust to any dataset type
- **Dark glassmorphism UI** — responsive, accessible frontend with no external UI framework dependency

### AI & Intelligence
- **Groq AI Chatbot** — powered by LLaMA 3.3 70B via Groq API; answers natural language questions about the loaded dataset with full conversation memory
- **AI Insights** — auto-generated business insights from KPI data using the analytics engine
- **Smart Recommendations** — actionable recommendations derived from dataset patterns
- **Predictive Analytics** — linear + SES ensemble forecasting with seasonality adjustment and confidence bands

### Data Management
- **Dataset Profiling** — row/column counts, data types, null rates, cardinality, and statistical summaries
- **Data Quality Checks** — missing value detection, duplicate identification, outlier analysis, inconsistency flagging, and a composite quality score
- **Schema Mapping** — automatic column detection for sales, date, region, category, and item fields across any dataset structure

### NLP Pipeline
- **Intent Classification** — TF-IDF + scikit-learn classifier trained on sales query patterns
- **Entity Extraction** — product name, region, category, and metric entity recognition
- **Query Execution** — structured query execution against the active DataFrame
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
│   ├── nlp_processor.py        # Query parsing entry point
│   ├── data_processor.py       # Query execution against DataFrame
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

- **NLP Processor** (`nlp/nlp_processor.py`) — entry point; orchestrates preprocessing → intent classification → entity extraction → query parsing
- **Intent Classifier** (`nlp/intent_classifier.py`) — TF-IDF vectorizer + scikit-learn classifier trained on sales query patterns (Sales Query, Profit Query, Ranking Query, Regional Query, Trend Query, Category Query, Segment Query, Comparison Query)
- **Entity Extractor** (`nlp/entity_extractor.py`) — extracts product names, regions, categories, metrics, and time references from query text
- **Data Processor** (`nlp/data_processor.py`) — executes structured queries against the active pandas DataFrame
- **Response Generator** (`nlp/response_generator.py`) — converts query results into natural language template responses
- **Voice Input** (`nlp/voice_input.py`) — microphone transcription via SpeechRecognition (Google backend); accepts audio bytes for FastAPI endpoint
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
- **KPI Generator** (`dashboard/kpi_generator.py`) — produces up to 12 adaptive KPI cards from any dataset; handles sales-specific metrics (total sales, profit margin, avg order value) and generic numeric summaries
- **Visualisation** (`dashboard/visualization.py`) — auto-generates charts (line, bar, doughnut, scatter, heatmap) based on detected column types
- **Data Cleaning** (`dashboard/data_cleaning.py`) — automated cleaning pipeline with imputation and deduplication; tracks a cleaning report for KPI display

### Module 5 — Integration & Interface
Integrates all modules and builds the user-facing interface.

- **FastAPI Backend** (`api.py`) — 1,700+ line unified API with 30+ endpoints covering auth, upload, dashboard, profiling, quality, chatbot, analytics, prediction, reports, voice, and email scheduling
- **Frontend** (`frontend/`) — 13 HTML pages with a shared CSS design system; vanilla JS with no framework dependency; Chart.js for visualisation; SheetJS for client-side file parsing
- **Groq AI Chat** — `chat_message` endpoint builds a dynamic system prompt from the active dataset, runs the NLP pipeline for structured data context, then calls Groq LLaMA 3.3 70B with full conversation history
- **Chatbot Engine** (`chatbot/chatbot_engine.py`) — Streamlit-compatible Groq chatbot with `st.cache_resource` memory management

---

## API Reference

All endpoints require a `Bearer` JWT token in the `Authorization` header unless noted.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Login — returns JWT token |
| `POST` | `/api/auth/register` | Register new user |
| `GET` | `/api/auth/me` | Get current user profile |
| `GET` | `/api/users` | List all users (Admin only) |
| `PUT` | `/api/users/role` | Update user role (Admin only) |
| `DELETE` | `/api/users/{email}` | Delete user (Admin only) |

### Dashboard & Data

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/metrics` | KPIs, charts, insights, recommendations |
| `POST` | `/api/dashboard/upload` | Upload dataset (CSV / Excel / JSON) |
| `GET` | `/api/profiling` | Full dataset profile |
| `GET` | `/api/quality` | Data quality report and score |
| `GET` | `/api/analytics` | Deep analytics (category, region, product) |
| `GET` | `/api/predict` | Sales / value forecast with confidence bands |

### Chatbot

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat/message` | Send message — returns Groq AI response |
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
| `SMTP_HOST` | Optional | SMTP server hostname (e.g. `smtp.gmail.com`) |
| `SMTP_PORT` | Optional | SMTP port (default `587`) |
| `SMTP_USER` | Optional | SMTP username / sender email |
| `SMTP_PASSWORD` | Optional | SMTP app password |
| `SMTP_USE_TLS` | Optional | `true` or `false` (default `true`) |
| `SENDER_EMAIL` | Optional | From address for scheduled emails |
| `SENDER_NAME` | Optional | Display name for scheduled emails |
| `DATABASE_URL` | Optional | SQLite path (default `database/scheduler.db`) |

> **Note:** Email scheduling is fully optional. If `SMTP_USER` and `SMTP_PASSWORD` are not set, all email endpoints return a clear "disabled" message and the rest of the app continues normally.

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

> Change this password immediately after first login.

---

## Deployment

### Start command

```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

### Platform notes

- Set all environment variables in your hosting platform's dashboard — do not upload `.env` to production
- The `data/uploads/` directory is git-ignored; configure persistent storage if your platform uses ephemeral filesystems
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
