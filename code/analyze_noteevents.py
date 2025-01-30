import pandas as pd
import os
from dotenv import load_dotenv

def analyze_noteevents():
    """Analyze the contents of NOTEEVENTS.csv"""
    # Load environment variables
    load_dotenv()
    
    notes_path = os.getenv('MIMIC_NOTES_PATH')
    if not os.path.isabs(notes_path):
        notes_path = os.path.abspath(os.path.join(os.getcwd(), notes_path))
    
    print(f"\nAnalyzing: {notes_path}")
    
    try:
        # First check file size
        file_size = os.path.getsize(notes_path) / (1024 * 1024)  # Size in MB
        print(f"File size: {file_size:.2f} MB")
        
        # Read the first few lines directly
        print("\nFirst 5 lines of the file:")
        with open(notes_path, 'r') as f:
            for i, line in enumerate(f):
                if i < 5:
                    print(line.strip())
                else:
                    break
        
        # Try reading with pandas
        print("\nReading with pandas...")
        df = pd.read_csv(notes_path)
        print(f"\nDataframe shape: {df.shape}")
        
        # Analyze each column
        print("\nColumn analysis:")
        for col in df.columns:
            print(f"\n{col}:")
            print(f"  Type: {df[col].dtype}")
            print(f"  Null values: {df[col].isnull().sum()}")
            print(f"  Number of unique values: {df[col].nunique()}")
            
            # For category-like columns, show unique values
            if any(term in col.upper() for term in ['CATEGORY', 'TYPE', 'DESC']):
                print("  Unique values:")
                for val in df[col].unique():
                    print(f"    - {val}")
        
        # Look specifically for discharge summaries
        category_cols = [col for col in df.columns 
                        if any(term in col.upper() 
                              for term in ['CATEGORY', 'TYPE', 'DESC'])]
        
        for col in category_cols:
            print(f"\nSearching for discharge summaries in {col}:")
            mask = df[col].str.contains('discharge|summary', 
                                      case=False, 
                                      na=False)
            matches = df[mask][col].unique()
            if len(matches) > 0:
                print("Found matches:")
                for match in matches:
                    count = df[df[col] == match].shape[0]
                    print(f"  - {match}: {count} records")
            else:
                print("No matches found")
        
    except Exception as e:
        print(f"\nError analyzing file: {str(e)}")
        
        # Try reading in chunks
        print("\nTrying to read in chunks...")
        try:
            chunk_size = 1000
            chunks = pd.read_csv(notes_path, chunksize=chunk_size)
            
            for i, chunk in enumerate(chunks):
                print(f"\nChunk {i+1}:")
                print(f"Shape: {chunk.shape}")
                if 'category' in chunk.columns:
                    print("\nCategories in this chunk:")
                    print(chunk['category'].value_counts())
                if i >= 4:  # Only look at first 5 chunks
                    break
                    
        except Exception as chunk_error:
            print(f"\nError reading chunks: {str(chunk_error)}")

if __name__ == "__main__":
    analyze_noteevents() 