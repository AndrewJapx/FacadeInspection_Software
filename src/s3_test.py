import boto3

# For LocalStack, set endpoint_url to 'http://localhost:4566'
s3 = boto3.client(
    's3',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='us-east-1',
    endpoint_url='http://localhost:4566'  # Uncomment for LocalStack
)

bucket_name = 'my-test-bucket'

# Create a bucket (skip if it already exists)
try:
    s3.create_bucket(Bucket=bucket_name)
    print(f"Bucket '{bucket_name}' created.")
except s3.exceptions.BucketAlreadyOwnedByYou:
    print(f"Bucket '{bucket_name}' already exists.")

# Upload a file (make sure 'local_file.txt' exists in your directory)
try:
    s3.upload_file('local_file.txt', bucket_name, 'uploaded_file.txt')
    print('File uploaded successfully.')
except Exception as e:
    print('Upload failed:', e)

# Download the file
try:
    s3.download_file(bucket_name, 'uploaded_file.txt', 'downloaded_file.txt')
    print('File downloaded successfully.')
except Exception as e:
    print('Download failed:', e)
