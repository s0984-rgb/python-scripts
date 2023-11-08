import logging
import os 

from libs.arguments import args

# Initialize logger
logger = logging.getLogger(__name__)
# Create formatter
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
# Create console handler and set formatting
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# Enable file logging
if args.enable_file_logging:
    # Create file handler and set formatting
    log_file = 'logs/gardener.logs'
    fh = logging.FileHandler(filename=log_file, encoding='utf_8', delay=False)
    fh.setFormatter(formatter)
    # Add fh handler
    logger.addHandler(fh)
    # Create logs folder if it does not exist
    try:
        os.makedirs("logs")
    except FileExistsError:
        pass

# Conditional log levels
if args.disable_logging: # If disable_logging is set
    logger.setLevel(logging.CRITICAL + 1)
elif args.debug: # If debug is set
    logger.setLevel(logging.DEBUG)
else: # Default logging
    logger.setLevel(logging.INFO)
