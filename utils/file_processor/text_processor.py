"""
Module for processing and analyzing text files and text chunks.
"""
import logging

# Internal imports
from .utils import split_text_into_chunks, summarize_text_results
from .medical_terms import detect_medical_terms # Keep this import

logger = logging.getLogger(__name__)

# Modify function signature to accept model_manager
def process_text_file(file, model_manager):
    """Process a text file with medical content"""
    content = file.read().decode('utf-8')

    # Basic preprocessing
    content = content.strip()

    # Extract meaningful text chunks for analysis
    chunks = split_text_into_chunks(content)

    # Process each chunk with the model
    results = []
    for chunk in chunks:
        # Pass model_manager to process_text_chunk
        chunk_result = process_text_chunk(chunk, model_manager)
        results.append(chunk_result)

    # Detect medical terms using the LLM via model_manager
    # Pass model_manager to detect_medical_terms
    medical_terms = detect_medical_terms(content, model_manager)

    # Combine results
    combined_result = {
        "file_type": "text",
        "chunks_processed": len(chunks),
        # The result is now a list of strings
        "medical_terms_detected": medical_terms[:20] if len(medical_terms) > 20 else medical_terms,
        "medical_term_count": len(medical_terms),
        "response": summarize_text_results(results, content)
    }

    return combined_result

# Modify function signature to accept model_manager
def process_text_chunk(text, model_manager):
    """Process a chunk of text using the ClinicalGPT model via model_manager"""
    if not text:
        return {"response": "No text to analyze"}

    try:
        # Format the prompt for CausalLM model
        prompt = f"User: Please analyze the following medical text and provide insights:\n\n{text}\n\nAssistant:"

        # Use model_manager to generate response
        response_text = model_manager.generate_response(prompt)

        return {
            "response": response_text
        }

    except Exception as e:
        logger.error(f"Error processing text chunk: {str(e)}")
        return {"error": f"Error processing text: {str(e)}"}
