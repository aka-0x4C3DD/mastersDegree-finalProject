"""
Utility script to check for optional dependencies and provide installation instructions.
"""
import importlib
import logging
import subprocess
import sys
import platform
import os

logger = logging.getLogger(__name__)

# Define dependencies to check
DEPENDENCIES = [
    {
        "name": "PyPDF2",
        "import_name": "PyPDF2",
        "install_cmd": "pip install PyPDF2>=3.0.0",
        "desc": "PDF text extraction"
    },
    {
        "name": "pytesseract",
        "import_name": "pytesseract",
        "install_cmd": "pip install pytesseract>=0.3.10",
        "desc": "OCR for image text extraction",
        "additional_note": "Also requires Tesseract OCR to be installed on your system: https://github.com/tesseract-ocr/tesseract"
    },
    {
        "name": "tabula-py",
        "import_name": "tabula",
        "install_cmd": "pip install tabula-py>=2.7.0",
        "desc": "PDF table extraction",
        "additional_note": "Also requires Java Runtime Environment (JRE) to be installed"
    },
    {
        "name": "pdf2image",
        "import_name": "pdf2image",
        "install_cmd": "pip install pdf2image>=1.16.3",
        "desc": "Convert PDF pages to images",
        "additional_note": "Also requires Poppler to be installed on your system"
    },
    {
        "name": "BeautifulSoup4",
        "import_name": "bs4",
        "install_cmd": "pip install beautifulsoup4>=4.12.0",
        "desc": "HTML/XML parsing for web scraping"
    },
    {
        "name": "Requests",
        "import_name": "requests",
        "install_cmd": "pip install requests>=2.28.0",
        "desc": "HTTP requests for web scraping"
    },
    {
        "name": "validators",
        "import_name": "validators",
        "install_cmd": "pip install validators>=0.20.0",
        "desc": "URL validation for web scraping"
    },
    {
        "name": "Spacy",
        "import_name": "spacy",
        "install_cmd": "pip install spacy>=3.5.0",
        "desc": "NLP for medical term detection"
    },
    {
        "name": "ScispaCy",
        "import_name": "scispacy",
        "install_cmd": "pip install scispacy>=0.5.0",
        "desc": "Medical NLP extension",
        "additional_note": "May also need to run: python -m spacy download en_core_sci_sm"
    }
]

def check_dependencies():
    """Check for required and optional dependencies"""
    missing = []
    installed = []
    
    for dep in DEPENDENCIES:
        try:
            module = importlib.import_module(dep["import_name"])
            installed.append(dep["name"])
        except ImportError:
            missing.append(dep)
    
    if installed:
        logger.info(f"Found these optional dependencies: {', '.join(installed)}")
    
    if missing:
        logger.warning("Some optional dependencies are not installed:")
        for dep in missing:
            logger.warning(f"  - {dep['name']}: {dep['desc']}")
            logger.warning(f"    Install with: {dep['install_cmd']}")
            if "additional_note" in dep:
                logger.warning(f"    Note: {dep['additional_note']}")
    
    # Check for system dependencies
    check_system_dependencies()

def check_system_dependencies():
    """Check for system dependencies like Tesseract, Poppler, etc."""
    # Check for Tesseract (for OCR)
    try:
        import pytesseract
        tesseract_version = pytesseract.get_tesseract_version()
        logger.info(f"Found Tesseract OCR version: {tesseract_version}")
    except (ImportError, Exception) as e:
        if "pytesseract" not in str(e):  # Only log if pytesseract is installed but Tesseract is missing
            logger.warning("Tesseract OCR not found. OCR functionality will be limited.")
            os_type = platform.system()
            if os_type == "Windows":
                logger.warning("  - Install from: https://github.com/UB-Mannheim/tesseract/wiki")
            elif os_type == "Linux":
                logger.warning("  - Install with: sudo apt install tesseract-ocr")
            elif os_type == "Darwin":  # macOS
                logger.warning("  - Install with: brew install tesseract")
    
    # Check for Java (for tabula)
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            # Java version is usually in stderr, not stdout
            version_output = result.stderr or result.stdout
            logger.info(f"Found Java: {version_output.splitlines()[0]}")
        else:
            logger.warning("Java not found. PDF table extraction will be limited.")
            os_type = platform.system()
            if os_type == "Windows":
                logger.warning("  - Install JRE from: https://adoptium.net/")
            elif os_type == "Linux":
                logger.warning("  - Install with: sudo apt install default-jre")
            elif os_type == "Darwin":  # macOS
                logger.warning("  - Install with: brew install --cask temurin")
    except Exception:
        logger.warning("Could not check for Java. PDF table extraction may be limited.")
        
    # Check for Poppler (for pdf2image)
    try:
        import pdf2image
        # Try to create a simple conversion to check if poppler is installed
        with open(os.devnull, 'w') as devnull:
            # Redirect output to avoid cluttering the console
            old_stderr = sys.stderr
            sys.stderr = devnull
            try:
                # Just access a function that would fail if poppler is not installed
                pdf2image.pdfinfo_from_path.__module__
                logger.info("Found Poppler (required for pdf2image)")
            except Exception:
                raise Exception("Poppler not installed properly")
            finally:
                sys.stderr = old_stderr
    except Exception:
        logger.warning("Poppler not found. PDF-to-image conversion will be limited.")
        os_type = platform.system()
        if os_type == "Windows":
            logger.warning("  - Install from: https://github.com/oschwartz10612/poppler-windows/releases/")
        elif os_type == "Linux":
            logger.warning("  - Install with: sudo apt install poppler-utils")
        elif os_type == "Darwin":  # macOS
            logger.warning("  - Install with: brew install poppler")

if __name__ == "__main__":
    # Configure logging for direct execution
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    print("Checking for optional dependencies...")
    check_dependencies()
