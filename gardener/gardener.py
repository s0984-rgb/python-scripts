import argparse
import glob
import json
import logging
import os
import time

parser = argparse.ArgumentParser(prog='python gardener.py', description="Deletes all files matching the 'file_patter' in the 'path' provided as keys in the JSON array. Logs all files deleted in ./logs/gardener.logs")
parser.add_argument('--system', '-s', help="System generating the recurring files. Translates to root keys in the JSON array.", default="All", type=str)
parser.add_argument('--config', '-c', help="Configuration file for the script in JSON array format. Needs a root key defined in argument --system. With keys 'path' and 'file_pattern'. e.g.: \n '{\"a\": {\"path\": \"/path/to/folder/a\", \"file_pattern\": \"*.log\"}, \"b\": {\"path\": \"/path/to/folder/b\", \"file_pattern\": \"*.txt\"}}'", default="settings.json", type=str)
parser.add_argument('--age', '-a', help="Change default mtime parameter (e.g. '1' 'm' for 1 minute). Defaults = 1 d", default="1" "d", type=str, nargs=2)
parser.add_argument('--debug', '-d', help="Change default logging to debug", action='store_true')
parser.add_argument('--disable_logging', help="Prevent script from logging at all", action='store_true')
args = parser.parse_args()

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
log_file = 'logs/gardener.logs'
fh = logging.FileHandler(filename=log_file, encoding='utf_8', delay=False)
fh.setFormatter(formatter)
# Create console handler and set formatting
ch = logging.StreamHandler()
ch.setFormatter(formatter)
# Add fh handler
logger.addHandler(fh)

# Conditional log levels
if args.debug: # If debug is set
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)
elif args.disable_logging: # If disable_logging is set
    logger.setLevel(logging.CRITICAL + 1)
else: # Default logging
    logger.setLevel(logging.INFO)

# Import config
def import_json(json_file):
    try:
        with open(json_file) as f:
            jsoncontent = json.load(f)
            logger.debug("Config file '%s' loaded", json_file)
            return jsoncontent
    except Exception as e:
        logger.exception("Cannot load default config")
        raise e

# Check the --age parameters
# Should receive in format <int> <str>
def check_age(a,b):
    if not a.isdigit() or not b.isalpha():
        logger.error("Age parameter not correctly set. Received '%s %s', expected '<int> <str>'", a, b)
        raise SystemExit(-1)
    else:
        try:
            divisor = divisors[b]
            logger.debug("Unit is '%s', Divisor is '%s'", b, divisor)
            return divisor
        except KeyError as e:
            logger.error("No key mapped to '%s' in divisors dict. Divisors dict: \"%s\"", b, divisors)
            raise e

# Check the age of a file
# Returns the duration of time since the file was modified in seconds
def file_age(filepath):
    present_time = time.time()
    file_mtime = os.path.getmtime(filepath)
    time_diff = present_time - file_mtime
    logger.debug("Time difference of file \'%s\' is \'%s\'", filepath, time_diff)
    return time_diff

# Delete files
def delete_file(settings,object,divisor,time):
    deleted_files = []
    files = glob.glob(settings[object]["path"] + '//**//' + settings[object]["file_pattern"], recursive=True)
    for count,file in enumerate(files):
        file_count = count++1
        if file_age(file)/divisor > int(time):
            try:
                os.remove(file)
                deleted_files.append(file)
                logger.debug("(%s) File '%s' deleted", file_count, file)
            except PermissionError:
                logger.warning("(%s) Cannot delete file '%s' - permission denied", file_count, file)
                pass
            except Exception as e:
                logger.exception("(%s) Cannot delete file '%s'", file_count, file)
                raise e
    deleted_count = len(deleted_files)
    if deleted_count > 0:
        logger.info("Deleted '%s' files for system '%s'", deleted_count, object)
    else:
        logger.debug("No files deleted for system '%s'", object)

def main():
    config_file = args.config
    logger.debug('Config file used is \'%s\'', config_file)
    system = args.system
    logger.debug('System to delete files for is \'%s\'', system)
    age,div = args.age
    logger.debug('Files older than \'%s\' \'%s\' will be deleted', age, div)

    # Load config
    config = import_json(config_file)

    # Main execution
    dividor=check_age(age,div)
    if system == "All":
        for item in config:
            delete_file(config,item,dividor,age)
    else:
        delete_file(config,system,dividor,age)

if __name__ == "__main__":
    main()
