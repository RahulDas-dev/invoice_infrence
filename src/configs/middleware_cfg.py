from typing import Any, Optional

from pydantic import Field, NonNegativeInt, PositiveInt, computed_field
from pydantic_settings import BaseSettings
from sqlalchemy import URL


class DatabaseConfig(BaseSettings):
    DB_HOST: str = Field(
        description="Hostname or IP address of the database server.",
        default="localhost",
    )

    DB_PORT: PositiveInt = Field(
        description="Port number for database connection.",
        default=5432,
    )

    DB_USERNAME: str = Field(
        description="Username for database authentication.",
        default="postgres",
    )

    DB_PASSWORD: str = Field(
        description="Password for database authentication.",
        default="",
    )

    DB_DATABASE: str = Field(
        description="Name of the database to connect to.",
        default="invoice_infer.db",
    )

    SQLALCHEMY_DATABASE_URI_SCHEME: str = Field(
        description="Database URI scheme for SQLAlchemy connection.",
        default="postgresql+pg8000",
    )

    SQLALCHEMY_POOL_SIZE: NonNegativeInt = Field(
        description="Maximum number of database connections in the pool.",
        default=30,
    )

    SQLALCHEMY_MAX_OVERFLOW: NonNegativeInt = Field(
        description="Maximum number of connections that can be created beyond the pool_size.",
        default=10,
    )

    SQLALCHEMY_POOL_RECYCLE: NonNegativeInt = Field(
        description="Number of seconds after which a connection is automatically recycled.",
        default=3600,
    )

    SQLALCHEMY_POOL_PRE_PING: bool = Field(
        description="If True, enables connection pool pre-ping feature to check connections.",
        default=False,
    )

    SQLALCHEMY_ECHO: bool | str = Field(
        description="If True, SQLAlchemy will log all SQL statements.",
        default=False,
    )

    @property
    def dbtype(self) -> str:
        if "postgresql" in self.SQLALCHEMY_DATABASE_URI_SCHEME:
            return "postgresql"
        if "mysql" in self.SQLALCHEMY_DATABASE_URI_SCHEME:
            return "mysql"
        if "sqlite" in self.SQLALCHEMY_DATABASE_URI_SCHEME:
            return "sqlite"
        return "unknown"

    @computed_field
    def SQLALCHEMY_ENGINE_OPTIONS(self) -> dict[str, Any]:  # noqa: N802
        if self.dbtype == "sqlite":
            return {}
        return {
            "pool_size": self.SQLALCHEMY_POOL_SIZE,
            "max_overflow": self.SQLALCHEMY_MAX_OVERFLOW,
            "pool_recycle": self.SQLALCHEMY_POOL_RECYCLE,
            "pool_pre_ping": self.SQLALCHEMY_POOL_PRE_PING,
            "connect_args": {"options": "-c timezone=UTC"},
        }

    @computed_field
    def SQLALCHEMY_DATABASE_URI(self) -> str:  # noqa: N802
        drivername_ = self.SQLALCHEMY_DATABASE_URI_SCHEME
        username_ = None if self.dbtype == "sqlite" else self.DB_USERNAME
        password_ = None if self.dbtype == "sqlite" else self.DB_PASSWORD
        host_ = None if self.dbtype == "sqlite" else self.DB_HOST
        port_ = None if self.dbtype == "sqlite" else self.DB_PORT
        return URL(
            drivername=drivername_,
            username=username_,
            password=password_,
            host=host_,
            port=port_,
            database=self.DB_DATABASE,
            query={},  # type: ignore
        ).render_as_string(hide_password=True)


class LoggingConfig(BaseSettings):
    """
    Configuration for application logging
    """

    LOG_LEVEL: str = Field(
        description="Logging level, default to INFO. Set to ERROR for production environments.",
        default="INFO",
    )
    LOG_FILE: Optional[str] = Field(
        description="File path for log output.",
        default=None,
    )
    LOG_FILE_MAX_SIZE: PositiveInt = Field(
        description="Maximum file size for file rotation retention, the unit is megabytes (MB)",
        default=20,
    )
    LOG_FILE_BACKUP_COUNT: PositiveInt = Field(
        description="Maximum file backup count file rotation retention",
        default=5,
    )
    LOG_FORMAT: str = Field(
        description="Format string for log messages",
        default="%(asctime)s.%(msecs)03d %(levelname)s [%(threadName)s] [%(filename)s:%(lineno)d] - %(message)s",
    )

    LOG_DATEFORMAT: Optional[str] = Field(
        description="Date format string for log timestamps",
        default=None,
    )
