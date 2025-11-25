# src/inventory_system/config/database.py
import urllib.parse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .settings import settings


class DatabaseManager:
    def __init__(self) -> None:
        self.engine = None
        self.SessionLocal = None

    def setup(self) -> None:
        """Initialize database connection"""
        # URL encode the password for special characters
        encoded_password = urllib.parse.quote_plus(settings.db_password)

        connection_string = (
            f"mssql+pyodbc://{settings.db_user}:{encoded_password}@"
            f"{settings.db_host}:{settings.db_port}/{settings.db_name}?"
            f"driver={settings.db_driver}&TrustServerCertificate=yes"
        )

        self.engine = create_engine(connection_string, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self):
        """Get database session"""
        if not self.SessionLocal:
            self.setup()
        return self.SessionLocal()

    def create_tables(self) -> None:
        """Create all tables"""
        from ..models.base import Base

        Base.metadata.create_all(bind=self.engine)


# Global database manager instance
db_manager = DatabaseManager()
