import spacy
import logging
from spacy.matcher import Matcher

logger = logging.getLogger(__name__)

# Load the spaCy model (consider using a more general model if needed)
# Using scispaCy model for potential medical context, but logic aims broader
try:
    # nlp = spacy.load("en_core_web_sm") # Option for a general model
    nlp = spacy.load("en_core_sci_sm") 
    logger.info("Loaded spaCy model 'en_core_sci_sm' for term detection.")
except OSError:
    logger.error("spaCy model 'en_core_sci_sm' not found. Please run 'python -m spacy download en_core_sci_sm'")
    nlp = None
except ImportError:
     logger.error("spaCy or scispaCy not installed. Please install them.")
     nlp = None

def detect_medical_terms(text):
    """Detects medical terms using scispaCy NER."""
    if not nlp:
        logger.warning("spaCy model not loaded. Cannot detect medical terms.")
        return []
    if not text:
        return []
        
    doc = nlp(text)
    terms = []
    for ent in doc.ents:
        terms.append({
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char
        })
    logger.debug(f"Detected {len(terms)} medical entities.")
    return terms

def extract_search_keywords(text, max_keywords=10):
    """
    Extracts relevant keywords (nouns, proper nouns, entities) from text 
    for use in web searches.
    """
    if not nlp:
        logger.warning("spaCy model not loaded. Cannot extract keywords.")
        return ""
    if not text:
        return ""

    doc = nlp(text)
    keywords = set()

    # 1. Add Named Entities (prioritize these)
    for ent in doc.ents:
        # Clean up entity text slightly (optional)
        keywords.add(ent.text.strip())

    # 2. Add important Nouns and Proper Nouns not already covered by entities
    allowed_pos = {"NOUN", "PROPN"}
    for token in doc:
        if not token.is_stop and not token.is_punct and token.pos_ in allowed_pos:
            # Check if the token is part of an already added entity
            part_of_entity = any(ent.start <= token.i < ent.end for ent in doc.ents)
            if not part_of_entity:
                keywords.add(token.lemma_.lower()) # Use lemma for nouns

    # 3. Consider Noun Chunks (phrases like "type 2 diabetes")
    for chunk in doc.noun_chunks:
         # Check if the chunk significantly overlaps with an existing entity
         chunk_in_entity = any(ent.start_char <= chunk.start_char and ent.end_char >= chunk.end_char for ent in doc.ents)
         if not chunk_in_entity:
              keywords.add(chunk.text.strip())


    # Limit the number of keywords and join them
    keyword_list = sorted(list(keywords), key=len, reverse=True) # Prioritize longer phrases
    final_keywords = keyword_list[:max_keywords]
    
    keyword_string = " ".join(final_keywords)
    logger.info(f"Extracted keywords for search: '{keyword_string}' from text: '{text[:50]}...'")
    return keyword_string

# Make the new function available
__all__ = ['detect_medical_terms', 'extract_search_keywords']
