"""
Module for processing and analyzing PDF files.
"""
import os
import tempfile
import logging
import PyPDF2
from PIL import Image
import io
import re

# Try to import tabula for table extraction (optional)
try:
    import tabula
    HAS_TABULA = True
except ImportError:
    HAS_TABULA = False

# Try to import pdf2image for better image-based extraction when needed
try:
    import pdf2image
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

# Internal imports
from .text_processor import process_text_chunk

logger = logging.getLogger(__name__)

def process_pdf_file(file, model, tokenizer, device):
    """Process a PDF file with medical content"""
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
            file.save(temp_path)
        
        # Extract text from the PDF
        extracted_text = extract_text_from_pdf(temp_path)
        
        # Extract tables if possible
        tables = []
        if HAS_TABULA:
            try:
                tables = extract_tables_from_pdf(temp_path)
            except Exception as e:
                logger.warning(f"Table extraction failed: {str(e)}")
        
        # Build a summary of the PDF content
        summary = f"PDF Analysis Summary:\n\n"
        
        # If we have tables, add a note about them
        if tables:
            summary += f"- Found {len(tables)} tables in the document.\n"
            # Convert first table to string representation for context
            if len(tables) > 0:
                summary += f"\nSample table content:\n{tables[0].to_string(index=False)}\n\n"
        
        # Add some of the extracted text
        max_preview_length = 3000  # Limit preview to avoid token limits
        if len(extracted_text) > max_preview_length:
            text_preview = extracted_text[:max_preview_length] + "...\n(text truncated due to length)"
        else:
            text_preview = extracted_text
        
        summary += f"\nExtracted text from PDF:\n\n{text_preview}"
        
        # Process the extracted text with the model
        result = process_text_chunk(summary, model, tokenizer, device)
        
        # Return the results
        return {
            "file_type": "pdf",
            "pdf_pages": count_pages(temp_path),
            "has_tables": len(tables) > 0,
            "table_count": len(tables),
            "text_length": len(extracted_text),
            "response": result.get("response", "No analysis available.")
        }
    finally:
        # Clean up the temporary file
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass

def extract_text_from_pdf(pdf_path):
    """Extract text content from a PDF file"""
    extracted_text = ""
    
    try:
        with open(pdf_path, 'rb') as pdf_file:
            # Using PyPDF2 for text extraction
            reader = PyPDF2.PdfReader(pdf_file)
            
            # Track if we need to use image-based extraction as fallback
            needs_ocr = True
            
            # Try text extraction first
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                
                if page_text and page_text.strip():
                    needs_ocr = False  # We got some text, so PDF is not entirely images
                    extracted_text += f"\n--- Page {page_num + 1} ---\n"
                    extracted_text += page_text + "\n"
            
            # If no text was extracted and we have pdf2image+pytesseract, try OCR
            if not extracted_text.strip() and needs_ocr and HAS_PDF2IMAGE:
                logger.info("PDF appears to contain only images. Attempting OCR...")
                extracted_text = extract_text_with_ocr(pdf_path)
                
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        extracted_text += f"\nError extracting text: {str(e)}"
        
    return extracted_text.strip()

def extract_text_with_ocr(pdf_path):
    """Extract text from PDF using OCR (for image-based PDFs)"""
    try:
        # Import pytesseract only when needed
        import pytesseract
        
        # Convert PDF pages to images
        images = pdf2image.convert_from_path(pdf_path)
        
        extracted_text = ""
        for i, image in enumerate(images):
            # Perform OCR on each image
            page_text = pytesseract.image_to_string(image, lang='eng')
            extracted_text += f"\n--- Page {i + 1} (OCR) ---\n"
            extracted_text += page_text + "\n"
            
        return extracted_text
    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}")
        return f"OCR extraction failed: {str(e)}"

def extract_tables_from_pdf(pdf_path):
    """Extract tables from PDF using tabula"""
    try:
        # Use tabula to extract tables
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        return tables
    except Exception as e:
        logger.error(f"Table extraction failed: {str(e)}")
        return []

def count_pages(pdf_path):
    """Count the number of pages in a PDF file"""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            return len(reader.pages)
    except Exception as e:
        logger.error(f"Error counting PDF pages: {str(e)}")
        return 0
