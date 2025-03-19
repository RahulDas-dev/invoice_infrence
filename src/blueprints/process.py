import threading
from pathlib import Path
from typing import Optional, Tuple

from flask import current_app
from flask_restx import Namespace, Resource, abort, fields, reqparse
from flask_restx._http import HTTPStatus
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from core.agent import InvoiceAgent

from .signals import house_keeping

ns = Namespace("process", description="Process Uploaded Document Extracts Invoice Information")

upload_parser = reqparse.RequestParser()

upload_parser.add_argument("document", type=FileStorage, location="files", required=True)

item_model = ns.model(
    "item",
    {
        "price": fields.String,
        "quantity": fields.String,
        "description": fields.String,
    },
)

invoice_model = ns.model(
    "invoice_details",
    {
        "invoice_number": fields.String,
        "invoice_date": fields.String,
        "seller_name": fields.String,
        "buyer_name": fields.String,
        "total_amount": fields.String,
        "items": fields.List(fields.Nested(item_model)),
        "page_no": fields.Integer,
    },
)
model = ns.model("Invoice", {"invoice": fields.List(fields.Nested(invoice_model))})


@ns.route("/", endpoint="process")
class Upload(Resource):
    def _allowed_file(self, filename: Optional[str]) -> Tuple[Optional[str], bool]:
        if filename is None:
            return None, False
        file_extension = filename.rsplit(".", 1)[1].lower() if "." in filename else None
        return file_extension, file_extension in current_app.config["ALLOWED_EXTENSIONS"]

    def _save_document(self, document: FileStorage) -> Path:
        if document.filename is None:
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Error While Saving Document , File Name not Found")
        safe_filename = secure_filename(document.filename)
        save_path = Path(current_app.config["TMP_PDF_PATH"]) / Path(safe_filename)
        try:
            document.save(save_path)
            ns.logger.info(f"Document temporaryly saved at {save_path!s}")
        except Exception as err:
            ns.logger.error(f"Error While Saving Document {err!s}")
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Error While Saving Document")
        return save_path

    @ns.marshal_with(model, code=HTTPStatus.CREATED)
    @ns.doc(
        responses={
            201: "Success",
            400: "Invalid File Format",
            500: "Error While Saving Document",
        }
    )
    @ns.expect(upload_parser)
    def post(self) -> tuple:
        args = upload_parser.parse_args()
        document = args["document"]
        if document is None or not isinstance(document, FileStorage) or document.filename is None:
            return abort(HTTPStatus.BAD_REQUEST, "Invalid File Object")
        # Check if the file is allowed
        file_extn, is_allowed = self._allowed_file(document.filename)
        if not is_allowed:
            ns.logger.error("Invalid File Format")
            return abort(HTTPStatus.BAD_REQUEST, "Invalid File Format")
        # Save the document
        save_path = self._save_document(document)
        # Process the invoice
        try:
            propeller_path_ = current_app.config["PROPELLER_PATH"]
            tmp_image_path_ = current_app.config["TMP_IMG_PATH"]
            max_width_ = current_app.config["MAX_IMG_WIDTH"]
            max_height_ = current_app.config["MAX_IMG_HEIGHT"]
            data, img_temp_dir = InvoiceAgent(
                propeler_path=propeller_path_,
                output_folder=tmp_image_path_,
                max_width=max_width_,
                max_height=max_height_,
            ).run(save_path)
        except Exception:
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Error While Processing Invoice")
        # house_keeping.send(self, file_path=str(save_path))
        if current_app.config.get("CLEANUP_TEMP_FILES", False):
            threading.Thread(
                target=house_keeping.send,
                name="house_keeping_thread",
                args=[self],
                kwargs={"file_paths": [save_path, img_temp_dir]},
            ).start()
        return data, 201
