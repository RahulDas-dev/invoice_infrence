from flask import Response

from app import InvoiceInferApp

# from library import UniqueIdGenerator
from .base import BaseExtension


class LifespanExtension(BaseExtension):
    @classmethod
    def register(cls, app: InvoiceInferApp) -> None:
        # @app.before_request
        # def before_request() -> None:
        #    UniqueIdGenerator.increment_thread_recycles()

        @app.after_request
        def after_request(response: Response) -> Response:
            response.headers.add("X-Version", app.config.get("API_VERSION"))
            response.headers.add("X-Env", app.config.get("DEPLOYMENT_ENV"))
            response.headers.add("X-Timezn", app.config.get("TIMEZONE"))
            response.headers.add("X-Language", app.config.get("LANGUAGE"))
            return response
