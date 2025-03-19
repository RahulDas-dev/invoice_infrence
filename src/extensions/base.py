from abc import ABC, abstractmethod
from typing import Any, ClassVar

from app import InvoiceInferApp


class BaseExtension(ABC):
    is_disabled: ClassVar[bool] = False
    registration_order: ClassVar[int] = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        raise TypeError("This class is not meant to be instantiated")

    @classmethod
    @abstractmethod
    def register(cls, app: InvoiceInferApp) -> None:
        raise NotImplementedError("This method must be implemented in a subclass")
