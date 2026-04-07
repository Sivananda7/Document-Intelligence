import os
import boto3
from botocore.exceptions import NoCredentialsError
import uuid

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'document-intelligence-bucket')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')

class StorageRepository:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
            endpoint_url=S3_ENDPOINT_URL
        )
        
    def create_bucket_if_not_exists(self):
        """Create the configured S3 bucket if it doesn't already exist."""
        try:
            self.s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        except Exception:
            try:
                self.s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
                print(f"Bucket '{S3_BUCKET_NAME}' created.")
            except Exception as e:
                print(f"Failed to create bucket: {e}")

    def upload_file(self, file_path: str, original_filename: str) -> str:
        """Uploads a file from disk to S3 and returns the resulting Object URI."""
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        try:
            with open(file_path, "rb") as f:
                self.s3_client.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=unique_filename,
                    Body=f
                )
            # Create a mock s3 protocol URI for mapping
            s3_uri = f"s3://{S3_BUCKET_NAME}/{unique_filename}"
            print(f"Successfully uploaded {unique_filename} to {s3_uri}")
            return s3_uri
        except NoCredentialsError:
            print("Credentials not available for S3.")
            raise
        except Exception as e:
            print(f"Failed to upload to S3: {e}")
            raise

# Instantiate a global storage repo
storage_repo = StorageRepository()
