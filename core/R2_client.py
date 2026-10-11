import boto3
from botocore.config import Config
from data_model.config import settings  # 先载入 .env

r2 = boto3.client(
    service_name="s3",
    endpoint_url=settings.R2_ENDPOINT,
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    region_name="auto",
    config=Config(
        signature_version="s3v4",
        connect_timeout=10,
        read_timeout=120,
        retries={"max_attempts": 3, "mode": "standard"},
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    ),
)
R2_BUCKET = settings.R2_BUCKET
