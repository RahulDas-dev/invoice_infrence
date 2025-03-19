from dotenv import load_dotenv

from app import InvoiceInferApp

from .base import BaseExtension


class LoadEnvExtension(BaseExtension):
    @classmethod
    def register(cls, app: InvoiceInferApp) -> None:  # noqa: ARG003
        load_dotenv()
