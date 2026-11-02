"""
Pytest Fixtures for CloudGuard Phase 1 Test Suite.
"""
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Imports from cloudguard-api package
from cloudguard_api import app as cloudguard_app, Base as CGBase, get_db as get_cg_db

# Imports from demo_app package
from demo_app.main import app as demo_app_fastapi, Base as DemoBase, get_db as get_demo_db


@pytest.fixture(scope="session")
def tmp_test_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("cloudguard_tests")


@pytest.fixture
def cg_db_session(tmp_test_dir):
    """Provides an isolated SQLite database session for CloudGuard API testing."""
    db_file = tmp_test_dir / "test_cloudguard.db"
    engine = create_engine(f"sqlite:///{db_file.as_posix()}", connect_args={"check_same_thread": False})
    CGBase.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        CGBase.metadata.drop_all(bind=engine)


@pytest.fixture
def cg_client(cg_db_session):
    """FastAPI TestClient for CloudGuard API overriding database dependency."""
    def override_get_db():
        try:
            yield cg_db_session
        finally:
            pass

    cloudguard_app.dependency_overrides[get_cg_db] = override_get_db
    with TestClient(cloudguard_app) as client:
        yield client
    cloudguard_app.dependency_overrides.clear()


@pytest.fixture
def demo_client(tmp_test_dir):
    """FastAPI TestClient for Demo Application."""
    demo_file = tmp_test_dir / "test_demo_app.db"
    demo_engine = create_engine(f"sqlite:///{demo_file.as_posix()}", connect_args={"check_same_thread": False})
    DemoBase.metadata.create_all(bind=demo_engine)
    DemoSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=demo_engine)

    def override_demo_get_db():
        session = DemoSessionLocal()
        try:
            yield session
        finally:
            session.close()

    demo_app_fastapi.dependency_overrides[get_demo_db] = override_demo_get_db
    with TestClient(demo_app_fastapi) as client:
        yield client
    demo_app_fastapi.dependency_overrides.clear()


@pytest.fixture
def dr_env(tmp_path):
    from demo_app.models.base import Base as BankingBase
    from demo_app.seeder import seed_banking_data
    from app.dr.local_provider import LocalPostgresDisasterRecoveryProvider

    backup_dir = tmp_path / "dr_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Primary Database (Seeded Source)
    primary_file = tmp_path / "primary_source.db"
    primary_url = f"sqlite:///{primary_file.as_posix()}"
    p_engine = create_engine(primary_url)
    BankingBase.metadata.create_all(p_engine)

    SessionP = sessionmaker(bind=p_engine)
    with SessionP() as sp:
        seed_banking_data(sp, customers_count=3)

    # Isolated Target Database (New Sandbox)
    target_file = tmp_path / "isolated_sandbox_drill.db"
    target_url = f"sqlite:///{target_file.as_posix()}"

    provider = LocalPostgresDisasterRecoveryProvider(backup_dir=backup_dir)

    return {
        "backup_dir": backup_dir,
        "primary_url": primary_url,
        "target_url": target_url,
        "provider": provider,
        "primary_file": primary_file,
        "target_file": target_file
    }
