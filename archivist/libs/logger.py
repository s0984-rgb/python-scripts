import logging

from libs.arguments import args

# Set default logging config
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Set custom logging config
if args.disable_logging:
    logger.setLevel(logging.CRITICAL + 1)
elif args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# from logger import logger
