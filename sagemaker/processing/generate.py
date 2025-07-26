import os
import boto3
import joblib
import pandas as pd
import sys
from urllib.parse import urlparse
import torch
import pickle
import io


class CPU_Unpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == "torch.storage" and name == "_load_from_bytes":
            return lambda b: torch.load(io.BytesIO(b), map_location="cpu")
        else:
            return super().find_class(module, name)


def main():
    """
    Main function to generate synthetic data using a pre-trained CTGAN model.
    """
    try:
        print("--- STARTING PROCESSING JOB ---")
        
        # --- Get Parameters from Environment Variables ---
        num_rows_str = os.environ.get("NUM_ROWS")
        model_path = os.environ.get("MODEL_PATH")
        job_name = os.environ.get("JOB_NAME")
        
        print(f"ENV VAR NUM_ROWS: {num_rows_str}")
        print(f"ENV VAR MODEL_PATH: {model_path}")
        print(f"ENV VAR JOB_NAME: {job_name}")

        if not all([num_rows_str, model_path, job_name]):
            raise ValueError("Missing one or more required environment variables: NUM_ROWS, MODEL_PATH, JOB_NAME")

        num_rows = int(num_rows_str)

        # --- Load Model ---
        print(f"Attempting to load model from: {model_path}")
        if model_path.startswith("s3://"):
            s3_client = boto3.client("s3")
            parsed_uri = urlparse(model_path)
            bucket = parsed_uri.netloc
            key = parsed_uri.path.lstrip('/')
            local_model_path = "/tmp/model.pkl"
            print(f"Downloading s3://{bucket}/{key} to {local_model_path}...")
            s3_client.download_file(bucket, key, local_model_path)
            with open(local_model_path, "rb") as f:
                model = CPU_Unpickler(f).load()
            print("Model downloaded and loaded successfully.")
        else:
            with open(model_path, "rb") as f:
                model = CPU_Unpickler(f).load()
            print("Model loaded from local path successfully.")

        # --- Generate Data ---
        print(f"Generating {num_rows} rows of synthetic data...")
        synthetic_data = model.sample(num_rows=num_rows)
        print("Synthetic data generated successfully.")

        # --- Save data ---
        # The script saves the file to this local path inside the container.
        # SageMaker will then automatically upload the contents of this directory to S3.
        output_dir = "/opt/ml/processing/output"
        if not os.environ.get("SM_CURRENT_HOST"):
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
        output_path = f"{output_dir}/{job_name}.parquet"
        print(f"Saving synthetic data to {output_path}...")
        synthetic_data.to_parquet(output_path, index=False)
        print("Data saved successfully.")
        
        print("--- PROCESSING JOB SUCCEEDED ---")

    except Exception as e:
        # Use sys.stderr to ensure the error is captured in CloudWatch logs
        print(f"--- PROCESSING JOB FAILED ---", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()