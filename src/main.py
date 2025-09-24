

print("[main.py] Top of file reached")
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from PySide6.QtWidgets import QApplication
from mainwindow import MainWindow
import sys

# --- LocalStack S3 connection test ---
def test_localstack_s3():
    print("[main.py] Testing LocalStack S3 connection...")
    s3 = boto3.client('s3', endpoint_url='http://localhost:4566')
    bucket_name = 'test-bucket'
    try:
        # Create bucket (ignore if exists)
        try:
            s3.create_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' created.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                print(f"Bucket '{bucket_name}' already exists.")
            else:
                print(f"Error creating bucket: {e}")
        # List buckets
        response = s3.list_buckets()
        print("Buckets:", [b['Name'] for b in response.get('Buckets', [])])
    except NoCredentialsError:
        print("No AWS credentials found. For LocalStack, dummy credentials are fine.")
    except Exception as e:
        print(f"S3 test error: {e}")



def main():
    print("[main.py] main() called")
    test_localstack_s3()  # Test S3 connection to LocalStack
    app = QApplication(sys.argv)
    window = MainWindow()
    print("[main.py] MainWindow created")
    window.show()
    print("[main.py] window.show() called")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()