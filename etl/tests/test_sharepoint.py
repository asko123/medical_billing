import pytest
from unittest.mock import patch, Mock
from etl.sharepoint import SharePointClient

def test_sharepoint_client_init(mock_config):
    with patch('etl.sharepoint.config', mock_config):
        client = SharePointClient()
        assert client.username == "test_user"
        assert client.password == "test_pass"
        assert client.base_url == "https://sharepoint.example.com"

def test_get_sharepoint_folder_path(mock_config, mock_response):
    with patch('etl.sharepoint.config', mock_config):
        with patch('requests.get') as mock_get:
            mock_response.json.return_value = {
                'd': {
                    'results': [
                        {'ServerRelativeUrl': '/path/to/file1.pdf'},
                        {'ServerRelativeUrl': '/path/to/file2.pdf'}
                    ]
                }
            }
            mock_get.return_value = mock_response
            
            client = SharePointClient()
            result = client.get_sharepoint_folder_path()
            
            assert result == '/path/to'
            mock_get.assert_called_once()

def test_download_pdf(mock_config, mock_response, sample_pdf_bytes):
    with patch('etl.sharepoint.config', mock_config):
        with patch('requests.get') as mock_get:
            mock_response.content = sample_pdf_bytes
            mock_get.return_value = mock_response
            
            client = SharePointClient()
            result = client.download_pdf("test.pdf", "/path/to")
            
            assert result == sample_pdf_bytes
            mock_get.assert_called_once() 