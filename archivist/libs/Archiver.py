import tarfile
import os
import json

from datetime import datetime

from libs.ArchiveTemplate import ArchiveTemplate
from libs.logger import logger

# ArchiveTemplate subclass for archiving & compressing archive objects
class Archiver(ArchiveTemplate):

    suffix = '.tgz'

    def __init__(self, name, max = 30, *args, **kwargs):
        ArchiveTemplate.__init__(self, *args, **kwargs)
        self.name = name
        self.max = int(max)
        self.max_bytes = self.max #* (1024 ** 3)
        self.archive_list = []
        self.timestamp = datetime.utcnow().isoformat(timespec='seconds').replace(':','')
        self.archived_data = []

    @property
    def new_files(self):
        return self.get_changed_files('new')

    # Reset tarinfo
    def reset(self, tarinfo):
        tarinfo.uid = tarinfo.gid = 0
        tarinfo.uname = tarinfo.gname = "root"
        return tarinfo
    
    # Add a list of files to the archive and update state file
    def add_to_archive(self, data, archive):
        try:
            with tarfile.open(archive, "w:gz") as tar:
                logger.debug('tarfile \'%s\' opened', archive)
                for target in data:
                    path = os.path.join(self.directory, target)
                    tar.add(path, target, filter=self.reset)
                    logger.info('Added file \'%s\' to the archive \'%s\'', path, archive)
                    self.archived_data.append({
                                            "relative_path": target,
                                            "archive_name": os.path.relpath(archive, self.directory)
                                            })
        except Exception as error:
            raise error

    # Appends a newly archived file to the archive state file
    def update_archived_files(self):
        try:
            data = self.state_data
            with open(self.state_file_path, "r+") as file:
                for item in self.archived_data:
                    if item not in data:
                        data.append(item)
                json.dump(data, file, indent=4)
        except FileNotFoundError:
            with open(self.state_file_path, "w") as file:
                json.dump(self.archived_data, file, indent=4)
        except Exception as error:
            raise error
    
    # Create archive of approx size 'self.max_bytes'
    def create(self):
        # Variables for tracking archives
        temp_archive = [] # Temporary list for tracking size of archives
        current_size = 0
        current_archive = 0
        for target in self.new_files:
            archive_name = self.name + '-' + self.timestamp + '-' + str(current_archive) + Archiver.suffix
            archive = os.path.join(self.directory, archive_name)
            file_path = os.path.join(self.directory, target)
            file_size = os.path.getsize(file_path)
            # If total size of archive is less than the max, create a temporary list of files that need to be archived
            if current_size + file_size <= self.max_bytes:
                temp_archive.append(target)
                current_size += file_size
            # Once archive max size is reached, flush to an archive, and incrementing unique naming variables
            else:
                # Append current iteration file before flushing
                temp_archive.append(target)
                # Flush to archive
                self.add_to_archive(temp_archive, archive)
                # Track the archive we just created
                self.archive_list.append((archive_name, archive))
                # Reset internal tracking variables
                temp_archive = []
                current_size = 0
                # Increment naming variables
                current_archive += 1
        # If we don't reach max, still create archive with the files we have
        if temp_archive:
            self.add_to_archive(temp_archive, archive)
            # Track the archive we just created
            self.archive_list.append((archive_name, archive))

    def cleanup(self):
        # Upload and delete all archives we just created
        for arc_name, arc in self.archive_list:
            # Upload the updated archive to S3
            self.upload_to_s3(arc, arc_name)
            # Delete the archive
            self.remove_file(arc)
        # Upload the updated archive state file to S3
        self.upload_to_s3(self.state_file_path, self.state_file)
        self.s3.close()
    
    def main(self):
        self.create()
        self.update_archived_files()
        self.cleanup()
