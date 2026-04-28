"""data_ingestion.py — File loading with multi-encoding support."""
import pandas as pd
import streamlit as st
import os

@st.cache_data
def load_file(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext == ".csv":
            for enc in ["utf-8", "latin1", "cp1252"]:
                try:
                    uploaded_file.seek(0)
                    return pd.read_csv(uploaded_file, encoding=enc)
                except (UnicodeDecodeError, Exception):
                    continue
        elif ext in [".xlsx", ".xls"]:
            return pd.read_excel(uploaded_file)
        elif ext == ".json":
            return pd.read_json(uploaded_file)
        else:
            st.error(f"Unsupported format: {ext}")
            return None
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def get_file_info(df):
    if df is None:
        return {}
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "size_kb": round(df.memory_usage(deep=True).sum() / 1024, 1),
        "missing_cells": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }
