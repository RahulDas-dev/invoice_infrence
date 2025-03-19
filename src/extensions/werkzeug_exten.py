from werkzeug.middleware.proxy_fix import ProxyFix

from app import InvoiceInferApp

from .base import BaseExtension


class WerkzeugExtension(BaseExtension):
    @classmethod
    def register(cls, app: InvoiceInferApp) -> None:
        app.wsgi_app = ProxyFix(app.wsgi_app)
