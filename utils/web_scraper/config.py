"""
Configuration module for web scraper - handles domain validation and config loading
"""
import os
import logging
import configparser
import validators

logger = logging.getLogger(__name__)

def load_trusted_domains_from_config():
    """Load trusted medical domains from config.ini file"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.ini')

    if os.path.exists(config_path):
        try:
            config.read(config_path)
            if 'web_scraper' in config and 'trusted_domains' in config['web_scraper']:
                # Split by comma and strip whitespace
                domains = [domain.strip() for domain in config['web_scraper']['trusted_domains'].split(',')]
                logger.info(f"Loaded {len(domains)} trusted domains from config.ini")
                return domains
            else:
                logger.warning("Missing web_scraper section or trusted_domains key in config.ini")
        except Exception as e:
            logger.error(f"Error loading config.ini: {str(e)}")
    else:
        logger.warning(f"Config file not found at {config_path}")

    # Return a minimal fallback list if config loading fails
    logger.warning("Using minimal fallback list of trusted domains")
    return [
        'https://www.nih.gov',
        'https://www.cdc.gov',
        'https://www.mayoclinic.org',
        'https://www.webmd.com',
        'https://www.who.int',
        'https://www.medlineplus.gov',
        'https://www.health.harvard.edu',
        'https://www.hopkinsmedicine.org',
        'https://www.clevelandclinic.org',
        'https://www.medicalnewstoday.com',
        'https://www.healthline.com',
    ]

# Load trusted domains
TRUSTED_DOMAINS = load_trusted_domains_from_config()

def is_trusted_domain(url):
    """Check if a URL belongs to a trusted medical domain"""
    if not url or not validators.url(url):
        return False

    # Convert URL to string if it's not already
    url_str = str(url)

    # Check if any trusted domain is in the URL
    return any(trusted_domain in url_str for trusted_domain in TRUSTED_DOMAINS)

def get_search_settings():
    """Get search settings from config"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.ini')

    # Default settings
    settings = {
        'max_results': 5,
        'timeout_seconds': 20,  # Increased default timeout to 20 seconds
        'enable_detailed_content': True
    }

    if os.path.exists(config_path):
        try:
            config.read(config_path)
            if 'search_settings' in config:
                section = config['search_settings']

                if 'max_results' in section:
                    settings['max_results'] = section.getint('max_results')

                if 'timeout_seconds' in section:
                    settings['timeout_seconds'] = section.getint('timeout_seconds')

                if 'enable_detailed_content' in section:
                    settings['enable_detailed_content'] = section.getboolean('enable_detailed_content')

            logger.info(f"Loaded search settings from config: {settings}")
        except Exception as e:
            logger.error(f"Error loading search settings: {str(e)}")

    return settings
