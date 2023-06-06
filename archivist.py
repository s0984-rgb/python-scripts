import argparse
import boto3
import botocore
import logging
import os
import sys
import tarfile

import datetime
from datetime import datetime

# Read command line args
parser = argparse.ArgumentParser(description="This is a script to archive (tar) a directory and upload it to object storage using S3")
parser.add_argument("-a", "--action", help="Action to commit on tar", choices=['archive', 'extract'], required=True)
parser.add_argument("-c", "--certificate_path", help="Path to the certificate to use for S3 endpoint", default="/tmp/ca.crt", required=False)
parser.add_argument("-b", "--bucket", help="Name of the S3 bucket to upload to", required=True)
parser.add_argument("-d", "--directory", help="Directory to run archive/extraction", required=True)
parser.add_argument("-i", "--key_id", help="S3 Key ID to use", required=True)
parser.add_argument("-k", "--key_secret", help="S3 Key Secret to use", required=True)
parser.add_argument("-n", "--name", help="Name of the archive *Appended with timestamp + '.tgz'*", default="archive.tar.gz", required=False)
parser.add_argument("-s", "--state_file", help="State file to use", default="archived_files.state", required=False)
parser.add_argument("-u", "--endpoint_url", help="endpoint url for s3 upload", required=True)
parser.add_argument("--debug", help="Set logging to Debug", action='store_true', required=False)
parser.add_argument("--disable_logging", help="Disable logging", action='store_true', required=False)
args = parser.parse_args()

# Set default logging config
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize S3 session
session = boto3.session.Session(aws_access_key_id=args.key_id, aws_secret_access_key=args.key_secret)
# Create client from session parameters
s3 = session.client("s3", endpoint_url=args.endpoint_url, verify=args.certificate_path)

# Set custom logging config
if args.debug:
    logger.setLevel(logging.DEBUG)
elif args.disable_logging:
    logger.setLevel(logging.CRITICAL + 1)
else:
    logger.setLevel(logging.INFO)

def reset(tarinfo):
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = "root"
    return tarinfo

# Add a list of files to the archive and update state file
def add_to_archive(file_data, archive, state_file):
    try:
        with tarfile.open(archive, "w:gz") as tar:
            logger.debug('tarfile \'%s\' opened', archive)
            for target,path in file_data:
                tar.add(path, target, filter=reset)
                logger.info('Added file \'%s\' to the archive %s', path, archive)
                update_archived_files(target, state_file)
        tar.close()
        logger.debug('tarfile \'%s\' closed', archive)
    except Exception as error:
        raise error

# Extact all files from an archive to a specified directory
def extract_archive(archive, directory):
    try:
        with tarfile.open(archive, 'r:gz') as tar:
            logger.debug('tarfile \'%s\' opened', archive)
            logger.info('Starting extraction of \'%s\' in \'%s\'', archive, directory)
            tar.extractall(path=directory)
            logger.info('Extraction complete')
        tar.close()
        logger.debug('tarfile \'%s\' closed', archive)
    except Exception as error:
        raise error

# Retrieves a list of all archives (objects) present in the specified S3 bucket and downloads them
def get_all_archives(bucket):
    try:
        objects = s3.list_objects(Bucket=bucket)
        object_list = []
        for object in objects['Contents']:
            key = object['Key']
            object_list.append(key)
        return object_list
    except KeyError as error:
        logger.exception('No contents found in S3 bucket \'%s\'', bucket)
        raise error
    except Exception as error:
        raise error

# Reads and returns the contents of the archive state file, which contains the list of previously archived files
def get_archived_files(state_file):
    try:
        if os.path.exists(state_file):
            with open(state_file, "r") as file:
                return file.read().splitlines()
        return []
    except Exception as error:
        raise error

# Appends a newly archived file to the archive state file
def update_archived_files(target, state_file):
    try:
        with open(state_file, "a") as file:
            file.write(target + "\n")
            logger.info('Added \'%s\' to archive state', target)
    except Exception as error:
        raise error

# Searches for new files in the specified directory that are not present in the archive state file
def get_new_files(directory, state_file):
    try:
        archived_files = list(get_archived_files(state_file))
        new_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                # Get absolute path on system
                file_path = os.path.join(root, file)
                # Get path relative to directory provided in --directory
                archive_file_name = os.path.relpath(file_path, directory)
                # Exclude anka state from archives
                if archive_file_name not in archived_files and not os.path.relpath(state_file, directory):
                    tup = (archive_file_name, file_path)
                    new_files.append(tup)
                    logger.debug('Detected new file for archive \'%s\'', archive_file_name)
        return new_files
    except Exception as error:
        raise error

# Searches for new files in the specified directory that are not present in the archive state file
def get_missing_files(directory, state_file):
    try:
        archived_files = list(get_archived_files(state_file))
        missing_files = []
        current_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                # Get absolute path on system
                file_path = os.path.join(root, file)
                # Get path relative to directory provided in --directory
                archive_file_name = os.path.relpath(file_path, directory)
                # Gather current state of filesystem
                current_files.append(archive_file_name)
        # Compare archived state to current state
        for archived_file in archived_files:
            if archived_file not in current_files:
                missing_files.append(archived_file)
                logger.debug('Detected missing file \'%s\'', missing_files)
        return missing_files
    except Exception as error:
        raise error

def remove_file(file_name):
    try:
        os.remove(file_name)
        logger.debug('File \'%s\' deleted', file_name)
    except FileNotFoundError:
        pass
    except Exception as error:
        logger.exception("Could not remove file \'%s\'", file_name)
        raise error

# Upload a file to S3
def upload_to_s3(file_path, bucket, object_name):
    try:
        s3.upload_file(file_path, bucket, object_name) # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html
        logger.info('Uploaded \'%s\' to bucket \'%s\', at key \'%s\'', file_path, bucket, object_name)
    except Exception as error:
        raise error

# Download a file from S3
def download_from_s3(bucket, object_name, file_path):
    try:
        s3.download_file(bucket, object_name, file_path) # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-example-download-file.html
        logger.info('Downloaded \'%s\' from bucket \'%s\' at \'%s\'', object_name, bucket, file_path)
    except botocore.exceptions.ClientError:
        logger.warning('Could not download file \'%s\'', file_path)
        pass
    except Exception as error:
        raise error

def main():
    # Define arguments
    directory = args.directory
    bucket_name = args.bucket
    action = args.action

    archive_state_file = args.state_file
    archive_state_path = os.path.join(directory, archive_state_file)

    timestamp = datetime.utcnow().isoformat(timespec='seconds').replace(':','')

    suffix = '.tgz'
    archive_name = args.name + '-' + timestamp + suffix
    archive_full_path = os.path.join(directory, archive_name)

    # Download the archived files list if it is not present
    if not os.path.exists(archive_state_path):
        download_from_s3(bucket_name, archive_state_file, archive_state_path)

    if action == 'archive':
        # Search for new files to add to the archive
        new_archives = get_new_files(directory, archive_state_path)

        # If there are new files to archive, then download the archive, update the archive, and upload it back
        if len(new_archives) != 0:
            # Add new files to the archive & update the archive list
            add_to_archive(new_archives, archive_full_path, archive_state_path)
            # Upload the updated archive to S3
            upload_to_s3(archive_full_path, bucket_name, archive_name)
            # Upload the updated archive state file to S3
            upload_to_s3(archive_state_path, bucket_name, archive_state_file)
            remove_file(archive_full_path)

    elif action == 'extract':
        if get_missing_files(directory, archive_state_path):
            objects = get_all_archives(bucket_name)
            for object in objects:
                if suffix in object:
                    object_full_path = os.path.join(directory, object)
                    download_from_s3(bucket_name, object, object_full_path)
                    extract_archive(object_full_path, directory)
                    remove_file(object_full_path)
        else:
            logger.debug("There are no files missing from the current state")

    # Close S3 connection
    s3.close()
    logger.debug('S3 connection closed')

if __name__ == "__main__":
    main()
