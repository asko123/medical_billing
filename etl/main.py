import os
import json
import time
from etl import config
from etl.sharepoint import SharePointClient
from etl.pdf_processor import PDFProcessor
from etl.lex_api import LexAPI
from etl.utils import Utils
import tempfile
from etl.FIS_Validator import FISValidator
import sys

logger = Utils.get_logger("main")

# Global instances for shared use.
sp_client = SharePointClient()
pdf_processor = PDFProcessor()
lex_api = LexAPI()
new_doc_ids = []  # This will hold newly ingested document ids.
STATE_FILE = os.path.join(os.path.dirname(__file__), "processed_files.json")

# Determine deployment environment via command-line argument; default to 'dev'
if len(sys.argv) > 1:
    deploy_env = sys.argv[1].lower()
else:
    deploy_env = "dev"
    
logger.info("Deployment environment: {}".format(deploy_env))

# Load environment-specific endpoints
try:
    env_config = config["environments"][deploy_env]
    config.update({
        "lex_ingest_url": env_config["lex_ingest_url"],
        "lex_search_url": env_config["lex_search_url"],
        "lex_delete_url": env_config["lex_delete_url"],
        "lex_status_url": env_config["lex_status_url"]
    })
    logger.info("Loaded configuration for environment: {}".format(deploy_env))
except KeyError as e:
    logger.error("Invalid environment '{}' or missing configuration: {}".format(deploy_env, e))
    raise

def load_processed_state():
    """Load the processed state from the JSON state file."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        logger.error("Error reading state file {}: {}".format(STATE_FILE, e))
        return {}

def save_processed_state(processed_files):
    """Save the processed state back to the state file."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(processed_files, f, indent=2)
    except Exception as e:
        logger.error("Error writing state file {}: {}".format(STATE_FILE, e))

def get_pdf_bytes_for_entry(file, folder_path):
    """
    Retrieve PDF bytes from either the local file system or SharePoint.
    """
    # Determine upload source dynamically based on config and environment.
    upload_from_local = config.get("upload_from_local", False)
    env_flag = os.environ.get("UPLOAD_FROM_LOCAL", None)
    if env_flag is not None:
        upload_from_local = env_flag.lower() in ("1", "true", "yes")

    try:
        if upload_from_local:
            local_folder = config.get("local_pdf_path", ".")
            pdf_file_path = os.path.join(local_folder, file)
            with open(pdf_file_path, "rb") as f:
                pdf_bytes = f.read()
            logger.info("Loaded {} from local file system.".format(file))
        else:
            pdf_bytes = sp_client.download_pdf(file, folder_path)
        return pdf_bytes
    except Exception as e:
        logger.error("Error obtaining PDF bytes for {}: {}".format(file, e))
        return None

def process_pdf_and_metadata(file, pdf_bytes, metadata):
    """
    Extract data from the PDF bytes; encode the text and convert the last updated date.
    Returns the base64 string and updated metadata.
    """
    try:
        extracted_data = pdf_processor.extract_data_from_pdf(pdf_bytes)
    except Exception as e:
        logger.error("Error extracting data from {}: {}".format(file, e))
        return None, None

    try:
        document_b64 = Utils.text_to_base64(extracted_data["text"])
    except Exception as e:
        logger.error("Error encoding data from {}: {}".format(file, e))
        return None, None

    try:
        metadata["lastUpdated_d"] = Utils.convert_to_long_type(metadata["lastUpdated_d"], "%Y-%m-%d")
    except Exception as e:
        logger.error("Error converting date for {}: {}".format(file, e))
        return None, None

    return document_b64, metadata


def build_payload(native_id, metadata, document_b64):
    """
    Build and return the payload document from the provided components.
    """
    fields = {
        "lastUpdated_d": metadata["lastUpdated_d"],
        "title": metadata["title"],
        "sourceName_s": metadata["sourceName_s"],
        "sourceDomain_s": metadata["sourceDomain_s"],
        "sourceOriginDivision_s": metadata["sourceOriginDivision_s"],
        "fileFormat_s": metadata["fileFormat_s"],
        "category_s": metadata.get("category_s", ""),
        "keywords_s": metadata.get("keywords_s", []),
        "securityFramework_s": metadata.get("securityFramework_s", []),
        "securityControl_s": metadata.get("securityControl_s", []),
        "reviewCadence_s": metadata.get("reviewCadence_s", ""),
        "useCase_s": metadata.get("useCase_s", "")
    }

    payload_document = {
        "nativeId": native_id,
        "title": metadata["title"],
        "fileExtension": metadata["fileFormat_s"],
        "mediaType": "text/plain",
        "entitlements": ["public"],
        "data": document_b64,
        "privacyLevel": "public",
        "fields": fields
    }
    return payload_document

def ingest_entry(entry, processed_files, folder_path, current_time):
    """
    Process an individual PDF entry: get its bytes, convert its contents,
    build its payload, and ingest it via Lex API.
    """
    file = entry["filename"]
    native_id = entry["native_id"]
    metadata = entry["metadata"]

    pdf_bytes = get_pdf_bytes_for_entry(file, folder_path)
    if pdf_bytes is None:
        return None

    # Determine the source: if uploading from local, use the local file directly
    upload_from_local = config.get("upload_from_local", False)
    fis_validator = FISValidator()

    if upload_from_local:
        # When file is available locally, use its existing path.
        local_file_path = os.path.join(config.get("local_pdf_path", "."), file)
        is_safe = fis_validator.upload_file(local_file_path)
    else:
        # Otherwise, write the PDF bytes to a temporary file for FIS validation.
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(pdf_bytes)
                temp_file.flush()
                temp_file_path = temp_file.name
        except Exception as ex:
            logger.error("Error writing temporary file for FIS validation for {}: {}".format(file, ex))
            return None

        is_safe = fis_validator.upload_file(temp_file_path)

        try:
            os.unlink(temp_file_path)
        except Exception as ex:
            logger.error("Error deleting temporary file {} for {}: {}".format(temp_file_path, file, ex))

    if not is_safe:
        logger.error("File {} failed FIS malware scan. Skipping ingestion.".format(file))
        return None

    document_b64, updated_metadata = process_pdf_and_metadata(file, pdf_bytes, metadata)
    if document_b64 is None:
        return None

    payload_document = build_payload(native_id, updated_metadata, document_b64)
    try:
        doc_id = lex_api.ingest_document([payload_document])
        logger.info("Ingested document id for {}: {}".format(file, doc_id))
        processed_files[file] = {
            "doc_id": doc_id,
            "ingested_time": current_time
        }
        entry["doc_id"] = doc_id
        return doc_id
    except Exception as e:
        logger.error("Error ingesting document {}: {}".format(file, e))
        return None

def ingest_documents():
    """
    Orchestrates the entire ingestion process.
    Downloads PDFs (from SharePoint or local), processes them, and ingests them via Lex API.
    """
    global new_doc_ids
    processed_files = load_processed_state()
    new_doc_ids = []

    try:
        folder_path = sp_client.get_sharepoint_folder_path()
    except Exception as e:
        logger.error("Error getting SharePoint folder path: {}".format(e))
        folder_path = ""

    current_time = time.time()
    threshold_months = config.get("reingest_threshold_months", 4)
    threshold_seconds = threshold_months * 30 * 24 * 3600

    for entry in config["pdf_entries"]:
        file = entry["filename"]
        if file in processed_files:
            last_ingested = processed_files[file]["ingested_time"]
            if (current_time - last_ingested) < threshold_seconds:
                logger.info("Skipping already processed file (recent): {}".format(file))
                continue
            else:
                logger.info("Reingesting file (threshold exceeded): {}".format(file))
        else:
            logger.info("Processing new file: {}".format(file))

        doc_id = ingest_entry(entry, processed_files, folder_path, current_time)
        if doc_id:
            new_doc_ids.append(doc_id)

    save_processed_state(processed_files)
    return new_doc_ids, lex_api

def check_document_status(doc_ids, lex_api):
    for doc_id in doc_ids:
        try:
            status = lex_api.get_ingestion_status(doc_id)
            logger.info("Status for {}: {}".format(doc_id, status))
        except Exception as e:
            logger.error("Error fetching status for {}: {}".format(doc_id, e))

def search_documents(lex_api, query="recovery from cyber attacks"):
    try:
        results = lex_api.search_documents(query)
        logger.info("Search results: {}".format(results))
        for result in results:
            title = result["fields"]["title"]
            doc_id = result["id"]
            data_preview = (result["fields"]["data"][:150] + "...")
            if len(result["fields"]["data"]) <= 150:
                data_preview = result["fields"]["data"]
            logger.info("Title: {}, ID: {}, Text Summary: {}".format(title, doc_id, data_preview))
    except Exception as e:
        logger.error("Error performing search: {}".format(e))

def delete_document_example(lex_api, native_id="DRO_three_little_pigs"):
    try:
        response = lex_api.delete_document(native_id)
        logger.info("Delete response: {}".format(response))
    except Exception as e:
        logger.error("Error deleting document with native_id {}: {}".format(native_id, e))

def main():
    try:
        doc_ids, _ = ingest_documents()

        # Wait for a fixed delay before checking ingestion status to allow for any API latency.
        status_delay = config.get("lex_status_delay", 10)
        logger.info("Waiting {} seconds before checking document status...".format(status_delay))
        time.sleep(status_delay)

        check_document_status(doc_ids, lex_api)
    except Exception as e:
        logger.error("Error executing main ETL process: {}".format(e))

if __name__ == "__main__":
    main() 