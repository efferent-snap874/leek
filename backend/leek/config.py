from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    celery_broker_url: str = Field(validation_alias="CELERY_BROKER_URL")
    database_url: str = Field(
        default="sqlite+aiosqlite:///leek.db",
        validation_alias="DATABASE_URL",
    )
    retention_days: int = 7
    port: int = 8585
    host: str = "0.0.0.0"

    model_config = {"env_prefix": "LEEK_"}


settings = Settings()
