# CloudGuard Automated Testing Guide

CloudGuard includes a comprehensive test suite of **77 automated tests** validating all 7 phases:
- Core Disaster Recovery Pipeline (Phase 3)
- Validation Engine & Error Injection (Phase 4)
- Multi-Format Compliance Reports (Phase 5)
- React Monitoring Dashboard & API (Phase 6)
- AWS Integration & EventBridge Deduplication (Phase 7)
- Demo Banking Application Core Logic & Ledger Invariants (Phase 2)

---

## 1. Running Test Suites

### Run All Root Platform Tests (54 Tests)
```bash
pytest tests -v
```

### Run Demo Banking Workload Tests (23 Tests)
```bash
pytest demo-application/tests -v
```

### Run Entire Combined Test Suite (77 Tests)
```bash
pytest tests demo-application/tests -v
```

---

## 2. Phase-by-Phase Test Breakdown

| Phase Test Suite | File Location | Key Validations |
| :--- | :--- | :--- |
| **Phase 3: DR Pipeline** | `tests/test_dr_pipeline.py` | `pg_dump` backups, SHA-256 manifests, isolated restore, duration logging, safety interlocks against primary overwrite. |
| **Phase 4: Validation Engine** | `tests/test_validation_engine_phase4.py` | Deep DB checks, manifest-driven parity, foreign key validation, ledger accounting math, container health probes. |
| **Phase 5: Report Generator** | `tests/test_report_generator_phase5.py` | 15 required report fields, JSON, PDF (ReportLab), HTML rendering, S3 and local storage adapters, RTO/RPO SLA notes. |
| **Phase 6: Frontend Dashboard** | `tests/test_frontend_dashboard_phase6.py` | Applications API, live backup/drill stats, Vite bundle integrity, 5 required pages, prohibition of remediation actions. |
| **Phase 7: AWS Integration** | `tests/test_aws_integration_phase7.py` | EventBridge restore event parsing, deduplication/idempotency, Rule 10 authentic credentials check, CloudWatch emission. |

---

## 3. Failure Classification & Error Injection Testing

CloudGuard's validation engine is rigorously tested against realistic disaster scenarios. In each case, CloudGuard detects, classifies, and reports the failure without executing automated remediation:

### Test Case 1: Database Connectivity Failure (`DATABASE_ERROR`)
- **Command**: `pytest tests/test_validation_engine_phase4.py -k test_failing_scenario_database_error_on_connectivity_failure -v`
- **Simulation**: Target database port is unreachable or credentials are bad.
- **Verification**: Status set to `FAIL`; check classified as `DATABASE_ERROR`.

### Test Case 2: Schema Drift / Missing Table (`DATABASE_ERROR`)
- **Command**: `pytest tests/test_validation_engine_phase4.py -k test_failing_scenario_database_error_on_missing_table -v`
- **Simulation**: Table `transactions` dropped from restored target.
- **Verification**: Detected immediately; reported with missing table name.

### Test Case 3: Record Count Parity Discrepancy (`DATA_INTEGRITY_ERROR`)
- **Command**: `pytest tests/test_validation_engine_phase4.py -k test_failing_scenario_data_integrity_error_on_record_count_discrepancy -v`
- **Simulation**: Target has fewer accounts than recorded in backup manifest.
- **Verification**: Flags manifest discrepancy; reports observed vs expected count.

### Test Case 4: Foreign Key Constraint Violation (`DATA_INTEGRITY_ERROR`)
- **Command**: `pytest tests/test_validation_engine_phase4.py -k test_failing_scenario_data_integrity_error_on_foreign_key_violation -v`
- **Simulation**: Transaction row references a non-existent account ID.
- **Verification**: Caught by relational integrity validator; flagged as `DATA_INTEGRITY_ERROR`.

### Test Case 5: Ledger Balance Discrepancy (`DATA_INTEGRITY_ERROR`)
- **Command**: `pytest tests/test_validation_engine_phase4.py -k test_failing_scenario_data_integrity_error_on_ledger_math_discrepancy -v`
- **Simulation**: Sum of transaction history does not match account balance.
- **Verification**: Flags mathematical ledger discrepancy; status set to `FAIL`.

### Test Case 6: RPO Freshness Breach (`BACKUP_ERROR`)
- **Command**: `pytest tests/test_validation_engine_phase4.py -k test_failing_scenario_backup_error_on_rpo_freshness_breach -v`
- **Simulation**: Backup snapshot is 120 minutes old (exceeds 60m SLA).
- **Verification**: Reports `RPO_TARGET_BREACH`; status set to `FAIL`.

### Test Case 7: RTO Duration Breach (`TIMEOUT_ERROR`)
- **Command**: `pytest tests/test_validation_engine_phase4.py -k test_failing_scenario_timeout_error_on_rto_duration_breach -v`
- **Simulation**: Restore execution takes 350 seconds (exceeds 300s SLA).
- **Verification**: Reports `RTO_TARGET_BREACH`; status set to `FAIL`.

---

## 4. Verification of Scope Constraints

To verify that CloudGuard contains no automatic remediation, restart, failover, or execute action buttons:
```bash
pytest tests/test_validation_engine_phase4.py -k test_non_remediation_constraint -v
pytest tests/test_report_generator_phase5.py -k test_non_remediation_constraint_in_reports -v
pytest tests/test_frontend_dashboard_phase6.py -k test_frontend_strictly_prohibits_remediation_and_execution_actions -v
pytest tests/test_aws_integration_phase7.py -k test_strict_non_remediation_constraint_in_aws_code -v
```
All four assertions verify that the platform remains strictly read-only and compliance-oriented.
