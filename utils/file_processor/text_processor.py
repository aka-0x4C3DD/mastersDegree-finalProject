"""
Module for processing and analyzing text files and text chunks.
"""
import torch
import logging

# Internal imports
from .utils import split_text_into_chunks, summarize_text_results
from .medical_terms import detect_medical_terms

logger = logging.getLogger(__name__)

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
    
    # Detect medical terms using the main model
    medical_terms = detect_medical_terms(content, model, tokenizer, device)
    
    # Combine results
    combined_result = {
        "file_type": "text",
        "chunks_processed": len(chunks),
        "medical_terms_detected": medical_terms[:20] if len(medical_terms) > 20 else medical_terms,
        "medical_term_count": len(medical_terms),
        "response": summarize_text_results(results, content)
    }
    
    return combined_result

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
