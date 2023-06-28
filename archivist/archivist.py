import os

import datetime
from datetime import datetime

from libs.logger import logger
from libs.arguments import args
from libs import helper, s3

def main():
    # Define arguments
    directory = args.directory
    bucket = args.bucket
    command = args.cmd
    max_archive_size_gb = int(args.max_size)
    max_archive_size_bytes = max_archive_size_gb # * (1024 ** 3)
    suffix = '.tgz'

    # Timestamp at run
    timestamp = datetime.utcnow().isoformat(timespec='seconds').replace(':','')

    state_file = args.state_file
    state_file_path = os.path.join(directory, state_file)

    # Download the archived files list if it is not present
    if not os.path.exists(state_file_path):
         s3.download_from_s3(bucket, state_file, state_file_path)

    # Search for any changed files in the directory vs the state
    new_files, missing_files = helper.get_changed_files(directory, state_file_path)

    match command:
        case 'archive':
            if new_files:
                from libs import archiver
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
                        archiver.add_to_archive(temp_archive, archive, state_file_path, directory)
                        # Track the archive we just created
                        archive_list.append((archive_name, archive))
                        # Increment naming variables
                        current_archive += 1
                        # Reset internal tracking variables
                        current_size = 0
                        temp_archive = []
                # If we don't reach max, still create archive with the files we have
                if temp_archive:
                    archiver.add_to_archive(temp_archive, archive, state_file_path, directory)
                    # Track the archive we just created
                    archive_list.append((archive_name, archive))
                # Upload and delete all archives we just created
                for arc_name, arc in archive_list:
                    # Upload the updated archive to S3
                    s3.upload_to_s3(arc, bucket, arc_name)
                    # Delete the archive
                    helper.remove_file(arc)
                # Upload the updated archive state file to S3
                s3.upload_to_s3(state_file_path, bucket, state_file)
        case 'extract':
            if missing_files:
                from libs import extractor
                logger.debug('Missing files: \'%s\'', missing_files)
                # Read state data
                state_data = helper.get_archived_files(state_file_path)
                # Retrieves entry in state file for missing files
                state_entries = [item for item in state_data if item['relative_path'] in missing_files]
                # Converts missing files entries into map array like: [{"archive_name": ["list", "of", "files", "to", "extract", "from", "archive"]}]
                missing_file_map = helper.reduce_map(state_entries)
                for item in missing_file_map:
                    archive_full_path = os.path.join(directory, item)
                    # Download the archive if it is not present
                    if not os.path.isfile(archive_full_path):
                        s3.download_from_s3(bucket, item, archive_full_path)
                    # Retrieve TarInfo of members that must be extracted
                    tar_members = extractor.get_missing_members(missing_file_map, archive_full_path)
                    # Extract only missing files
                    extractor.extract_archive(archive_full_path, directory, tar_members)
                    # Do not store archives on local disk
                    helper.remove_file(archive_full_path)
            else:
                logger.debug("There are no files missing from the current state")

    # Close S3 connection
    s3.s3.close()
    logger.debug('S3 connection closed')

if __name__ == "__main__":
    main()
