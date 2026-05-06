"""
Per-user uploaded dataset storage for the FastAPI integration.

This keeps uploaded data separate by authenticated user and survives server
restart without pretending every dataset is sales data.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import pandas as pd


UPLOAD_DIR = Path("data") / "uploads"
ACTIVE_UPLOAD_PATH = Path("data") / "_active_upload.pkl"
ACTIVE_META_PATH = Path("data") / "_active_upload_meta.json"


def _safe_user_key(user_id: str) -> str:
    key = (user_id or "anonymous").strip().lower()
    key = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
    return key or "anonymous"


def _paths(user_id: str) -> tuple[Path, Path]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    key = _safe_user_key(user_id)
    return UPLOAD_DIR / f"{key}.pkl", UPLOAD_DIR / f"{key}_meta.json"


def save_user_upload(user_id: str, df: pd.DataFrame, meta: dict) -> None:
    data_path, meta_path = _paths(user_id)
    df.to_pickle(data_path)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def load_user_upload(user_id: str) -> Optional[pd.DataFrame]:
    data_path, _ = _paths(user_id)
    if not data_path.exists():
        return None
    return pd.read_pickle(data_path)


def load_user_meta(user_id: str) -> dict:
    _, meta_path = _paths(user_id)
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def clear_user_upload(user_id: str) -> None:
    data_path, meta_path = _paths(user_id)
    for path in (data_path, meta_path):
        if path.exists():
            path.unlink()


def save_active_upload(df: pd.DataFrame, meta: dict) -> None:
    ACTIVE_UPLOAD_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(ACTIVE_UPLOAD_PATH)
    ACTIVE_META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def load_active_upload() -> Optional[pd.DataFrame]:
    if not ACTIVE_UPLOAD_PATH.exists():
        return None
    return pd.read_pickle(ACTIVE_UPLOAD_PATH)


def load_active_meta() -> dict:
    if not ACTIVE_META_PATH.exists():
        return {}
    try:
        return json.loads(ACTIVE_META_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def clear_active_upload() -> None:
    for path in (ACTIVE_UPLOAD_PATH, ACTIVE_META_PATH):
        if path.exists():
            path.unlink()
