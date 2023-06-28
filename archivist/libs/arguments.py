import argparse

# Read command line args
# Top level parser
parser = argparse.ArgumentParser(description="This is a script to archive (tar) a directory and upload it to object storage using S3")
parser.add_argument("--debug", help="Set logging to Debug", action='store_true', required=False)
parser.add_argument("--disable_logging", help="Disable logging", action='store_true', required=False)
parser.add_argument("-b", "--bucket", type=str, help="Name of the S3 bucket to upload to", required=True)
parser.add_argument("-c", "--certificate_path", type=str, help="Path to the certificate to use for S3 endpoint", default="/tmp/ca.crt", required=False)
parser.add_argument("-d", "--directory", type=str, help="Directory to run archive/extraction", required=True)
parser.add_argument("-i", "--key_id", type=str, help="S3 Key ID to use", required=True)
parser.add_argument("-k", "--key_secret", type=str, help="S3 Key Secret to use", required=True)
parser.add_argument("-s", "--state_file", type=str, help="State file to use", default="archived_files.state", required=False)
parser.add_argument("-u", "--endpoint_url", type=str, help="endpoint url for s3 upload", required=True)

# Sub-command parser
sub_parser = parser.add_subparsers(dest='cmd', required=True)

# Archive sub-command
archive_parser = sub_parser.add_parser('archive', help='Archive a specified directory')
archive_parser.add_argument("-m", "--max_size", type=int, help="Max file size of the archive in GB. Splits large archive into multi files. Default = 30", default=30, required=False)
archive_parser.add_argument("-n", "--name", type=str, help="Name of the archive *Appended with timestamp + '.tgz'*", default="archive", required=False)

# Extract sub-command
extract_parser = sub_parser.add_parser('extract', help='Extract specified archive into directory')

# Import this
args = parser.parse_args()
