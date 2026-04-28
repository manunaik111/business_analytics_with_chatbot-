import pandas as pd

def generate_profile(df: pd.DataFrame) -> dict:
    """
    Generates high-level statistical summaries and basic descriptors (shape, data types).
    Returns a dictionary structured for dynamic rendering in Streamlit.
    """
    if df is None or df.empty:
        return {"status": "error", "message": "The dataset is empty or not loaded.", "data": None}
        
    try:
        # Generates core statistical distributions for numeric columns
        stats_df = df.describe()
        
        # Determine explicit column types dynamically
        col_types = pd.DataFrame(df.dtypes, columns=['Data Type'])
        col_types_str = col_types.to_dict()['Data Type']
        str_types = {k: str(v) for k, v in col_types_str.items()}
        
        profile_data = {
            "total_rows": len(df),
            "total_cols": len(df.columns),
            "columns": list(df.columns),
            "types": str_types,
            "statistics": stats_df,
            "memory_usage": df.memory_usage(deep=True).sum()
        }
        
        return {
            "status": "success",
            "message": "Successfully generated dataset profile.",
            "data": profile_data
        }
    except Exception as e:
        return {"status": "error", "message": f"Error profiling data: {e}", "data": None}
