"""
Pytest Fixtures for Banking Application Test Suite.
Uses SQLite in-memory database with StaticPool for fast, zero-lock testing.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from demo_app.database import Base, get_db
from demo_app.models import Customer, Account, Transaction
from demo_app.main import app
from demo_app.seeder import seed_banking_data


@pytest.fixture
def banking_db():
    """Provides a fresh, isolated in-memory database with seeded banking data."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    seed_banking_data(session, customers_count=3)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def banking_client(banking_db):
    """TestClient overriding database session dependency."""
    def override_get_db():
        try:
            yield banking_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
