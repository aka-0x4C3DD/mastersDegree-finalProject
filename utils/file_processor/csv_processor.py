"""
Module for processing and analyzing CSV files.
"""
import csv
import io
import logging

# Internal imports
from .text_processor import process_text_chunk

logger = logging.getLogger(__name__)

def process_csv_file(file, model_manager):
    """Process a CSV file with medical data"""
    content = file.read().decode('utf-8')
    
    # Parse CSV
    reader = csv.reader(io.StringIO(content))
    headers = next(reader, [])
    rows = list(reader)
    
    # Extract key columns for analysis
    summary = f"Analyzed CSV file with {len(rows)} rows and {len(headers)} columns.\n"
    summary += f"Headers: {', '.join(headers)}\n\n"
    
    # If the CSV is small enough, provide a sample analysis
    if len(rows) <= 10:
        text_to_analyze = summary + "\n".join([", ".join(row) for row in rows[:5]])
    else:
        # Select a subset of rows for analysis
        text_to_analyze = summary + "\n".join([", ".join(row) for row in rows[:5]])
        text_to_analyze += "\n...\n" + "\n".join([", ".join(row) for row in rows[-3:]])
    
    # Process the extracted text, passing model_manager
    result = process_text_chunk(text_to_analyze, model_manager)
    
    return {
        "file_type": "csv",
        "rows": len(rows),
        "columns": len(headers),
        "headers": headers,
        "response": result.get("response", "No analysis available.")
    }
