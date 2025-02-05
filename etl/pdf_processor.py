"""
Module: pdf_processor.py
Description: Contains the PDFProcessor class that extracts text and tables from PDF files using pdfplumber.
It includes logic for aggregating tables spanning multiple pages.
"""
import pdfplumber
from io import BytesIO
from etl.utils import Utils

logger = Utils.get_logger("pdf_processor")

class PDFProcessor:
    @staticmethod
    def extract_data_from_pdf(pdf_bytes):
        """
        Extract text and tables from a PDF file given as bytes, using pdfplumber.
        
        This method returns a dictionary with:
         - "text": A string containing the full extracted text.
         - "tables": A list of aggregated tables.
        
        If a page encounters extraction issues due to unusual formatting, a warning is logged and processing continues.
        """
        full_text = ""
        aggregated_tables = []  # List to hold aggregated tables
        
        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                for idx, page in enumerate(pdf.pages, start=1):
                    # Attempt to extract text from the page
                    try:
                        page_text = page.extract_text() or ""
                    except Exception as e:
                        logger.warning("Error extracting text from page {}: {}".format(idx, e))
                        page_text = ""
                    full_text += page_text + "\n"
                    
                    # Attempt to extract tables from the page
                    try:
                        page_tables = page.extract_tables()
                    except Exception as e:
                        logger.warning("Error extracting tables from page {}: {}".format(idx, e))
                        continue
                    
                    for table in page_tables:
                        if not table or len(table) == 0:
                            continue

                        # Assume the first row is the header.
                        current_header = table[0]
                        
                        # If there is at least one aggregated table and the header matches,
                        # consider this table as a continuation.
                        if aggregated_tables:
                            last_table = aggregated_tables[-1]
                            if len(last_table) > 0 and len(current_header) == len(last_table[0]) and current_header == last_table[0]:
                                if len(table) > 1:
                                    last_table.extend(table[1:])
                                continue
                        aggregated_tables.append(table)
            logger.info("Extracted data from PDF successfully.")
            return {"text": full_text, "tables": aggregated_tables}
        except Exception as e:
            logger.error("Error extracting data from PDF: {}".format(e))
            raise 