import os
import tempfile
import torch
import logging
import json
import csv
import re
import io
from PIL import Image
from transformers import pipeline
import spacy
import numpy as np
from collections import Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for NLP models
nlp = None
medical_ner = None

def load_nlp_models():
    """Load NLP models for medical text processing"""
    global nlp, medical_ner
    try:
        # Try to load ScispaCy model for biomedical text
        import scispacy
        nlp = spacy.load("en_core_sci_sm")
        logger.info("Loaded ScispaCy model for medical NER")
    except (ImportError, OSError) as e:
        # Fall back to standard spaCy model if ScispaCy is not available
        logger.warning(f"ScispaCy model not available: {e}. Using standard spaCy model.")
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("Standard spaCy model not found, downloading it...")
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")
        
    # Load a medical NER model from Hugging Face (if available)
    try:
        medical_ner = pipeline("ner", model="d4data/biomedical-ner-all", aggregation_strategy="simple")
        logger.info("Loaded Hugging Face biomedical NER model")
    except Exception as e:
        logger.warning(f"Could not load Hugging Face medical NER model: {e}")
        medical_ner = None

# Load models on module import
load_nlp_models()

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
    """Process an image file with medical content (uses OCR if needed)"""
    # This is a placeholder - in a real app, you might use OCR or image analysis
    return {
        "file_type": "image",
        "response": "Image analysis is not implemented in this version. In a full implementation, this would use OCR to extract text from the image, or medical image analysis to identify conditions."
    }

def process_pdf_file(file, model, tokenizer, device):
    """Process a PDF file with medical content"""
    # This is a placeholder - in a real app, you would use a PDF parser
    return {
        "file_type": "pdf",
        "response": "PDF analysis is not implemented in this version. In a full implementation, this would extract text from the PDF and analyze it using the ClinicalGPT model."
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

def detect_medical_terms(text):
    """Advanced detection of medical terms in text using NLP techniques"""
    if not text:
        return []
    
    # Set of medical terms detected
    medical_terms = set()
    
    # Method 1: Use spaCy for entity detection
    if nlp:
        try:
            doc = nlp(text)
            
            # Extract entities that are likely medical terms
            for ent in doc.ents:
                if ent.label_ in ["DISEASE", "CHEMICAL", "PROCEDURE", "ANATOMY", "MEDICALCONDITION", 
                                  "SYMPTOM", "TREATMENT", "DRUG", "MEDICATION", "B-DISO", "I-DISO", 
                                  "B-PROC", "I-PROC", "B-ANAT", "I-ANAT", "UMLS"]:
                    medical_terms.add(ent.text.lower())
            
            # Look for medical terms in noun chunks (for when entity recognition misses some terms)
            for chunk in doc.noun_chunks:
                # Filter by frequency in medical contexts (weight by term length)
                if chunk.text.lower() in MEDICAL_TERMS_FREQUENCY:
                    medical_terms.add(chunk.text.lower())
        except Exception as e:
            logger.error(f"Error in spaCy processing: {str(e)}")
    
    # Method 2: Use Hugging Face transformer model for medical NER
    if medical_ner:
        try:
            # Process text in chunks to avoid context length limitations
            chunk_size = 512
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            
            for chunk in chunks:
                results = medical_ner(chunk)
                for result in results:
                    if result.get('entity_group') in ['DISEASE', 'CHEMICAL', 'TREATMENT', 'DRUG', 'SYMPTOM']:
                        medical_terms.add(result.get('word').lower())
        except Exception as e:
            logger.error(f"Error in Hugging Face NER processing: {str(e)}")
    
    # Method 3: Use regex with comprehensive medical terminology
    for term_category, terms in MEDICAL_TERMINOLOGY.items():
        for term in terms:
            if re.search(r'\b' + re.escape(term) + r'\b', text.lower()):
                medical_terms.add(term)
    
    # Convert set back to list and sort alphabetically
    return sorted(list(medical_terms))

# More comprehensive medical terminology database
MEDICAL_TERMINOLOGY = {
    "conditions": [
        'diabetes', 'hypertension', 'cancer', 'asthma', 'arthritis', 'alzheimer', 
        'parkinson', 'obesity', 'depression', 'anxiety', 'schizophrenia', 'bipolar', 
        'adhd', 'autism', 'influenza', 'pneumonia', 'covid', 'insomnia', 'fibromyalgia',
        'osteoporosis', 'copd', 'anemia', 'leukemia', 'lymphoma', 'melanoma', 'eczema', 
        'psoriasis', 'lupus', 'epilepsy', 'sclerosis', 'hepatitis', 'cirrhosis', 'gastritis'
    ],
    "symptoms": [
        'pain', 'ache', 'nausea', 'dizziness', 'fatigue', 'fever', 'cough', 'rash',
        'swelling', 'inflammation', 'bleeding', 'bruising', 'numbness', 'tingling',
        'stiffness', 'weakness', 'shortness of breath', 'chest pain', 'congestion',
        'insomnia', 'headache', 'migraine', 'runny nose', 'sore throat', 'wheezing'
    ],
    "anatomy": [
        'heart', 'lung', 'liver', 'kidney', 'brain', 'spine', 'joint', 'artery', 'vein',
        'muscle', 'bone', 'tendon', 'ligament', 'cartilage', 'thyroid', 'pancreas',
        'intestine', 'colon', 'stomach', 'esophagus', 'skin', 'nerve', 'blood', 'tissue'
    ],
    "procedures": [
        'surgery', 'transplant', 'biopsy', 'scan', 'mri', 'ct scan', 'x-ray', 'ultrasound', 
        'therapy', 'vaccination', 'immunization', 'screening', 'dialysis', 'transfusion',
        'chemotherapy', 'radiation', 'bypass', 'stent', 'implant', 'laparoscopy', 'endoscopy'
    ],
    "medications": [
        'antibiotic', 'antiviral', 'analgesic', 'nsaid', 'steroid', 'insulin', 'statin',
        'diuretic', 'antihistamine', 'antidepressant', 'antipsychotic', 'sedative',
        'vaccine', 'opioid', 'bronchodilator', 'anticoagulant', 'antihypertensive'
    ]
}

# Frequency table of common medical terms (simplified)
MEDICAL_TERMS_FREQUENCY = {
    'diabetes': 0.95, 'hypertension': 0.93, 'cancer': 0.9, 'asthma': 0.85,
    'heart disease': 0.92, 'stroke': 0.88, 'alzheimer': 0.82, 'arthritis': 0.8,
    'depression': 0.78, 'anxiety': 0.75, 'infection': 0.85, 'inflammation': 0.7,
    'vaccine': 0.85, 'antibiotic': 0.75, 'surgery': 0.8, 'therapy': 0.7,
    'diagnosis': 0.9, 'prognosis': 0.85, 'treatment': 0.9, 'symptom': 0.88
}

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