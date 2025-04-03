import logging

logger = logging.getLogger(__name__)

# Modified function to use LLM
def detect_medical_terms(text: str, model_manager) -> list[str]:
    """Detects medical terms using the primary LLM."""
    if not model_manager or not text:
        logger.warning("Model manager not available or text is empty. Cannot detect medical terms.")
        return []

    prompt = f"""Analyze the following text and extract all significant medical terms, including diseases, symptoms, medications, procedures, and anatomical references. List only the unique terms, separated by commas. Do not include explanations or introductory phrases.

Text:
"{text}"

Medical Terms:"""

    try:
        # Use the model_manager to generate the response
        response = model_manager.generate_response(prompt) # Use the generate_response method

        if not response:
            logger.warning("Received empty response from LLM for medical term extraction.")
            return []

        # Parse the comma-separated response from the LLM
        terms_string = response.strip()
        terms = [term.strip().lower() for term in terms_string.split(',') if term.strip()]
        unique_terms = sorted(list(set(terms))) # Ensure uniqueness and sort
        logger.debug(f"Detected {len(unique_terms)} medical terms via LLM.")
        # Return a list of strings, as the original structured output is hard to replicate
        return unique_terms

    except Exception as e:
        logger.error(f"Error during medical term detection with LLM: {e}", exc_info=True)
        return []


# Modified function to use LLM
def extract_search_keywords(text: str, model_manager, max_keywords=10) -> str:
    """
    Extracts relevant keywords from text using the primary LLM
    for use in web searches. Returns a space-separated string.
    """
    if not model_manager or not text:
        logger.warning("Model manager not available or text is empty. Cannot extract keywords.")
        return ""

    prompt = f"""Analyze the following text and extract the most important keywords or key phrases suitable for a web search about the main medical topics discussed. List the top {max_keywords} keywords/phrases, separated by spaces. Focus on nouns, proper nouns, medical conditions, treatments, and symptoms.

Text:
"{text}"

Keywords:"""

    try:
        # Use the model_manager to generate the response
        response = model_manager.generate_response(prompt) # Use the generate_response method

        if not response:
            logger.warning("Received empty response from LLM for keyword extraction.")
            return ""

        # The response should already be space-separated keywords
        keyword_string = response.strip()
        # Optional: Limit the number of words just in case
        keyword_list = keyword_string.split()
        final_keywords = keyword_list[:max_keywords]
        keyword_string = " ".join(final_keywords)

        logger.info(f"Extracted keywords via LLM for search: '{keyword_string}' from text: '{text[:50]}...'")
        return keyword_string

    except Exception as e:
        logger.error(f"Error during keyword extraction with LLM: {e}", exc_info=True)
        return ""


# Update __all__ to reflect the modified functions (if names changed, update here)
__all__ = ['detect_medical_terms', 'extract_search_keywords']
