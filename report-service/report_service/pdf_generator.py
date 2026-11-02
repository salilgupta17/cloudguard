"""
PDF Disaster Recovery Report Generator.
Generates structured multi-page PDF executive compliance documents using reportlab.
"""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from .models import ReportData


class PdfReportGenerator:
    """Generates professional executive Disaster Recovery PDF reports."""

    @staticmethod
    def generate(report_data: ReportData) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        normal = styles["Normal"]
        
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Title"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            alignment=0,
            fontName="Helvetica-Bold"
        )

        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=normal,
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#475569")
        )

        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#0369a1"),
            spaceBefore=14,
            spaceAfter=6,
            fontName="Helvetica-Bold"
        )

        badge_style = ParagraphStyle(
            "StatusBadge",
            parent=normal,
            fontSize=12,
            leading=16,
            fontName="Helvetica-Bold",
            alignment=2
        )

        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=normal,
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#334155")
        )

        story = []

        # 1. Header & Verdict Banner
        status_color = colors.HexColor("#16a34a") if report_data.final_status == "PASS" else colors.HexColor("#dc2626")
        if report_data.final_status == "INCOMPLETE":
            status_color = colors.HexColor("#d97706")

        header_table = Table([
            [
                Paragraph("<b>CloudGuard — Disaster Recovery</b>", subtitle_style),
                Paragraph(f"<font color='{status_color.hexval()}'><b>VERDICT: {report_data.final_status}</b></font>", badge_style)
            ],
            [
                Paragraph("Disaster Recovery Drill Report", title_style),
                ""
            ]
        ], colWidths=[360, 170])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceBefore=4, spaceAfter=14))

        # 2. Executive Summary
        story.append(Paragraph("Executive Summary", h2_style))
        story.append(Paragraph(report_data.summary or "Disaster recovery drill completed.", normal))
        story.append(Spacer(1, 10))

        # 3. Core Identifiers & Metadata Table
        story.append(Paragraph("Test Provenance & Metadata", h2_style))
        meta_data = [
            [Paragraph("<b>Application Name:</b>", normal), Paragraph(report_data.application_name, normal),
             Paragraph("<b>Test Drill ID:</b>", normal), Paragraph(report_data.test_id[:16] + "...", normal)],
            [Paragraph("<b>Backup Identifier:</b>", normal), Paragraph(report_data.backup_id, normal),
             Paragraph("<b>Backup Timestamp:</b>", normal), Paragraph(report_data.backup_timestamp or "N/A", normal)],
            [Paragraph("<b>Restore Job Status:</b>", normal), Paragraph(f"<b>{report_data.restore_job_status}</b>", normal),
             Paragraph("<b>Final Status:</b>", normal), Paragraph(f"<b>{report_data.final_status}</b>", normal)],
            [Paragraph("<b>Started At:</b>", normal), Paragraph(report_data.started_at, normal),
             Paragraph("<b>Completed At:</b>", normal), Paragraph(report_data.completed_at, normal)]
        ]
        meta_table = Table(meta_data, colWidths=[110, 155, 110, 155])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 12))

        # 4. Service Level Agreements (SLAs) Table
        story.append(Paragraph("Service Level Agreement (SLA) Benchmarks", h2_style))
        rto_status_str = "<font color='#16a34a'><b>MET</b></font>" if report_data.rto_met else "<font color='#dc2626'><b>BREACHED</b></font>"
        rpo_status_str = "<font color='#16a34a'><b>MET</b></font>" if report_data.rpo_met else "<font color='#dc2626'><b>BREACHED</b></font>"

        sla_data = [
            [Paragraph("<b>Objective</b>", normal), Paragraph("<b>Observed</b>", normal), Paragraph("<b>Target SLA</b>", normal), Paragraph("<b>Compliance</b>", normal)],
            [Paragraph("<b>Recovery Time (RTO)</b>", normal), Paragraph(f"{report_data.recovery_drill_duration_seconds:.2f}s", normal), Paragraph(f"&lt; {report_data.configured_targets.target_rto_seconds:.1f}s", normal), Paragraph(rto_status_str, normal)],
            [Paragraph("<b>Backup Freshness (RPO)</b>", normal), Paragraph(f"{report_data.backup_age_minutes:.1f}m", normal), Paragraph(f"&lt; {report_data.configured_targets.target_rpo_minutes:.1f}m", normal), Paragraph(rpo_status_str, normal)],
        ]
        sla_table = Table(sla_data, colWidths=[150, 120, 130, 130])
        sla_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e0f2fe")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(sla_table)
        story.append(Spacer(1, 6))

        # RTO & RPO Methodological Disclaimers
        rto_box = Table([[Paragraph(f"<b>RTO Distinction:</b> {report_data.rto_methodological_note}", disclaimer_style)]], colWidths=[530])
        rto_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94a3b8")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(rto_box)
        story.append(Spacer(1, 4))

        rpo_box = Table([[Paragraph(f"<b>RPO Clarification:</b> {report_data.rpo_methodological_note}", disclaimer_style)]], colWidths=[530])
        rpo_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94a3b8")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(rpo_box)
        story.append(Spacer(1, 12))

        # 5. System Health & Verification Summary
        story.append(Paragraph("System Health & Verification Summary", h2_style))
        health_data = [
            [Paragraph("<b>Component</b>", normal), Paragraph("<b>Verification Domain</b>", normal), Paragraph("<b>Status</b>", normal)],
            [Paragraph("Database Health", normal), Paragraph("PostgreSQL connectivity, tables presence, and schema compatibility", normal),
             Paragraph("<font color='#16a34a'><b>PASSED</b></font>" if report_data.database_health.get("passed", True) else "<font color='#dc2626'><b>FAILED</b></font>", normal)],
            [Paragraph("Docker Application Health", normal), Paragraph("Container lifecycle, process startup, runtime health", normal),
             Paragraph("<font color='#16a34a'><b>PASSED</b></font>" if report_data.docker_application_health.get("passed", True) else "<font color='#dc2626'><b>FAILED</b></font>", normal)],
            [Paragraph("API Validation", normal), Paragraph("GET /health, GET /ready, read-only business validation export APIs", normal),
             Paragraph("<font color='#16a34a'><b>PASSED</b></font>" if report_data.api_validation_results.get("passed", True) else "<font color='#dc2626'><b>FAILED</b></font>", normal)],
            [Paragraph("Data Integrity", normal), Paragraph("Record counts vs backup manifest, foreign key checks, ledger balance reconciliation", normal),
             Paragraph("<font color='#16a34a'><b>PASSED</b></font>" if report_data.data_integrity_checks.get("passed", True) else "<font color='#dc2626'><b>FAILED</b></font>", normal)]
        ]
        health_table = Table(health_data, colWidths=[140, 290, 100])
        health_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(health_table)
        story.append(Spacer(1, 12))

        # 6. Detected Failures (if any)
        if report_data.detected_failures:
            story.append(Paragraph(f"Detected Failures ({len(report_data.detected_failures)})", h2_style))
            fail_rows = [[Paragraph("<b>Category</b>", normal), Paragraph("<b>Check Name</b>", normal), Paragraph("<b>Description</b>", normal)]]
            for f in report_data.detected_failures:
                fail_rows.append([
                    Paragraph(f"<font color='#dc2626'><b>{f.category}</b></font>", normal),
                    Paragraph(f.check_name, normal),
                    Paragraph(f.error_message, normal)
                ])
            fail_table = Table(fail_rows, colWidths=[130, 150, 250])
            fail_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#fee2e2")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#fca5a5")),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(fail_table)
            story.append(Spacer(1, 10))

        # 7. Error Details / Logs
        if report_data.error_details:
            story.append(Paragraph("Error Details", h2_style))
            err_box = Table([[Paragraph(f"<font color='#dc2626'>{report_data.error_details}</font>", disclaimer_style)]], colWidths=[530])
            err_box.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef2f2")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#ef4444")),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(err_box)
            story.append(Spacer(1, 10))

        # Footer
        story.append(Spacer(1, 14))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=6, spaceAfter=8))
        story.append(Paragraph(
            "<b>CloudGuard V1 DR Monitoring Engine</b> — Verification and audit platform only. "
            "Read-only diagnostic reporting without automated intervention.",
            disclaimer_style
        ))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
