import json
import os
import boto3
import botocore
import sys

from libs.logger import logger

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

    @property
    def state_data(self):
        return self._get_archived_files()

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
