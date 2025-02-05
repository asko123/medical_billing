import pytest
from unittest.mock import patch, Mock
from etl.main import ingest_documents, check_document_status
from etl.config import config
import json
import os

@pytest.fixture
def mock_sharepoint_response():
    """Mock SharePoint API response"""
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.content = b"%PDF-1.4 test content"
    mock_resp.json.return_value = {
        'd': {
            'results': [
                {'ServerRelativeUrl': '/path/to/test.pdf'}
            ]
        }
    }
    return mock_resp

@pytest.fixture
def mock_fis_responses():
    """Mock FIS API responses"""
    submission_resp = Mock()
    submission_resp.status_code = 200
    submission_resp.json.return_value = {"id": "test-submission-id"}

    status_resp = Mock()
    status_resp.status_code = 200
    status_resp.json.return_value = {
        "submission": {
            "progress": "COMPLETE",
            "results": {"result": "APPROPRIATE"}
        }
    }
    
    return submission_resp, status_resp

@pytest.fixture
def mock_lex_responses():
    """Mock Lex API responses"""
    ingest_resp = Mock()
    ingest_resp.status_code = 200
    ingest_resp.json.return_value = {
        "successDocs": [{"documentId": "test-doc-id"}]
    }

    status_resp = Mock()
    status_resp.status_code = 200
    status_resp.json.return_value = {
        "status": "COMPLETED",
        "message": "Document processed successfully"
    }
    
    return ingest_resp, status_resp

def test_full_etl_pipeline(mock_config, mock_sharepoint_response, mock_fis_responses, mock_lex_responses):
    """
    Integration test for the full ETL pipeline:
    1. Download PDF from SharePoint
    2. Process PDF content
    3. Validate through FIS
    4. Ingest into Lex
    5. Check ingestion status
    """
    fis_submission_resp, fis_status_resp = mock_fis_responses
    lex_ingest_resp, lex_status_resp = mock_lex_responses

    # Create a temporary state file for testing
    test_state_file = "test_processed_files.json"
    if os.path.exists(test_state_file):
        os.remove(test_state_file)

    with patch('etl.main.STATE_FILE', test_state_file), \
         patch('etl.sharepoint.config', mock_config), \
         patch('etl.lex_api.config', mock_config), \
         patch('etl.FIS_Validator.config', mock_config), \
         patch('requests.get', return_value=mock_sharepoint_response), \
         patch('requests.Session') as mock_session, \
         patch('requests.post') as mock_post:
        
        # Mock FIS validation responses
        mock_session.return_value.post.return_value = fis_submission_resp
        mock_session.return_value.get.return_value = fis_status_resp
        
        # Mock Lex API responses
        mock_post.return_value = lex_ingest_resp
        
        # Run the ETL pipeline
        doc_ids, lex_api = ingest_documents()
        
        # Verify document IDs were returned
        assert len(doc_ids) > 0
        assert doc_ids[0] == "test-doc-id"
        
        # Check that state file was created
        assert os.path.exists(test_state_file)
        with open(test_state_file, 'r') as f:
            state = json.load(f)
            assert len(state) > 0
        
        # Verify status check
        with patch('requests.get', return_value=lex_status_resp):
            check_document_status(doc_ids, lex_api)

    # Cleanup
    if os.path.exists(test_state_file):
        os.remove(test_state_file)

def test_etl_pipeline_with_fis_rejection(mock_config, mock_sharepoint_response, mock_fis_responses, mock_lex_responses):
    """
    Integration test for ETL pipeline when FIS validation fails
    """
    fis_submission_resp, _ = mock_fis_responses
    
    # Create FIS rejection response
    fis_reject_resp = Mock()
    fis_reject_resp.status_code = 200
    fis_reject_resp.json.return_value = {
        "submission": {
            "progress": "COMPLETE",
            "results": {"result": "INAPPROPRIATE"}
        }
    }

    with patch('etl.sharepoint.config', mock_config), \
         patch('etl.lex_api.config', mock_config), \
         patch('etl.FIS_Validator.config', mock_config), \
         patch('requests.get', return_value=mock_sharepoint_response), \
         patch('requests.Session') as mock_session:
        
        # Mock FIS validation responses
        mock_session.return_value.post.return_value = fis_submission_resp
        mock_session.return_value.get.return_value = fis_reject_resp
        
        # Run the ETL pipeline
        doc_ids, _ = ingest_documents()
        
        # Verify no documents were ingested due to FIS rejection
        assert len(doc_ids) == 0

def test_etl_pipeline_retry_logic(mock_config, mock_sharepoint_response, mock_fis_responses, mock_lex_responses):
    """
    Integration test for ETL pipeline retry logic
    """
    fis_submission_resp, fis_status_resp = mock_fis_responses
    lex_ingest_resp, _ = mock_lex_responses

    # Create a response for initial failure
    fail_resp = Mock()
    fail_resp.status_code = 500
    fail_resp.json.side_effect = Exception("API Error")

    with patch('etl.sharepoint.config', mock_config), \
         patch('etl.lex_api.config', mock_config), \
         patch('etl.FIS_Validator.config', mock_config), \
         patch('requests.get', return_value=mock_sharepoint_response), \
         patch('requests.Session') as mock_session, \
         patch('requests.post') as mock_post:
        
        # Mock FIS validation to fail first, then succeed
        mock_session.return_value.post.side_effect = [fail_resp, fis_submission_resp]
        mock_session.return_value.get.return_value = fis_status_resp
        
        # Mock Lex API response
        mock_post.return_value = lex_ingest_resp
        
        # Run the ETL pipeline
        doc_ids, _ = ingest_documents()
        
        # Verify documents were eventually ingested after retry
        assert len(doc_ids) > 0
        assert doc_ids[0] == "test-doc-id" 