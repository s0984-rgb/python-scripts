import tarfile
import os

from libs.ArchiveTemplate import ArchiveTemplate
from libs.logger import logger

# ArchiveTemplate subclass for extracting archive objects
class Extractor(ArchiveTemplate):

    @property
    def missing_files(self):
        return self._get_changed_files('missing')

    @property
    def _state_entries(self):
        return [item for item in self.state_data if item['relative_path'] in self.missing_files]
    
    @property
    def _missing_files_map(self):
        return self._reduce_map(self._state_entries)

    # Retrieve TarInfo of member files from missing files map
    def _get_missing_members(self, archive):
        missing_files_list = []
        with tarfile.open(archive, 'r:gz') as tar:
            members = tar.getmembers()
        for key in self._missing_files_map:
            for member in members:
                if member.name in self._missing_files_map[key]:
                    missing_files_list.append(member)
        return missing_files_list
    
    # Take missing files, and return map of { "archive": [list of files to extract from "archive"] }
    def _reduce_map(self, data):
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
    def _extract_archive(self, archive, member_list):
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
        for item in self._missing_files_map:
            archive_full_path = os.path.join(self.directory, item)
            # Download the archive if it is not present
            if not os.path.isfile(archive_full_path):
                self._download_from_s3(item, archive_full_path)
            # Retrieve TarInfo of members that must be extracted
            tar_members = self._get_missing_members(archive_full_path)
            # Extract only missing files
            self._extract_archive(archive_full_path, tar_members)
            # Do not store archives on local disk
            self._remove_file(archive_full_path)
