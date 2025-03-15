import os
import tempfile
import torch
import logging
import json
import csv
import re
import io
from PIL import Image
import cv2
import pytesseract
import numpy as np
from transformers import pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_file(file, model, tokenizer, device):
    """Process different types of medical files
    
    Args:
        file: File object from Flask's request.files
        model: The loaded ClinicalGPT model
        tokenizer: The loaded tokenizer
        device: The device (CPU/GPU) to run inference on
    
    Returns:
        Dictionary with processed results
    """
    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()
    
    try:
        # Process file based on extension
        if file_ext == '.txt':
            return process_text_file(file, model, tokenizer, device)
        elif file_ext == '.csv':
            return process_csv_file(file, model, tokenizer, device)
        elif file_ext == '.json':
            return process_json_file(file, model, tokenizer, device)
        elif file_ext in ['.jpg', '.jpeg', '.png']:
            return process_image_file(file, model, tokenizer, device)
        elif file_ext == '.pdf':
            return process_pdf_file(file, model, tokenizer, device)
        else:
            return {"error": f"Unsupported file type: {file_ext}"}
    
    except Exception as e:
        logger.error(f"Error processing file {filename}: {str(e)}")
        return {"error": f"Error processing file: {str(e)}"}

def process_text_file(file, model, tokenizer, device):
    """Process a text file with medical content"""
    content = file.read().decode('utf-8')
    
    # Basic preprocessing
    content = content.strip()
    
    # Extract meaningful text chunks for analysis
    chunks = split_text_into_chunks(content)
    
    # Process each chunk with the model
    results = []
    for chunk in chunks:
        chunk_result = process_text_chunk(chunk, model, tokenizer, device)
        results.append(chunk_result)
    
    # Combine results
    combined_result = {
        "file_type": "text",
        "chunks_processed": len(chunks),
        "response": summarize_text_results(results, content)
    }
    
    return combined_result

def process_csv_file(file, model, tokenizer, device):
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
    
    # Process the extracted text
    result = process_text_chunk(text_to_analyze, model, tokenizer, device)
    
    return {
        "file_type": "csv",
        "rows": len(rows),
        "columns": len(headers),
        "headers": headers,
        "response": result.get("response", "No analysis available.")
    }

def process_json_file(file, model, tokenizer, device):
    """Process a JSON file with medical data"""
    content = file.read().decode('utf-8')
    
    try:
        json_data = json.loads(content)
        
        # Convert JSON to a readable format for analysis
        if isinstance(json_data, dict):
            text_to_analyze = json.dumps(json_data, indent=2)
        elif isinstance(json_data, list) and len(json_data) > 0:
            # If it's a list, take a sample for analysis
            sample = json_data[:5] if len(json_data) > 5 else json_data
            text_to_analyze = json.dumps(sample, indent=2)
        else:
            text_to_analyze = content
        
        # Process the extracted text
        result = process_text_chunk(text_to_analyze, model, tokenizer, device)
        
        return {
            "file_type": "json",
            "structure": "array" if isinstance(json_data, list) else "object",
            "size": len(json_data) if isinstance(json_data, list) else len(json_data.keys()),
            "response": result.get("response", "No analysis available.")
        }
    
    except json.JSONDecodeError:
        return {
            "file_type": "json",
            "error": "Invalid JSON format",
            "response": "The uploaded file is not valid JSON. Please check the format."
        }

def process_image_file(file, model, tokenizer, device):
    """Process an image file with medical content using OCR"""
    try:
        # Read and preprocess image
        img = Image.open(file)
        open_cv_image = np.array(img)
        gray_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
        _, binary_image = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY)
        
        # Perform OCR
        extracted_text = pytesseract.image_to_string(binary_image)
        
        if not extracted_text.strip():
            return {
                "file_type": "image",
                "response": "No text detected in this image. The image may contain only graphics or the text is not machine-readable."
            }
        
        # Analyze extracted text
        chunk_result = process_text_chunk(extracted_text, model, tokenizer, device)
        
        return {
            "file_type": "image",
            "response": chunk_result.get("response", "No analysis available"),
            "extracted_text": extracted_text
        }
    
    except Exception as e:
        logger.error(f"Image processing error: {str(e)}")
        return {
            "file_type": "image",
            "error": f"Error processing image: {str(e)}"
        }

def process_pdf_file(file, model, tokenizer, device):
    """Process a PDF file with medical content using PyPDF2"""
    try:
        import PyPDF2
    except ImportError:
        return {
            "file_type": "pdf",
            "error": "PyPDF2 not installed. Install with 'pip install PyPDF2' to enable PDF processing."
        }
    
    pdf_reader = PyPDF2.PdfReader(file)
    text_chunks = []
    
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text = page.extract_text()
        if text.strip():  # Skip empty pages
            text_chunks.append(text)
    
    full_text = "\n\n".join(text_chunks)
    
    if not full_text.strip():
        return {
            "file_type": "pdf",
            "response": "No text could be extracted from this PDF. It may contain only images or be formatted in a way that prevents text extraction."
        }
    
    # Process the extracted text using existing functions
    chunks = split_text_into_chunks(full_text)
    results = []
    for chunk in chunks:
        chunk_result = process_text_chunk(chunk, model, tokenizer, device)
        results.append(chunk_result)
    
    summary = summarize_text_results(results, full_text)
    
    return {
        "file_type": "pdf",
        "pages": len(pdf_reader.pages),
        "extractable_text": len(full_text) > 0,
        "response": summary
    }

def process_text_chunk(text, model, tokenizer, device):
    """Process a chunk of text using the ClinicalGPT model"""
    if not text:
        return {"response": "No text to analyze"}
    
    try:
        # Format the prompt for CausalLM model
        prompt = f"User: Please analyze the following medical text and provide insights:\n\n{text}\n\nAssistant:"
        
        # Tokenize and prepare input
        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {key: val.to(device) for key, val in inputs.items()}
        
        # Generate response with the causal language model
        with torch.no_grad():
            output = model.generate(
                inputs["input_ids"],
                max_length=1024,
                do_sample=True,
                top_p=0.9,
                temperature=0.6,
                num_return_sequences=1
            )
        
        # Decode the generated response
        generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract just the response part (after "Assistant:")
        response_text = generated_text.split("Assistant:", 1)[-1].strip()
        
        return {
            "response": response_text
        }
    
    except Exception as e:
        logger.error(f"Error processing text chunk: {str(e)}")
        return {"error": f"Error processing text: {str(e)}"}

def generate_response_from_embeddings(text, embeddings):
    """Generate a response based on the embeddings and input text"""
    # This is now a legacy function as we're using direct generation
    # Kept for compatibility with existing code
    medical_terms = detect_medical_terms(text)
    
    if medical_terms:
        response = f"I detected the following medical terms in your document: {', '.join(medical_terms[:5])}"
        if len(medical_terms) > 5:
            response += f" and {len(medical_terms) - 5} more."
        response += "\n\nIn a full implementation, I would provide detailed analysis of these medical concepts."
    else:
        response = "I didn't detect specific medical terms in the document. In a full implementation, I would analyze the content and provide medical insights."
    
    return response

def detect_medical_terms(text):
    """Simple detection of medical terms in text"""
    # This is a basic implementation - in a real app, you would use a more sophisticated approach
    common_medical_terms = [
        'diabetes', 'hypertension', 'cancer', 'cardiovascular', 'asthma', 
        'arthritis', 'alzheimer', 'parkinson', 'obesity', 'depression',
        'anxiety', 'schizophrenia', 'bipolar', 'adhd', 'autism',
        'influenza', 'pneumonia', 'covid', 'vaccination', 'immunization',
        'medication', 'prescription', 'diagnosis', 'prognosis', 'symptom',
        'treatment', 'therapy', 'surgery', 'chronic', 'acute'
    ]
    
    # Simple regex to find whole words
    found_terms = []
    for term in common_medical_terms:
        if re.search(r'\b' + re.escape(term) + r'\b', text.lower()):
            found_terms.append(term)
    
    return found_terms

def split_text_into_chunks(text, max_chunk_size=500):
    """Split text into manageable chunks for processing"""
    # Simple implementation - split by newlines and then by chunk size
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) < max_chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # If no paragraphs were found, split by size
    if not chunks:
        for i in range(0, len(text), max_chunk_size):
            chunks.append(text[i:i+max_chunk_size])
    
    return chunks

def summarize_text_results(results, original_text):
    """Summarize results from multiple text chunks"""
    # For ClinicalGPT, we can directly use the generated responses
    # as they should already be well-structured
    
    # If we have only one chunk, return that response
    if len(results) == 1 and "response" in results[0]:
        return results[0]["response"]
        
    # If we have multiple chunks, combine them
    responses = [r.get("response", "") for r in results if "response" in r]
    
    if not responses:
        return "Could not generate analysis for this document."
    
    # Combine the responses with proper formatting
    summary = "Analysis of document (summarized from multiple sections):\n\n"
    
    # Add each response as a section
    for i, response in enumerate(responses):
        summary += f"--- Section {i+1} Analysis ---\n"
        summary += response + "\n\n"
    
    return summary
