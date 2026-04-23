import pandas as pd
import numpy as np

def analyze_quality(df: pd.DataFrame) -> dict:
    """
    Analyzes specific data quality characteristics including duplications, 
    missing values, outlier estimations, and generates a Quality Score.
    """
    if df is None or df.empty:
        return {"status": "error", "message": "The dataset is empty or not loaded.", "data": None}
        
    try:
        # 1. Missing Values
        missing_counts = df.isnull().sum()
        total_missing = missing_counts.sum()
        missing_df = pd.DataFrame(missing_counts[missing_counts > 0], columns=['Missing Values'])
        
        # 2. Duplicates
        duplicate_count = df.duplicated().sum()
        
        # 3. Basic Outliers Calculation via IQR for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outlier_count = 0
        outliers_dict = {}
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            col_outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            outliers_dict[col] = int(col_outliers)
            outlier_count += col_outliers
            
        # 4. Generate overall arbitrary Quality Score (0-100)
        total_cells = df.size
        deduction_missing = (total_missing / total_cells) * 100 if total_cells > 0 else 0
        deduction_dupes = (duplicate_count / len(df)) * 100 if len(df) > 0 else 0
        
        score = max(0, min(100, 100 - (deduction_missing * 1.5) - (deduction_dupes * 2.0)))
        
        quality_data = {
            "score": round(score, 1),
            "missing_total": int(total_missing),
            "missing_summary": missing_df,
            "duplicate_rows": int(duplicate_count),
            "outliers_total": int(outlier_count),
            "outliers_summary": outliers_dict
        }
        
        return {
            "status": "success",
            "message": "Successfully generated data quality report.",
            "data": quality_data
        }
    except Exception as e:
        return {"status": "error", "message": f"Error performing quality analysis: {e}", "data": None}
