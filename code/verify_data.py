import os
import pandas as pd
import shutil
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_file_size(file_path):
    """Check if file has actual content beyond header"""
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb < 0.001:  # Less than 1KB
        return False, f"File appears empty: {file_path} (size: {size_mb:.2f} MB)"
    
    return True, f"File OK: {file_path} (size: {size_mb:.2f} MB)"

def verify_mimic_data():
    """Verify MIMIC data files and their contents"""
    # Get paths from environment variables
    notes_path = os.getenv('MIMIC_NOTES_PATH')
    procedures_path = os.getenv('MIMIC_PROCEDURES_PATH')
    
    if not notes_path or not procedures_path:
        print("Error: Environment variables MIMIC_NOTES_PATH and/or MIMIC_PROCEDURES_PATH not set")
        return
    
    # Convert relative paths to absolute if needed
    if not os.path.isabs(notes_path):
        notes_path = os.path.abspath(os.path.join(os.getcwd(), notes_path))
    if not os.path.isabs(procedures_path):
        procedures_path = os.path.abspath(os.path.join(os.getcwd(), procedures_path))
    
    print(f"\nUsing paths from .env file:")
    print(f"NOTEEVENTS path: {notes_path}")
    print(f"PROCEDURES path: {procedures_path}")
    
    required_files = {
        os.path.basename(notes_path): {
            'path': notes_path,
            'min_size_mb': 100,
            'required_columns': ['ROW_ID', 'SUBJECT_ID', 'HADM_ID', 'CATEGORY', 'TEXT']
        },
        os.path.basename(procedures_path): {
            'path': procedures_path,
            'min_size_mb': 1,
            'required_columns': ['SUBJECT_ID', 'HADM_ID', 'ICD9_CODE']
        }
    }
    
    print("\nVerifying MIMIC data files...")
    
    issues_found = False
    for filename, requirements in required_files.items():
        file_path = requirements['path']
        print(f"\nChecking {filename}...")
        
        # Check if file exists and has content
        ok, msg = verify_file_size(file_path)
        print(msg)
        if not ok:
            issues_found = True
            continue
        
        # Try to read and validate the file
        try:
            # First try reading just the header
            print(f"Reading header from {filename}...")
            header = pd.read_csv(file_path, nrows=0)
            print(f"Columns found: {header.columns.tolist()}")
            
            # Then try reading a few rows
            print(f"Reading sample rows from {filename}...")
            df = pd.read_csv(file_path, nrows=5)
            print(f"Successfully read {len(df)} sample rows")
            
            # Check required columns
            missing_cols = [col for col in requirements['required_columns'] 
                          if col.upper() not in [c.upper() for c in df.columns]]
            
            if missing_cols:
                print(f"Missing required columns: {missing_cols}")
                print(f"Available columns: {df.columns.tolist()}")
                issues_found = True
            
            # Print sample of data
            print("\nSample data:")
            print(df.head())
            
        except Exception as e:
            print(f"Error reading {filename}: {str(e)}")
            issues_found = True
    
    if issues_found:
        print("\nIssues were found with the MIMIC data files.")
        print("\nPlease ensure:")
        print("1. The paths in .env file are correct")
        print("2. Files have the correct format and content")
        print("3. Files have read permissions")
    else:
        print("\nAll MIMIC data files appear to be valid!")

if __name__ == "__main__":
    verify_mimic_data() 