# Archivist

This project allows you to syncronize local storage with an S3 backend.

## Why?

Some processes do not have a clustering mechanism which allows it to replicate data across multiple nodes.

This script is designed to replicate data across multiple nodes with independent storage using S3 as a backend.

It will limit the size of each individual archive to the specified size (default 30GB).

## Usage

To use this cli tool, you must run it with the necessary required parameters.

This can be run as a scheduled task/cronjob or alternatively, it can be run as a sidecar container.

By default, the script will try uploading to AWS S3. However, you can write to another object storage that supports S3 protocol by using the `--endpoint_url` parameter.

### Examples
generic:
```bash
python3 archivist.py <action> -d /path/to/directory/ -c /path/to/cert/file.crt -b my_bucket -i my_s3_key_id -k my_s3_key_secret
```

archive with debug logging, limit size to 10GB, archives with name prefix `test`, and state file named `test.state`
```bash
python3 archivist.py --debug archive -n test -s test.state -d /path/to/directory/ -c /path/to/cert/file.crt -b my_bucket -i my_s3_secret_id -k my_s3_secret_key -m 10
```

extract with debug logging, using state file 'test.state'
```bash
python3 archivist.py --debug extract -s test.state -d /path/to/directory/ -c /path/to/cert/file.crt -b my_bucket -i my_s3_secret_id -k my_s3_secret_key
```
