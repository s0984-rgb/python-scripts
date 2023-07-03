import boto3
import botocore
import sys

from libs.arguments import args
from libs.logger import logger

# Initialize S3 session
session = boto3.session.Session(aws_access_key_id=args.key_id, aws_secret_access_key=args.key_secret)
# Create client from session parameters
s3 = session.client("s3", endpoint_url=args.endpoint_url, verify=args.certificate_path)

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
