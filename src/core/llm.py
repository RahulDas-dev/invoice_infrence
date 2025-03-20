import logging
import re
from pathlib import Path
from string import Template
from typing import Any, Dict, Tuple

from pydantic_ai import Agent, BinaryContent, ModelRetry
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.bedrock import BedrockProvider

from .prompts import SYSTEM_MESSAGE_1, SYSTEM_MESSAGE_2, USER_MESSAGE_1
from .schemas import Invoice, InvoiceData
from .utility import get_secret_keys, image_to_byte_string

logger = logging.getLogger(__name__)


page_template = Template("""
                        Page No $page_no
$page_content
""")


class MultiPageAgent:
    def __init__(self):
        self._agent1 = Agent(
            model=BedrockConverseModel(
                model_name="us.meta.llama3-2-90b-instruct-v1:0",
                provider=BedrockProvider(**get_secret_keys()),
            ),
            system_prompt=SYSTEM_MESSAGE_1,
            result_type=str,
            model_settings={"temperature": 0},
        )

        agent2 = Agent(
            model=OpenAIModel("gpt-4o"),
            system_prompt=SYSTEM_MESSAGE_2,
            result_type=Invoice,
            model_settings={"temperature": 0},
        )

        @agent2.result_validator
        async def validate_result(result: Any) -> Any:
            if isinstance(result, Invoice):
                return result
            return ModelRetry("Final result Format is not Correct ")

        self._agent2 = agent2

    def sorted_images(self, image_dir: Path) -> list[Path]:
        """Returns a list of PNG files sorted by page number."""
        image_files = list(image_dir.rglob("*.png"))

        # Regex to extract page number
        def extract_page_num(file: Path) -> int:
            match = re.search(r"Page_(\d+)\.png", file.name)
            return int(match.group(1)) if match else 1000000  # Handle non-matching files by placing them at the end

        return sorted(image_files, key=extract_page_num)

    def run(self, image_dir: Path) -> Tuple[Dict[str, Any], str]:
        pdf_content, page_no = [], 0
        for file in self.sorted_images(image_dir):
            page_no += 1
            logger.info(f"Agent1 Processing Page : {file.name}")
            img_byte, mimetype = image_to_byte_string(file.resolve())
            input_msg = [
                USER_MESSAGE_1,
                BinaryContent(data=img_byte, media_type=mimetype),
            ]
            result1 = self._agent1.run_sync(input_msg)
            pdf_content.append((page_no, page_template.substitute(page_no=page_no, page_content=result1.data)))
        logger.info(f"Agent1 has completed the processing of {page_no} pages")
        final_result = []
        for p_no, content in pdf_content:
            logger.info(f"Agent2 Processing Page No : {p_no}")
            result2 = self._agent2.run_sync([content])
            if isinstance(result2.data, Invoice):
                final_result.append(result2.data)
        invoice_data = InvoiceData(details=final_result)
        return invoice_data.model_dump(), "\n".join(item for _, item in pdf_content)
