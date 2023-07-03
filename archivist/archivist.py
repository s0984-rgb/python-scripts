from libs.logger import logger
from libs.arguments import args
from libs.Archive import Archiver, Extractor

def main():
    match args.cmd:
        case 'archive':
            new_archive = Archiver(directory=args.directory,
                                  state_file=args.state_file,
                                  name=args.name,
                                  max=args.max_size,
                                  key_id=args.key_id,
                                  key_secret=args.key_secret,
                                  endpoint_url=args.endpoint_url,
                                  bucket=args.bucket,
                                  certificate_path=args.certificate_path)
            if new_archive.new_files:
                new_archive.create()
                new_archive.cleanup()
            else:
                logger.debug('There are no new files')
        case 'extract':
            extraction = Extractor(directory=args.directory,
                                   state_file=args.state_file,
                                   key_id=args.key_id,
                                   key_secret=args.key_secret,
                                   endpoint_url=args.endpoint_url,
                                   bucket=args.bucket,
                                   certificate_path=args.certificate_path)
            if extraction.missing_files:
                extraction.extract()
            else:
                logger.debug("There are no files missing from the current state")

if __name__ == "__main__":
    main()
