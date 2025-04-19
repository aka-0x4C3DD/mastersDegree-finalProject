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
# Reduce the default max_keywords significantly
def extract_search_keywords(text: str, model_manager, max_keywords=7) -> str:
    """
    Extracts relevant keywords from text using the primary LLM
    for use in web searches. Returns a space-separated string.
    """
    if not model_manager or not text:
        logger.warning("Model manager not available or text is empty. Cannot extract keywords.")
        return ""

    # Extract important words from the original query to ensure they're preserved
    important_words = [word for word in text.split() if len(word) > 3 and word.lower() not in
                      ['and', 'the', 'for', 'with', 'from', 'about', 'that', 'this', 'these', 'those']]

    # Improved prompt with more specific instructions and emphasis on staying relevant to the query
    prompt = f"""Extract EXACTLY {max_keywords} specific search keywords from the following query.

Your task is to identify the most important search terms that would help find relevant medical information about the EXACT topic in the query.

1. Focus on diseases, locations, dates, statistics, medical conditions, and specific entities mentioned.
2. Include proper nouns, medical terms, and specific identifiers.
3. DO NOT introduce topics that aren't explicitly mentioned in the original query.
4. DO NOT generalize to broader medical topics unless the query is vague.
5. Return ONLY the keywords separated by spaces, with no additional text.

Query: "{text}"

Keywords:"""

    try:
        # Use the model_manager to generate the response
        response = model_manager.generate_response(prompt) # Use the generate_response method

        if not response:
            logger.warning("Received empty response from LLM for keyword extraction.")
            # Fallback to using the original text if keyword extraction fails
            logger.info(f"Falling back to using original text for search: '{text[:50]}...'")
            return text # Return original text as fallback

        # The response should ideally be space-separated keywords
        keyword_string = response.strip()
        # Basic cleanup: remove potential instruction remnants if they appear
        if "keywords:" in keyword_string.lower():
             keyword_string = keyword_string.split("Keywords:")[-1].strip()

        # Process the keywords
        keyword_list = keyword_string.split()
        # Filter out very short words that are unlikely to be useful keywords
        filtered_keywords = [kw for kw in keyword_list if len(kw) > 2][:max_keywords]

        # Validation: Check if the extracted keywords seem relevant to the original query
        # Extract lowercase versions of original query words and keywords for comparison
        query_words = set(word.lower() for word in text.split() if len(word) > 3)
        keyword_words = set(word.lower() for word in filtered_keywords)

        # If there's no overlap between the query and keywords, it might be irrelevant
        if query_words and not query_words.intersection(keyword_words) and len(filtered_keywords) > 0:
            logger.warning("Extracted keywords don't appear related to the original query. Adding important query terms.")
            # Add important words from the original query to ensure relevance
            combined_keywords = filtered_keywords[:max(1, max_keywords-3)] + important_words[:min(3, len(important_words))]
            keyword_string = " ".join(combined_keywords)
        else:
            keyword_string = " ".join(filtered_keywords)

        # If after processing, the keyword string is empty, fallback to original text
        if not keyword_string:
             logger.warning("Keyword extraction resulted in empty string, falling back to original text.")
             return text

        logger.info(f"Extracted keywords via LLM for search: '{keyword_string}' from text: '{text[:50]}...'")
        return keyword_string

    except Exception as e:
        logger.error(f"Error during keyword extraction with LLM: {e}", exc_info=True)
        # Fallback to original text on error
        logger.info(f"Falling back to using original text due to error: '{text[:50]}...'")
        return text


# Update __all__ to reflect the modified functions (if names changed, update here)
__all__ = ['detect_medical_terms', 'extract_search_keywords']
