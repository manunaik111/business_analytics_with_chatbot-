#!/usr/bin/env python3
"""
Sales Dashboard - Main Entry Point
This script launches the Streamlit sales dashboard.
"""

import os
import subprocess
import webbrowser
import time


def check_required_files():
    """Check if required files exist"""
    
    required_files = [
        "streamlit_app.py",
        "analysis.py",
        "dashboard.py",
        "SALES_DATA_SETT.csv"
    ]

    for file in required_files:
        if not os.path.exists(file):
            print(f"Missing file: {file}")
            return False

    print("All required files found.")
    return True


def launch_dashboard():
    """Launch Streamlit dashboard"""

    print("Starting Streamlit Dashboard...")

    subprocess.Popen(["streamlit", "run", "streamlit_app.py"])

    # wait for server to start
    time.sleep(3)

    webbrowser.open("http://localhost:8501")

    print("Dashboard opened in browser!")


def main():
    """Main function"""

    print("=" * 60)
    print("SALES ANALYTICS DASHBOARD")
    print("=" * 60)

    if check_required_files():
        launch_dashboard()
    else:
        print("Please make sure all project files exist.")


if __name__ == "__main__":
    main()