# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.inventory_system.main import app
from src.inventory_system.config.database import db_manager
from src.inventory_system.models.base import Base

# Test database
TEST_DATABASE_URL = (
    "mssql+pyodbc://sa:YourStrong!Passw0rd@localhost:1433/inventory_test"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
)


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def test_session(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(test_session):
    """FastAPI test client using the test database session."""

    def override_get_db():
        try:
            yield test_session
        finally:
            pass

    # NOTE: In your FastAPI app, ensure this key matches the dependency you want to override.
    app.dependency_overrides[db_manager.get_session] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
