from flask_restx import Api

from .process import ns as process_ns

api = Api(
    title="Process Document API",
    version="1.0.0",
    description="Process Uploaded Document Extracts Invoice Information",
    doc="/docs/",
)

api.add_namespace(process_ns)
