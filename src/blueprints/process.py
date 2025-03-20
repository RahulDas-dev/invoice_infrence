import threading
from pathlib import Path
from typing import Optional, Tuple

from flask import current_app
from flask_restx import Namespace, Resource, abort, fields, reqparse
from flask_restx._http import HTTPStatus
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from core.llm import MultiPageAgent
from core.pdf_to_image import PdfToImageConverter

from .signals import house_keeping

ns = Namespace("process", description="Process Uploaded Document Extracts Invoice Information")

upload_parser = reqparse.RequestParser()

upload_parser.add_argument("document", type=FileStorage, location="files", required=True)

item_model = ns.model(
    "item",
    {
        "slno": fields.Integer,
        "price": fields.String,
        "quantity": fields.String,
        "description": fields.String,
        "currency": fields.String,
    },
)

company_model = ns.model(
    "company",
    {
        "name": fields.String,
        "gst_no": fields.String,
        "pan_no": fields.String,
        "address": fields.String,
        "phone_number": fields.String,
        "email": fields.String,
    },
)

tax_component = ns.model(
    "tax_components",
    {
        "CGST": fields.Float,
        "SGST": fields.Float,
        "IGST": fields.Float,
    },
)
invoice_model = ns.model(
    "invoice_details",
    {
        "invoice_number": fields.String,
        "invoice_date": fields.String,
        "seller_details": fields.Nested(company_model),
        "buyer_details": fields.Nested(company_model),
        "items": fields.List(fields.Nested(item_model)),
        "total_tax": fields.Nested(tax_component),
        "total_charge": fields.Float,
        "total_discount": fields.Float,
        "total_amount": fields.Float,
        "amount_paid": fields.Float,
        "amount_due": fields.Float,
        "page_no": fields.Integer,
    },
)
model = ns.model("Invoice", {"details": fields.List(fields.Nested(invoice_model))})


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
            img_directory = PdfToImageConverter(
                propeler_path=propeller_path_,
                output_folder=tmp_image_path_,
                max_width=max_width_,
                max_height=max_height_,
            ).run(save_path)
        except Exception:
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Error pdf 2 Image Convversion")
        if img_directory is None:
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Error pdf 2 Image Convversion")
        try:
            data, dadta_str = MultiPageAgent().run(img_directory)
        except Exception:
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Error LLM Agent Processing")
        if current_app.config.get("CLEANUP_TEMP_FILES", False):
            threading.Thread(
                target=house_keeping.send,
                name="house_keeping_thread",
                args=[self],
                kwargs={"file_paths": [save_path, img_directory]},
            ).start()
        return data, 201
