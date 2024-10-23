import boto3
import os
from botocore.exceptions import ClientError, EndpointConnectionError

# AWS Configuration
AWS_ACCESS_KEY = 'AKIAW5WU5DDTFHJRNIFE'
AWS_SECRET_KEY = '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'
AWS_REGION = 'eu-north-1'  # Stockholm region

def test_aws_connection(s3_client):
    """Test AWS connection and permissions"""
    try:
        s3_client.list_buckets()
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidAccessKeyId':
            print("Error: Invalid AWS access key. Please check your credentials.")
        elif e.response['Error']['Code'] == 'SignatureDoesNotMatch':
            print("Error: Invalid AWS secret key. Please check your credentials.")
        else:
            print(f"AWS Credentials Error: {str(e)}")
        return False
    except EndpointConnectionError:
        print(f"Error connecting to AWS endpoint in {AWS_REGION}. Please check your internet connection.")
        return False

def upload_to_s3():
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )
        
        # Test connection before proceeding
        if not test_aws_connection(s3_client):
            return

        # S3 configuration
        bucket_name = 'audiojam-spotify'
        local_file = 'similarity.pkl'
        s3_key = 'similarity.pkl'

        # Verify local file
        if not os.path.exists(local_file):
            print(f"Error: {local_file} not found in {os.getcwd()}")
            return
            
        # Get file size
        file_size = os.path.getsize(local_file)
        print(f"File size: {file_size / (1024*1024):.2f} MB")

        # Check if file already exists in S3
        try:
            s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            print("Warning: File already exists in S3. Proceeding with overwrite...")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print("Uploading new file to S3...")
            else:
                raise

        # Upload file
        print(f"Starting upload to s3://{bucket_name}/{s3_key} in {AWS_REGION}...")
        s3_client.upload_file(
            Filename=local_file,
            Bucket=bucket_name,
            Key=s3_key,
            Callback=lambda bytes_transferred: print(f"Uploaded {bytes_transferred / (1024*1024):.2f} MB", end='\r')
        )
        
        print(f"\nSuccessfully uploaded {local_file} to s3://{bucket_name}/{s3_key}")
        
        # Verify upload
        try:
            obj = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            print(f"Upload verified! File size in S3: {obj['ContentLength'] / (1024*1024):.2f} MB")
        except ClientError as e:
            print(f"Upload verification failed: {str(e)}")

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            print(f"Error: Bucket '{bucket_name}' does not exist")
        elif e.response['Error']['Code'] == 'AccessDenied':
            print("Error: Access denied. Please check your IAM permissions")
        else:
            print(f"AWS Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    upload_to_s3()