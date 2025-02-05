import pytest
from unittest.mock import patch, Mock
from etl.pdf_processor import PDFProcessor
import pdfplumber

def test_extract_data_from_pdf(sample_pdf_bytes):
    with patch('pdfplumber.open') as mock_open:
        # Mock the PDF pages
        mock_page = Mock()
        mock_page.extract_text.return_value = "Sample text"
        mock_page.extract_tables.return_value = [
            [["Header"], ["Row 1"]],
            [["Header"], ["Row 2"]]
        ]
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page, mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        mock_open.return_value = mock_pdf
        
        processor = PDFProcessor()
        result = processor.extract_data_from_pdf(sample_pdf_bytes)
        
        assert "Sample text" in result["text"]
        assert len(result["tables"]) > 0
        mock_open.assert_called_once()

def test_extract_data_from_pdf_handles_empty_page():
    with patch('pdfplumber.open') as mock_open:
        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        mock_page.extract_tables.return_value = []
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        mock_open.return_value = mock_pdf
        
        processor = PDFProcessor()
        result = processor.extract_data_from_pdf(b"empty pdf")
        
        assert result["text"].strip() == ""
        assert result["tables"] == [] 