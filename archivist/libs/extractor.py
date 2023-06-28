import tarfile

from libs.logger import logger

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
