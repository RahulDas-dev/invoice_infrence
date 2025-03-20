import io
import os
from pathlib import Path
from typing import Tuple

from PIL import Image


def get_secret_keys() -> dict:
    return {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_KEY"),
        "region_name": os.getenv("REGION_NAME"),
    }


def image_to_byte_string(image_path: str | Path) -> Tuple[bytes, str]:
    image = Image.open(image_path)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")  # or 'JPEG', etc.
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr, image.get_format_mimetype() or "image/png"
