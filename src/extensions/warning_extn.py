from app import InvoiceInferApp

from .base import BaseExtension


class WarningExtension(BaseExtension):
    @classmethod
    def is_enabled(cls) -> bool:
        return False

    @classmethod
    def register(cls, app: InvoiceInferApp) -> None:  # noqa: ARG003
        import warnings

        warnings.simplefilter("ignore", ResourceWarning)
