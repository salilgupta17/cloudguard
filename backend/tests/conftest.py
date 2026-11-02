"""
Pytest Fixtures for CloudGuard DR Engine Testing.
Sets up isolated temporary databases for primary and isolated test targets.
"""
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from backend.app.models.base import Base
from backend.app.data.seeder import seed_synthetic_database
from backend.app.storage.local import LocalFileSystemStorage


@pytest.fixture
def tmp_dr_dirs(tmp_path: Path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return {
        "backup_dir": backup_dir,
        "primary_db_path": tmp_path / "primary_test.db",
        "restore_db_path": tmp_path / "isolated_sandbox_test.db",
    }


@pytest.fixture
def seeded_primary_db(tmp_dr_dirs):
    primary_url = f"sqlite:///{tmp_dr_dirs['primary_db_path'].as_posix()}"
    engine = create_engine(primary_url)
    Base.metadata.create_all(engine)

    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        counts = seed_synthetic_database(
            session=session,
            num_orgs=2,
            users_per_org=3,
            orders_per_user=2
        )

    return {
        "url": primary_url,
        "engine": engine,
        "counts": counts,
        "db_path": tmp_dr_dirs["primary_db_path"]
    }


@pytest.fixture
def isolated_sandbox_db_url(tmp_dr_dirs):
    return f"sqlite:///{tmp_dr_dirs['restore_db_path'].as_posix()}"


@pytest.fixture
def local_storage(tmp_dr_dirs):
    return LocalFileSystemStorage(base_dir=tmp_dr_dirs["backup_dir"])
