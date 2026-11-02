"""Report Service Package."""
from .models import ReportData, ConfiguredTargets, DetectedFailure
from .storage import ReportStorageInterface, LocalReportStorage, S3ReportStorage
from .html_generator import HtmlReportGenerator
from .pdf_generator import PdfReportGenerator
from .generator import ReportGenerator
from .formatters import ReportFormatter

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
