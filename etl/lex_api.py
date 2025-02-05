"""
Module: lex_api.py
Description: Contains the LexAPI class to interact with the Lex ingestion system.
Provides methods for ingesting documents, checking ingestion status, performing searches, and deleting documents.
Authentication uses gs_auth, and endpoints come from configuration.
"""
import requests
import json
import gs_auth
from etl import config
from etl.utils import Utils

logger = Utils.get_logger("lex_api")

class LexAPI:
    def __init__(self):
        # Any initialization can be done here.
        pass

    def _get_headers(self):
        """
        Generate request headers for Lex API calls using gs_auth.
        """
        try:
            token = gs_auth.get_gssso()
            headers = {
                'Cookie': f'GSSSO={token}',
                'x-api-key': f'GSSSO={token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            return headers
        except Exception as e:
            logger.error("Error generating headers for Lex API: {}".format(e))
            raise

    def ingest_document(self, payload):
        """
        Ingest a document into Lex ingest API.
        The payload should be a list containing one document dict.
        Returns the documentId from the API response.
        """
        try:
            headers = self._get_headers()
            timeout_value = config.get("lex_timeout", 30)
            response = requests.post(
                config["lex_ingest_url"],
                headers=headers,
                data=json.dumps(payload),
                verify=False,
                timeout=timeout_value
            )
            if response.status_code != 200:
                logger.error("Ingestion failed: {}".format(response.text))
                raise Exception(f"Ingestion failed: {response.text}")
            doc_id = response.json()["successDocs"][0]["documentId"]
            logger.info("Successfully ingested document. Doc ID: {}".format(doc_id))
            return doc_id
        except Exception as e:
            logger.error("Error in ingest_document: {}".format(e))
            raise

    def get_ingestion_status(self, doc_id):
        """
        Get the ingestion status for a given document ID.
        """
        try:
            headers = self._get_headers()
            status_base_url = config["lex_status_url"]
            url = f"{status_base_url}{doc_id}"
            timeout_value = config.get("lex_timeout", 30)
            response = requests.get(url, headers=headers, verify=False, timeout=timeout_value)
            response.raise_for_status()
            logger.info("Fetched ingestion status for doc_id {}.".format(doc_id))
            return response.json()
        except Exception as e:
            logger.error("Error in get_ingestion_status for doc_id {}: {}".format(doc_id, e))
            raise

    def search_documents(self, query, source="TEST", size=2, page=1, schemaIds=["tech_risk_ai"]):
        """
        Search for documents using the Lex search API.
        Returns a list of search results.
        """
        try:
            headers = self._get_headers()
            payload = {
                'query': query,
                'source': source,
                'size': size,
                'page': page,
                'schemaIds': schemaIds,
                'queryFilters': {},
                'rankingProfile': 'hybrid'
            }
            timeout_value = config.get("lex_timeout", 30)
            response = requests.post(
                config["lex_search_url"],
                headers=headers,
                data=json.dumps(payload),
                verify=False,
                timeout=timeout_value
            )
            response.raise_for_status()
            logger.info("Search query executed successfully.")
            return response.json()['data']['searchResults']
        except Exception as e:
            logger.error("Error in search_documents: {}".format(e))
            raise

    def delete_document(self, native_id):
        """
        Delete a document from Lex using its native ID.
        """
        try:
            headers = self._get_headers()
            url = f"{config['lex_delete_url']}/{native_id}"
            timeout_value = config.get("lex_timeout", 30)
            response = requests.delete(url, headers=headers, verify=False, timeout=timeout_value)
            response.raise_for_status()
            logger.info("Deleted document with native_id: {}".format(native_id))
            return response.text
        except Exception as e:
            logger.error("Error deleting document native_id {}: {}".format(native_id, e))
            raise 