import tarfile
import os

from libs.ArchiveTemplate import ArchiveTemplate
from libs.logger import logger

# ArchiveTemplate subclass for extracting archive objects
class Extractor(ArchiveTemplate):

    @property
    def missing_files(self):
        return self.get_changed_files('missing')

    @property
    def state_entries(self):
        return [item for item in self.state_data if item['relative_path'] in self.missing_files]
    
    @property
    def missing_file_map(self):
        return self.reduce_map(self.state_entries)

    # Retrieve TarInfo of member files from missing files map
    def get_missing_members(self, archive):
        missing_files_list = []
        with tarfile.open(archive, 'r:gz') as tar:
            members = tar.getmembers()
        for key in self.missing_file_map:
            for member in members:
                if member.name in self.missing_file_map[key]:
                    missing_files_list.append(member)
        return missing_files_list
    
    # Take missing files, and return map of { "archive": [list of files to extract from "archive"] }
    def reduce_map(self, data):
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
    
    # Extact all files from an archive to a specified directory
    def extract_archive(self, archive, member_list):
        try:
            files = [ x.name for x in member_list ]
            logger.info("Extracting file(s) \'%s\' from archive \'%s\' into directory \'%s\'", files, archive, self.directory)
            with tarfile.open(archive, 'r:gz') as tar:
                logger.debug('Starting extraction of \'%s\' into \'%s\'', archive, self.directory)
                tar.extractall(path=self.directory, members=member_list)
            logger.debug('Extraction complete')
        except Exception as error:
            raise error
    
    def extract(self):
        logger.debug('Missing files: \'%s\'', self.missing_files)
        for item in self.missing_file_map:
            archive_full_path = os.path.join(self.directory, item)
            # Download the archive if it is not present
            if not os.path.isfile(archive_full_path):
                self.download_from_s3(item, archive_full_path)
            # Retrieve TarInfo of members that must be extracted
            tar_members = self.get_missing_members(archive_full_path)
            # Extract only missing files
            self.extract_archive(archive_full_path, tar_members)
            # Do not store archives on local disk
            self.remove_file(archive_full_path)
