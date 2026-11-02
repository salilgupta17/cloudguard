"""
RecoveryReport REST API Endpoints.
APIs to list, view, and download automated disaster recovery reports in JSON, HTML, and PDF.
Strictly reporting-only; no remediation recommendations or execution buttons.
"""
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response, HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.recovery_report import RecoveryReport
from app.models.recovery_test import RecoveryTest
from app.models.backup_metadata import BackupMetadata
from app.models.validation_result import ValidationResult
from app.schemas.recovery_report import RecoveryReportCreate, RecoveryReportResponse
from app.core.logging import logger
from report_service import ReportGenerator, LocalReportStorage


router = APIRouter(prefix="/api/v1/reports", tags=["Recovery Reports"])
storage = LocalReportStorage(base_dir=settings.REPORTS_DIR)


def _get_or_generate_report_data(report_id: str, db: Session):
    """
    Retrieves stored JSON report data, or dynamically generates from database records.
    """
    # 1. Check if report_id matches a RecoveryReport or RecoveryTest
    rec = db.query(RecoveryReport).filter(
        (RecoveryReport.report_id == report_id) | (RecoveryReport.test_id == report_id)
    ).first()

    test = db.query(RecoveryTest).filter(
        (RecoveryTest.test_id == report_id) | (RecoveryTest.test_id == (rec.test_id if rec else ""))
    ).first()

    if not rec and not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disaster recovery report '{report_id}' not found."
        )

    # 2. Check if already stored on disk
    target_id = test.test_id if test else rec.test_id
    if storage.report_exists(target_id, "json"):
        raw_json = storage.get_report(target_id, "json")
        try:
            return json.loads(raw_json)
        except Exception:
            pass

    # 3. Dynamically assemble ReportData from database records
    backup_meta = None
    if test and test.backup_id:
        backup_meta = db.query(BackupMetadata).filter(BackupMetadata.backup_id == test.backup_id).first()

    val_results = db.query(ValidationResult).filter(ValidationResult.test_id == target_id).all()
    checks_list = []
    for vr in val_results:
        try:
            chk_data = json.loads(vr.details_json)
            checks_list.append(chk_data)
        except Exception:
            checks_list.append({
                "check_name": vr.validation_type,
                "status": "PASS" if vr.passed else "FAIL",
                "duration": 0.0,
                "observed_value": None,
                "expected_value": None,
                "error_message": None if vr.passed else "Validation failed"
            })

    rep_gen = ReportGenerator(storage=storage)
    report_data = rep_gen.build_report_data(
        application_name=test.application_name if test else "demo-banking-application",
        test_id=target_id,
        backup_id=test.backup_id if test else (backup_meta.backup_id if backup_meta else "UNKNOWN"),
        backup_created_at=backup_meta.created_at if backup_meta else (test.started_at if test else None),
        test_started_at=test.started_at if test else (rec.created_at if rec else None),
        test_completed_at=test.completed_at if test else (rec.created_at if rec else None),
        restore_job_status="SUCCESS" if (test and test.status == "SUCCESS") else ("FAILED" if test else "INCOMPLETE"),
        validation_results={"checks": checks_list, "overall_passed": all(v.passed for v in val_results)},
        restore_duration_seconds=test.restore_duration_seconds if (test and test.restore_duration_seconds) else (rec.rto_seconds if rec else 0.0),
        target_rto_seconds=settings.TARGET_RTO_SECONDS,
        target_rpo_minutes=settings.TARGET_RPO_MINUTES,
        error_details=test.error_details if test else None,
        logs=test.logs if test else None
    )

    # Persist artifacts in JSON, HTML, and PDF
    rep_gen.generate_all_formats(report_data)
    return report_data.to_dict()


@router.post("", response_model=RecoveryReportResponse, status_code=status.HTTP_201_CREATED)
def create_recovery_report(payload: RecoveryReportCreate, db: Session = Depends(get_db)):
    """Stores the final executive recovery compliance report for a drill."""
    test = db.query(RecoveryTest).filter(RecoveryTest.test_id == payload.test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecoveryTest with ID '{payload.test_id}' not found."
        )

    existing = db.query(RecoveryReport).filter(RecoveryReport.test_id == payload.test_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"RecoveryReport already exists for test '{payload.test_id}'."
        )

    record = RecoveryReport(
        report_id=str(uuid.uuid4()),
        test_id=payload.test_id,
        status=payload.status,
        rto_seconds=payload.rto_seconds,
        rpo_minutes=payload.rpo_minutes,
        summary=payload.summary
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(f"Generated RecoveryReport [{record.report_id}] with status {record.status}")
    return record


@router.get("", response_model=List[RecoveryReportResponse])
def list_reports(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Lists historical recovery reports."""
    query = db.query(RecoveryReport)
    if status:
        query = query.filter(RecoveryReport.status == status)
    return query.order_by(RecoveryReport.created_at.desc()).limit(limit).all()


@router.get("/by-test/{test_id}", response_model=RecoveryReportResponse)
def get_report_by_test(test_id: str, db: Session = Depends(get_db)):
    """Retrieves recovery report database summary for a specific test drill."""
    record = db.query(RecoveryReport).filter(RecoveryReport.test_id == test_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecoveryReport for test '{test_id}' not found."
        )
    return record


@router.get("/{report_id}")
def view_report_json(report_id: str, db: Session = Depends(get_db)):
    """
    Views the comprehensive 15-field Disaster Recovery Report in JSON format.
    """
    return _get_or_generate_report_data(report_id, db)


@router.get("/{report_id}/html", response_class=HTMLResponse)
def view_report_html(report_id: str, db: Session = Depends(get_db)):
    """
    Renders human-readable executive disaster recovery report in HTML.
    """
    data = _get_or_generate_report_data(report_id, db)
    target_id = data.get("test_id", report_id)
    html_content = storage.get_report(target_id, "html")
    return HTMLResponse(content=html_content)


@router.get("/{report_id}/pdf")
def view_report_pdf(report_id: str, db: Session = Depends(get_db)):
    """
    Views or downloads executive disaster recovery report in PDF format.
    """
    data = _get_or_generate_report_data(report_id, db)
    target_id = data.get("test_id", report_id)
    pdf_bytes = storage.get_report(target_id, "pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=cloudguard-dr-report-{target_id[:8]}.pdf"}
    )


@router.get("/{report_id}/download")
def download_report_file(
    report_id: str,
    format: str = Query(default="pdf", pattern="^(pdf|html|json)$"),
    db: Session = Depends(get_db)
):
    """
    Downloads the disaster recovery report file in requested format ('pdf', 'html', 'json').
    """
    data = _get_or_generate_report_data(report_id, db)
    target_id = data.get("test_id", report_id)

    fmt = format.lower()
    content = storage.get_report(target_id, fmt)

    if fmt == "pdf":
        media_type = "application/pdf"
        body = content
    elif fmt == "html":
        media_type = "text/html"
        body = content.encode("utf-8") if isinstance(content, str) else content
    else:
        media_type = "application/json"
        body = content.encode("utf-8") if isinstance(content, str) else content

    filename = f"cloudguard-dr-report-{target_id[:8]}.{fmt}"
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
