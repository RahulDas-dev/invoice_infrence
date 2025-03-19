from pydantic_settings import SettingsConfigDict

from .deployment_cfg import DeploymentConfig
from .feature_cfg import FeatureConfig
from .middleware_cfg import DatabaseConfig, LoggingConfig


class InvoiceInferConfig(DeploymentConfig, LoggingConfig, DatabaseConfig, FeatureConfig):
    model_config = SettingsConfigDict(env_file=".config", env_file_encoding="utf-8", extra="ignore")
