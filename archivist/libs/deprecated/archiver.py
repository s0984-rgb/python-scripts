import tarfile
import json
import os

from libs.logger import logger
from libs.helper import get_archived_files

# Reset tarinfo
def reset(tarinfo):
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = "root"
    return tarinfo

# Add a list of files to the archive and update state file
def add_to_archive(file_data, archive, state_file, directory):
    try:
        with tarfile.open(archive, "w:gz") as tar:
            logger.debug('tarfile \'%s\' opened', archive)
            archived_data = []
            for target in file_data:
                path = os.path.join(directory, target)
                tar.add(path, target, filter=reset)
                logger.info('Added file \'%s\' to the archive \'%s\'', path, archive)
                archived_data.append({
                                        "relative_path": target,
                                        "archive_name": os.path.relpath(archive, directory)
                                    })
        logger.debug('tarfile \'%s\' closed', archive)
        update_archived_files(archived_data, state_file)
    except Exception as error:
        raise error

# Appends a newly archived file to the archive state file
def update_archived_files(data, state_file):
    try:
        file_data = get_archived_files(state_file)
        with open(state_file, "r+") as file:
            for obj in data:
                file_data.append(obj)
            json.dump(file_data, file, indent=4)
    except FileNotFoundError:
        with open(state_file, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as error:
        raise error
    finally:
        logger.debug('State file \'%s\' updated', state_file)
