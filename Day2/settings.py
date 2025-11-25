# src/inventory_system/config/settings.py
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    db_host: str = "localhost"
    db_port: int = 1433
    db_name: str = "inventory"
    db_user: str = "sa"
    db_password: str
    db_driver: str = "ODBC Driver 18 for SQL Server"

    # Application
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    # Security
    secret_key: str

    class Config:
        env_file = ".env"


settings = Settings()
