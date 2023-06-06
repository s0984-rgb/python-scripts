import argparse
from email.policy import default
from encodings import utf_8
import glob
import json
import logging
import os
import time

parser = argparse.ArgumentParser(prog='python delete_files.py', description="Permanently delete recurring files. Logs how many files were deleted from which system in ./logs/deleted_files.log.")
parser.add_argument('--system', '-s', help="system generating the recurring files", type=str)
parser.add_argument('--config', '-c', help="configuration file for the script in JSON format", type=str)
parser.add_argument('--age', '-a', help='change default mtime parameter (e.g. "1" "m" for 1 minute). Defaults = 1 d', default="1" "d", type=str, nargs=2)
parser.add_argument('--debug', '-d', help="change default logging to debug", action='store_true')
parser.add_argument('--disable_logging', help="prevent script from logging at all", action='store_true')
args = parser.parse_args()

_config_file = args.config
_system = args.system
_age,_div = args.age
_debug = args.debug
_disable_logging = args.disable_logging

divisors = {
    's': 1,
    'm': 60,
    'h': 3600,
    'd': 86400,
    'w': 604800,
    'M': 2628000
    }

# Create logs folder if it does not exist
try:
    os.makedirs("logs") 
except FileExistsError:
    pass

# Initialize logger
logger = logging.getLogger(__name__)
# Create formatter
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
# Create file handler and set formatting
fh = logging.FileHandler(filename='logs/deleted_files.log', encoding='utf_8', delay=False)
fh.setFormatter(formatter)
# Create console handler and set formatting
ch = logging.StreamHandler()
ch.setFormatter(formatter)
# Add fh handler
logger.addHandler(fh)

# Conditional log levels
if _debug: # If debug is set
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)
elif _disable_logging: # If disable_logging is set
    logger.setLevel(logging.CRITICAL + 1)
else: # Default logging
    logger.setLevel(logging.INFO)

# Import config
def import_json(json_file):
    with open(json_file) as f:
        jsoncontent = json.load(f)
        logger.debug("Config file '%s' loaded", json_file)
        return jsoncontent

# Check the --age parameters
# Should receive in format <int> <str>
def check_age(a,b):
    if a.isalpha() or b.isdigit():
        logger.error("Age parameter not correctly set. Received '%s %s', expected '<int> <str>'", a, b)
        raise SystemExit(-1)
    try:
        divisor = divisors[b]
        logger.debug("Unit is '%s', Divisor is '%s'", b, divisor)
        return divisor
    except KeyError:
        logger.error("No key mapped to '%s' in divisors dict. Divisors dict: \"%s\"", b, divisors)
        raise SystemExit(-1)

# Check the age of a file
# Returns the duration of time since the file was modified in seconds
def file_age(filepath):
    present_time = time.time()
    file_mtime = os.path.getmtime(filepath)
    return present_time - file_mtime

# Delete files
def delete_file(settings,object,divisor,time):
    deleted_files = []
    files = glob.glob(settings[object]["path"] + '\\**\\' + settings[object]["file_pattern"], recursive=True)
    for count,file in enumerate(files):
        file_count = count++1
        if file_age(file)/divisor > int(time):
            try:
                os.remove(file)
                deleted_files.append(file)
                logger.debug("(%s) File '%s' deleted", file_count, file)
            except PermissionError:
                logger.debug("(%s) Cannot delete file '%s' - permission denied", file_count, file)
                pass
            except Exception:
                logger.exception("(%s) Cannot delete file '%s'", file_count, file)
                raise SystemExit(-1)
    deleted_count = len(deleted_files)
    if deleted_count > 0:
        logger.info("Deleted '%s' files for system '%s'", deleted_count, object)
    else:
        logger.debug("No files deleted for system '%s'", object)


# Load config
if _config_file is None:
    _config_file = 'settings.json'
    try:
        config = import_json(_config_file)
    except Exception:
        logger.exception("Cannot load default config. Make sure '%s' exists or provide a config file using '--config'. See 'settings.json.example' for example configuration file.", _config_file)
        raise SystemExit(-1)
else:
    try:
        config = import_json(_config_file)
    except Exception:
        logger.exception("Cannot load config file '%s'", _config_file)
        raise SystemExit(-1)

# Main execution
div=check_age(_age,_div)
if _system is None:
    for item in config:
        try:
            delete_file(config,item,div,_age)
        except Exception:
            logger.exception("Cannot delete systems files defined in config file '%s'", _config_file)
            raise SystemExit(-1)
else:
    try:
        delete_file(config,_system,div,_age)
    except Exception:
        logger.exception("Cannot delete files for system '%s'", _system)
        raise SystemExit(-1)

def main():
    

if __name__ == "__main__":
    main()
