from pathlib import Path

from pydantic import Field, PositiveInt, field_validator
from pydantic_settings import BaseSettings


class FeatureConfig(BaseSettings):
    PROPELLER_PATH: str = Field(description="Path to the propeller model", default="")
    TMP_PDF_PATH: str = Field(description="Path to the invoice model", default="")
    TMP_IMG_PATH: str = Field(description="Path to the temporary image", default="")
    ALLOWED_EXTENSIONS: list[str] = Field(
        description="Allowed extensions for the uploaded files", default_factory=lambda: ["pdf", "PDF"]
    )
    CLEANUP_TEMP_FILES: bool = Field(description="Cleanup temporary files", default=True)
    MAX_IMG_WIDTH: PositiveInt = Field(description="Maximum image width", default=1120)
    MAX_IMG_HEIGHT: PositiveInt = Field(description="Maximum image height", default=1120)

    @field_validator("PROPELLER_PATH", "TMP_PDF_PATH", "TMP_IMG_PATH", mode="before")
    @classmethod
    def validate_directory(cls, value: str) -> str:
        if not Path(value).is_dir():
            raise ValueError(f"{value} is not a valid directory")
        return value
