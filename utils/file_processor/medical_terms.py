"""
Module for detecting medical terminology in text.
"""
import torch
import re
import logging
import spacy
import numpy as np
from collections import Counter

logger = logging.getLogger(__name__)

# Global variables for NLP models
nlp = None

def load_nlp_models():
    """Load NLP models for medical text processing"""
    global nlp
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

# Load spaCy model on module import
load_nlp_models()

def detect_medical_terms(text, model=None, tokenizer=None, device=None):
    """Advanced detection of medical terms in text using LLM and NLP techniques"""
    if not text:
        return []
    
    # Set of medical terms detected
    medical_terms = set()
    
    # Method 1: Use the main LLM model if available (primary method)
    if model and tokenizer and device:
        try:
            # Format the prompt specifically for NER
            prompt = f"""Extract all medical terms from the following text. 
Return only the medical terms as a comma-separated list, with no additional explanation or text.
Examples of medical terms include conditions, symptoms, medications, anatomical structures, and procedures.

Text: {text[:1000]}  # Limit text length to avoid token limits

Medical terms:"""
            
            # Tokenize and prepare input
            inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=512)
            inputs = {key: val.to(device) for key, val in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                output = model.generate(
                    inputs["input_ids"],
                    max_length=512,
                    do_sample=False,  # Use greedy decoding for more reliable entity extraction
                    temperature=0.1,  # Lower temperature for more focused answers
                    num_return_sequences=1
                )
            
            # Decode the response
            response_text = tokenizer.decode(output[0], skip_special_tokens=True)
            
            # Extract just the medical terms part (after "Medical terms:")
            if "Medical terms:" in response_text:
                terms_text = response_text.split("Medical terms:", 1)[1].strip()
                
                # Process the comma-separated list
                for term in terms_text.split(','):
                    term = term.strip().lower()
                    if term and len(term) > 1:  # Avoid single characters
                        medical_terms.add(term)
                
                logger.info(f"LLM identified {len(medical_terms)} medical terms")
        except Exception as e:
            logger.error(f"Error using LLM for medical term detection: {str(e)}")
    
    # Method 2: Use spaCy for entity detection as backup
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
                # Filter by frequency in medical contexts
                if chunk.text.lower() in MEDICAL_TERMS_FREQUENCY:
                    medical_terms.add(chunk.text.lower())
                    
            logger.info(f"spaCy identified additional medical terms")
        except Exception as e:
            logger.error(f"Error in spaCy processing: {str(e)}")
    
    # Method 3: Use regex with comprehensive medical terminology (fallback)
    terms_before = len(medical_terms)
    for term_category, terms in MEDICAL_TERMINOLOGY.items():
        for term in terms:
            if re.search(r'\b' + re.escape(term) + r'\b', text.lower()):
                medical_terms.add(term)
    
    logger.info(f"Pattern matching added {len(medical_terms) - terms_before} additional terms")
    
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
