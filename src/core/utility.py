import os


def get_secret_keys() -> dict:
    return {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_KEY"),
        "region_name": os.getenv("REGION_NAME"),
    }
