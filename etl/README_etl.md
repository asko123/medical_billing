# ETL Pipeline for RAG

This repository contains a modular ETL pipeline designed for a Retrieval Augmented Generation (RAG) model. The pipeline downloads PDF files from SharePoint, extracts their text content, and ingests the data into the Lex API. The configuration (such as endpoints and file details) is managed using a YAML file.

## Folder Structure
 etl/
├── config.py # Loads configuration from config.yaml
├── config.yaml # YAML file containing all configuration parameters
├── lex_api.py # Contains the LexAPI class to interact with the Lex API (ingest, search, delete)
├── pdf_processor.py # Contains the PDFProcessor class to extract text from PDFs
├── sharepoint.py # Contains the SharePointClient class to interact with SharePoint (fetch folder path, download PDFs)
├── utils.py # Contains the Utils class with helper functions (e.g., time conversion, base64 encoding)
└── main.py # Main orchestration file that executes

## Dependencies

Ensure you have the following dependencies installed:
- PyYAML 
- PyPDF2
- requests
- requests_ntlm
- gs_auth  

## Configuration

The pipeline configuration is stored in the YAML file `etl/config.yaml`. This file includes settings such as:

- SharePoint endpoints
- The list of PDFs to process
- Native IDs and metadata for each PDF
- Lex API endpoints for ingestion, search, and deletion

The `etl/config.py` module loads this configuration and makes it available as a Python dictionary via:   

```python
from etl import config

# Access configuration parameters
USER_NAME = config["user_name"] 
```

## Code Flow

### 1. Configuration Loading
- **File:** `etl/config.yaml` and `etl/config.py`  
- **Description:**  
  The YAML file contains all relevant configuration settings. The `config.py` module loads the YAML file into a Python dictionary named `config`, which is then used by all other modules.

### 2. SharePoint Interaction
- **File:** `etl/sharepoint.py`  
- **Description:**  
  The `SharePointClient` class connects to SharePoint using NTLM authentication. It retrieves the folder path where PDFs are stored and downloads them as byte streams.

### 3. PDF Processing
- **File:** `etl/pdf_processor.py`  
- **Description:**  
  The `PDFProcessor` class extracts text from PDF files using pdfplumber. The extracted text is later encoded in base64 format before ingestion.

### 4. Utility Functions
- **File:** `etl/utils.py`  
- **Description:**  
  The `Utils` class provides helper functions including:
  - Converting a datetime string to epoch seconds.
  - Encoding text to a base64 string.

### 5. Lex API Interaction
- **File:** `etl/lex_api.py`  
- **Description:**  
  The `LexAPI` class interacts with the Lex service to:
  - Ingest documents.
  - Check the ingestion status.
  - Perform search queries.
  - Delete documents based on native IDs.  
  It uses the configuration values loaded from the YAML file and authentication provided by the `gs_auth` module.

### 6. ETL Orchestration
- **File:** `etl/main.py`  
- **Description:**  
  The `main.py` file orchestrates the entire ETL process. It breaks the workflow into distinct functions that:
  - Download, process, and ingest documents.
  - Check the ingestion status.
  - Execute search queries.
  - Delete a sample document.  
  The main function (`run_etl()`) calls these utility functions in the proper order, ensuring that the `main()` function itself contains no business logic.

## How to Run

To execute the ETL pipeline, run the following command from the root of your project:

```bash
#!/bin/bash
# Set environment variable to override the config setting:
# This ensures that UPLOAD_FROM_LOCAL is false.
export UPLOAD_FROM_LOCAL=false

# Run the ETL process.
python etl/main.py
```

This command triggers the following sequence:
1. **Ingestion:**  
   Downloads PDF files from SharePoint, extracts the text, and ingests the data into Lex via the Lex API.
2. **Status Check:**  
   Prints the ingestion status for each document.
3. **Search:**  
   Performs a search query to retrieve and display document information.
4. **Deletion Example:**  
   Demonstrates how to delete a document using its native ID.

  




