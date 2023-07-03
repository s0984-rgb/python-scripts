import json
import os

from libs.logger import logger

# Get the list of files that have changed (new or missing)
def get_changed_files(directory, state_file):
    directory_files = []
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                # Get path relative to directory provided in --directory
                archive_file_name = os.path.relpath(os.path.join(root, file), directory)
                # Exclude state file from tracking
                if archive_file_name not in os.path.relpath(state_file, directory):
                    # Gather current state of filesystem
                    directory_files.append(archive_file_name)
        current_files = set(directory_files)
        archived_files = set([ x['relative_path'] for x in get_archived_files(state_file) ])
        new_files = current_files - archived_files
        missing_files = archived_files - current_files
        return list(new_files), list(missing_files)
    except Exception as error:
        raise error

# Read the contents of the archive state file
def get_archived_files(state_file):
    try:
        with open(state_file, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Remove a file
def remove_file(file_name):
    try:
        os.remove(file_name)
        logger.info('Removed file \'%s\'', file_name)
    except FileNotFoundError:
        logger.warning('File \'%s\' does not exist', file_name)
    except Exception as error:
        raise error

# Take missing files, and return map of archive: [list of files to extract from archive]
def reduce_map(data):
    data_map = {}
    for key in data:
        archive_name = key['archive_name']
        relative_path = key['relative_path']
        try:
            data_map[archive_name].append(relative_path)
        except KeyError:
            data_map[archive_name] = [relative_path]
        except Exception as error:
            raise error
    return data_map
