import os
import boto3
from botocore.config import Config
from data_model.config import settings  # 先载入 .env

r2 = boto3.client(
    service_name="s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto",
    config=Config(signature_version="s3v4", connect_timeout=10, read_timeout=120,
                  retries={"max_attempts": 3, "mode": "standard"}),
)
R2_BUCKET = os.getenv("R2_BUCKET")