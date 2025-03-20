import logging
from pathlib import Path
from typing import Optional

from pdf2image import convert_from_path
from PIL.Image import Image

logger = logging.getLogger(__name__)


class PdfToImageConverter:
    def __init__(self, propeler_path: str, output_folder: str, max_width: int = 1120, max_height: int = 1120):
        self.propeler_path = propeler_path
        self.output_folder = output_folder
        self.max_width, self.max_height = max_width, max_height
        self._thread_count = 1

    def _get_image_path(self, pdf_path: str | Path) -> Path:
        filename = Path(pdf_path).stem
        return Path(self.output_folder) / Path(filename)

    def _convert_to_image(self, pdf_path: str | Path, fmt: str = "png") -> Path:
        output_folder = self._get_image_path(pdf_path)
        Path.mkdir(output_folder, exist_ok=True)
        images = convert_from_path(pdf_path, poppler_path=self.propeler_path, fmt=fmt)
        for index, image in enumerate(images):
            page_no = index + 1
            page_save_path = output_folder / f"Page_{page_no:02}.png"
            self._resize_and_save(image, page_save_path)
        return output_folder

    def _resize_and_save(self, image: Image, save_path: str | Path) -> None:
        width, height = image.size
        logger.info(f"Processing Images of shape {width}, {height}")
        if width < height and height > self.max_height:
            new_height = self.max_height
            new_width = int(new_height * (width / height))
            new_image = image.resize((new_width, new_height))
            logger.info(f"Resized Images to shape {new_image.size}")
            new_image.save(save_path, "PNG")
        elif width > height and width > self.max_width:
            new_width = self.max_width
            new_height = int(new_width * (height / width))
            new_image = image.resize((new_width, new_height))
            logger.info(f"Resized Images to shape {new_image.size}")
            new_image.save(save_path, "PNG")
        else:
            image.save(save_path, "PNG")

    def run(self, pdf_path: str | Path) -> Optional[Path]:
        try:
            output_folder = self._convert_to_image(pdf_path)
        except Exception as e:
            logger.error(f"Error While Processing Pdf str{e}")
            output_folder = None
        return output_folder
