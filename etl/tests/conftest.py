import pytest
from unittest.mock import Mock
import json
import os

@pytest.fixture
def sample_pdf_bytes():
    """Returns sample PDF bytes for testing"""
    return b"%PDF-1.4 sample pdf content"

@pytest.fixture
def mock_config():
    """Returns a mock configuration"""
    return {
        "environments": {
            "dev": {
                "lex_ingest_url": "https://dev.example.com/ingest",
                "lex_search_url": "https://dev.example.com/search",
                "lex_delete_url": "https://dev.example.com/delete",
                "lex_status_url": "https://dev.example.com/status"
            }
        },
        "FIS": {
            "submission_url": "https://fis.example.com/submissions",
            "FIS_api_key": "test-key"
        },
        "user_name": "test_user",
        "password": "test_pass",
        "sharepoint_base_url": "https://sharepoint.example.com",
        "sharepoint_pdf_url": "https://sharepoint.example.com/files",
        "verify_cert": "/path/to/cert.pem"
    }

@pytest.fixture
def mock_response():
    """Returns a mock requests.Response object"""
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = Mock()
    return mock_resp 

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup any state specific to the execution of all tests."""
    # Setup code here if needed
    yield
    # Cleanup code here if needed 