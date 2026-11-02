"""
HTML Disaster Recovery Report Generator.
Renders responsive executive reports with SLA badges,
audit breakdowns, and regulatory disclaimers.
"""
from jinja2 import Template
from .models import ReportData

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CloudGuard DR Report — {{ report.application_name }} ({{ report.test_id[:8] }})</title>
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --border-color: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-green: #34d399;
            --accent-red: #f87171;
            --accent-amber: #fbbf24;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            margin: 0;
            padding: 32px 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1080px;
            margin: 0 auto;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 24px;
            margin-bottom: 32px;
        }
        .brand {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: var(--accent-blue);
        }
        .title {
            font-size: 20px;
            font-weight: 700;
            margin: 4px 0 0 0;
            color: var(--text-primary);
        }
        .badge {
            display: inline-block;
            padding: 6px 16px;
            border-radius: 9999px;
            font-weight: 800;
            font-size: 14px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .badge-pass { background-color: rgba(52, 211, 153, 0.2); color: #34d399; border: 1px solid #34d399; }
        .badge-fail { background-color: rgba(248, 113, 113, 0.2); color: #f87171; border: 1px solid #f87171; }
        .badge-incomplete { background-color: rgba(251, 191, 36, 0.2); color: #fbbf24; border: 1px solid #fbbf24; }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 28px;
        }
        .card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
        }
        .card-title {
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--accent-blue);
            margin-top: 0;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .metric-value {
            font-size: 28px;
            font-weight: 800;
            margin-bottom: 4px;
        }
        .metric-target {
            font-size: 13px;
            color: var(--text-secondary);
        }
        .table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            margin-top: 8px;
        }
        .table th, .table td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        .table th {
            color: var(--text-secondary);
            font-weight: 600;
            background-color: rgba(15, 23, 42, 0.4);
        }
        .disclaimer-box {
            background-color: rgba(56, 189, 248, 0.08);
            border-left: 4px solid var(--accent-blue);
            padding: 14px 18px;
            border-radius: 0 8px 8px 0;
            margin-top: 12px;
            font-size: 13px;
            color: #cbd5e1;
        }
        .failure-box {
            background-color: rgba(248, 113, 113, 0.1);
            border-left: 4px solid var(--accent-red);
            padding: 14px 18px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 16px;
        }
        .code-block {
            background-color: #0b1120;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 14px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 12px;
            color: #cbd5e1;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 250px;
            overflow-y: auto;
        }
        .footer {
            margin-top: 48px;
            padding-top: 20px;
            border-top: 1px solid var(--border-color);
            font-size: 12px;
            color: var(--text-secondary);
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div>
                <div class="brand">CloudGuard — DR Verification Platform</div>
                <h1 class="title">Disaster Recovery Drill Report</h1>
                <div style="color: var(--text-secondary); font-size: 13px; margin-top: 4px;">
                    Protected Application: <strong style="color: white;">{{ report.application_name }}</strong> |
                    Drill ID: <code>{{ report.test_id }}</code>
                </div>
            </div>
            <div>
                {% if report.final_status == "PASS" %}
                    <span class="badge badge-pass">✓ PASS</span>
                {% elif report.final_status == "FAIL" %}
                    <span class="badge badge-fail">✕ FAIL</span>
                {% else %}
                    <span class="badge badge-incomplete">⚠ INCOMPLETE</span>
                {% endif %}
            </div>
        </div>

        <!-- Executive Summary -->
        <div class="card" style="margin-bottom: 24px;">
            <div class="card-title">Executive Summary</div>
            <p style="margin: 0; font-size: 15px;">{{ report.summary }}</p>
        </div>

        <!-- SLA Benchmarks Grid -->
        <div class="grid">
            <!-- RTO Card -->
            <div class="card">
                <div class="card-title">
                    <span>Recovery Time (RTO)</span>
                    {% if report.rto_met %}
                        <span style="color: var(--accent-green); font-weight: 700;">✓ SLA MET</span>
                    {% else %}
                        <span style="color: var(--accent-red); font-weight: 700;">✕ SLA BREACHED</span>
                    {% endif %}
                </div>
                <div class="metric-value" style="color: {% if report.rto_met %}var(--accent-green){% else %}var(--accent-red){% endif %};">
                    {{ report.recovery_drill_duration_seconds }}s
                </div>
                <div class="metric-target">Target SLA: &lt; {{ report.configured_targets.target_rto_seconds }}s</div>
                <div class="disclaimer-box">
                    <strong>RTO Distinction:</strong> {{ report.rto_methodological_note }}
                </div>
            </div>

            <!-- RPO Card -->
            <div class="card">
                <div class="card-title">
                    <span>Backup Freshness (RPO)</span>
                    {% if report.rpo_met %}
                        <span style="color: var(--accent-green); font-weight: 700;">✓ SLA MET</span>
                    {% else %}
                        <span style="color: var(--accent-red); font-weight: 700;">✕ SLA BREACHED</span>
                    {% endif %}
                </div>
                <div class="metric-value" style="color: {% if report.rpo_met %}var(--accent-green){% else %}var(--accent-red){% endif %};">
                    {{ report.backup_age_minutes }}m
                </div>
                <div class="metric-target">Target SLA: &lt; {{ report.configured_targets.target_rpo_minutes }}m</div>
                <div class="disclaimer-box">
                    <strong>RPO Clarification:</strong> {{ report.rpo_methodological_note }}
                </div>
            </div>
        </div>

        <!-- Drill & Backup Metadata Grid -->
        <div class="grid">
            <div class="card">
                <div class="card-title">Backup & Restore Provenance</div>
                <table class="table">
                    <tr><td>Backup Identifier</td><td><code>{{ report.backup_id }}</code></td></tr>
                    <tr><td>Backup Snapshot Time</td><td>{{ report.backup_timestamp or "N/A" }}</td></tr>
                    <tr><td>Restore Execution Status</td><td><strong>{{ report.restore_job_status }}</strong></td></tr>
                    <tr><td>Drill Started</td><td>{{ report.started_at }}</td></tr>
                    <tr><td>Drill Completed</td><td>{{ report.completed_at }}</td></tr>
                </table>
            </div>

            <div class="card">
                <div class="card-title">System Health & Integrity State</div>
                <table class="table">
                    <tr>
                        <td>Database Health</td>
                        <td>{% if report.database_health.get("passed", true) %}<span style="color: var(--accent-green);">● Healthy</span>{% else %}<span style="color: var(--accent-red);">● Failed</span>{% endif %}</td>
                    </tr>
                    <tr>
                        <td>Docker Application Health</td>
                        <td>{% if report.docker_application_health.get("passed", true) %}<span style="color: var(--accent-green);">● Running (Healthy)</span>{% else %}<span style="color: var(--accent-red);">● Unhealthy</span>{% endif %}</td>
                    </tr>
                    <tr>
                        <td>API Probes (/health, /ready, business)</td>
                        <td>{% if report.api_validation_results.get("passed", true) %}<span style="color: var(--accent-green);">● All Probes 200 OK</span>{% else %}<span style="color: var(--accent-red);">● Endpoint Failed</span>{% endif %}</td>
                    </tr>
                    <tr>
                        <td>Data Integrity (Manifest Parity & Ledger)</td>
                        <td>{% if report.data_integrity_checks.get("passed", true) %}<span style="color: var(--accent-green);">● 100% Parity Verified</span>{% else %}<span style="color: var(--accent-red);">● Integrity Violation</span>{% endif %}</td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Detected Failures Section -->
        {% if report.detected_failures %}
        <div class="card" style="margin-bottom: 24px;">
            <div class="card-title" style="color: var(--accent-red);">Detected Failures ({{ report.detected_failures|length }})</div>
            {% for fail in report.detected_failures %}
            <div class="failure-box">
                <strong style="color: var(--accent-red);">[{{ fail.category }}] {{ fail.check_name }}:</strong>
                <p style="margin: 4px 0 0 0; font-size: 14px;">{{ fail.error_message }}</p>
                {% if fail.observed_value %}
                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">
                    Observed: <code>{{ fail.observed_value }}</code> | Expected: <code>{{ fail.expected_value }}</code>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Error Details & Logs -->
        {% if report.error_details or report.execution_logs_snippet %}
        <div class="card" style="margin-bottom: 24px;">
            <div class="card-title">Diagnostics & Execution Logs</div>
            {% if report.error_details %}
            <div style="margin-bottom: 12px;">
                <strong style="color: var(--accent-red); font-size: 13px;">Error Details:</strong>
                <div class="code-block">{{ report.error_details }}</div>
            </div>
            {% endif %}
            {% if report.execution_logs_snippet %}
            <div>
                <strong style="font-size: 13px; color: var(--text-secondary);">Execution Logs Snippet:</strong>
                <div class="code-block">{{ report.execution_logs_snippet }}</div>
            </div>
            {% endif %}
        </div>
        {% endif %}

        <!-- Footer -->
        <div class="footer">
            <p>CloudGuard V1 — Disaster Recovery Monitoring and Reporting Platform</p>
            <p>Report generated at {{ report.generated_at }}. Strictly verification and audit reporting only. Read-only diagnostics.</p>
        </div>
    </div>
</body>
</html>
"""


class HtmlReportGenerator:
    """Renders high-fidelity HTML reports from ReportData."""

    @staticmethod
    def generate(report_data: ReportData) -> str:
        template = Template(HTML_TEMPLATE)
        return template.render(report=report_data)
