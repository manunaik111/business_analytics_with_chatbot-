"""
data_management/file_upload.py

File upload validation and parsing helpers.
Two layers:
  1.  Pure-Python functions (validate_bytes, parse_bytes_to_df) — used by api.py.
  2.  Streamlit UI section (file_upload_section) — used by main_app.py.

The FastAPI upload route calls only the pure-Python layer.
"""

import io
import pandas as pd

# ── Optional Streamlit (UI layer only) ────────────────────────────────────────
try:
    import streamlit as st
    import time
    HAS_STREAMLIT = True
except ImportError:
    st = None       # type: ignore[assignment]
    HAS_STREAMLIT = False

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SUPPORTED_EXTENSIONS: set[str] = {"csv", "xlsx", "xls", "json"}
MAX_FILE_SIZE_MB: int = 200

# ─────────────────────────────────────────────────────────────────────────────
#  PURE-PYTHON VALIDATION & PARSING  (no Streamlit)
# ─────────────────────────────────────────────────────────────────────────────

class UploadValidationError(ValueError):
    """Raised when an uploaded file fails validation."""


def validate_filename_and_size(filename: str, size_bytes: int) -> None:
    """
    Validate extension and file size.
    Raises UploadValidationError with a clear message on failure.
    """
    if not filename:
        raise UploadValidationError("No filename provided.")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise UploadValidationError(
            f"Unsupported file type '.{ext}'. "
            f"Please upload one of: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )

    size_mb = size_bytes / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise UploadValidationError(
            f"File size ({size_mb:.1f} MB) exceeds the {MAX_FILE_SIZE_MB} MB limit."
        )


def parse_bytes_to_df(contents: bytes, filename: str) -> pd.DataFrame:
    """
    Parse raw file bytes into a DataFrame.
    Handles:
      - CSV  (tries utf-8 → latin1 → cp1252 encodings)
      - Excel (.xlsx, .xls)
      - JSON

    Raises UploadValidationError with a clear message on failure.
    """
    if not contents:
        raise UploadValidationError("Uploaded file is empty (0 bytes).")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "csv":
        df = _parse_csv(contents, filename)
    elif ext in ("xlsx", "xls"):
        df = _parse_excel(contents, filename)
    elif ext == "json":
        df = _parse_json(contents, filename)
    else:
        raise UploadValidationError(
            f"Unsupported file extension '.{ext}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )

    return df


def _parse_csv(contents: bytes, filename: str) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "latin1", "cp1252"):
        try:
            df = pd.read_csv(io.BytesIO(contents), encoding=encoding, low_memory=False)
            _validate_dataframe(df, filename)
            return df
        except UploadValidationError:
            raise
        except UnicodeDecodeError:
            continue
        except Exception as exc:
            raise UploadValidationError(f"Could not parse CSV: {exc}") from exc
    raise UploadValidationError(
        "Could not read CSV file with any supported encoding "
        "(tried utf-8, latin1, cp1252). "
        "Please save the file as UTF-8 and try again."
    )


def _parse_excel(contents: bytes, filename: str) -> pd.DataFrame:
    try:
        df = pd.read_excel(io.BytesIO(contents))
        _validate_dataframe(df, filename)
        return df
    except UploadValidationError:
        raise
    except Exception as exc:
        raise UploadValidationError(f"Could not parse Excel file: {exc}") from exc


def _parse_json(contents: bytes, filename: str) -> pd.DataFrame:
    try:
        df = pd.read_json(io.BytesIO(contents))
        _validate_dataframe(df, filename)
        return df
    except UploadValidationError:
        raise
    except Exception as exc:
        raise UploadValidationError(f"Could not parse JSON file: {exc}") from exc


def _validate_dataframe(df: pd.DataFrame, filename: str) -> None:
    """Raise UploadValidationError for common structural problems."""
    if df is None or df.empty:
        raise UploadValidationError(
            f"'{filename}' contains no rows. Please upload a file with data."
        )
    if len(df.columns) == 0:
        raise UploadValidationError(
            f"'{filename}' has no columns. The file appears to be empty or malformed."
        )
    # Duplicate column names
    cols = [str(c).strip() for c in df.columns]
    seen: set[str] = set()
    dupes: list[str] = []
    for c in cols:
        if c in seen:
            dupes.append(c)
        seen.add(c)
    if dupes:
        raise UploadValidationError(
            f"Duplicate column names detected: {', '.join(set(dupes))}. "
            "Please rename duplicate columns and re-upload."
        )
    # Detect unsupported structure (e.g. single column that is a stringified dict)
    if len(df.columns) == 1:
        sample_val = str(df.iloc[0, 0]) if len(df) > 0 else ""
        if sample_val.strip().startswith("{"):
            raise UploadValidationError(
                "File appears to contain JSON strings inside CSV cells. "
                "Please export your data as a flat table."
            )


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from column names and return a copy."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def auto_parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Try to parse any column whose name contains 'date' or 'time' as datetime.
    Leaves other columns untouched. Returns a copy.
    """
    df = df.copy()
    for col in df.columns:
        if any(kw in col.lower() for kw in ("date", "time", "timestamp")):
            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  STREAMLIT UI SECTION  (called from main_app.py only)
# ─────────────────────────────────────────────────────────────────────────────

def _apply_styles() -> None:
    if not HAS_STREAMLIT or st is None:
        return
    st.markdown("""
        <style>
        .stApp { background-color: #F0F4FA; }
        .main-title { font-size:2.5rem; font-weight:700; color:#1A73E8;
                      text-align:center; margin-bottom:0.2rem; }
        .sub-title  { font-size:1rem; color:#555; text-align:center;
                      margin-bottom:2rem; }
        .upload-box { background:#FFF; border:2px dashed #1A73E8;
                      border-radius:16px; padding:2rem; text-align:center;
                      margin-bottom:1.5rem; }
        .metric-card { background:#FFF; border-radius:12px; padding:1.2rem;
                       text-align:center; box-shadow:0 2px 8px rgba(0,0,0,.08);
                       border-left:4px solid #1A73E8; }
        .metric-label { font-size:.85rem; color:#888; margin-bottom:.3rem; }
        .metric-value { font-size:1.6rem; font-weight:700; color:#1A73E8; }
        .success-banner { background:linear-gradient(135deg,#E8F5E9,#C8E6C9);
                          border-left:5px solid #34A853; border-radius:12px;
                          padding:1rem 1.5rem; font-size:1rem; color:#1B5E20;
                          font-weight:600; margin-bottom:1.5rem; }
        #MainMenu { visibility:hidden; } footer { visibility:hidden; }
        </style>
    """, unsafe_allow_html=True)


def file_upload_section():
    """
    Streamlit UI for dataset upload.
    Returns the uploaded DataFrame or None.
    """
    if not HAS_STREAMLIT or st is None:
        return None

    _apply_styles()

    st.markdown('<div class="main-title">📂 Data Upload</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Upload your dataset · CSV · Excel · JSON · Max 200 MB</div>',
        unsafe_allow_html=True
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        label="Drag and drop your file here or click to browse",
        type=list(SUPPORTED_EXTENSIONS),
        help=f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))} — Max {MAX_FILE_SIZE_MB} MB",
        key="main_uploader",
    )

    if uploaded_file is None:
        return None

    # Validate
    try:
        validate_filename_and_size(uploaded_file.name, uploaded_file.size)
    except UploadValidationError as exc:
        st.error(f"❌ {exc}")
        return None

    # Progress animation
    progress = st.progress(0, text="Processing your file…")
    for i in range(100):
        time.sleep(0.008)
        progress.progress(i + 1, text=f"Loading… {i + 1}%")
    progress.empty()

    # Parse
    try:
        contents = uploaded_file.read()
        df = parse_bytes_to_df(contents, uploaded_file.name)
        df = normalize_columns(df)
        df = auto_parse_dates(df)
    except UploadValidationError as exc:
        st.error(f"❌ {exc}")
        return None
    except Exception as exc:
        st.error(f"❌ Unexpected error reading file: {exc}")
        return None

    # Store in session
    st.session_state["uploaded_df"]  = df
    st.session_state["file_name"]    = uploaded_file.name

    # Success banner
    st.markdown(
        f'<div class="success-banner">✅ <b>{uploaded_file.name}</b> uploaded — '
        f'{df.shape[0]:,} rows × {df.shape[1]} columns</div>',
        unsafe_allow_html=True
    )

    # Metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">📄 File</div>'
                    f'<div class="metric-value" style="font-size:1rem">{uploaded_file.name}</div>'
                    f'</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">🔢 Rows</div>'
                    f'<div class="metric-value">{df.shape[0]:,}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">📊 Columns</div>'
                    f'<div class="metric-value">{df.shape[1]}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">🔍 Data Preview (First 5 Rows)</div>',
                unsafe_allow_html=True)
    st.dataframe(df.head(), use_container_width=True)

    return df
