import pytest
from unittest.mock import patch, Mock
from etl.FIS_Validator import FISValidator

def test_upload_file_success(mock_config, mock_response):
    with patch('etl.FIS_Validator.config', mock_config):
        with patch('requests.Session') as mock_session:
            # Mock the initial submission response
            mock_response.json.return_value = {"id": "test-submission-id"}
            mock_session.return_value.post.return_value = mock_response
            
            # Mock the validation status response
            status_response = Mock()
            status_response.status_code = 200
            status_response.json.return_value = {
                "submission": {
                    "progress": "COMPLETE",
                    "results": {"result": "APPROPRIATE"}
                }
            }
            mock_session.return_value.get.return_value = status_response
            
            validator = FISValidator()
            result = validator.upload_file("test.pdf")
            
            assert result is True
            mock_session.return_value.post.assert_called_once()

def test_upload_file_inappropriate(mock_config, mock_response):
    with patch('etl.FIS_Validator.config', mock_config):
        with patch('requests.Session') as mock_session:
            # Mock the initial submission response
            mock_response.json.return_value = {"id": "test-submission-id"}
            mock_session.return_value.post.return_value = mock_response
            
            # Mock the validation status response
            status_response = Mock()
            status_response.status_code = 200
            status_response.json.return_value = {
                "submission": {
                    "progress": "COMPLETE",
                    "results": {"result": "INAPPROPRIATE"}
                }
            }
            mock_session.return_value.get.return_value = status_response
            
            validator = FISValidator()
            result = validator.upload_file("test.pdf")
            
            assert result is False

def test_upload_file_timeout(mock_config, mock_response):
    with patch('etl.FIS_Validator.config', mock_config):
        with patch('requests.Session') as mock_session:
            # Mock the initial submission response
            mock_response.json.return_value = {"id": "test-submission-id"}
            mock_session.return_value.post.return_value = mock_response
            
            # Mock the validation status response that never completes
            status_response = Mock()
            status_response.status_code = 200
            status_response.json.return_value = {
                "submission": {
                    "progress": "IN_PROGRESS"
                }
            }
            mock_session.return_value.get.return_value = status_response
            
            validator = FISValidator()
            result = validator.upload_file("test.pdf")
            
            assert result is False 