# CloudGuard — AWS Disaster Recovery Monitoring & Reporting Platform

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-cyan.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38bdf8.svg)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![AWS](https://img.shields.io/badge/AWS-RDS%20%7C%20Backup%20%7C%20EventBridge%20%7C%20ECS%20%7C%20S3%20%7C%20CloudWatch-FF9900.svg)](https://aws.amazon.com/)
[![Terraform](https://img.shields.io/badge/Terraform-1.5+-623CE4.svg)](https://www.terraform.io/)
[![Tests](https://img.shields.io/badge/Tests-77%20Passed-emerald.svg)](https://docs.pytest.org/)

**CloudGuard** is an automated AWS Disaster Recovery (DR) verification, monitoring, and compliance platform. It continuously validates whether production databases and containerized FastAPI applications can be reliably restored from backups in an isolated sandbox environment within committed **RTO (Recovery Time Objective < 300s)** and **RPO (Recovery Point Objective < 60m)** SLAs.

---

## 🛡️ Key Principles & Architectural Scope

> [!IMPORTANT]
> **CloudGuard is strictly a reporting, monitoring, and verification platform.**
> - ❌ **No automatic error remediation or healing**
> - ❌ **No automatic container restarts**
> - ❌ **No production database failover**
> - ❌ **No remediation action buttons** (No Fix, Restart, Retry, Failover, or Restore Production)
> - 🔒 **Strict Isolation Interlock**: The primary production database can **NEVER** be targeted for restore or cleanup. All drills execute within segregated sandbox environments.

---

## 🔄 Disaster Recovery Pipeline Flow

```
Application ➔ PostgreSQL / RDS ➔ AWS Backup Snapshot ➔ EventBridge Restore Event 
➔ Isolated Sandbox Restore ➔ Deep Parity & Checksum Validation ➔ Error Detection 
➔ 15-Item Compliance Report (JSON/PDF/HTML) ➔ S3 Reports Vault ➔ Operations Dashboard
```

---

## 📊 Dashboard Pages (React + Vite + Tailwind CSS)

1. **Overview**: Total recovery tests, passed/failed metrics, average drill duration, latest result, and interactive architecture flow visualizer.
2. **Applications**: Protected workload inventory, PostgreSQL 16 schema details (`customers`, `accounts`, `transactions`), and SHA-256 backup manifest catalog.
3. **Recovery Tests**: Historical drill records, status/date filters, granular check results modal, and failure diagnostics.
4. **Reports**: Compliance report catalog, multi-tab modal preview (Executive Summary, Rendered HTML, Raw JSON), and direct PDF/JSON download buttons.
5. **Monitoring**: Interactive SVG duration curve (with **300s Target RTO red SLA limit**), backup freshness curve (with **60m Target RPO amber threshold**), success distribution bar, and error classification breakdown.

---

## 📑 15-Item Compliance Report Generator

Every disaster recovery drill generates audit-ready reports in **JSON**, **PDF** (via ReportLab), and **HTML**:
1. Application name
2. Recovery test ID
3. Backup identifier and timestamp
4. Restore job status
5. Database health (PostgreSQL connectivity, required tables, schema compatibility)
6. Docker application health (Container status, `/health`, `/ready`)
7. API validation results (Read-only endpoints, `/api/v1/validation/ledger/summary`)
8. Data integrity checks (Record counts vs backup manifest, foreign key checks, ledger accounting math)
9. Recovery drill duration (Observed sandbox execution time)
10. Backup age / recovery point freshness
11. Configured RTO (<300s) and RPO (<60m) targets
12. Detected failures (Categorized: `DATABASE_ERROR`, `API_ERROR`, `DATA_INTEGRITY_ERROR`, `TIMEOUT_ERROR`, etc.)
13. Error details and execution log references
14. Final `PASS` / `FAIL` / `INCOMPLETE` status
15. Test start and completion timestamps

### SLA Methodological Distinctions
- **RTO**: *Observed recovery drill duration reflects synthetic sandbox restore + validation time. Actual production RTO includes DNS cutover, traffic diversion, replication catching up, and application cluster scaling.*
- **RPO**: *Backup age reflects snapshot freshness at drill execution. Actual RPO requires transaction log / WAL replay analysis and transaction ledger gap verification; snapshot age alone does not guarantee zero data loss.*

---

## 📁 Repository Structure

```
cloudguard/
├── cloudguard-api/               # FastAPI DR Orchestration Backend
│   ├── app/
│   │   ├── api/                 # REST Routers (dr_pipeline, reports, recovery_tests, backups, applications)
│   │   ├── dr/                  # DR Engine (aws_provider, local_provider, runner, safety, aws_worker, eventbridge)
│   │   └── core/                # Logging, CloudWatch metrics, exceptions
├── demo-application/             # Core Banking Workload (FastAPI + PostgreSQL)
│   ├── app/                     # Customer, account, transaction models & ledger verification APIs
├── validation-engine/            # Deep Database & Application Validator
│   ├── validation_engine/       # Schema, parity, checksum, foreign key, ledger math validators
├── report-service/               # Multi-Format Report Generator & S3 Storage
│   ├── report_service/          # JSON, ReportLab PDF, Jinja2 HTML, S3 & Local storage
├── frontend/                     # React 18 + Vite + Tailwind CSS Dashboard
│   ├── src/                     # Overview, Applications, RecoveryTests, Reports, Monitoring pages
├── infrastructure/
│   ├── docker/                  # Docker Compose configuration and init scripts
│   └── terraform/               # Production AWS Infrastructure as Code (Terraform >= 1.5)
│       └── modules/             # VPC, RDS, Backup, EventBridge, ECS, S3, CloudWatch, IAM
├── tests/                       # Automated Test Suite (77 Tests Passing)
└── docs/                        # Architecture, Deployment, Testing & Interview Guides
    ├── ARCHITECTURE.md          # Mermaid architecture and pipeline diagrams
    ├── DEPLOYMENT_GUIDE.md      # Local and AWS Terraform deployment instructions
    ├── TESTING_GUIDE.md         # Automated test execution and error injection guide
    └── INTERVIEW_DEMO.md        # Step-by-step interview demonstration script
```

---

## 🚀 Quickstart (Local Mode)

```bash
# 1. Clone repository and start Docker services
git clone https://github.com/your-org/cloudguard.git
cd cloudguard
docker-compose up -d

# 2. Run the React Dashboard
cd frontend
npm install
npm run dev
# Dashboard opens at http://localhost:5173

# 3. Run the automated test suite
pytest tests -v
pytest demo-application/tests -v
```

---

## ☁️ AWS Cloud Integration (Terraform)

CloudGuard includes complete Terraform definitions in `infrastructure/terraform/`:
- **VPC**: 3-tier network isolation (Public, Private Application, Private Isolated Database).
- **RDS**: PostgreSQL 16 Multi-AZ instance with automated backup retention.
- **AWS Backup**: Vault with KMS CMK encryption and automated Restore Testing Plan.
- **EventBridge**: Rule capturing `Restore Job State Change` events with deduplication.
- **ECS Fargate**: Validation Worker task running in private subnets.
- **S3**: Bucket with KMS encryption, TLS enforcement, and Glacier lifecycle policies.
- **CloudWatch**: Structured JSON logs and alarms for RTO (>300s) and RPO (>60m) SLA breaches.
- **IAM**: Least-privilege roles with explicit `Deny` on primary production database deletion.

*See [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) for full deployment instructions.*

---

## 📖 Documentation & Interview Guides

- **[Architecture & Pipeline Specification](docs/ARCHITECTURE.md)**: Mermaid diagrams, network topology, and safety interlocks.
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)**: Local Docker Compose and AWS Terraform provisioning.
- **[Testing & Error Injection Guide](docs/TESTING_GUIDE.md)**: How to run tests and simulate disaster failures.
- **[Interview Demonstration Script](docs/INTERVIEW_DEMO.md)**: Step-by-step 5-minute presentation guide.
