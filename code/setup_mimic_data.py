import os
import shutil
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_and_setup_mimic_data():
    """Check and setup MIMIC data files"""
    
    # Get paths from environment variables
    notes_path = os.getenv('MIMIC_NOTES_PATH')
    procedures_path = os.getenv('MIMIC_PROCEDURES_PATH')
    
    # Convert to absolute paths
    notes_path = os.path.abspath(notes_path)
    procedures_path = os.path.abspath(procedures_path)
    
    print("\nChecking MIMIC data setup...")
    print(f"NOTEEVENTS path: {notes_path}")
    print(f"PROCEDURES path: {procedures_path}")
    
    # Check NOTEEVENTS.csv
    if os.path.exists(notes_path):
        file_size = os.path.getsize(notes_path) / (1024 * 1024)  # Size in MB
        print(f"\nNOTEEVENTS.csv exists (size: {file_size:.2f} MB)")
        
        if file_size < 1:  # Less than 1MB
            print("Warning: NOTEEVENTS.csv appears to be empty or contains only headers")
            print("Expected size should be several GB")
    else:
        print("\nError: NOTEEVENTS.csv not found")
    
    # Check PROCEDURES_ICD.csv
    if os.path.exists(procedures_path):
        file_size = os.path.getsize(procedures_path) / (1024 * 1024)  # Size in MB
        print(f"\nPROCEDURES_ICD.csv exists (size: {file_size:.2f} MB)")
        
        if file_size < 0.1:  # Less than 100KB
            print("Warning: PROCEDURES_ICD.csv appears to be empty or too small")
    else:
        print("\nError: PROCEDURES_ICD.csv not found")
    
    # Try to read headers
    try:
        print("\nTrying to read NOTEEVENTS.csv header...")
        with open(notes_path, 'r') as f:
            header = f.readline().strip()
            print(f"Header: {header}")
            
            # Read next line to check if there's data
            data_line = f.readline().strip()
            if not data_line:
                print("Warning: No data found after header")
            else:
                print("Found data after header")
    except Exception as e:
        print(f"Error reading NOTEEVENTS.csv: {e}")
    
    print("\nMIMIC Data Requirements:")
    print("1. NOTEEVENTS.csv should be several GB in size")
    print("2. NOTEEVENTS.csv should contain millions of clinical notes")
    print("3. Make sure you have the complete MIMIC-III dataset")
    print("\nTo fix:")
    print("1. Download the complete MIMIC-III dataset")
    print("2. Extract NOTEEVENTS.csv and PROCEDURES_ICD.csv")
    print("3. Copy the files to the paths specified in .env")
    print("4. Make sure the files have read permissions")

if __name__ == "__main__":
    check_and_setup_mimic_data() 