import importlib
import logging
import shutil
import platform
import subprocess

logger = logging.getLogger(__name__)

# Define optional dependencies and their installation instructions
OPTIONAL_DEPENDENCIES = {
    'PyPDF2': {'package': 'PyPDF2', 'version': '>=3.0.0', 'purpose': 'PDF text extraction'},
    'pytesseract': {'package': 'pytesseract', 'version': '>=0.3.10', 'purpose': 'OCR for image text extraction', 'system': 'Tesseract'},
    'tabula': {'package': 'tabula-py', 'version': '>=2.7.0', 'purpose': 'PDF table extraction', 'system': 'Java'},
    'pdf2image': {'package': 'pdf2image', 'version': '>=1.16.3', 'purpose': 'Convert PDF pages to images', 'system': 'Poppler'},
    'spacy': {'package': 'spacy', 'version': '>=3.5.0', 'purpose': 'NLP for medical term detection'},
    'scispacy': {'package': 'scispacy', 'version': '>=0.5.0', 'purpose': 'Medical NLP extension', 'depends': 'spacy', 'model': 'en_core_sci_sm'},
    'selenium': {'package': 'selenium', 'version': '>=4.10.0', 'purpose': 'Advanced web scraping for dynamic content', 'system': 'WebDriver'},
    'webdriver_manager': {'package': 'webdriver-manager', 'version': '>=4.0.0', 'purpose': 'Automatic WebDriver management', 'depends': 'selenium'},
}

# System dependencies details
SYSTEM_DEPENDENCIES = {
    'Tesseract': {
        'check_command': ['tesseract', '--version'],
        'install_url': 'https://github.com/tesseract-ocr/tesseract',
        'notes': 'Ensure Tesseract executable is in your system PATH.'
    },
    'Java': {
        'check_command': ['java', '-version'],
        'install_url': 'https://adoptium.net/',
        'notes': 'Java Runtime Environment (JRE) 8 or higher recommended.'
    },
    'Poppler': {
        'check_command': ['pdftoppm', '-v'] if platform.system() != 'Windows' else None, # Windows check is harder via command line
        'check_func': 'check_poppler_windows' if platform.system() == 'Windows' else None,
        'install_url': 'https://poppler.freedesktop.org/' if platform.system() != 'Windows' else 'https://github.com/oschwartz10612/poppler-windows/releases/',
        'notes': 'Ensure Poppler binaries (like pdftoppm) are in your system PATH.'
    },
    'WebDriver': {
        'check_func': 'check_webdriver',
        'install_url': 'ChromeDriver: https://chromedriver.chromium.org/downloads or GeckoDriver: https://github.com/mozilla/geckodriver/releases',
        'notes': 'Requires Chrome/Firefox browser. webdriver-manager attempts automatic setup. Manual install may be needed if auto-setup fails.'
    }
}

def check_module(module_name, package_name=None, version_spec=None):
    """Check if a Python module is installed and meets version requirements."""
    package_name = package_name or module_name
    try:
        module = importlib.import_module(module_name)
        if version_spec and hasattr(module, '__version__'):
            from packaging import version
            # Simple version check (can be enhanced with specifiers like >=)
            # For now, just check if installed version is available
            logger.debug(f"Found {module_name} version {module.__version__}")
            # Add more complex version comparison if needed using 'packaging.version'
        return True
    except ImportError:
        return False
    except Exception as e:
        logger.warning(f"Could not check version for {module_name}: {e}")
        return True # Assume installed if import works but version check fails

def check_system_command(command):
    """Check if a system command exists and runs."""
    try:
        # Use shell=True on Windows for commands like 'java -version' which might output to stderr
        use_shell = platform.system() == 'Windows'
        process = subprocess.run(command, capture_output=True, text=True, check=False, shell=use_shell, timeout=5)
        # Check return code and if there's any output (some version commands use stderr)
        if process.returncode == 0 or (process.stderr or process.stdout):
             logger.debug(f"System command '{' '.join(command)}' executed successfully.")
             return True
        logger.warning(f"System command '{' '.join(command)}' failed with return code {process.returncode}.")
        return False
    except FileNotFoundError:
        logger.warning(f"System command not found: {command[0]}")
        return False
    except subprocess.TimeoutExpired:
        logger.warning(f"System command '{' '.join(command)}' timed out.")
        return False
    except Exception as e:
        logger.error(f"Error checking system command '{' '.join(command)}': {e}")
        return False

def check_poppler_windows():
    """Attempt to check for Poppler on Windows by checking common install paths or PATH."""
    # 1. Check PATH first using shutil.which
    if shutil.which('pdftoppm'):
        logger.debug("Found pdftoppm in PATH.")
        return True
    # 2. Add checks for common installation directories if needed (more complex)
    logger.warning("pdftoppm not found in PATH. Poppler might be missing or not configured correctly.")
    return False

def check_webdriver():
    """Check if webdriver-manager can find/install ChromeDriver."""
    if not check_module('webdriver_manager'):
        logger.warning("webdriver-manager not installed, cannot automatically check WebDriver.")
        return False # Cannot perform check without the manager

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        # Attempt to get the driver path - this triggers download/update if needed
        logger.info("Checking ChromeDriver status via webdriver-manager...")
        driver_path = ChromeDriverManager().install()
        if driver_path and isinstance(driver_path, str) and shutil.which(driver_path):
             logger.info(f"ChromeDriver seems available via webdriver-manager at: {driver_path}")
             return True
        else:
             logger.warning("webdriver-manager did not return a valid path for ChromeDriver.")
             return False
    except Exception as e:
        logger.error(f"Error checking/installing ChromeDriver via webdriver-manager: {e}")
        logger.error("Ensure Google Chrome is installed. Manual WebDriver setup might be required.")
        return False

def check_spacy_model(model_name):
    """Check if a spaCy model is installed."""
    try:
        import spacy
        spacy.load(model_name)
        logger.debug(f"spaCy model '{model_name}' is installed.")
        return True
    except OSError:
        logger.warning(f"spaCy model '{model_name}' not found.")
        return False
    except Exception as e:
        logger.error(f"Error checking spaCy model '{model_name}': {e}")
        return False

def check_dependencies():
    """Check for all optional Python and system dependencies."""
    logger.info("Checking optional dependencies...")
    missing_python = []
    missing_system = {} # Store missing system deps and their details

    # Check Python dependencies
    for name, details in OPTIONAL_DEPENDENCIES.items():
        # Check dependency first if specified
        depends_on = details.get('depends')
        if depends_on and not check_module(depends_on, OPTIONAL_DEPENDENCIES[depends_on]['package']):
            logger.warning(f"Skipping check for '{name}' because dependency '{depends_on}' is missing.")
            continue # Skip check if dependency is missing

        if not check_module(name, details['package'], details.get('version')):
            missing_python.append(details)
        elif details.get('model') and not check_spacy_model(details['model']):
             # Special case for spacy models
             details['install_command'] = f"python -m spacy download {details['model']}"
             missing_python.append(details)


    # Check System dependencies linked to Python packages
    for name, details in OPTIONAL_DEPENDENCIES.items():
        system_dep_name = details.get('system')
        if system_dep_name and system_dep_name in SYSTEM_DEPENDENCIES:
            sys_dep_details = SYSTEM_DEPENDENCIES[system_dep_name]
            check_passed = False
            if sys_dep_details.get('check_func'):
                # Use custom check function
                check_func = globals().get(sys_dep_details['check_func'])
                if check_func:
                    check_passed = check_func()
                else:
                    logger.error(f"Check function '{sys_dep_details['check_func']}' not found.")
            elif sys_dep_details.get('check_command'):
                # Use command line check
                check_passed = check_system_command(sys_dep_details['check_command'])

            if not check_passed:
                # Only report missing system dependency if the corresponding Python package *is* installed
                # or if it's a fundamental one like WebDriver needed by Selenium
                python_package_installed = check_module(name, details['package'])
                if python_package_installed or name == 'selenium': # Always check WebDriver if Selenium is listed
                    if system_dep_name not in missing_system:
                         missing_system[system_dep_name] = sys_dep_details
                         logger.warning(f"System dependency '{system_dep_name}' for '{name}' seems to be missing or not configured.")


    # Report missing dependencies
    if missing_python or missing_system:
        print("\n--- Optional Dependency Check ---") # Use print for visibility during startup
        if missing_python:
            print("Some optional Python packages are not installed:")
            for dep in missing_python:
                install_cmd = dep.get('install_command', f"pip install \"{dep['package']}{dep.get('version', '')}\"")
                print(f"  - {dep['package']}: {dep['purpose']}")
                print(f"    Install with: {install_cmd}")
                if dep.get('model'):
                    print(f"    Note: Also requires spaCy model '{dep['model']}'")

        if missing_system:
             print("\nSome system dependencies seem to be missing or not configured:")
             for name, details in missing_system.items():
                 print(f"  - {name}: Required for {', '.join([p for p, d in OPTIONAL_DEPENDENCIES.items() if d.get('system') == name])}")
                 print(f"    Install from: {details['install_url']}")
                 if details.get('notes'):
                     print(f"    Note: {details['notes']}")

        print("---------------------------------\n")
    else:
        logger.info("All optional dependencies seem to be installed and configured.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    check_dependencies()
