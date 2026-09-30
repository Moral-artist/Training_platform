import os
import boto3

r2 = boto3.client(
    service_name="s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto",
)

R2_BUCKET = os.getenv("R2_BUCKET")