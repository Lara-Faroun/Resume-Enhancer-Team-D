from fastapi import FastAPI
import logging
from core.config import get_settings, Settings


app = FastAPI()

# =================Logger Configurations=================
logging.basicConfig(
    level=logging.INFO,  
    format='%(name)s - %(levelname)s - %(message)s',  # Message format
    datefmt='%Y-%m-%d %H:%M:%S',  
    handlers=[
        logging.StreamHandler(),  # Logs to the console
    ]
)

logger = logging.getLogger(__name__)

