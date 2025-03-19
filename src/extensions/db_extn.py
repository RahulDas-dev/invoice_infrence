from app import InvoiceInferApp
from database import db

from .base import BaseExtension


class DatabaseExtension(BaseExtension):
    @classmethod
    def register(cls, app: InvoiceInferApp) -> None:
        db.init_app(app)
        with app.app_context():
            # db.metadata.create_all(db.engine)
            db.create_all()
