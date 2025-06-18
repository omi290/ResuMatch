import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# RapidAPI Configuration
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
RAPIDAPI_HOST = "extracta.p.rapidapi.com"
RAPIDAPI_URL = "https://extracta.p.rapidapi.com/extract"

# API Headers
RAPIDAPI_HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST
}

# Log configuration status
if not RAPIDAPI_KEY:
    logger.warning("RAPIDAPI_KEY not found in environment variables")
else:
    logger.info("RAPIDAPI configuration loaded successfully")
    logger.info(f"Host: {RAPIDAPI_HOST}")
    logger.info(f"URL: {RAPIDAPI_URL}") 