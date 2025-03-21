import logging
import sys
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import flask

from app import InvoiceInferApp

from .base import BaseExtension


def get_request_id() -> str:
    if getattr(flask.g, "request_id", None):
        return flask.g.request_id

    new_uuid = uuid.uuid4().hex[:10]
    flask.g.request_id = new_uuid

    return new_uuid


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.req_id = get_request_id() if flask.has_request_context() else ""
        return True


class LoggingExtension(BaseExtension):
    @classmethod
    def register(cls, app: InvoiceInferApp) -> None:
        log_handlers: list[logging.Handler] = []
        log_file = app.config.get("LOG_FILE")
        if log_file:
            log_dir = Path(log_file).parent
            if not Path(log_file).parent.is_dir():
                Path.mkdir(log_dir, parents=True, exist_ok=True)
            maxbytes_ = int(app.config.get("LOG_FILE_MAX_SIZE", 20)) * 1024 * 1024
            backup_count_ = app.config.get("LOG_FILE_BACKUP_COUNT", 5)
            log_handlers.append(
                RotatingFileHandler(
                    filename=log_file,
                    maxBytes=maxbytes_,
                    backupCount=backup_count_,
                )
            )

        # Always add StreamHandler to log to console
        sh = logging.StreamHandler(sys.stdout)
        sh.addFilter(RequestIdFilter())
        log_handlers.append(sh)

        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.basicConfig(
            level=app.config.get("LOG_LEVEL", logging.INFO),
            format=app.config.get("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            datefmt=app.config.get("LOG_DATE_FORMAT"),
            handlers=log_handlers,
            force=True,
        )
        app_tz: str = app.config.get("TIMEZONE", "UTC")
        if app_tz:
            from datetime import datetime
            from time import struct_time

            import pytz

            timezone = pytz.timezone(app_tz)

            def time_converter(seconds: Optional[float]) -> struct_time:
                if seconds is None:
                    return datetime.now(tz=timezone).timetuple()
                return datetime.fromtimestamp(seconds, tz=timezone).timetuple()

            for handler in logging.root.handlers:
                if handler.formatter:
                    handler.formatter.converter = time_converter
