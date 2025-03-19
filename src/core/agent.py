import logging
from pathlib import Path
from typing import Dict, Tuple

from pdf2image import convert_from_path

from .llm import MultiPageAgent, SinglePageAgent

logger = logging.getLogger(__name__)


class InvoiceAgent:
    def __init__(self, propeler_path: str, output_folder: str, max_width: int = 1120, max_height: int = 1120):
        self.propeler_path = propeler_path
        self.output_folder = output_folder
        self.max_width, self.max_height = max_width, max_height

    def run(self, pdf_path: str | Path) -> Tuple[Dict[str, str], Path]:
        filename = Path(pdf_path).stem
        output_folder = Path(self.output_folder) / Path(filename)
        Path.mkdir(output_folder, exist_ok=True)
        images = convert_from_path(pdf_path, poppler_path=self.propeler_path, fmt="png")
        for index, image in enumerate(images):
            page_no = index + 1
            width, height = image.size
            logger.info(f"Processing Images of shape {width}, {height}")
            if width < height and height > self.max_height:
                new_height = self.max_height
                new_width = int(new_height * (width / height))
                new_image = image.resize((new_width, new_height))
                logger.info(f"Resized Images to shape {new_image.size}")
                new_image.save(output_folder / f"Page_{page_no:02}.png", "PNG")
            elif width > height and width > self.max_width:
                new_width = self.max_width
                new_height = int(new_width * (height / width))
                new_image = image.resize((new_width, new_height))
                logger.info(f"Resized Images to shape {new_image.size}")
                new_image.save(output_folder / f"Page_{page_no:02}.png", "PNG")
            else:
                image.save(output_folder / f"Page_{page_no:02}.png", "PNG")

        if len(images) == 1:
            logger.info(f"Processing Single Page Invoice : {filename}")
            filename = next(file.resolve() for file in output_folder.rglob("*.png"))
            return SinglePageAgent().run(filename), output_folder
        logger.info(f"Processing Multiple Page Invoice : {filename}")
        return MultiPageAgent().run(output_folder), output_folder
