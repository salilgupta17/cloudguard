"""Report Service Package (app alias)."""
from report_service import (
    ReportData,
    ConfiguredTargets,
    DetectedFailure,
    ReportStorageInterface,
    LocalReportStorage,
    S3ReportStorage,
    HtmlReportGenerator,
    PdfReportGenerator,
    ReportGenerator,
    ReportFormatter
)

__all__ = [
    "ReportData",
    "ConfiguredTargets",
    "DetectedFailure",
    "ReportStorageInterface",
    "LocalReportStorage",
    "S3ReportStorage",
    "HtmlReportGenerator",
    "PdfReportGenerator",
    "ReportGenerator",
    "ReportFormatter"
]
