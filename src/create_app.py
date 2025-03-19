# ruff: noqa: LOG015
import logging
import time

from app import InvoiceInferApp
from blueprints import api
from configs import app_config


def _register_extensions(app: InvoiceInferApp, bebug: bool = False) -> None:
    from src.extensions import (
        DatabaseExtension,
        HealthExtension,
        LifespanExtension,
        LoadEnvExtension,
        LoggingExtension,
        TimezoneExtension,
        WarningExtension,
        WerkzeugExtension,
    )

    extensions = [
        TimezoneExtension,
        WarningExtension,
        LoggingExtension,
        WerkzeugExtension,
        DatabaseExtension,
        LifespanExtension,
        HealthExtension,
        LoadEnvExtension,
    ]
    for extension in extensions:
        if extension.is_disabled:
            logging.info(f"Skipping {extension.__name__}")
            continue
        logging.info(f"Registering {extension.__name__} ...")
        start_time = time.perf_counter()
        extension.register(app)
        if bebug:
            logging.info(
                f"{extension.__name__} registered , latency: {round((time.perf_counter() - start_time) * 1000, 3)}ms"
            )


def _register_blueprints(app: InvoiceInferApp, debug: bool = False) -> None:
    api.init_app(app)


def create_application() -> InvoiceInferApp:
    start_time = time.perf_counter()
    app = InvoiceInferApp(__name__)
    app.config.from_mapping(app_config.model_dump())
    debug_ = app.config.get("DEBUG", False)
    _register_extensions(app, debug_)
    _register_blueprints(app, debug_)
    if debug_:
        latency = round((time.perf_counter() - start_time) * 1000, 3)
        logging.info(f"Application created in {latency} seconds")
    return app
