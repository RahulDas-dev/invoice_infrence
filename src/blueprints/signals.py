import logging
from pathlib import Path
from typing import Any, List

from blinker import signal

logger = logging.getLogger(__name__)

house_keeping = signal("clenup_temp_files")


def cleanup_temp_files(sender: Any, file_paths: List[str | Path]) -> None:  # noqa: ARG001
    logger.info("House keeping Going on ...")
    try:
        for f_path in file_paths:
            Path(f_path).unlink()
        logger.info("House keeping Complited")
    except Exception as e:
        logger.error(f"Error while removing file {file_paths}: {e}")


house_keeping.connect(cleanup_temp_files)
