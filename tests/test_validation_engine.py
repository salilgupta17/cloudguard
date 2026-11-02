"""
Unit Tests for validation-engine module.
"""
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from validation_engine import DatabaseValidator, ValidationEngine

TestBase = declarative_base()
TestBase.__test__ = False

class SampleRecord(TestBase):
    __tablename__ = "sample_records"
    id = Column(String(36), primary_key=True)
    val = Column(Integer, nullable=False)


def test_database_validator_parity_success(tmp_test_dir):
    p_path = tmp_test_dir / "prim_val.db"
    r_path = tmp_test_dir / "rest_val.db"
    p_url = f"sqlite:///{p_path.as_posix()}"
    r_url = f"sqlite:///{r_path.as_posix()}"

    p_eng = create_engine(p_url)
    r_eng = create_engine(r_url)
    TestBase.metadata.create_all(p_eng)
    TestBase.metadata.create_all(r_eng)

    # Insert identical data
    SessionP = sessionmaker(bind=p_eng)
    SessionR = sessionmaker(bind=r_eng)

    with SessionP() as sp, SessionR() as sr:
        sp.add(SampleRecord(id="1", val=100))
        sp.add(SampleRecord(id="2", val=200))
        sp.commit()

        sr.add(SampleRecord(id="1", val=100))
        sr.add(SampleRecord(id="2", val=200))
        sr.commit()

    validator = DatabaseValidator(p_url, r_url)
    result = validator.validate_schema_and_parity()

    assert result["passed"] is True
    assert result["table_reports"]["sample_records"]["row_count_matched"] is True
    assert result["table_reports"]["sample_records"]["checksum_matched"] is True
    assert len(result["errors"]) == 0


def test_database_validator_detects_data_discrepancy(tmp_test_dir):
    p_path = tmp_test_dir / "prim_disc.db"
    r_path = tmp_test_dir / "rest_disc.db"
    p_url = f"sqlite:///{p_path.as_posix()}"
    r_url = f"sqlite:///{r_path.as_posix()}"

    p_eng = create_engine(p_url)
    r_eng = create_engine(r_url)
    TestBase.metadata.create_all(p_eng)
    TestBase.metadata.create_all(r_eng)

    SessionP = sessionmaker(bind=p_eng)
    SessionR = sessionmaker(bind=r_eng)

    with SessionP() as sp, SessionR() as sr:
        sp.add(SampleRecord(id="1", val=100))
        sp.add(SampleRecord(id="2", val=200))
        sp.commit()

        # Restored DB is missing 1 record (data loss)
        sr.add(SampleRecord(id="1", val=100))
        sr.commit()

    validator = DatabaseValidator(p_url, r_url)
    result = validator.validate_schema_and_parity()

    assert result["passed"] is False
    assert result["table_reports"]["sample_records"]["row_count_matched"] is False
    assert any("row mismatch" in err for err in result["errors"])
