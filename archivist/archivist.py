from libs.arguments import args
from libs.Archive import Archiver, Extractor

def main():
    if args.cmd == 'archive':
        with Archiver(directory=args.directory,
                        state_file=args.state_file,
                        name=args.name,
                        max=args.max_size,
                        key_id=args.key_id,
                        key_secret=args.key_secret,
                        endpoint_url=args.endpoint_url,
                        bucket=args.bucket,
                        certificate_path=args.certificate_path) as archive:
            archive.create()
    elif args.cmd == 'extract':
        with Extractor(directory=args.directory,
                        state_file=args.state_file,
                        key_id=args.key_id,
                        key_secret=args.key_secret,
                        endpoint_url=args.endpoint_url,
                        bucket=args.bucket,
                        certificate_path=args.certificate_path) as extractor:
            extractor.extract()

if __name__ == "__main__":
    main()
