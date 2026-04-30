"""
api.py — Zero Click AI · FastAPI Backend v2.1
Complete corrected version — all function signatures verified against team files.

Files used:
  analytics/analysis.py          → RetailDataAnalyzer, calculate_kpis()
  analytics/insights.py          → generate_ai_insights(kpis)
  analytics/my_recommendations.py → generate_smart_recommendations(kpis)
  analytics/predictive_engine.py  → SalesPredictiveEngine(df=df).run_full_forecast()
  data_management/dataset_profiling.py → generate_profiling_table(df)
  data_management/data_quality.py → check_duplicates, check_missing_values,
                                     check_outliers, check_inconsistencies,
                                     compute_quality_score, generate_warnings
  dashboard/data_analysis.py      → get_column_types(df)
  dashboard/kpi_generator.py      → generate_kpis(df, col_types) → list of tuples
  report_generator.py             → generate_report_pdf(df,kpis,ml,forecast,insights,charts)
                                     generate_report_excel(df,kpis,ml,forecast,insights)
  email_scheduler/smtp_client.py  → EmailClient
  email_scheduler/job_scheduler.py → ReportScheduler
  email_scheduler/db_manager.py   → DatabaseManager
"""

import os, io, json, asyncio, uuid, sys, sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional

# Fix 1 — load .env before os.getenv() is called anywhere
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import numpy as np
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
# Fix 2 — python-jose instead of PyJWT (avoids fresh-install crash)
from jose import jwt, JWTError
from passlib.context import CryptContext

# Fix 5 — schema mapper import
try:
    from data_management.schema_mapper import (
        map_columns, detect_dataset_type,
        get_missing_warnings, build_chatbot_suggestions
    )
    HAS_SCHEMA_MAPPER = True
except Exception:
    HAS_SCHEMA_MAPPER = False

try:
    from data_management.upload_store import (
        save_user_upload, load_user_upload, load_user_meta, clear_user_upload
    )
    HAS_UPLOAD_STORE = True
except Exception:
    HAS_UPLOAD_STORE = False
# File upload validation/parsing helpers
try:
    from data_management.file_upload import (
        validate_filename_and_size, parse_bytes_to_df,
        normalize_columns, auto_parse_dates, UploadValidationError
    )
    HAS_FILE_UPLOAD = True
except Exception:
    HAS_FILE_UPLOAD = False


# ── Suppress stdout from team modules that use print() ───────────────────────
@contextmanager
def _suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old

# ── Internal module imports with safe fallbacks ───────────────────────────────
try:
    from analytics.insights import generate_ai_insights
    HAS_AI_INSIGHTS = True
except Exception:
    HAS_AI_INSIGHTS = False

try:
    from analytics.my_recommendations import generate_smart_recommendations
    HAS_RECS = True
except Exception:
    HAS_RECS = False

try:
    from analytics.analysis import RetailDataAnalyzer
    HAS_ANALYZER = True
except Exception:
    HAS_ANALYZER = False

try:
    from analytics.predictive_engine import SalesPredictiveEngine
    HAS_PREDICT = True
except Exception:
    HAS_PREDICT = False

# dataset_profiling imports streamlit — import only the pure function
try:
    import importlib.util, types
    # Stub streamlit so dataset_profiling doesn't crash
    if "streamlit" not in sys.modules:
        sys.modules["streamlit"] = types.ModuleType("streamlit")
    from data_management.dataset_profiling import (
        generate_profiling_table, generate_profiling_summary, validate_upload
    )
    HAS_PROFILING = True
except Exception:
    HAS_PROFILING = False

# data_quality also imports streamlit — same stub approach
try:
    from data_management.data_quality import (
        check_duplicates, check_missing_values, check_outliers,
        check_inconsistencies, compute_quality_score, generate_warnings
    )
    HAS_QUALITY = True
except Exception:
    HAS_QUALITY = False

# NLP modules
try:
    from nlp.nlp_processor import process_query
    from nlp.data_processor import execute_query
    from nlp.response_generator import generate_response
    HAS_NLP = True
except Exception:
    HAS_NLP = False

# Report generator
try:
    from report_generator import generate_report_pdf, generate_report_excel
    HAS_REPORTS = True
except Exception:
    HAS_REPORTS = False

# dashboard modules
try:
    from dashboard.data_analysis import get_column_types
    HAS_COL_TYPES = True
except Exception:
    HAS_COL_TYPES = False

# Email scheduler modules (from zip)
try:
    from email_scheduler.db_manager import DatabaseManager
    from email_scheduler.job_scheduler import ReportScheduler
    from email_scheduler.smtp_client import EmailClient
    _email_db = DatabaseManager()
    _email_db.initialize()
    _scheduler = ReportScheduler(_email_db)
    _scheduler.start()
    HAS_SCHEDULER = True
except Exception:
    HAS_SCHEDULER = False
    _email_db = None
    _scheduler = None

# ── Config ────────────────────────────────────────────────────────────────────
SECRET_KEY   = os.getenv("JWT_SECRET", "genesis-secret-key-change-in-prod")
ALGORITHM    = "HS256"
TOKEN_EXPIRY = 24
USER_DB_PATH = os.getenv("USER_DB_PATH") or os.getenv("DATABASE_URL", os.path.join("database", "users.db"))
USER_DB_TABLE = "app_users"
LEGACY_USERS_FILE = "users.json"
DATA_FILE    = os.path.join("data", "SALES_DATA_SETT.csv")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

os.makedirs("generated_reports", exist_ok=True)
os.makedirs(os.path.dirname(USER_DB_PATH) or ".", exist_ok=True)

pwd_ctx  = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

app = FastAPI(title="Zero Click AI API", version="2.1.0")

# Fix 3 — Serve frontend from one URL (FastAPI serves everything)
_frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(_frontend_path):
    app.mount("/app", StaticFiles(directory=_frontend_path, html=True), name="frontend")

@app.get("/")
def frontend_root():
    return RedirectResponse(url="/app/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

# ── In-memory state ───────────────────────────────────────────────────────────
_uploaded_df_cache: dict[str, pd.DataFrame] = {}
_upload_meta_cache: dict[str, dict] = {}
_chat_history: dict = {}

# ── Role permission map ───────────────────────────────────────────────────────
ROLE_PERMS = {
    "Admin":         {"upload","download","chatbot","raw_data","manage_users",
                      "ai_insights","all_charts","schedule_email","profiling","quality","predict"},
    "Sales Manager": {"upload","download","chatbot","raw_data","ai_insights",
                      "all_charts","profiling","quality","predict"},
    "Analyst":       {"upload","download","chatbot","raw_data","ai_insights",
                      "all_charts","profiling","quality","predict"},
    "Executive":     {"download","chatbot","ai_insights","all_charts"},
    "Viewer":        {"chatbot","all_charts"},
}

def _has_perm(user, perm):
    return perm in ROLE_PERMS.get(user.get("role", "Viewer"), set())

def _require_perm(user, perm):
    if not _has_perm(user, perm):
        raise HTTPException(403, f"Your role does not have '{perm}' permission.")


def _json_safe(value):
    """Convert numpy/pandas scalar values into JSON-serializable Python values."""
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _email_env_status() -> dict:
    provider_preference = os.getenv("EMAIL_PROVIDER", "smtp").strip().lower()
    resend_key = os.getenv("RESEND_API_KEY", "").strip()
    sender_email = os.getenv("SENDER_EMAIL", "").strip()
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = (os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS", "")).strip()

    has_resend = bool(resend_key and sender_email)
    has_smtp = bool(smtp_user and smtp_password)
    if provider_preference == "resend":
        active_provider = "resend" if has_resend else "disabled"
    elif provider_preference == "smtp":
        active_provider = "smtp" if has_smtp else "disabled"
    else:
        active_provider = "resend" if has_resend else ("smtp" if has_smtp else "disabled")

    enabled = HAS_SCHEDULER and active_provider != "disabled"
    if enabled:
        message = f"Email scheduler is available via {active_provider.capitalize()}."
    else:
        message = (
            "Email is optional and currently disabled. Set EMAIL_PROVIDER=resend with "
            "RESEND_API_KEY and SENDER_EMAIL, or configure SMTP_USER and SMTP_PASSWORD."
        )

    return {
        "enabled": enabled,
        "has_scheduler_module": HAS_SCHEDULER,
        "provider_preference": provider_preference,
        "provider": active_provider,
        "has_resend_credentials": has_resend,
        "has_smtp_credentials": has_smtp,
        "message": message,
    }


def _require_email_enabled() -> None:
    status = _email_env_status()
    if not status["has_scheduler_module"]:
        raise HTTPException(503, "Email scheduler module not available. Ensure email_scheduler/ folder is in project root.")
    if not status["enabled"]:
        raise HTTPException(503, status["message"])

# ═════════════════════════════════════════════════════════════════════════════
# USER STORAGE
# ═════════════════════════════════════════════════════════════════════════════
def _user_db_conn():
    conn = sqlite3.connect(USER_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _seed_default_users(conn) -> None:
    conn.execute(
        f"""
        INSERT OR IGNORE INTO {USER_DB_TABLE} (email, name, password_hash, role, created_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "admin@sales.com",
            "Sales Admin",
            pwd_ctx.hash("Admin@1234"),
            "Admin",
            datetime.utcnow().isoformat(),
            1,
        ),
    )


def _migrate_legacy_users(conn) -> None:
    if not os.path.exists(LEGACY_USERS_FILE):
        return

    count = conn.execute(f"SELECT COUNT(*) FROM {USER_DB_TABLE}").fetchone()[0]
    if count > 0:
        return

    try:
        with open(LEGACY_USERS_FILE) as f:
            legacy_users = json.load(f)
    except Exception:
        legacy_users = {}

    for email, user in legacy_users.items():
        conn.execute(
            f"""
            INSERT OR REPLACE INTO {USER_DB_TABLE} (email, name, password_hash, role, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                email.lower().strip(),
                user.get("name", ""),
                user.get("password", ""),
                user.get("role", "Viewer"),
                user.get("created_at", datetime.utcnow().isoformat()),
                1 if user.get("active", True) else 0,
            ),
        )


def _init_user_store() -> None:
    conn = _user_db_conn()
    try:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {USER_DB_TABLE} (
                email TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        _migrate_legacy_users(conn)
        _seed_default_users(conn)
        conn.commit()
    finally:
        conn.close()


def _load_users() -> dict:
    _init_user_store()
    conn = _user_db_conn()
    try:
        rows = conn.execute(
            f"""
            SELECT email, name, password_hash, role, created_at, is_active
            FROM {USER_DB_TABLE}
            ORDER BY email
            """
        ).fetchall()
    finally:
        conn.close()

    return {
        row["email"]: {
            "name": row["name"],
            "password": row["password_hash"],
            "role": row["role"],
            "created_at": row["created_at"],
            "active": bool(row["is_active"]),
        }
        for row in rows
    }


def _save_users(users: dict) -> None:
    _init_user_store()
    conn = _user_db_conn()
    try:
        existing = {
            row["email"]
            for row in conn.execute(f"SELECT email FROM {USER_DB_TABLE}").fetchall()
        }
        incoming = {email.lower().strip() for email in users.keys()}

        for email, user in users.items():
            normalized_email = email.lower().strip()
            conn.execute(
                f"""
                INSERT INTO {USER_DB_TABLE} (email, name, password_hash, role, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    name = excluded.name,
                    password_hash = excluded.password_hash,
                    role = excluded.role,
                    created_at = excluded.created_at,
                    is_active = excluded.is_active
                """,
                (
                    normalized_email,
                    user.get("name", ""),
                    user.get("password", ""),
                    user.get("role", "Viewer"),
                    user.get("created_at", datetime.utcnow().isoformat()),
                    1 if user.get("active", True) else 0,
                ),
            )

        removed = existing - incoming
        if removed:
            conn.executemany(f"DELETE FROM {USER_DB_TABLE} WHERE email = ?", [(email,) for email in removed])

        conn.commit()
    finally:
        conn.close()

# ═════════════════════════════════════════════════════════════════════════════
# JWT
# ═════════════════════════════════════════════════════════════════════════════
def _create_token(email: str, role: str) -> str:
    return jwt.encode(
        {"sub": email, "role": role,
         "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY)},
        SECRET_KEY, algorithm=ALGORITHM
    )

def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(401, "Invalid or expired token.")

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not creds:
        raise HTTPException(401, "Not authenticated.")
    return _decode_token(creds.credentials)

# ═════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═════════════════════════════════════════════════════════════════════════════
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class ChatRequest(BaseModel):
    message: str
    filters: dict = {}
    rows: list = []

class UpdateRoleRequest(BaseModel):
    email: str
    role: str

class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "Viewer"

class EmailScheduleRequest(BaseModel):
    recipient_email: str
    subject: str = "Scheduled Sales Report"
    frequency: str = "Daily"        # Daily | Weekly | Monthly
    schedule_time: str = "09:00"
    report_type: str = "full"       # summary | insights | dashboard | performance | full
    filters: dict = {}

class VoiceSpeakRequest(BaseModel):
    text: str

# ═════════════════════════════════════════════════════════════════════════════
# DATA HELPERS
# ═════════════════════════════════════════════════════════════════════════════
def _user_id(user: Optional[dict]) -> str:
    return (user or {}).get("sub", "anonymous")


def _get_upload_meta(user: Optional[dict]) -> dict:
    if not user:
        return {}
    uid = _user_id(user)
    if uid in _upload_meta_cache:
        return _upload_meta_cache[uid].copy()
    if HAS_UPLOAD_STORE:
        meta = load_user_meta(uid)
        if meta:
            _upload_meta_cache[uid] = meta
            return meta.copy()
    return {}


def _set_user_upload(user: dict, df: pd.DataFrame, meta: dict) -> None:
    uid = _user_id(user)
    _uploaded_df_cache[uid] = df.copy()
    _upload_meta_cache[uid] = meta.copy()
    if HAS_UPLOAD_STORE:
        save_user_upload(uid, df, meta)


def _clear_user_upload(user: dict) -> None:
    uid = _user_id(user)
    _uploaded_df_cache.pop(uid, None)
    _upload_meta_cache.pop(uid, None)
    if HAS_UPLOAD_STORE:
        clear_user_upload(uid)


def _get_df(user: Optional[dict] = None) -> Optional[pd.DataFrame]:
    """Return current user's uploaded df if available, else default CSV."""
    if user:
        uid = _user_id(user)
        if uid in _uploaded_df_cache:
            return _uploaded_df_cache[uid].copy()
        if HAS_UPLOAD_STORE:
            try:
                stored = load_user_upload(uid)
                if stored is not None:
                    _uploaded_df_cache[uid] = stored
                    _upload_meta_cache[uid] = load_user_meta(uid)
                    return stored.copy()
            except Exception:
                pass
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
            df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True, errors="coerce")
            df["Ship Date"]  = pd.to_datetime(df["Ship Date"],  dayfirst=True, errors="coerce")
            if "shipping_delay_days" not in df.columns:
                df["shipping_delay_days"] = (df["Ship Date"] - df["Order Date"]).dt.days.fillna(0)
            return df
        except Exception:
            pass
    return None

def _apply_filters(df: pd.DataFrame, category: str, region: str,
                   year: str, profit: str) -> pd.DataFrame:
    f = df.copy()
    if category != "All" and "Category" in f.columns:
        f = f[f["Category"] == category]
    if region != "All" and "Region" in f.columns:
        f = f[f["Region"] == region]
    if year != "All":
        date_col = None
        if "Order Date" in f.columns and pd.api.types.is_datetime64_any_dtype(f["Order Date"]):
            date_col = "Order Date"
        else:
            for c in f.columns:
                if pd.api.types.is_datetime64_any_dtype(f[c]):
                    date_col = c
                    break
        if date_col:
            try:
                f = f[f[date_col].dt.year == int(year)]
            except Exception:
                pass
    if profit == "Profitable" and "Profit" in f.columns:
        f = f[f["Profit"] > 0]
    elif profit == "Loss Making" and "Profit" in f.columns:
        f = f[f["Profit"] < 0]
    return f

def _build_kpis_dict(df: pd.DataFrame) -> dict:
    """
    Build kpi dict matching RetailDataAnalyzer.calculate_kpis() structure.
    Used by generate_smart_recommendations() and generate_ai_insights().
    Keys: total_sales, total_profit, total_orders, total_quantity,
          unique_customers, avg_order_value, avg_discount, avg_shipping_delay
    """
    s      = float(df["Sales"].sum())     if "Sales"    in df.columns else 0.0
    p      = float(df["Profit"].sum())    if "Profit"   in df.columns else 0.0
    orders = int(df["Order ID"].nunique()) if "Order ID" in df.columns else len(df)
    qty    = int(df["Quantity"].sum())    if "Quantity" in df.columns else 0
    custs  = int(df["Customer ID"].nunique()) if "Customer ID" in df.columns else 0
    disc   = float(df["Discount"].mean()) if "Discount" in df.columns else 0.0
    ship   = float(df["shipping_delay_days"].mean()) if "shipping_delay_days" in df.columns else 0.0
    if pd.isna(ship):
        ship = 0.0
    return {
        "total_sales":       s,
        "total_profit":      p,
        "total_orders":      orders,
        "total_quantity":    qty,
        "unique_customers":  custs,
        "avg_order_value":   s / orders if orders > 0 else 0.0,
        "avg_discount":      disc,
        "avg_shipping_delay": ship,
    }


def _is_sales_compatible(df: pd.DataFrame) -> bool:
    return "Sales" in df.columns


def _find_datetime_column(df: pd.DataFrame) -> Optional[str]:
    if "Order Date" in df.columns:
        return "Order Date"
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    for col in df.columns:
        if "date" in str(col).lower():
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().sum() >= max(2, int(len(df) * 0.6)):
                df[col] = parsed
                return col
    return None


def _find_numeric_target_column(df: pd.DataFrame) -> Optional[str]:
    preferred = ["Sales", "Revenue", "Amount", "Total", "Profit", "Quantity"]
    for col in preferred:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            return col
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    return numeric_cols[0] if numeric_cols else None


def _find_region_column(df: pd.DataFrame) -> Optional[str]:
    if "Region" in df.columns:
        return "Region"
    for col in df.columns:
        key = str(col).lower()
        if any(token in key for token in ["region", "state", "country", "location", "city", "market"]):
            return col
    return None


def _find_category_column(df: pd.DataFrame) -> Optional[str]:
    if "Category" in df.columns:
        return "Category"
    for col in df.columns:
        key = str(col).lower()
        if any(token in key for token in ["category", "segment", "type", "severity", "group", "class"]):
            return col
    return None


def _find_item_column(df: pd.DataFrame) -> Optional[str]:
    preferred = ["Product Name", "Product", "Item", "Name"]
    for col in preferred:
        if col in df.columns:
            return col
    for col in df.select_dtypes(include=["object", "category"]).columns:
        key = str(col).lower()
        if any(token in key for token in ["product", "item", "name", "description", "authority", "model"]):
            return col
    categorical = df.select_dtypes(include=["object", "category"]).columns.tolist()
    return categorical[0] if categorical else None


def _apply_request_filters(df: Optional[pd.DataFrame], filters: Optional[dict]) -> Optional[pd.DataFrame]:
    if df is None:
        return None
    filters = filters or {}
    return _apply_filters(
        df,
        str(filters.get("category", "All")),
        str(filters.get("region", "All")),
        str(filters.get("year", "All")),
        str(filters.get("profit", "All")),
    )


def _format_chat_metric(value, money: bool = False, digits: int = 2) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)

    if money:
        if abs(num) >= 100 or num == int(num):
            return f"${num:,.0f}"
        return f"${num:,.{digits}f}"
    if abs(num) >= 100 or num == int(num):
        return f"{num:,.0f}"
    return f"{num:,.{digits}f}"


def _detect_metric_column_from_question(question: str, df: pd.DataFrame) -> Optional[str]:
    lower = question.lower()
    aliases = [
        ("sales", "Sales"),
        ("revenue", "Revenue"),
        ("revenue", "Sales"),
        ("profit", "Profit"),
        ("quantity", "Quantity"),
        ("discount", "Discount"),
        ("order", "Order ID"),
        ("customer", "Customer ID"),
    ]
    for term, column in aliases:
        if term in lower and column in df.columns:
            return column

    if HAS_NLP:
        try:
            parsed = process_query(question, df=df, dataset_meta={})
            metric = parsed.get("metric")
            if metric in df.columns:
                return metric
        except Exception:
            pass

    return _find_numeric_target_column(df)


def _try_structured_chat_response(question: str, df: Optional[pd.DataFrame], meta: dict, history: list = None) -> Optional[str]:
    import re as _re
    lower = question.strip().lower()
    if not lower:
        return "Ask me about your dataset, KPIs, or the current filters."

    # Fix #12: Follow-up question detection
    # Detect short follow-ups like "what about West?", "and for 2023?", "how about Technology?"
    history = history or []
    _followup_triggers = ("what about", "how about", "and for", "and the", "what of",
                          "now for", "same for", "also for", "for the")
    is_followup = any(lower.startswith(t) for t in _followup_triggers) or (
        len(lower.split()) <= 4 and not any(lower.startswith(g) for g in
            ["hi", "hello", "hey", "help", "who", "what", "show", "list", "top",
             "total", "how many", "compare", "trend"])
    )
    if is_followup and history and df is not None and not df.empty:
        import re as _re_fu
        # Extract the filter value from the question (last 1-2 words)
        filter_val = _re_fu.sub(
            r"^(what about|how about|and for|and the|what of|now for|same for|also for|for the)\s*",
            "", lower
        ).strip().rstrip("?")
        if filter_val:
            # Look up all categorical columns and see if filter_val matches a value
            cat_cols = [_find_category_column(df), _find_region_column(df)]
            for gc in cat_cols:
                if not gc:
                    continue
                unique_vals = df[gc].dropna().astype(str).str.lower().unique()
                matched = next((v for v in unique_vals if filter_val in v or v in filter_val), None)
                if matched:
                    mask = df[gc].astype(str).str.lower() == matched
                    sub_df = df[mask]
                    if sub_df.empty:
                        continue
                    display = df[gc][mask].iloc[0]
                    # Infer what the last answer was about from history
                    last_bot = next(
                        (h["content"] for h in reversed(history) if h["role"] == "assistant"), ""
                    )
                    target_col = _find_numeric_target_column(sub_df)
                    if "profit" in last_bot.lower() and "Profit" in sub_df.columns:
                        target_col = "Profit"
                    elif "sales" in last_bot.lower() and "Sales" in sub_df.columns:
                        target_col = "Sales"
                    elif "revenue" in last_bot.lower() and "Sales" in sub_df.columns:
                        target_col = "Sales"
                    if target_col and target_col in sub_df.columns:
                        total = sub_df[target_col].sum()
                        money = target_col in {"Sales", "Revenue", "Profit"}
                        avg = sub_df[target_col].mean()
                        return (
                            f"For {display}: {target_col} total is "
                            f"{_format_chat_metric(total, money=money)}, "
                            f"avg {_format_chat_metric(avg, money=money)} "
                            f"across {len(sub_df):,} records."
                        )

    # Greetings
    _greet = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "how are you"]
    if any(lower == g or lower.startswith(g + " ") or lower.startswith(g + "!") or lower.startswith(g + ",") for g in _greet):
        return "Hi! I can help with KPIs, trends, top performers, comparisons, data quality, and more. What would you like to know?"

    # Thanks / Bye  (#18 fix)
    if any(lower == g or lower.startswith(g) for g in ["thanks", "thank you", "cheers", "bye", "goodbye", "see you"]):
        return "You're welcome! Let me know if you have any other questions about the data."

    # Identity / help  (#1 fix — zero token)
    _identity = [
        "who are you", "what are you", "what can you do", "what do you do",
        "tell me about yourself", "tell me about you", "what is this",
        "what is zero click", "what is caesar", "what is this chatbot",
        "help me", "help", "how can you help", "how do you work",
        "what kind of questions", "what questions can i ask",
        "what should i ask", "what can i ask",
        "are you an ai", "are you a bot", "are you human",
        "introduce yourself", "your name", "who made you",
    ]
    if any(p in lower for p in _identity):
        return (
            "I'm your AI Dataset Assistant. Here's what you can ask:\n"
            "\u2022 KPIs: 'total sales', 'profit margin', 'total orders'\n"
            "\u2022 Top/Bottom: 'top 5 products by sales', 'worst region by profit'\n"
            "\u2022 Comparisons: 'compare sales by category', 'breakdown by region'\n"
            "\u2022 Trends: 'monthly sales trend', 'yearly revenue breakdown'\n"
            "\u2022 Data quality: 'any missing values?', 'show duplicates'\n"
            "\u2022 Stats: 'average discount', 'min profit', 'unique customers'"
        )

    if df is None or df.empty:
        return "No data is loaded for the current filters yet."

    # Setup
    metric_col = _detect_metric_column_from_question(question, df)
    money_metric = metric_col in {"Sales", "Revenue", "Profit"}
    kpis = _build_kpis_dict(df)
    numeric_target = _find_numeric_target_column(df)

    def _money(col): return col in {"Sales", "Revenue", "Profit"}

    def _groupby_answer(group_col, target_col, ascending=False, top_n=None, label=""):
        """Generic groupby helper — avoids repeating the same pattern."""
        if not group_col or not target_col:
            return None
        if not pd.api.types.is_numeric_dtype(df[target_col]):
            return None
        grouped = df.groupby(group_col)[target_col].sum().sort_values(ascending=ascending)
        if grouped.empty:
            return None
        if top_n:
            grouped = grouped.head(top_n)
            money = _money(target_col)
            lines = [f"{i+1}. {lbl} ({_format_chat_metric(v, money=money)})" for i,(lbl,v) in enumerate(grouped.items())]
            return (label or f"Top {top_n} by {target_col.lower()}") + ":\n" + "\n".join(lines)
        money = _money(target_col)
        direction = "lowest" if ascending else "top"
        return f"{grouped.index[0]} has the {direction} {target_col.lower()} at {_format_chat_metric(grouped.iloc[0], money=money)}."

    # Row count
    if any(t in lower for t in ("row count", "record count", "how many rows", "how many records",
                                "number of rows", "number of records", "total records")):
        return f"There are {len(df):,} records in the current filtered dataset."

    # Columns / schema
    if any(t in lower for t in ("column", "schema", "field", "what data", "what information")):
        cols = df.columns.tolist()
        preview = ", ".join(cols[:10])
        suffix = f" ... and {len(cols)-10} more" if len(cols) > 10 else ""
        return f"This dataset has {len(cols)} columns: {preview}{suffix}."

    # Dataset name
    if "dataset" in lower and any(t in lower for t in ("what", "which", "current", "loaded", "upload")):
        dataset_name = meta.get("filename") or meta.get("datasetName") or "the current dataset"
        return f"You are working with '{dataset_name}', filtered to {len(df):,} rows."

    # Total sales
    if any(t in lower for t in ("total sales", "sales total", "total revenue", "revenue total")) and _is_sales_compatible(df):
        return f"Total sales for the current filters: {_format_chat_metric(kpis['total_sales'], money=True)}."

    # Total profit
    if any(t in lower for t in ("total profit", "profit total", "net profit")) and "Profit" in df.columns:
        return f"Total profit for the current filters: {_format_chat_metric(kpis['total_profit'], money=True)}."

    # Profit margin
    if "profit margin" in lower and kpis["total_sales"]:
        margin = (kpis["total_profit"] / kpis["total_sales"]) * 100
        return f"Profit margin for the current filters: {margin:,.1f}%."

    # Orders
    if any(t in lower for t in ("total orders", "number of orders", "how many orders", "order count")):
        return f"Total orders for the current filters: {kpis['total_orders']:,}."

    # Quantity
    if any(t in lower for t in ("total quantity", "units sold", "quantity sold", "total units")) and "Quantity" in df.columns:
        return f"Total quantity sold: {kpis['total_quantity']:,} units."

    # Customers  (#8 fix)
    if any(t in lower for t in ("unique customers", "how many customers", "number of customers",
                                "customer count", "total customers")):
        cust_col = "Customer ID" if "Customer ID" in df.columns else next(
            (c for c in df.columns if "customer" in c.lower()), None)
        if cust_col:
            count = int(df[cust_col].nunique())
            return f"There are {count:,} unique customers in the current filtered dataset."

    # Shipping / delivery  (#9 fix)
    if any(t in lower for t in ("shipping", "delivery", "ship time", "shipping delay", "days to ship", "avg ship")):
        if "shipping_delay_days" in df.columns:
            avg_ship = float(df["shipping_delay_days"].mean())
            if not pd.isna(avg_ship):
                return f"Average shipping delay: {avg_ship:.1f} days for the current filters."
        elif "Ship Date" in df.columns and "Order Date" in df.columns:
            delay = (pd.to_datetime(df["Ship Date"], errors="coerce") -
                     pd.to_datetime(df["Order Date"], errors="coerce")).dt.days.mean()
            if not pd.isna(delay):
                return f"Average shipping delay: {delay:.1f} days for the current filters."

    # Discount
    if any(t in lower for t in ("discount", "avg discount", "average discount")) and "Discount" in df.columns:
        avg_disc = float(df["Discount"].mean()) * 100
        return f"Average discount rate: {avg_disc:.1f}% for the current filters."

    # Average / Mean  (#3 fix — works even without pre-detected metric_col)
    avg_col = metric_col if metric_col and metric_col in df.columns else numeric_target
    if any(t in lower for t in ("average", "avg", "mean")) and avg_col:
        if pd.api.types.is_numeric_dtype(df[avg_col]):
            val = pd.to_numeric(df[avg_col], errors="coerce").mean()
            if not pd.isna(val):
                return f"Average {avg_col.lower()}: {_format_chat_metric(val, money=_money(avg_col))}."

    # Min / Lowest single value  (#10 fix)
    min_col = metric_col if metric_col and metric_col in df.columns else numeric_target
    if any(t in lower for t in ("minimum", "min value", "lowest value", "smallest")) and min_col:
        if pd.api.types.is_numeric_dtype(df[min_col]):
            val = pd.to_numeric(df[min_col], errors="coerce").min()
            if not pd.isna(val):
                return f"Minimum {min_col.lower()}: {_format_chat_metric(val, money=_money(min_col))}."

    # Max / Highest single value
    max_col = metric_col if metric_col and metric_col in df.columns else numeric_target
    if any(t in lower for t in ("maximum", "max value", "highest value", "largest value")) and max_col:
        if pd.api.types.is_numeric_dtype(df[max_col]):
            val = pd.to_numeric(df[max_col], errors="coerce").max()
            if not pd.isna(val):
                return f"Maximum {max_col.lower()}: {_format_chat_metric(val, money=_money(max_col))}."

    # Compare / Breakdown  (#5 fix)
    _cmp = ("compare", "breakdown", "split by", "group by", "by region", "by category",
            "across regions", "across categories", "per region", "per category",
            "for each region", "for each category")
    if any(t in lower for t in _cmp):
        if any(t in lower for t in ("region", "state", "country", "city", "location")):
            group_col = _find_region_column(df)
        elif any(t in lower for t in ("sub-category", "subcategory")):
            group_col = next((c for c in df.columns if "sub" in c.lower() and "cat" in c.lower()), _find_category_column(df))
        else:
            group_col = _find_category_column(df)
        target_col = metric_col if metric_col and metric_col in df.columns and metric_col != "Order ID" else numeric_target
        if group_col and target_col and pd.api.types.is_numeric_dtype(df[target_col]):
            grouped = df.groupby(group_col)[target_col].sum().sort_values(ascending=False)
            if not grouped.empty:
                money = _money(target_col)
                lines = [f"  {lbl}: {_format_chat_metric(v, money=money)}" for lbl, v in grouped.items()]
                return f"{target_col} breakdown by {group_col}:\n" + "\n".join(lines)

    # Sub-category breakdown  (#11 fix)
    if any(t in lower for t in ("sub-category", "subcategory", "sub category")):
        subcat_col = next((c for c in df.columns if "sub" in c.lower() and "cat" in c.lower()), None)
        target_col = metric_col if metric_col and metric_col in df.columns and metric_col != "Order ID" else numeric_target
        if subcat_col and target_col and pd.api.types.is_numeric_dtype(df[target_col]):
            grouped = df.groupby(subcat_col)[target_col].sum().sort_values(ascending=False).head(10)
            if not grouped.empty:
                money = _money(target_col)
                lines = [f"{i+1}. {lbl} ({_format_chat_metric(v, money=money)})" for i,(lbl,v) in enumerate(grouped.items())]
                return f"Top sub-categories by {target_col.lower()}:\n" + "\n".join(lines)

    # Bottom/Worst region  (#4 fix)
    _region_worst = ("worst region", "lowest region", "bottom region", "least region",
                     "which region has the lowest", "which region has the least",
                     "region with the lowest", "region with the least")
    _region_best = ("top region", "best region", "highest region", "leading region",
                    "which region", "region with the highest", "region with the most",
                    "region with the best", "region has the highest", "region has the most")
    if any(t in lower for t in _region_worst):
        target_col = metric_col if metric_col and metric_col in df.columns and metric_col != "Order ID" else numeric_target
        ans = _groupby_answer(_find_region_column(df), target_col, ascending=True)
        if ans: return ans
    elif any(t in lower for t in _region_best):
        target_col = metric_col if metric_col and metric_col in df.columns and metric_col != "Order ID" else numeric_target
        ans = _groupby_answer(_find_region_column(df), target_col, ascending=False)
        if ans: return ans

    # Bottom/Worst category  (#4 fix)
    _cat_worst = ("worst category", "lowest category", "bottom category", "least category",
                  "which category has the lowest", "which category has the least",
                  "category with the lowest", "category with the least")
    _cat_best = ("top category", "best category", "highest category", "leading category",
                 "which category", "category with the highest", "category with the most",
                 "category with the best", "category has the highest", "category has the most")
    if any(t in lower for t in _cat_worst):
        target_col = metric_col if metric_col and metric_col in df.columns and metric_col != "Order ID" else numeric_target
        ans = _groupby_answer(_find_category_column(df), target_col, ascending=True)
        if ans: return ans
    elif any(t in lower for t in _cat_best):
        target_col = metric_col if metric_col and metric_col in df.columns and metric_col != "Order ID" else numeric_target
        ans = _groupby_answer(_find_category_column(df), target_col, ascending=False)
        if ans: return ans

    # Top / Bottom N products  (#4, #16 fix — dynamic N)
    _prod_best = ("top product", "best product", "top 5 product", "top 10 product",
                  "highest product", "product names", "top product names", "top products",
                  "what are the top", "show top", "list top")
    _prod_worst = ("worst product", "bottom product", "lowest product", "least product")
    n_match = _re.search(r"top\s+(\d+)|bottom\s+(\d+)|worst\s+(\d+)", lower)
    top_n = int(next(g for g in n_match.groups() if g) if n_match else 5)
    top_n = min(top_n, 20)
    if any(t in lower for t in _prod_worst):
        target_col = metric_col if metric_col and metric_col in df.columns and metric_col != "Order ID" else numeric_target
        ans = _groupby_answer(_find_item_column(df), target_col, ascending=True, top_n=top_n,
                              label=f"Bottom {top_n} by {(target_col or 'items').lower()}")
        if ans: return ans
    elif any(t in lower for t in _prod_best):
        target_col = metric_col if metric_col and metric_col in df.columns and metric_col != "Order ID" else numeric_target
        ans = _groupby_answer(_find_item_column(df), target_col, ascending=False, top_n=top_n,
                              label=f"Top {top_n} by {(target_col or 'items').lower()}")
        if ans:
            return ans
        # Fallback: list items by frequency if no numeric target
        item_col = _find_item_column(df)
        if item_col:
            top_items = df[item_col].dropna().value_counts().head(top_n)
            lines = [f"{i+1}. {lbl}" for i, lbl in enumerate(top_items.index)]
            return f"Top {top_n} {item_col} values:\n" + "\n".join(lines)

    # Monthly trend — chronological list  (#7, #14 fix)
    if any(t in lower for t in ("trend", "monthly", "over time", "by month", "month by month")):
        date_col = _find_datetime_column(df.copy())
        target_col = metric_col if metric_col and metric_col in df.columns and metric_col != "Order ID" else numeric_target
        if date_col and target_col and pd.api.types.is_numeric_dtype(df[target_col]):
            td = df[[date_col, target_col]].copy()
            td[date_col] = pd.to_datetime(td[date_col], errors="coerce")
            td[target_col] = pd.to_numeric(td[target_col], errors="coerce")
            td = td.dropna(subset=[date_col, target_col])
            if not td.empty:
                td["_period"] = td[date_col].dt.to_period("M").astype(str)
                monthly = td.groupby("_period")[target_col].sum().sort_index()  # chronological
                if not monthly.empty:
                    money = _money(target_col)
                    lines = [f"  {p}: {_format_chat_metric(v, money=money)}" for p, v in monthly.items()]
                    best = monthly.idxmax()
                    return (f"Monthly {target_col.lower()} trend:\n" + "\n".join(lines) +
                            f"\n\nPeak: {best} ({_format_chat_metric(monthly[best], money=money)})")

    # Yearly breakdown
    if "year" in lower and any(t in lower for t in ("trend", "by year", "each year", "annual", "yearly", "per year")):
        date_col = _find_datetime_column(df.copy())
        target_col = metric_col if metric_col and metric_col in df.columns and metric_col != "Order ID" else numeric_target
        if date_col and target_col and pd.api.types.is_numeric_dtype(df[target_col]):
            td = df[[date_col, target_col]].copy()
            td[date_col] = pd.to_datetime(td[date_col], errors="coerce")
            td[target_col] = pd.to_numeric(td[target_col], errors="coerce")
            td = td.dropna(subset=[date_col, target_col])
            if not td.empty:
                td["_yr"] = td[date_col].dt.year.astype(str)
                yearly = td.groupby("_yr")[target_col].sum().sort_index()
                money = _money(target_col)
                lines = [f"  {yr}: {_format_chat_metric(v, money=money)}" for yr, v in yearly.items()]
                return f"Yearly {target_col.lower()} breakdown:\n" + "\n".join(lines)

    # Specific value filter: "profit for Technology", "sales in West region"
    # Catches: "X for [value]", "X in [value]", "[value] X"
    _filter_preps = (" for ", " in ", " of ")
    if any(prep in lower for prep in _filter_preps) and metric_col and metric_col in df.columns:
        cat_col = _find_category_column(df)
        reg_col = _find_region_column(df)
        for group_col in [cat_col, reg_col]:
            if not group_col:
                continue
            unique_vals = df[group_col].dropna().astype(str).str.lower().unique().tolist()
            matched_val = next((v for v in unique_vals if v in lower), None)
            if matched_val and pd.api.types.is_numeric_dtype(df[metric_col]):
                mask = df[group_col].astype(str).str.lower() == matched_val
                filtered = df[mask]
                if not filtered.empty:
                    total = filtered[metric_col].sum()
                    display_val = df[group_col][mask].iloc[0]  # original casing
                    return (f"{metric_col} for {display_val}: "
                            f"{_format_chat_metric(total, money=_money(metric_col))}."
                            f" ({len(filtered):,} records)")

    # NLP pipeline fallback (schema/quality/profiling/aggregation intents)
    if HAS_NLP:
        try:
            parsed = process_query(question, df=df, dataset_meta=meta)
            result = execute_query(df, parsed)
            data = result.get("data")
            if parsed.get("intent") in {"schema", "quality", "profiling"}:
                return generate_response(parsed, result)
            if parsed.get("intent") == "aggregation" and not isinstance(data, pd.DataFrame):
                return generate_response(parsed, result)
        except Exception:
            pass

    return None


def _strongest_correlation(df: pd.DataFrame):
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if len(num_cols) < 2:
        return None
    corr = df[num_cols].corr(numeric_only=True).abs()
    if corr.empty:
        return None
    np.fill_diagonal(corr.values, 0)
    if corr.max().max() <= 0:
        return None
    pair = corr.stack().idxmax()
    value = corr.loc[pair[0], pair[1]]
    return pair[0], pair[1], float(value)


def _build_simple_forecast_payload(
    df: pd.DataFrame,
    date_col: str,
    target_col: str,
    forecast_periods: int,
    target_growth: float,
) -> dict:
    d2 = df[[date_col, target_col]].copy()
    d2[date_col] = pd.to_datetime(d2[date_col], errors="coerce")
    d2[target_col] = pd.to_numeric(d2[target_col], errors="coerce")
    d2 = d2.dropna(subset=[date_col, target_col])
    if d2.empty:
        return {
            "status": "error",
            "message": "Prediction could not run because the selected date/target columns do not contain usable values.",
        }

    d2["_period"] = d2[date_col].dt.to_period("M").dt.to_timestamp()
    monthly = d2.groupby("_period")[target_col].sum().reset_index().sort_values("_period")
    if len(monthly) < 3:
        return {
            "status": "error",
            "message": "Prediction needs at least 3 monthly data points after grouping by date.",
        }

    vals = monthly[target_col].astype(float).values
    avg = float(np.mean(vals[-6:])) if len(vals) >= 6 else float(np.mean(vals))
    growth_rate = target_growth / 100

    # Trend baseline via linear regression over monthly aggregates.
    x = np.arange(len(vals), dtype=float)
    if len(vals) >= 2:
        slope, intercept = np.polyfit(x, vals, 1)
    else:
        slope, intercept = 0.0, float(vals[0])
    lin_fit = intercept + slope * x
    lin_residuals = vals - lin_fit
    ss_res = float(np.sum(lin_residuals ** 2))
    ss_tot = float(np.sum((vals - np.mean(vals)) ** 2))
    r2 = float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0
    r2 = max(0.0, min(1.0, r2))

    # Simple exponential smoothing level (mirrors analytics/predictive_engine spirit).
    pct_changes = pd.Series(vals).pct_change().dropna()
    vol = float(pct_changes.std()) if len(pct_changes) else 0.0
    alpha = 0.45 if vol > 0.25 else 0.35 if vol > 0.15 else 0.25
    ses_level = float(vals[0])
    for val in vals[1:]:
        ses_level = alpha * float(val) + (1 - alpha) * ses_level

    # Seasonality factors by calendar month (when enough history exists).
    seasonality_map = {m: 1.0 for m in range(1, 13)}
    overall_mean = float(np.mean(vals)) if len(vals) else 0.0
    if len(monthly) >= 12 and overall_mean > 0:
        monthly = monthly.copy()
        monthly["_month_num"] = monthly["_period"].dt.month
        seasonality = monthly.groupby("_month_num")[target_col].mean() / overall_mean
        for month_num, factor in seasonality.items():
            safe_factor = float(factor) if np.isfinite(factor) and factor > 0 else 1.0
            seasonality_map[int(month_num)] = safe_factor

    forecast_values = []
    last_date = monthly["_period"].max()
    forecast_labels = []
    for i in range(forecast_periods):
        step = i + 1
        next_date = last_date + pd.DateOffset(months=step)
        lin_pred = max(0.0, float(intercept + slope * (len(vals) + i)))
        ses_pred = max(0.0, ses_level + slope * 0.35 * step)
        # Higher trend fit quality => trust linear trend more.
        trend_w = 0.55 + 0.35 * r2
        base_blend = trend_w * lin_pred + (1 - trend_w) * ses_pred
        growth_factor = (1 + growth_rate / max(1, forecast_periods)) ** step
        seasonal_factor = seasonality_map.get(int(next_date.month), 1.0)
        pred = base_blend * growth_factor * seasonal_factor
        forecast_values.append(round(pred, 2))
        forecast_labels.append(next_date.strftime("%b %Y"))

    # Confidence band based on historical residual spread.
    residual_std = float(np.std(lin_residuals)) if len(vals) >= 2 else max(1.0, avg * 0.08)
    if residual_std <= 0:
        residual_std = max(1.0, avg * 0.08)
    lower, upper = [], []
    for i, pred in enumerate(forecast_values):
        width = residual_std * (1.0 + 0.03 * i)
        lower.append(round(max(0.0, pred - width), 2))
        upper.append(round(pred + width, 2))

    return {
        "status": "success",
        "mode": "generic" if target_col != "Sales" or date_col != "Order Date" else "sales",
        "target_column": target_col,
        "date_column": date_col,
        "periods": forecast_periods,
        "target_growth": target_growth,
        "historical": {
            "labels": monthly["_period"].dt.strftime("%b %Y").tolist(),
            "values": [round(float(v), 2) for v in monthly[target_col].tolist()],
        },
        "forecast": {
            "labels": forecast_labels,
            "values": forecast_values,
            "lower": lower,
            "upper": upper,
        },
        "summary": {
            "target_column": target_col,
            "date_column": date_col,
            "avg_monthly_value": round(avg, 2),
            "forecast_horizon": f"{forecast_periods} months",
            "monthly_points": int(len(monthly)),
            "model": "Linear + SES ensemble with seasonality",
            "fit_r2": round(r2, 4),
            "ses_alpha": round(alpha, 2),
        },
    }

def _build_kpis_list(df: pd.DataFrame) -> list:
    """
    Fix 6 — Build KPI cards that adapt to whatever columns exist.
    Sales datasets get full financial KPIs.
    Any other dataset gets numeric column summaries.
    """
    kpis = []
    # Always show record count
    kpis.append({"label": "Total Records", "value": f"{len(df):,}", "sub": "Filtered rows"})

    # Sales KPIs — only if Sales column exists
    if "Sales" in df.columns:
        s = float(df["Sales"].sum())
        kpis.insert(0, {"label": "Total Sales", "value": f"${s:,.0f}", "sub": "Revenue"})
    if "Profit" in df.columns:
        p = float(df["Profit"].sum())
        s = float(df["Sales"].sum()) if "Sales" in df.columns else 0
        margin = (p / s * 100) if s else 0
        kpis.append({"label": "Total Profit",  "value": f"${p:,.0f}",    "sub": "Net profit"})
        kpis.append({"label": "Profit Margin", "value": f"{margin:.1f}%","sub": "Overall margin"})
    if "Discount" in df.columns:
        d = float(df["Discount"].mean()) * 100
        kpis.append({"label": "Avg Discount", "value": f"{d:.1f}%", "sub": "Discount rate"})
    if "shipping_delay_days" in df.columns:
        ship = float(df["shipping_delay_days"].mean())
        if not pd.isna(ship):
            kpis.append({"label": "Avg Shipping", "value": f"{ship:.0f} days", "sub": "Delivery time"})

    orders = int(df["Order ID"].nunique()) if "Order ID" in df.columns else None
    if orders:
        kpis.append({"label": "Total Orders", "value": f"{orders:,}", "sub": "Unique orders"})

    # Generic numeric KPIs for non-sales datasets
    if "Sales" not in df.columns:
        num_cols = df.select_dtypes(include="number").columns.tolist()[:4]
        for col in num_cols:
            short = col[:18] + ("…" if len(col) > 18 else "")
            total = df[col].sum()
            avg   = df[col].mean()
            kpis.append({
                "label": f"Total {short}",
                "value": f"{total:,.0f}",
                "sub":   f"Avg {avg:,.1f}"
            })

    return kpis[:8]  # Cap at 8 cards

def _build_charts(df: pd.DataFrame) -> dict:
    """Fix 6b — Adaptive charts based on available columns."""
    charts = {}
    num_cols = df.select_dtypes(include="number").columns.tolist()
    # Pick best numeric target — Sales if exists, otherwise first numeric column
    target = "Sales" if "Sales" in df.columns else (num_cols[0] if num_cols else None)

    # Category breakdown
    cat_col = _find_category_column(df)
    if cat_col and target:
        try:
            cat = df.groupby(cat_col)[target].sum()
            charts["cat"] = {"labels": cat.index.tolist(), "values": cat.values.tolist()}
        except Exception:
            pass

    # Monthly trend
    date_col = "Order Date" if "Order Date" in df.columns else None
    if not date_col:
        # Try any datetime column
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                date_col = c
                break
    if date_col and target:
        try:
            d2 = df.copy()
            d2["_m"] = pd.to_datetime(d2[date_col], errors="coerce").dt.to_period("M").dt.to_timestamp()
            m = d2.groupby("_m")[target].sum().reset_index()
            charts["monthly"] = {
                "labels": m["_m"].dt.strftime("%b %Y").tolist(),
                "values": m[target].tolist()
            }
        except Exception:
            pass

    # Top items (product or first categorical column)
    item_col = "Product Name" if "Product Name" in df.columns else None
    if not item_col:
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        item_col = cat_cols[0] if cat_cols else None
    if item_col and target:
        try:
            top = df.groupby(item_col)[target].sum().nlargest(5)
            charts["products"] = {"labels": [str(l)[:20] for l in top.index.tolist()], "values": top.values.tolist()}
        except Exception:
            pass

    # Regional breakdown
    reg_col = _find_region_column(df)
    if reg_col and target:
        try:
            reg = df.groupby(reg_col)[target].sum()
            charts["region"] = {"labels": reg.index.tolist(), "values": reg.values.tolist()}
        except Exception:
            pass

    return charts

def _build_insights(df: pd.DataFrame) -> list:
    """Dataset-aware insights that stay truthful for both sales and non-sales data."""
    if df is None or df.empty:
        return ["No filtered records are available for insight generation."]

    if _is_sales_compatible(df) and HAS_AI_INSIGHTS:
        try:
            return generate_ai_insights(_build_kpis_dict(df))
        except Exception:
            pass

    insights = [f"Filtered dataset contains {len(df):,} rows and {len(df.columns)} columns."]
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if _is_sales_compatible(df) and "Category" in df.columns:
        sales_by_cat = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)
        if not sales_by_cat.empty:
            insights.append(f"{sales_by_cat.index[0]} contributes the highest sales total.")

    if "Profit" in df.columns and "Region" in df.columns:
        profit_by_region = df.groupby("Region")["Profit"].sum().sort_values(ascending=False)
        if not profit_by_region.empty:
            insights.append(f"{profit_by_region.index[0]} has the strongest total profit.")

    date_col = _find_datetime_column(df.copy())
    target_col = _find_numeric_target_column(df)
    if date_col and target_col:
        d2 = df[[date_col, target_col]].copy()
        d2[date_col] = pd.to_datetime(d2[date_col], errors="coerce")
        d2[target_col] = pd.to_numeric(d2[target_col], errors="coerce")
        d2 = d2.dropna(subset=[date_col, target_col])
        if not d2.empty:
            d2["_period"] = d2[date_col].dt.to_period("M").astype(str)
            by_period = d2.groupby("_period")[target_col].sum().sort_values(ascending=False)
            if not by_period.empty:
                insights.append(f"{by_period.index[0]} is the strongest recorded period for {target_col}.")

    if num_cols:
        primary = num_cols[0]
        insights.append(f"{primary} averages {df[primary].mean():,.2f} across the filtered records.")

    corr = _strongest_correlation(df)
    if corr:
        left, right, value = corr
        insights.append(f"{left} and {right} show the strongest numeric relationship (corr {value:.2f}).")

    if cat_cols:
        top_cat_col = cat_cols[0]
        counts = df[top_cat_col].astype(str).value_counts()
        if not counts.empty:
            insights.append(f"Most common {top_cat_col}: {counts.index[0]} ({counts.iloc[0]:,} records).")

    dupes = int(df.duplicated().sum())
    if dupes:
        insights.append(f"The filtered dataset still contains {dupes:,} duplicate rows.")

    missing = int(df.isnull().sum().sum())
    if missing:
        insights.append(f"The filtered dataset contains {missing:,} missing values.")

    return insights[:6]

def _build_recommendations(df: pd.DataFrame) -> list:
    """Dataset-aware recommendations that avoid fabricated sales advice."""
    if df is None or df.empty:
        return ["Upload and filter data first to generate recommendations."]

    if _is_sales_compatible(df) and HAS_RECS:
        try:
            return generate_smart_recommendations(_build_kpis_dict(df))
        except Exception:
            pass

    recs = []
    missing_ratio = float(df.isnull().sum().sum()) / max(1, df.shape[0] * max(1, df.shape[1]))
    if missing_ratio > 0.05:
        recs.append("Address missing values before relying on downstream analytics.")

    dupes = int(df.duplicated().sum())
    if dupes:
        recs.append("Remove duplicate rows to improve KPI and insight accuracy.")

    date_col = _find_datetime_column(df.copy())
    target_col = _find_numeric_target_column(df)
    if date_col and target_col:
        recs.append(f"Track {target_col} over time using {date_col} to monitor trend shifts.")

    corr = _strongest_correlation(df)
    if corr:
        left, right, _ = corr
        recs.append(f"Investigate the relationship between {left} and {right} before making decisions.")

    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if cat_cols:
        recs.append(f"Break down performance by {cat_cols[0]} to identify high-impact groups.")

    if not recs:
        recs.append("The filtered dataset looks stable; continue monitoring with broader time or category filters.")

    return recs[:5]

def _build_table_rows(df: pd.DataFrame, limit: int = 100) -> list:
    preferred = []
    for col in [
        _find_region_column(df),
        _find_category_column(df),
        "Sub-Category" if "Sub-Category" in df.columns else None,
        _find_item_column(df),
        _find_numeric_target_column(df),
        "Profit" if "Profit" in df.columns else None,
        "Quantity" if "Quantity" in df.columns else None,
        "Discount" if "Discount" in df.columns else None,
        _find_datetime_column(df.copy()),
    ]:
        if col and col not in preferred and col in df.columns:
            preferred.append(col)

    if not preferred:
        preferred = df.columns.tolist()[:8]

    sub = df[preferred].head(limit).copy()
    for col in sub.columns:
        if pd.api.types.is_datetime64_any_dtype(sub[col]):
            sub[col] = sub[col].dt.strftime("%Y-%m-%d")
    return sub.fillna("").to_dict(orient="records")

def _build_report_kpis(df: pd.DataFrame):
    """
    Build kpis in the format expected by report_generator.py.
    generate_kpis() returns list of (label, value, sub) tuples.
    """
    if HAS_COL_TYPES:
        try:
            from dashboard.kpi_generator import generate_kpis
            col_types = get_column_types(df)
            return generate_kpis(df, col_types)
        except Exception:
            pass
    # Fallback: return list of tuples matching expected format
    kd = _build_kpis_dict(df)
    s, p = kd["total_sales"], kd["total_profit"]
    margin = (p / s * 100) if s else 0
    return [
        ("Total Sales",   f"${s:,.0f}",      "Revenue"),
        ("Total Profit",  f"${p:,.0f}",      "Net profit"),
        ("Profit Margin", f"{margin:.1f}%",  "Overall margin"),
        ("Total Orders",  f"{kd['total_orders']:,}", "Orders"),
    ]

# ═════════════════════════════════════════════════════════════════════════════
# 1. AUTH ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════
@app.post("/api/auth/login")
def login(req: LoginRequest):
    users = _load_users()
    user  = users.get(req.email.lower().strip())
    if not user:
        raise HTTPException(401, "Invalid email or password.")
    if not user.get("active", True):
        raise HTTPException(403, "Account is deactivated.")
    pw = user.get("password", "")
    valid = (pwd_ctx.verify(req.password, pw) if pw.startswith("$2") else req.password == pw)
    if not valid:
        raise HTTPException(401, "Invalid email or password.")
    token = _create_token(req.email, user.get("role", "Viewer"))
    return {
        "access_token": token,
        "user": {"email": req.email, "name": user.get("name",""), "role": user.get("role","Viewer")}
    }

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    users = _load_users()
    email = req.email.lower().strip()
    if email in users:
        raise HTTPException(409, "Email already registered.")
    if len(req.password) < 8:
        raise HTTPException(422, "Password must be at least 8 characters.")
    users[email] = {
        "name": req.name, "password": pwd_ctx.hash(req.password),
        "role": "Viewer", "created_at": datetime.utcnow().isoformat(), "active": True
    }
    _save_users(users)
    return {"message": "Account created successfully."}

@app.get("/api/auth/me")
def get_me(_user: dict = Depends(get_current_user)):
    users = _load_users()
    email = _user.get("sub", "")
    user  = users.get(email, {})
    return {
        "email": email, "name": user.get("name",""), "role": user.get("role","Viewer"),
        "permissions": list(ROLE_PERMS.get(user.get("role","Viewer"), set()))
    }

# ═════════════════════════════════════════════════════════════════════════════
# 2. USER MANAGEMENT (Admin only)
# ═════════════════════════════════════════════════════════════════════════════
@app.get("/api/users")
def list_users(_user: dict = Depends(get_current_user)):
    _require_perm(_user, "manage_users")
    return [{"email": e, "name": d.get("name",""), "role": d.get("role","Viewer"),
             "active": d.get("active",True), "created_at": d.get("created_at","")}
            for e, d in _load_users().items()]

@app.post("/api/users")
def create_user(req: CreateUserRequest, _user: dict = Depends(get_current_user)):
    _require_perm(_user, "manage_users")
    users = _load_users(); email = req.email.lower().strip()
    if email in users:
        raise HTTPException(409, "Email already registered.")
    if req.role not in ROLE_PERMS:
        raise HTTPException(422, f"Invalid role. Choose: {list(ROLE_PERMS)}")
    users[email] = {"name": req.name, "password": pwd_ctx.hash(req.password),
                    "role": req.role, "created_at": datetime.utcnow().isoformat(), "active": True}
    _save_users(users)
    return {"message": f"User {email} created with role {req.role}."}

@app.put("/api/users/role")
def update_role(req: UpdateRoleRequest, _user: dict = Depends(get_current_user)):
    _require_perm(_user, "manage_users")
    users = _load_users(); email = req.email.lower().strip()
    if email not in users:
        raise HTTPException(404, "User not found.")
    if req.role not in ROLE_PERMS:
        raise HTTPException(422, "Invalid role.")
    users[email]["role"] = req.role; _save_users(users)
    return {"message": f"Role updated to {req.role} for {email}."}

@app.delete("/api/users/{email}")
def delete_user(email: str, _user: dict = Depends(get_current_user)):
    _require_perm(_user, "manage_users")
    users = _load_users(); email = email.lower().strip()
    if email not in users:
        raise HTTPException(404, "User not found.")
    if email == _user.get("sub"):
        raise HTTPException(400, "Cannot delete your own account.")
    users[email]["active"] = False; _save_users(users)
    return {"message": f"User {email} deactivated."}

# ═════════════════════════════════════════════════════════════════════════════
# 3. FILE UPLOAD
# ═════════════════════════════════════════════════════════════════════════════
@app.post("/api/dashboard/upload")
async def upload_file(file: UploadFile = File(...), _user: dict = Depends(get_current_user)):
    _require_perm(_user, "upload")
    contents = await file.read()
    if HAS_FILE_UPLOAD:
        try:
            validate_filename_and_size(file.filename, len(contents))
            df = parse_bytes_to_df(contents, file.filename)
            df = normalize_columns(df)
        except UploadValidationError as e:
            status = 413 if "exceeds" in str(e).lower() else 422
            raise HTTPException(status, str(e))
    else:
        if len(contents) > 200 * 1024 * 1024:
            raise HTTPException(413, "File exceeds 200MB limit.")
        if not contents:
            raise HTTPException(422, "Uploaded file is empty.")
        ext = os.path.splitext(file.filename)[1].lower()
        try:
            if ext == ".csv":
                df = None
                for enc in ["utf-8-sig", "utf-8", "latin1", "cp1252"]:
                    try:
                        df = pd.read_csv(io.BytesIO(contents), encoding=enc, low_memory=False)
                        break
                    except UnicodeDecodeError:
                        continue
                if df is None:
                    raise HTTPException(422, "Could not decode CSV file.")
            elif ext in (".xlsx", ".xls"):
                df = pd.read_excel(io.BytesIO(contents))
            elif ext == ".json":
                df = pd.read_json(io.BytesIO(contents))
            else:
                raise HTTPException(422, f"Unsupported format: {ext}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(422, f"Could not parse file: {e}")

        if df.empty:
            raise HTTPException(422, "Uploaded file has no rows.")

        df.columns = [str(c).strip() for c in df.columns]
        if len(set(df.columns)) != len(df.columns):
            raise HTTPException(422, "Uploaded file has duplicate column names. Please rename duplicate columns and try again.")

    structural_warnings = []
    if HAS_PROFILING:
        try:
            structural_warnings = validate_upload(df, file.filename)
        except Exception:
            structural_warnings = []

    # Fix 5 — run schema mapper to rename columns to standard names
    col_mapping = {}
    dataset_type = "generic"
    if HAS_SCHEMA_MAPPER:
        df, col_mapping = map_columns(df)
        dataset_type = detect_dataset_type(df)

    # Auto-parse date columns
    if HAS_FILE_UPLOAD:
        df = auto_parse_dates(df)
    else:
        for col in df.columns:
            if any(k in col.lower() for k in ["date", "time"]):
                df[col] = pd.to_datetime(df[col], errors="coerce")

    # Compute shipping delay
    if "shipping_delay_days" not in df.columns:
        if "Ship Date" in df.columns and "Order Date" in df.columns:
            df["shipping_delay_days"] = (
                df["Ship Date"] - df["Order Date"]
            ).dt.days.fillna(0)

    # Build warnings and chatbot suggestions for this dataset
    upload_warnings = get_missing_warnings(df) if HAS_SCHEMA_MAPPER else []
    upload_warnings = structural_warnings + upload_warnings
    suggestions = build_chatbot_suggestions(df) if HAS_SCHEMA_MAPPER else []

    upload_meta = {
        "filename":     file.filename,
        "rows":         len(df),
        "columns":      len(df.columns),
        "uploaded_by":  _user.get("sub", ""),
        "uploaded_at":  datetime.utcnow().isoformat(),
        "dataset_type": dataset_type,
        "col_mapping":  col_mapping,
        "warnings":     upload_warnings,
        "suggestions":  suggestions,
    }
    _set_user_upload(_user, df, upload_meta)
    return {
        "message":      f"Uploaded {file.filename} — {len(df):,} rows × {len(df.columns)} columns",
        "rows":         len(df),
        "columns":      len(df.columns),
        "filename":     file.filename,
        "dataset_type": dataset_type,
        "warnings":     upload_warnings,
        "col_mapping":  col_mapping,
        "suggestions":  suggestions,
    }

# ═════════════════════════════════════════════════════════════════════════════

@app.delete("/api/dashboard/upload")
def reset_dataset(_user: dict = Depends(get_current_user)):
    """Clear the current user's uploaded dataset and revert to the default CSV."""
    _require_perm(_user, "upload")
    _clear_user_upload(_user)
    return {"message": "Uploaded dataset cleared. Default dataset restored."}

# 4+5. DATASET PROFILING (Team 1)
# ═════════════════════════════════════════════════════════════════════════════
@app.get("/api/data/profile")
def get_profile(_user: dict = Depends(get_current_user)):
    _require_perm(_user, "profiling")
    df = _get_df(_user)
    if df is None:
        raise HTTPException(404, "No dataset loaded.")
    meta = _get_upload_meta(_user)

    tc = df.shape[0] * df.shape[1]
    mc = int(df.isnull().sum().sum())
    completeness = round((1 - mc / tc) * 100, 2) if tc else 0

    columns_data = []
    summary = {}
    if HAS_PROFILING:
        try:
            prof = generate_profiling_table(df)
            columns_data = prof.to_dict(orient="records")
            summary = generate_profiling_summary(df)
        except Exception:
            pass

    return {
        "overview": {
            "rows":          df.shape[0],
            "columns":       df.shape[1],
            "completeness":  completeness,
            "duplicates":    int(df.duplicated().sum()),
            "numeric_cols":  len(df.select_dtypes(include=np.number).columns),
            "missing_cells": mc
        },
        "columns":    columns_data,
        "summary":    summary,
        "stats":      df.describe().fillna("").to_dict(),
        "filename":   meta.get("filename", "Default dataset"),
        "uploaded_at":meta.get("uploaded_at", "")
    }

# ═════════════════════════════════════════════════════════════════════════════
# 6. DATA QUALITY (Team 1)
# ═════════════════════════════════════════════════════════════════════════════
@app.get("/api/data/quality")
def get_quality(_user: dict = Depends(get_current_user)):
    _require_perm(_user, "quality")
    df = _get_df(_user)
    if df is None:
        raise HTTPException(404, "No dataset loaded.")
    if not HAS_QUALITY:
        raise HTTPException(503, "Data quality module not available.")

    try:
        dup_result      = check_duplicates(df)
        missing_report  = check_missing_values(df)
        outlier_report, outlier_idx = check_outliers(df)
        inconsistencies = check_inconsistencies(df)
        scores          = compute_quality_score(df, dup_result, missing_report,
                                                outlier_report, inconsistencies)
        warnings        = generate_warnings(dup_result, missing_report,
                                            outlier_report, inconsistencies, scores)
        # Remove non-serializable dup_rows DataFrame from result
        dup_safe = {
            "count":      int(dup_result["count"]),
            "percentage": float(dup_result["percentage"]),
            "has_dupes":  bool(dup_result["has_dupes"])
        }
        return {
            "score":           _json_safe(scores),
            "duplicates":      dup_safe,
            "missing":         missing_report.to_dict(orient="records"),
            "outliers":        outlier_report.to_dict(orient="records") if not outlier_report.empty else [],
            "inconsistencies": _json_safe(inconsistencies),
            "warnings":        _json_safe(warnings)
        }
    except Exception as e:
        raise HTTPException(500, f"Quality check error: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# 7+8+9. DASHBOARD METRICS + FILTERS
# ═════════════════════════════════════════════════════════════════════════════
@app.get("/api/dashboard/metrics")
def get_metrics(
    category: str = Query("All"),
    region:   str = Query("All"),
    year:     str = Query("All"),
    profit:   str = Query("All"),
    _user: dict = Depends(get_current_user)
):
    df = _get_df(_user)
    if df is None:
        raise HTTPException(404, "No dataset loaded.")
    meta = _get_upload_meta(_user)

    filtered   = _apply_filters(df, category, region, year, profit)
    date_col   = _find_datetime_column(df.copy())
    target_col = _find_numeric_target_column(filtered if not filtered.empty else df)
    category_col = _find_category_column(df)
    region_col   = _find_region_column(df)
    item_col     = _find_item_column(df)
    years      = sorted(df[date_col].dt.year.dropna().unique().astype(int).tolist()) \
                 if date_col and pd.api.types.is_datetime64_any_dtype(df[date_col]) else []
    categories = sorted(df[category_col].dropna().astype(str).unique().tolist()) \
                 if category_col else []
    regions    = sorted(df[region_col].dropna().astype(str).unique().tolist()) \
                 if region_col else []

    return {
        "kpis":            _build_kpis_list(filtered),
        "charts":          _build_charts(filtered),
        "insights":        _build_insights(filtered),
        "recommendations": _build_recommendations(filtered),
        "rows":            _build_table_rows(filtered),
        "total":           len(filtered),
        "filters": {
            "years":      [str(y) for y in years],
            "categories": categories,
            "regions":    regions
        },
        "meta": {
            "filename":    meta.get("filename","Default dataset"),
            "uploaded_at": meta.get("uploaded_at",""),
            "dataset_type": meta.get("dataset_type","default"),
            "dashboard_mode": "sales" if _is_sales_compatible(filtered if not filtered.empty else df) else "generic",
            "warnings":    meta.get("warnings",[]),
            "suggestions": meta.get("suggestions",[]),
            "total_rows":  len(df),
            "filtered_rows": len(filtered),
            "target_column": target_col,
            "date_column": date_col,
            "category_column": category_col,
            "region_column": region_col,
            "item_column": item_col,
        }
    }

# ═════════════════════════════════════════════════════════════════════════════
# 10. REAL-TIME SSE
# ═════════════════════════════════════════════════════════════════════════════
@app.get("/api/dashboard/stream")
async def stream(
    category: str = Query("All"),
    region:   str = Query("All"),
    year:     str = Query("All"),
    profit:   str = Query("All"),
    _user: dict = Depends(get_current_user),  # Fix 4 — stream auth
):
    async def gen():
            if df is not None:
                f = _apply_filters(df, category, region, year, profit)
                payload = json.dumps({
                    "kpis":     _build_kpis_list(f),
                    "charts":   _build_charts(f),
                    "insights": _build_insights(f),
                    "total":    len(f),
                    "ts":       datetime.utcnow().isoformat()
                })
                yield f"data: {payload}\n\n"
            await asyncio.sleep(30)

    return StreamingResponse(gen(), media_type="text/event-stream")

# ═════════════════════════════════════════════════════════════════════════════
# 11. CHATBOT — Groq AI with Text-to-Pandas (Option 1)
#
# Flow:
#   1. Groq receives column schema + question → writes a pandas expression
#   2. We execute it safely against the real DataFrame
#   3. Groq receives the actual result → answers naturally
#   4. Fallback to summary-based answer if code generation/execution fails
# ═════════════════════════════════════════════════════════════════════════════

GROQ_CHAT_MODEL = "llama-3.3-70b-versatile"
_groq_client = None
HAS_GROQ = False


def _get_groq_client():
    """Lazy-init Groq client — reads key after dotenv is loaded."""
    global _groq_client, HAS_GROQ
    if _groq_client is not None:
        return _groq_client
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from groq import Groq as _GroqClient
        _groq_client = _GroqClient(api_key=api_key)
        HAS_GROQ = True
        return _groq_client
    except Exception:
        return None


# ── Safe pandas execution sandbox ────────────────────────────────────────────

# Blocked keywords — prevent any dangerous operations
_BLOCKED = [
    "import", "exec", "eval", "open", "os.", "sys.", "subprocess",
    "__", "globals", "locals", "getattr", "setattr", "delattr",
    "compile", "input", "print", "write", "delete", "drop",
    "to_csv", "to_excel", "to_sql", "to_json", "to_pickle",
]

def _safe_execute(code: str, df: pd.DataFrame) -> tuple[bool, str]:
    """
    Execute a pandas expression safely.
    Returns (success: bool, result_string: str)
    """
    code = code.strip()

    # Strip markdown code fences if Groq wrapped the code
    if code.startswith("```"):
        lines = code.split("\n")
        code = "\n".join(
            l for l in lines
            if not l.strip().startswith("```")
        ).strip()

    # Block dangerous patterns
    code_lower = code.lower()
    for blocked in _BLOCKED:
        if blocked in code_lower:
            return False, f"Blocked: unsafe operation '{blocked}' detected."

    # Only allow single-expression code (no multi-line assignments or loops)
    lines = [l.strip() for l in code.split("\n") if l.strip() and not l.strip().startswith("#")]
    if len(lines) > 5:
        return False, "Blocked: too many lines."

    try:
        # Provide a safe namespace with only df and pandas
        namespace = {
            "df": df.copy(),
            "pd": pd,
            "np": np,
        }
        result = eval(compile(code, "<string>", "eval"), {"__builtins__": {}}, namespace)

        # Format the result into a readable string
        if isinstance(result, pd.DataFrame):
            if result.empty:
                return True, "No rows matched that query."
            # Cap at 20 rows to avoid token overflow
            preview = result.head(20)
            return True, preview.to_string(index=True)
        elif isinstance(result, pd.Series):
            if result.empty:
                return True, "No data matched that query."
            preview = result.head(20)
            return True, preview.to_string()
        elif isinstance(result, (int, float, np.integer, np.floating)):
            return True, f"{result:,.4f}".rstrip("0").rstrip(".")
        else:
            return True, str(result)[:2000]

    except Exception as e:
        return False, f"Execution error: {e}"


def _build_schema_prompt(df: pd.DataFrame) -> str:
    """Build a compact schema description for the code-generation prompt.
    Capped at 20 columns and trimmed sample values to keep prompts token-efficient.
    """
    lines = ["DataFrame variable name: df"]
    lines.append(f"Shape: {len(df):,} rows × {len(df.columns)} columns")
    lines.append("")
    # Cap at 20 columns — prioritise numeric and known-important columns
    all_cols = df.columns.tolist()
    important = [c for c in all_cols if c in {
        "Sales", "Profit", "Revenue", "Quantity", "Discount",
        "Order ID", "Customer ID", "Region", "Category", "Sub-Category",
        "Product Name", "Order Date", "Ship Date", "shipping_delay_days",
    }]
    remaining = [c for c in all_cols if c not in important]
    cols_to_show = (important + remaining)[:20]
    if len(all_cols) > 20:
        lines.append(f"Columns (showing 20 of {len(all_cols)} — name | dtype | sample values):")
    else:
        lines.append("Columns (name | dtype | sample values):")
    for col in cols_to_show:
        dtype = str(df[col].dtype)
        try:
            if pd.api.types.is_numeric_dtype(df[col]):
                # Compact: only min/max
                sample = f"min={df[col].min():,.1f}, max={df[col].max():,.1f}"
            else:
                top = df[col].dropna().value_counts().head(3).index.tolist()
                sample = ", ".join(str(v)[:20] for v in top)  # truncate long values
        except Exception:
            sample = "N/A"
        lines.append(f"  - {col} ({dtype}): {sample}")
    return "\n".join(lines)


def _build_code_gen_prompt(df: pd.DataFrame, question: str) -> list[dict]:
    """Build the messages list for Groq to generate pandas code."""
    schema = _build_schema_prompt(df)
    system = f"""You are a pandas code generator. Given a DataFrame schema and a user question, write a single pandas expression that answers the question.

RULES:
- Output ONLY the pandas expression, nothing else — no explanation, no markdown, no comments
- Use the variable name: df
- The expression must be evaluable with eval()
- For aggregations use: df.groupby(...)[...].sum() / .mean() / .count() etc.
- For filtering use: df[df[...] == ...]
- For sorting use: df.sort_values(...)
- For top N use: df.nlargest(N, column)
- For counts use: df[column].value_counts()
- For statistics use: df[column].describe() or df[column].std() etc.
- Column names are case-sensitive — use exact names from the schema
- If the question cannot be answered with pandas, output exactly: CANNOT_ANSWER

DATAFRAME SCHEMA:
{schema}"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]


def _build_answer_prompt(df: Optional[pd.DataFrame], meta: dict,
                          question: str, query_result: Optional[str]) -> list[dict]:
    """Build the messages list for Groq to answer naturally using the query result."""
    is_sales = _is_sales_compatible(df) if df is not None else False
    persona  = "AI Sales Assistant" if is_sales else "AI Dataset Assistant"
    ds_name  = (meta.get("filename") or meta.get("datasetName") or
                meta.get("uploaded_file") or "the dataset")

    if query_result:
        context = f"""The user asked: "{question}"

A pandas query was run on the dataset and returned this result:
--- QUERY RESULT ---
{query_result[:3000]}
--- END RESULT ---

Answer the user's question naturally using this result. Be warm, direct, and concise (1-4 sentences).
Format numbers with commas and $ signs where appropriate."""
    else:
        # Fallback — no query result, use dataset summary
        summary_lines = [f"Dataset: {ds_name}"]
        if df is not None and not df.empty:
            num_cols = df.select_dtypes(include="number").columns.tolist()
            for col in num_cols[:6]:
                try:
                    summary_lines.append(
                        f"  {col}: total={df[col].sum():,.2f}, avg={df[col].mean():,.2f}"
                    )
                except Exception:
                    pass
            if is_sales:
                try:
                    kpis = _build_kpis_dict(df)
                    summary_lines += [
                        f"Total Sales: ${kpis['total_sales']:,.0f}",
                        f"Total Profit: ${kpis['total_profit']:,.0f}",
                        f"Total Orders: {kpis['total_orders']:,}",
                    ]
                except Exception:
                    pass
        context = f"""The user asked: "{question}"

Use this dataset summary to answer as best you can:
{chr(10).join(summary_lines)}

Be warm, direct, and concise (1-4 sentences)."""

    system = f"""You are {persona} for Zero Click AI — a smart, friendly colleague.
Your personality: warm, direct, confident. Give real answers with real numbers.
- For greetings: respond warmly and briefly
- For data questions: lead with the number, then a short insight
- Keep it 1-4 sentences
- If data is missing or filters returned nothing, say so honestly
- For questions completely unrelated to data, say you're here to help with the dataset"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": context},
    ]


@app.post("/api/chat/message")
def chat_message(req: ChatRequest, _user: dict = Depends(get_current_user)):
    _require_perm(_user, "chatbot")
    df    = _get_df(_user)
    email = _user.get("sub", "anonymous")
    meta  = _get_upload_meta(_user)
    filtered_df = _apply_request_filters(df, req.filters) if df is not None else None

    if email not in _chat_history:
        _chat_history[email] = []
    _chat_history[email].append({"role": "user", "content": req.message})
    if len(_chat_history[email]) > 20:
        _chat_history[email] = _chat_history[email][-20:]

    fast_response = _try_structured_chat_response(req.message, filtered_df, meta, history=_chat_history.get(email, []))
    if fast_response:
        _chat_history[email].append({"role": "assistant", "content": fast_response})
        return {
            "reply": fast_response,
            "intent": "structured",
            "history": _chat_history[email][-6:],
            "suggestions": meta.get("suggestions", []),
        }

    groq = _get_groq_client()

    if groq is None:
        # No Groq key — fall back to NLP pipeline
        response = "Groq API key not configured. Please set GROQ_API_KEY."
        if HAS_NLP and filtered_df is not None:
            try:
                parsed   = process_query(req.message, df=filtered_df, dataset_meta=meta)
                result   = execute_query(filtered_df, parsed)
                response = generate_response(parsed, result)
            except Exception:
                pass
        _chat_history[email].append({"role": "assistant", "content": response})
        return {"reply": response, "intent": None, "history": _chat_history[email][-6:], "suggestions": meta.get("suggestions", [])}

    query_result = None
    groq_said_cannot_answer = False
    is_data_question = filtered_df is not None and not filtered_df.empty

    # ── Step 1: Detect if this is a data question or a greeting/chitchat ──────
    # Simple heuristic — skip code generation for short greetings
    msg_lower = req.message.strip().lower()
    greeting_patterns = ["hi", "hello", "hey", "thanks", "thank you", "bye",
                         "good morning", "good afternoon", "good evening", "how are you"]
    is_greeting = any(msg_lower == g or msg_lower.startswith(g + " ") or msg_lower.startswith(g + "!") or msg_lower.startswith(g + ",")
                      for g in greeting_patterns)

    # Fix 4: Skip code-gen entirely if question has no data-related terms.
    # Prevents burning tokens on questions like "who are you", "what can you do".
    _DATA_TERMS = {
        "total", "sum", "average", "avg", "mean", "count", "max", "min",
        "top", "bottom", "highest", "lowest", "trend", "compare", "by region",
        "by category", "profit", "sales", "revenue", "order", "quantity",
        "discount", "month", "year", "over time", "performance", "product",
        "customer", "row", "record", "column", "field", "schema", "missing",
        "duplicate", "quality", "outlier", "forecast", "predict", "growth",
        "how many", "what is the", "show me", "list", "find",
    }
    has_data_terms = any(term in msg_lower for term in _DATA_TERMS)
    if not has_data_terms and filtered_df is not None:
        has_data_terms = any(col.lower() in msg_lower for col in filtered_df.columns)

    # ── Step 2: Generate and execute pandas code (only for real data questions) ─
    if is_data_question and not is_greeting and has_data_terms:
        try:
            code_messages = _build_code_gen_prompt(filtered_df, req.message)
            code_resp = groq.chat.completions.create(
                model=GROQ_CHAT_MODEL,
                messages=code_messages,
                max_tokens=256,
                temperature=0.1,   # low temp = deterministic, precise code
            )
            generated_code = code_resp.choices[0].message.content.strip()

            groq_said_cannot_answer = (generated_code == "CANNOT_ANSWER")
            if generated_code and not groq_said_cannot_answer:
                success, result_str = _safe_execute(generated_code, filtered_df)
                if success:
                    query_result = result_str
        except Exception:
            groq_said_cannot_answer = False
            query_result = None  # fall through to summary-based answer
    else:
        groq_said_cannot_answer = False

    # Fix #6: if Groq said CANNOT_ANSWER and we have no query result,
    # return a static response instead of burning a second Groq call.
    if groq_said_cannot_answer and query_result is None:
        static = (
            "I wasn't able to build a data query for that. Try asking something like:\n"
            "\u2022 'What is the total sales by region?'\n"
            "\u2022 'Top 5 products by profit'\n"
            "\u2022 'Average discount for Technology category'"
        )
        _chat_history[email].append({"role": "assistant", "content": static})
        return {"reply": static, "intent": "cannot_answer",
                "history": _chat_history[email][-6:], "suggestions": meta.get("suggestions", [])}

    # ── Step 3: Generate natural language answer ──────────────────────────────
    try:
        answer_messages = _build_answer_prompt(filtered_df, meta, req.message, query_result)

        # Fix 3: Inject only last 4 history messages (2 turns) to cap token use.
        system_msg = answer_messages[0]
        user_msg   = answer_messages[1]
        full_messages = [system_msg]
        recent_history = _chat_history[email][:-1]
        for h in recent_history[-4:]:
            full_messages.append({"role": h["role"], "content": h["content"]})
        full_messages.append(user_msg)

        answer_resp = groq.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=full_messages,
            max_tokens=512,
            temperature=0.7,
        )
        response = answer_resp.choices[0].message.content.strip()

    except Exception as e:
        response = f"⚠️ Error generating response: {e}"

    _chat_history[email].append({"role": "assistant", "content": response})

    return {
        "reply":       response,
        "intent":      None,
        "history":     _chat_history[email][-6:],
        "suggestions": meta.get("suggestions", []),
    }


@app.delete("/api/chat/history")
def clear_chat(_user: dict = Depends(get_current_user)):
    _chat_history[_user.get("sub","anonymous")] = []
    return {"message": "Chat history cleared."}


@app.get("/api/chat/status")
def chat_status(_user: dict = Depends(get_current_user)):
    """Debug endpoint — confirms whether Groq is active."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    groq = _get_groq_client()
    return {
        "groq_key_loaded": bool(key),
        "groq_key_preview": (key[:8] + "...") if key else "NOT FOUND",
        "groq_client_ready": groq is not None,
        "model": GROQ_CHAT_MODEL,
        "mode": "text-to-pandas + natural language answer",
    }

# ═════════════════════════════════════════════════════════════════════════════
# 12+14. AI INSIGHTS + RECOMMENDATIONS (Team 3)
# ═════════════════════════════════════════════════════════════════════════════
@app.get("/api/analytics/insights")
def get_insights(
    category: str = Query("All"),
    region:   str = Query("All"),
    year:     str = Query("All"),
    profit:   str = Query("All"),
    _user: dict = Depends(get_current_user)
):
    _require_perm(_user, "ai_insights")
    df = _get_df(_user)
    if df is None:
        raise HTTPException(404, "No dataset loaded.")

    filtered = _apply_filters(df, category, region, year, profit)
    target_col = _find_numeric_target_column(filtered)
    date_col = _find_datetime_column(filtered.copy())
    return {
        "dataset_mode":    "sales" if _is_sales_compatible(filtered) else "generic",
        "target_column":   target_col,
        "date_column":     date_col,
        "insights":        _build_insights(filtered),
        "recommendations": _build_recommendations(filtered),
        "kpi_insights":    _build_insights(filtered)
    }

# ═════════════════════════════════════════════════════════════════════════════
# 13. PREDICTIVE ANALYTICS (Team 3)
# ═════════════════════════════════════════════════════════════════════════════
@app.get("/api/analytics/predict")
def get_predictions(
    forecast_periods: int   = Query(6),
    target_growth:    float = Query(10.0),
    _user: dict = Depends(get_current_user)
):
    _require_perm(_user, "predict")
    df = _get_df(_user)
    if df is None:
        raise HTTPException(404, "No dataset loaded.")

    date_col = _find_datetime_column(df.copy())
    target_col = _find_numeric_target_column(df)
    if not date_col:
        return {
            "status": "error",
            "message": "Prediction requires a usable date column such as Order Date, date, or transaction_date.",
        }
    if not target_col:
        return {
            "status": "error",
            "message": "Prediction requires at least one numeric target column such as Sales, Revenue, Amount, or Quantity.",
        }

    # Use Team 3 SalesPredictiveEngine for sales-style datasets only.
    if HAS_PREDICT and date_col == "Order Date" and target_col == "Sales":
        try:
            engine = SalesPredictiveEngine(df=df.copy())
            with _suppress_stdout():
                results = engine.run_full_forecast(
                    forecast_periods=forecast_periods,
                    target_growth_pct=target_growth
                )

            lr = results.get("linear_forecast", pd.DataFrame())
            ses = results.get("ses_forecast", pd.DataFrame())
            targets = results.get("alerts", pd.DataFrame())
            monthly = results.get("monthly_sales", pd.DataFrame())

            response = {
                "status":        "success",
                "mode":          "sales",
                "date_column":   date_col,
                "target_column": target_col,
                "periods":       forecast_periods,
                "target_growth": target_growth,
                "summary": {
                    "avg_monthly_value": round(float(monthly["Sales"].mean()), 2) if isinstance(monthly, pd.DataFrame) and not monthly.empty else 0.0,
                    "forecast_horizon": f"{forecast_periods} months",
                    "monthly_points": int(len(monthly)) if isinstance(monthly, pd.DataFrame) else 0,
                }
            }

            if monthly is not None and not monthly.empty:
                response["historical"] = {
                    "labels": monthly["YearMonth"].astype(str).tolist(),
                    "values": [round(float(v), 2) for v in monthly["Sales"].tolist()]
                }

            if isinstance(lr, pd.DataFrame) and not lr.empty:
                response["forecast"] = {
                    "labels": lr.index.astype(str).tolist(),
                    "values": [round(float(v), 2) for v in lr["Predicted Sales"].tolist()],
                    "lower":  [round(float(v), 2) for v in lr["Lower Bound (95%)"].tolist()],
                    "upper":  [round(float(v), 2) for v in lr["Upper Bound (95%)"].tolist()]
                }

            if isinstance(ses, pd.DataFrame) and not ses.empty:
                response["forecast_alt"] = {
                    "labels": ses.index.astype(str).tolist(),
                    "values": [round(float(v), 2) for v in ses["SES Forecast"].tolist()],
                }

            if isinstance(targets, pd.DataFrame) and not targets.empty:
                response["targets"] = targets.reset_index().to_dict(orient="records")

            return response

        except Exception:
            # Fall through to simple fallback
            pass

    return _build_simple_forecast_payload(df, date_col, target_col, forecast_periods, target_growth)

# ═════════════════════════════════════════════════════════════════════════════
# 15. REPORT GENERATION (Team 4 + report_generator.py)
# ═════════════════════════════════════════════════════════════════════════════
def _prepare_report_inputs(df: pd.DataFrame):
    """
    Build all inputs needed by report_generator functions.
    Returns: (kpis, ml_results, forecast_data, insights, charts)
    """
    kpis = _build_report_kpis(df)  # list of tuples from generate_kpis()

    # Try to get forecast data from predictive engine
    forecast_data = None
    if HAS_PREDICT and _find_datetime_column(df.copy()) == "Order Date" and _find_numeric_target_column(df) == "Sales":
        try:
            engine = SalesPredictiveEngine(df=df.copy())
            with _suppress_stdout():
                raw_forecast = engine.run_full_forecast()
            linear = raw_forecast.get("linear_forecast", pd.DataFrame())
            if isinstance(linear, pd.DataFrame) and not linear.empty:
                report_df = linear.reset_index().rename(columns={
                    "Period": "ds",
                    "Predicted Sales": "yhat",
                    "Lower Bound (95%)": "yhat_lower",
                    "Upper Bound (95%)": "yhat_upper",
                })
                forecast_data = {
                    "model": "Linear trend + seasonal adjustment",
                    "forecast_df": report_df,
                }
        except Exception:
            forecast_data = None

    # AI insights string
    insights_list = _build_insights(df)
    insights = "\n".join(insights_list) if insights_list else "No insights available."

    # Charts dict — not needed for PDF (report_generator builds its own)
    charts = _build_charts(df)

    # ml_results — pass None; report_generator handles it
    ml_results = None

    return kpis, ml_results, forecast_data, insights, charts

@app.post("/api/reports/excel")
def download_excel(
    category: str = Query("All"),
    region:   str = Query("All"),
    year:     str = Query("All"),
    profit:   str = Query("All"),
    _user: dict = Depends(get_current_user)
):
    _require_perm(_user, "download")
    if not HAS_REPORTS:
        raise HTTPException(503, "Report generator not available.")
    df = _get_df(_user)
    if df is None:
        raise HTTPException(404, "No dataset loaded.")

    filtered = _apply_filters(df, category, region, year, profit)
    try:
        kpis, ml, forecast, insights, _ = _prepare_report_inputs(filtered)
        # generate_report_excel(df, kpis, ml_results, forecast_data, insights)
        data = generate_report_excel(filtered, kpis, ml, forecast, insights)
    except Exception as e:
        raise HTTPException(500, f"Excel report error: {e}")

    base_name = "sales_report" if _is_sales_compatible(filtered) else "dataset_report"

    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={base_name}.xlsx"}
    )

@app.post("/api/reports/pdf")
def download_pdf(
    category: str = Query("All"),
    region:   str = Query("All"),
    year:     str = Query("All"),
    profit:   str = Query("All"),
    _user: dict = Depends(get_current_user)
):
    _require_perm(_user, "download")
    if not HAS_REPORTS:
        raise HTTPException(503, "Report generator not available.")
    df = _get_df(_user)
    if df is None:
        raise HTTPException(404, "No dataset loaded.")

    filtered = _apply_filters(df, category, region, year, profit)
    try:
        kpis, ml, forecast, insights, charts = _prepare_report_inputs(filtered)
        # generate_report_pdf(df, kpis, ml_results, forecast_data, insights, charts)
        data = generate_report_pdf(filtered, kpis, ml, forecast, insights, charts)
    except Exception as e:
        raise HTTPException(500, f"PDF report error: {e}")

    base_name = "sales_report" if _is_sales_compatible(filtered) else "dataset_report"

    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={base_name}.pdf"}
    )

# ═════════════════════════════════════════════════════════════════════════════
# 16. EMAIL SCHEDULER (Team 5 — email_scheduler/ modules)
# ═════════════════════════════════════════════════════════════════════════════
@app.get("/api/email/status")
def email_status(_user: dict = Depends(get_current_user)):
    _require_perm(_user, "schedule_email")
    return _email_env_status()

@app.get("/api/email/schedules")
def list_schedules(_user: dict = Depends(get_current_user)):
    _require_perm(_user, "schedule_email")
    _require_email_enabled()
    return _email_db.get_all_schedules()

@app.post("/api/email/schedules")
def create_schedule(
    req: EmailScheduleRequest,
    background_tasks: BackgroundTasks,
    _user: dict = Depends(get_current_user)
):
    _require_perm(_user, "schedule_email")
    _require_email_enabled()
    try:
        schedule_data = {
            "recipients":    [req.recipient_email],
            "frequency":     req.frequency,
            "schedule_time": req.schedule_time,
            "report_type":   req.report_type,
            "active":        True,
            "created_by":    _user.get("sub","")
        }
        sid = _email_db.save_schedule(schedule_data)
        _scheduler.add_schedule(
            schedule_id=sid,
            frequency=req.frequency,
            schedule_time=req.schedule_time,
            report_type=req.report_type,
            recipients=[req.recipient_email]
        )
        # Send first report immediately using the user's active dataset
        user_df = _get_df(_user)
        trigger_result = _scheduler.trigger_now(sid, df=user_df)
        if trigger_result.get("success"):
            return {
                "message": f"Schedule #{sid} created. First report sent to {req.recipient_email}.",
                "id": sid,
                "trigger": trigger_result,
            }
        return {
            "message": f"Schedule #{sid} created, but first send failed: {trigger_result.get('error', 'Unknown error')}",
            "id": sid,
            "trigger": trigger_result,
        }
    except Exception as e:
        raise HTTPException(500, f"Scheduler error: {e}")

@app.delete("/api/email/schedules/{schedule_id}")
def delete_schedule(schedule_id: int, _user: dict = Depends(get_current_user)):
    _require_perm(_user, "schedule_email")
    _require_email_enabled()
    schedule = _email_db.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(404, "Schedule not found.")
    _scheduler.remove_schedule(schedule_id)
    _email_db.delete_schedule(schedule_id)
    return {"message": f"Schedule #{schedule_id} deleted."}

@app.post("/api/email/send-now")
def send_now(
    req: EmailScheduleRequest,
    background_tasks: BackgroundTasks,
    _user: dict = Depends(get_current_user)
):
    _require_perm(_user, "schedule_email")
    _require_email_enabled()
    try:
        # Create a one-time schedule, trigger, then delete
        schedule_data = {
            "recipients":    [req.recipient_email],
            "frequency":     "Daily",
            "schedule_time": "09:00",
            "report_type":   req.report_type,
            "active":        False,
            "created_by":    _user.get("sub","")
        }
        sid = _email_db.save_schedule(schedule_data)
        trigger_result = _scheduler.trigger_now(sid, df=_get_df(_user))
        _email_db.delete_schedule(sid)
        if trigger_result.get("success"):
            return {"message": f"Report sent to {req.recipient_email}.", "trigger": trigger_result}
        raise HTTPException(500, f"Email send failed: {trigger_result.get('error', 'Unknown error')}")
    except Exception as e:
        raise HTTPException(500, f"Send error: {e}")

@app.get("/api/email/logs")
def get_email_logs(
    schedule_id: Optional[int] = Query(None),
    _user: dict = Depends(get_current_user)
):
    _require_perm(_user, "schedule_email")
    _require_email_enabled()
    return _email_db.get_execution_logs(schedule_id=schedule_id)

@app.get("/api/email/stats")
def get_email_stats(_user: dict = Depends(get_current_user)):
    _require_perm(_user, "schedule_email")
    _require_email_enabled()
    return _email_db.get_delivery_stats()

# ═════════════════════════════════════════════════════════════════════════════
# 17. VOICE (Team 2)
# ═════════════════════════════════════════════════════════════════════════════
@app.post("/api/voice/transcribe")
async def transcribe_voice(
    audio: UploadFile = File(...),
    _user: dict = Depends(get_current_user)
):
    try:
        from nlp.voice_input import transcribe_audio_file
        contents = await audio.read()
        text     = transcribe_audio_file(contents)
        if not text:
            raise HTTPException(422, "Could not transcribe audio.")
        return {"text": text}
    except ImportError:
        raise HTTPException(503, "Voice transcription module not available.")

@app.post("/api/voice/speak")
def speak_text(req: VoiceSpeakRequest, _user: dict = Depends(get_current_user)):
    try:
        from nlp.voice_output import speak
        audio = speak(req.text)
        return StreamingResponse(audio, media_type="audio/mpeg")
    except ImportError:
        raise HTTPException(503, "Voice output module not available.")

# ═════════════════════════════════════════════════════════════════════════════
# 18. DATA STATUS + CLEAR
# ═════════════════════════════════════════════════════════════════════════════
@app.get("/api/data/status")
def data_status(_user: dict = Depends(get_current_user)):
    df = _get_df(_user)
    meta = _get_upload_meta(_user)
    return {
        "dataset_loaded": df is not None,
        "rows":           len(df) if df is not None else 0,
        "columns":        len(df.columns) if df is not None else 0,
        "filename":       meta.get("filename","Default dataset"),
        "uploaded_at":    meta.get("uploaded_at",""),
        "uploaded_by":    meta.get("uploaded_by",""),
        "dataset_type":   meta.get("dataset_type","default"),
        "warnings":       meta.get("warnings",[]),
        "suggestions":    meta.get("suggestions",[]),
    }

@app.delete("/api/data/clear")
def clear_data(_user: dict = Depends(get_current_user)):
    _require_perm(_user, "upload")
    _clear_user_upload(_user)
    return {"message": "Dataset cleared. Default dataset restored."}

# ═════════════════════════════════════════════════════════════════════════════
# 19+20. HEALTH + ROLES
# ═════════════════════════════════════════════════════════════════════════════
@app.get("/api/health")
def health():
    df = _get_df()
    return {
        "status":          "ok",
        "ts":              datetime.utcnow().isoformat(),
        "version":         "2.1.0",
        "dataset_loaded":  df is not None,
        "rows":            len(df) if df is not None else 0,
        "modules": {
            "nlp":       HAS_NLP,
            "analytics": HAS_ANALYZER,
            "predict":   HAS_PREDICT,
            "profiling": HAS_PROFILING,
            "quality":   HAS_QUALITY,
            "reports":   HAS_REPORTS,
            "scheduler": HAS_SCHEDULER,
        }
    }

@app.get("/api/roles")
def get_roles(_user: dict = Depends(get_current_user)):
    return {role: list(perms) for role, perms in ROLE_PERMS.items()}
