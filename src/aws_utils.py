import boto3
import os

def get_s3_client():
    """
    Returns a boto3 S3 client. Uses LocalStack if USE_LOCALSTACK=1 is set in the environment.
    """
    if os.environ.get('USE_LOCALSTACK') == '1':
        return boto3.client(
            's3',
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1',
            endpoint_url='http://localhost:4566'
        )
    else:
        return boto3.client('s3')

def upload_to_s3(local_path, bucket, s3_key):
    s3 = get_s3_client()
    s3.upload_file(local_path, bucket, s3_key)
    return f"https://{bucket}.s3.amazonaws.com/{s3_key}"
