
import boto3
import os
from urllib.parse import urlparse
import json

def handler(event, context):
    """
    Lambda handler function to process the event.
    """
    print(f"Received event: {json.dumps(event)}")
    s3_client = boto3.client("s3")

    try:
        # --- Get Parameters ---
        source_bucket = event.get("source_bucket")
        source_key = event.get("source_key")
        destination_key = event.get("destination_key")

        if not all([source_bucket, source_key, destination_key]):
            raise ValueError(
                "Missing one or more required parameters: 'source_bucket', 'source_key', 'destination_key'"
            )

        # --- Copy Object ---
        copy_source = {"Bucket": source_bucket, "Key": source_key}
        print(
            f"Copying object from s3://{source_bucket}/{source_key} to s3://{source_bucket}/{destination_key}"
        )
        s3_client.copy_object(
            CopySource=copy_source, Bucket=source_bucket, Key=destination_key
        )

        # --- Construct Published S3 URI ---
        published_s3_uri = f"s3://{source_bucket}/{destination_key}"
        print(f"Successfully published data to {published_s3_uri}")

        return {"statusCode": 200, "published_s3_uri": published_s3_uri}
    except Exception as e:
        print(f"Error: {e}")
        # Re-raise the exception to fail the Lambda execution
        raise e
