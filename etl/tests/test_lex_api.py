import pytest
from unittest.mock import patch, Mock
from etl.lex_api import LexAPI

def test_ingest_document(mock_config, mock_response):
    with patch('etl.lex_api.config', mock_config):
        with patch('requests.post') as mock_post:
            mock_response.json.return_value = {
                "successDocs": [{"documentId": "test-doc-id"}]
            }
            mock_post.return_value = mock_response
            
            api = LexAPI()
            result = api.ingest_document([{"test": "payload"}])
            
            assert result == "test-doc-id"
            mock_post.assert_called_once()

def test_get_ingestion_status(mock_config, mock_response):
    with patch('etl.lex_api.config', mock_config):
        with patch('requests.get') as mock_get:
            mock_response.json.return_value = {"status": "complete"}
            mock_get.return_value = mock_response
            
            api = LexAPI()
            result = api.get_ingestion_status("test-doc-id")
            
            assert result == {"status": "complete"}
            mock_get.assert_called_once()

def test_search_documents(mock_config, mock_response):
    with patch('etl.lex_api.config', mock_config):
        with patch('requests.post') as mock_post:
            mock_response.json.return_value = {
                "data": {"searchResults": [{"id": "doc1"}]}
            }
            mock_post.return_value = mock_response
            
            api = LexAPI()
            result = api.search_documents("test query")
            
            assert result == [{"id": "doc1"}]
            mock_post.assert_called_once() 