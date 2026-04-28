import streamlit as st
import pandas as pd

def handle_file_upload() -> pd.DataFrame:
    """
    Renders a unified file uploader widget and converts the uploaded CSV/Excel 
    into a Pandas DataFrame stored safely in session state.
    """
    uploaded_file = st.file_uploader("Upload your dataset (CSV, Excel)", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
                
            # Safely store to session state avoiding constant reloads
            st.session_state.df = df
            st.session_state.data_loaded = True
            
            st.success(f"Successfully loaded {uploaded_file.name} with {len(df)} rows!")
            return df
        except Exception as e:
            st.error(f"Error loading file: {e}")
            return None
    return None
