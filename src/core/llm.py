import copy
import logging
import re
from pathlib import Path

import boto3

from .perser import extract_xml_from_text, parse_invoice
from .prompts import SYSTEM_MESSAGE_1, SYSTEM_MESSAGE_2
from .utility import get_secret_keys

logger = logging.getLogger(__name__)


class SinglePageAgent:
    def __init__(self, retry_limit: int = 3):
        self.MODEL_ID = "us.meta.llama3-2-90b-instruct-v1:0"
        self.runtime = boto3.client("bedrock-runtime", **get_secret_keys())
        self.retry_limit = retry_limit

    def run(self, image_name: Path) -> dict:
        with open(image_name, "rb") as f:
            image = f.read()

        messages = [
            {
                "role": "user",
                "content": [
                    {"image": {"format": "png", "source": {"bytes": image}}},
                    {"text": SYSTEM_MESSAGE_1},
                ],
            },
        ]
        retry_count = self.retry_limit
        invoce_data = {}
        while retry_count > 0:
            response = self.runtime.converse(
                modelId=self.MODEL_ID, messages=messages, inferenceConfig={"maxTokens": 8192}
            )
            response_text = response["output"]["message"]["content"][0]["text"]
            logger.info(f"Retry Count: {retry_count}, LLM Response : {response_text}")
            invoce_data = self._process_invoice(response_text)
            if invoce_data:
                invoce_data["page_no"] = 1
                break
            retry_count -= 1
        return {"invoice": [invoce_data]}

    def _process_invoice(self, raw_text: str) -> dict:
        """Process full text to extract invoice data and additional details."""
        xml_data = extract_xml_from_text(raw_text)
        if xml_data is None:
            return {}
        if xml_data.lower() == "no_invoice":
            return {}
        return parse_invoice(xml_data)


class MultiPageAgent:
    def __init__(self, retry_limit: int = 3):
        self.MODEL_ID = "us.meta.llama3-2-90b-instruct-v1:0"
        self.runtime = boto3.client("bedrock-runtime", **get_secret_keys())
        self.retry_limit = retry_limit

    def sorted_images(self, image_dir: Path) -> list[Path]:
        """Returns a list of PNG files sorted by page number."""
        image_files = list(image_dir.rglob("*.png"))

        # Regex to extract page number
        def extract_page_num(file: Path) -> int:
            match = re.search(r"Page_(\d+)\.png", file.name)
            return int(match.group(1)) if match else 1000000  # Handle non-matching files by placing them at the end

        return sorted(image_files, key=extract_page_num)

    def run(self, image_dir: Path) -> dict:
        item_list = []
        messages = []
        page_no = 0
        for file in self.sorted_images(image_dir):
            page_no += 1
            logger.info(f"Processing Page : {file.resolve()}")
            response_text = self._process_page(file.resolve(), messages)
            if response_text not in [None, "NO_INVOICE", "NEXT_PAGE"]:
                invoice_data = self._process_invoice(copy.deepcopy(response_text))
                if invoice_data not in [None, "NO_INVOICE", "NEXT_PAGE"]:
                    invoice_data["page_no"] = page_no
                    item_list.append(invoice_data)
                messages = []
            else:
                messages.append({"role": "assistant", "content": response_text})
        return {"invoice": item_list}

    def _process_page(self, image_name: Path, messages: list) -> str:
        with open(image_name, "rb") as f:
            image = f.read()

        messages.append(
            {
                "role": "user",
                "content": [
                    {"image": {"format": "png", "source": {"bytes": image}}},
                    {"text": SYSTEM_MESSAGE_2},
                ],
            }
        )
        response = self.runtime.converse(modelId=self.MODEL_ID, messages=messages, inferenceConfig={"maxTokens": 8192})
        return response["output"]["message"]["content"][0]["text"]

    def _process_invoice(self, raw_text: str) -> dict | str | None:
        """Process full text to extract invoice data and additional details."""
        xml_data = extract_xml_from_text(raw_text)
        if xml_data is None:
            return None
        if xml_data.lower() == "no_invoice":
            return "NO_INVOICE"
        if xml_data.lower() == "next_page":
            return "NEXT_PAGE"
        return parse_invoice(xml_data)
