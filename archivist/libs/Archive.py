import boto3
import botocore
import json
import os
import sys
import tarfile

from datetime import datetime

from libs.logger import logger

# Base class
class ArchiveTemplate:

    def __init__(self, directory, state_file, key_id, key_secret, bucket, certificate_path, endpoint_url=None):
        self.directory = directory
        self.state_file = state_file
        self.key_id = key_id
        self.key_secret = key_secret
        self.endpoint_url = endpoint_url
        self.bucket = bucket
        self.certificate_path = certificate_path
        self._state_file_path = os.path.join(self.directory, self.state_file)

        # Initialize S3 session
        session = boto3.session.Session()
        # Create client from session parameters
        self.s3 = session.client("s3", endpoint_url=self.endpoint_url,
                                 aws_access_key_id=self.key_id,
                                 aws_secret_access_key=self.key_secret,
                                 verify=self.certificate_path)
        # Download the archived files list if it is not present
        if not os.path.exists(self._state_file_path):
            self._download_from_s3(file_name=self._state_file_path, object_name=self.state_file)
        # Check state file for discrepancies
        self.state_data = self._get_archived_files()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *exc):
        self._remove_file(self._state_file_path)

    # Get the list of files that have changed (new or missing)
    def _get_changed_files(self, type):
        directory_files = []
        try:
            for root, dirs, files in os.walk(self.directory):
                for file in files:
                    # Get path relative to directory provided in --directory
                    archive_file_name = os.path.relpath(os.path.join(root, file), self.directory)
                    # Exclude state file from tracking
                    if archive_file_name not in self.state_file:
                        # Gather current state of filesystem
                        directory_files.append(archive_file_name)
            current_files = set(directory_files)
            archived_files = set([ x['relative_path'] for x in self.state_data ])
            # Use asymmetric difference of sets to file new and missing files
            if type == 'new':
                file_diff = current_files - archived_files
            elif type == 'missing':
                file_diff = archived_files - current_files
            return list(file_diff)
        except Exception as error:
            raise error

    # Read the contents of the archive state file
    def _get_archived_files(self):
        try:
            with open(self._state_file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return []

    # Remove a file
    def _remove_file(self, file_path):
        try:
            os.remove(file_path)
            logger.info('Removed file \'%s\'', file_path)
        except FileNotFoundError:
            logger.warning('File \'%s\' does not exist', file_path)
        except Exception as error:
            raise error
    
    # Upload a file to S3 bucket with a given object name
    def _upload_to_s3(self, file_name, object_name):
        try:
            self.s3.upload_file(file_name, self.bucket, object_name)
            logger.info('Uploaded file \'%s\' to S3 bucket \'%s\' as \'%s\'', file_name, self.bucket, object_name)
        except botocore.exceptions.NoCredentialsError:
            logger.error('AWS credentials not found. Please check the provided key ID and secret')
            sys.exit(1)
        except botocore.exceptions.EndpointConnectionError:
            logger.error('Failed to connect to the specified S3 endpoint URL')
            sys.exit(1)
        except Exception as error:
            raise error

    # Download a file from S3 bucket to a local file path
    def _download_from_s3(self, object_name, file_name):
        try:
            self.s3.download_file(self.bucket, object_name, file_name)
            logger.info('Downloaded file \'%s\' from S3 bucket \'%s\' as \'%s\'', object_name, self.bucket, file_name)
        except botocore.exceptions.NoCredentialsError:
            logger.error('AWS credentials not found. Please check the provided key ID and secret')
            sys.exit(1)
        except botocore.exceptions.EndpointConnectionError:
            logger.error('Failed to connect to the specified S3 endpoint URL')
            sys.exit(1)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                logger.info("The object does not exist.")
            else:
                raise e
        except Exception as error:
            raise error

# ArchiveTemplate subclass for archiving & compressing archive objects
class Archiver(ArchiveTemplate):

    suffix = '.tgz'

    def __init__(self, name, max = 30, *args, **kwargs):
        ArchiveTemplate.__init__(self, *args, **kwargs)
        self.name = str(name)
        self.max = int(max)
        self.max_bytes = self.max * (1024 ** 3)
        self._archive_list = []
        self.timestamp = datetime.utcnow().isoformat(timespec='seconds').replace(':','')
        self.new_files = self._get_changed_files('new')

    def __exit__(self, *exc):
        # Upload and delete all archives we just created
        for arc_name, arc in self._archive_list:
            # Upload the updated archive to S3
            self._upload_to_s3(arc, arc_name)
            # Delete the archive
            self._remove_file(arc)
        # Upload the updated archive state file to S3
        if self._archive_list:
            self._upload_to_s3(self._state_file_path, self.state_file)
        self.s3.close()
        self._remove_file(self._state_file_path)

    # Reset tarinfo
    def _reset(self, tarinfo):
        tarinfo.uid = tarinfo.gid = 0
        tarinfo.uname = tarinfo.gname = "root"
        return tarinfo
    
    # Add a list of files to the archive and update state file
    def _add_to_archive(self, data, archive):
        try:
            archived_data = []
            with tarfile.open(archive, "w:gz") as tar:
                logger.debug('tarfile \'%s\' opened', archive)
                for target in data:
                    path = os.path.join(self.directory, target)
                    tar.add(path, target, filter=self._reset)
                    logger.info('Added file \'%s\' to the archive \'%s\'', path, archive)
                    archived_data.append({
                                          "relative_path": target,
                                          "archive_name": os.path.relpath(archive, self.directory)
                                        })
            self._update_archived_files(archived_data)
        except Exception as error:
            raise error

    # Appends a newly archived file to the archive state file
    def _update_archived_files(self, data):
        try:
            state_data = self.state_data
            with open(self._state_file_path, "r+") as file:
                for item in data:
                    if item not in state_data:
                        state_data.append(item)
                json.dump(state_data, file, indent=4)
        except FileNotFoundError:
            with open(self._state_file_path, "w") as file:
                json.dump(data, file, indent=4)
        except Exception as error:
            raise error
    
    # Create archive of approx size 'self.max_bytes'
    def create(self):
        if self.new_files:
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
                    self._add_to_archive(temp_archive, archive)
                    # Track the archive we just created
                    self._archive_list.append((archive_name, archive))
                    # Reset internal tracking variables
                    temp_archive = []
                    current_size = 0
                    # Increment naming variables
                    current_archive += 1
            # If we don't reach max, still create archive with the files we have
            if temp_archive:
                self._add_to_archive(temp_archive, archive)
                # Track the archive we just created
                self._archive_list.append((archive_name, archive))
        else:
            logger.debug('There are no new files')

# ArchiveTemplate subclass for extracting archive objects
class Extractor(ArchiveTemplate):

    def __init__(self, *args, **kwargs):
        ArchiveTemplate.__init__(self, *args, **kwargs)
        self.missing_files = self._get_changed_files('missing')
        self._state_entries = [item for item in self.state_data if item['relative_path'] in self.missing_files]
        self._missing_files_map = self._reduce_map(self._state_entries)

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
        if self.missing_files:
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
        else:
            logger.debug("There are no files missing from the current state")
