import os
import constants

def verify_mimic_data():
    """Verify that all required MIMIC data files are present"""
    required_files = {
        'NOTEEVENTS.csv': constants.NOTEEVENTS_FILE_PATH,
        'PROCEDURES_ICD.csv': constants.PROCEDURES_FILE_PATH,
        'DIAGNOSES_ICD.csv': constants.DIAGNOSES_FILE_PATH,
        'D_ICD_DIAGNOSES.csv': constants.DIAG_CODE_DESC_FILE_PATH,
        'D_ICD_PROCEDURES.csv': constants.PROC_CODE_DESC_FILE_PATH,
        'ICD9_descriptions': constants.ICD_DESC_FILE_PATH
    }
    
    print("\nChecking MIMIC data files...")
    missing_files = []
    for file_name, file_path in required_files.items():
        if os.path.exists(file_path):
            print(f"✓ Found {file_name}")
        else:
            print(f"✗ Missing {file_name}")
            missing_files.append(file_name)
    
    if missing_files:
        print("\nMissing files:")
        for file in missing_files:
            print(f"- {file}")
        print("\nPlease place these files in the mimicdata directory.")
        return False
    
    print("\nAll required MIMIC files are present!")
    return True

if __name__ == "__main__":
    verify_mimic_data() 