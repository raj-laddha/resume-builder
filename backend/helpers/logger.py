import logging
import os

# Determine environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

# Configure root logger only once
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

def get_logger(name: str):
    return logging.getLogger(name) 