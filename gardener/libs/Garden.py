import glob
import json
import os
import time

from libs.logger import logger

class Garden:
    divisors = {
                's': 1,
                'm': 60,
                'h': 3600,
                'd': 86400,
                'w': 604800,
                'M': 2628000
               }

    def __init__(self, config_file, system, age):
        self.config_file = config_file
        self.system = system
        self.age = age

        self.divisor = self._check_age()
        self.config = self._import_json()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *exc):
        return exc

    # Import config
    def _import_json(self):
        try:
            with open(self.config_file) as f:
                jsoncontent = json.load(f)
                logger.debug("Config file '%s' loaded", self.config_file)
                return jsoncontent
        except Exception as e:
            logger.exception("Cannot load default config")
            raise e
    
    # Check the --age parameters
    # Should receive in format <int> <str>
    def _check_age(self):
        a,b = self.age
        if not a.isdigit() or not b.isalpha():
            logger.error("Age parameter not correctly set. Received '%s %s', expected '<int> <str>'", a, b)
            raise SystemExit(-1)
        else:
            try:
                return Garden.divisors[b]
            except KeyError as e:
                logger.error("No key mapped to '%s' in divisors dict. Divisors dict: \"%s\"", b, Garden.divisors)
                raise e
    
    # Check the age of a file
    # Returns the duration of time since the file was modified in seconds
    def _file_age(self, filepath):
        present_time = time.time()
        file_mtime = os.path.getmtime(filepath)
        time_diff = present_time - file_mtime
        logger.debug("Time difference of file \'%s\' is \'%s\'", filepath, time_diff)
        return time_diff

    # Delete files
    def prune(self, object):
        deleted_files = []
        files = glob.glob(self.config[object]["path"] + '//**//' + self.config[object]["file_pattern"], recursive=True)
        for count,file in enumerate(files):
            file_count = count++1
            if self._file_age(file)/self.divisor > int(self.age[0]):
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
    
    def tend(self):
        if self.system.lower() == 'all':
            for item in self.config:
                self.prune(item)
        else:
            self.prune(self.system)