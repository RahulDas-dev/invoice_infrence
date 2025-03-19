import os
import time

from app import InvoiceInferApp

from .base import BaseExtension


class TimezoneExtension(BaseExtension):
    @classmethod
    def set_timezone(cls, timezone: str) -> None:
        os.environ["TZ"] = timezone
        if hasattr(time, "tzset"):
            time.tzset()  # type: ignore

    @classmethod
    def get_timezone(cls) -> str:
        return os.environ.get("TZ", "UTC")

    @classmethod
    def register(cls, app: InvoiceInferApp) -> None:  # noqa: ARG003
        cls.set_timezone("UTC")
