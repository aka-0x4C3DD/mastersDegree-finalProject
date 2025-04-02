"""
Utility functions for file processing.
"""
import logging

logger = logging.getLogger(__name__)

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
