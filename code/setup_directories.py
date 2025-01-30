import os

def create_directory_structure():
    """Create the necessary directory structure for the project"""
    directories = [
        'mimicdata',
        'mimicdata/processed',
        'mimicdata/caml',
        'models',
        'logs',
        'results'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

if __name__ == "__main__":
    create_directory_structure() 