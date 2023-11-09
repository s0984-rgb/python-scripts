import glob
import json
import os
import time
import re

from libs.arguments import age_regex_str, size_regex_str

from libs.logger import logger
class Garden:
    time_units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800,
        'M': 2628000
    }

    size_units = {"B": 1, "KB": 2**10, "MB": 2**20, "GB": 2**30, "TB": 2**40}

    def __init__(self, config_file, system, age, size):
        self.config_file = config_file
        self.system = system
        self.age = age
        self.min_size = size

        self.time_divisor = self._dict_parser(regex=age_regex_str, dict_name='time_units', obj=self.age)
        self.size_divisor = self._dict_parser(regex=size_regex_str, dict_name='size_units', obj=self.min_size, upper=True)
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

    def _dict_parser(self, regex, dict_name, obj, upper=False):
        regex = '(' + regex + ')'
        if upper:
            obj = obj.upper()
        if not re.match(r' ', obj):
            obj = re.sub(regex, r' \1', obj)
        number, unit = [string.strip() for string in obj.split()]
        return int(float(number)*getattr(Garden, dict_name)[unit])

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
        present_time = time.time()
        files = glob.glob(self.config[object]["path"] + '//**//' + self.config[object]["file_pattern"], recursive=True)
        for count,file in enumerate(files):
            file_count = count++1
            if self._file_age(file) >= int(self.time_divisor):
                file_size = os.path.getsize(file)
                if file_size >= int(self.size_divisor):
                    try:
                        os.remove(file)
                        deleted_files.append(file)
                        logger.debug("(%s) File '%s' deleted", file_count, file)
                    except Exception as e:
                        logger.exception("(%s) Cannot delete file '%s'", file_count, file)
                        raise e
                else:
                    logger.debug('File \'%s\' not large enough for deletion', file)
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