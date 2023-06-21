import argparse
import boto3
import botocore
import json
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
parser.add_argument("-m", "--max_size", help="Max file size of the archive in GB. Splits large archive into multi files. Default = 30", default=30, required=False)
parser.add_argument("-n", "--name", help="Name of the archive *Appended with timestamp + '.tgz'*", default="archive", required=False)
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
if args.disable_logging:
    logger.setLevel(logging.CRITICAL + 1)
elif args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

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

# Extact all files from an archive to a specified directory
def extract_archive(archive, directory, member_list):
    try:
        files = [ x.name for x in member_list ]
        logger.info("Extracting file(s) \'%s\' from archive \'%s\' into directory \'%s\'", files, archive, directory)
        with tarfile.open(archive, 'r:gz') as tar:
            logger.debug('Starting extraction of \'%s\' into \'%s\'', archive, directory)
            tar.extractall(path=directory, members=member_list)
        logger.debug('Extraction complete')
    except Exception as error:
        raise error

# Read the contents of the archive state file
def get_archived_files(state_file):
    try:
        with open(state_file, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

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

# Upload a file to S3 bucket with a given object name
def upload_to_s3(file_name, bucket, object_name):
    try:
        s3.upload_file(file_name, bucket, object_name)
        logger.info('Uploaded file \'%s\' to S3 bucket \'%s\' as \'%s\'', file_name, bucket, object_name)
    except botocore.exceptions.NoCredentialsError:
        logger.error('AWS credentials not found. Please check the provided key ID and secret')
        sys.exit(1)
    except botocore.exceptions.EndpointConnectionError:
        logger.error('Failed to connect to the specified S3 endpoint URL')
        sys.exit(1)
    except Exception as error:
        raise error

# Download a file from S3 bucket to a local file path
def download_from_s3(bucket, object_name, file_name):
    try:
        s3.download_file(bucket, object_name, file_name)
        logger.info('Downloaded file \'%s\' from S3 bucket \'%s\' as \'%s\'', object_name, bucket, file_name)
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

# Retrieve TarInfo of member files from missing files map
def get_missing_members(data, archive):
    missing_files_list = []
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
    for key in data:
        for member in members:
            if member.name in data[key]:
                missing_files_list.append(member)
    return missing_files_list

def main():
    # Define arguments
    directory = args.directory
    bucket = args.bucket
    action = args.action
    max_archive_size_gb = int(args.max_size)
    max_archive_size_bytes = max_archive_size_gb * (1024 ** 3)
    suffix = '.tgz'

    # Timestamp at run
    timestamp = datetime.utcnow().isoformat(timespec='seconds').replace(':','')

    state_file = args.state_file
    state_file_path = os.path.join(directory, state_file)

    # Download the archived files list if it is not present
    if not os.path.exists(state_file_path):
        download_from_s3(bucket, state_file, state_file_path)

    # Search for any changed files in the directory vs the state
    new_files, missing_files = get_changed_files(directory, state_file_path)

    match action:
        case 'archive':
            if new_files:
                # Add new files to the archive & update the archive list
                temp_archive = [] # Temporary list for tracking size of archives
                archive_list = [] # List of archives created
                current_size = 0
                current_archive = 0
                for target in new_files:
                    archive_name = args.name + '-' + timestamp + '-' + str(current_archive) + suffix
                    archive = os.path.join(directory, archive_name)
                    path = os.path.join(directory, target)
                    size = os.path.getsize(path)
                    # If total size of archive is less than the max, create a temporary list of files that need to be archived
                    if current_size + size < max_archive_size_bytes:
                        temp_archive.append(target)
                        current_size += size
                    # Once archive max size is reached, flush to an archive, and incrementing unique naming variables
                    else:
                        # Append current iteration file before flushing
                        temp_archive.append(target)
                        # Flush to archive
                        add_to_archive(temp_archive, archive, state_file_path, directory)
                        # Track the archive we just created
                        archive_list.append((archive_name, archive))
                        # Increment naming variables
                        current_archive += 1
                        # Reset internal tracking variables
                        current_size = 0
                        temp_archive = []
                # If we don't reach max, still create archive with the files we have
                if temp_archive:
                    add_to_archive(temp_archive, archive, state_file_path, directory)
                    # Track the archive we just created
                    archive_list.append((archive_name, archive))
                # Upload and delete all archives we just created
                for arc_name, arc in archive_list:
                    # Upload the updated archive to S3
                    upload_to_s3(arc, bucket, arc_name)
                    # Delete the archive
                    remove_file(arc)
                # Upload the updated archive state file to S3
                upload_to_s3(state_file_path, bucket, state_file)
        case 'extract':
            if missing_files:
                logger.debug('Missing files: \'%s\'', missing_files)
                # Read state data
                state_data = get_archived_files(state_file_path)
                # Retrieves entry in state file for missing files
                state_entries = [item for item in state_data if item['relative_path'] in missing_files]
                # Converts missing files entries into map array like: [{"archive_name": ["list", "of", "files", "to", "extract", "from", "archive"]}]
                missing_file_map = reduce_map(state_entries)
                for item in missing_file_map:
                    archive_full_path = os.path.join(directory, item)
                    # Download the archive if it is not present
                    if not os.path.isfile(archive_full_path):
                        download_from_s3(bucket, item, archive_full_path)
                    # Retrieve TarInfo of members that must be extracted
                    tar_members = get_missing_members(missing_file_map, archive_full_path)
                    # Extract only missing files
                    extract_archive(archive_full_path, directory, tar_members)
                    # Do not store archives on local disk
                    remove_file(archive_full_path)
            else:
                logger.debug("There are no files missing from the current state")

    # Close S3 connection
    s3.close()
    logger.debug('S3 connection closed')

if __name__ == "__main__":
    main()
