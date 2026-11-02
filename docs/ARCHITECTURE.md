# CloudGuard Architecture & Engineering Specification

CloudGuard is an automated AWS Disaster Recovery (DR) Verification, Monitoring, and Compliance Reporting platform. It validates whether PostgreSQL databases and containerized FastAPI applications can be successfully restored from backups in an isolated sandbox environment without mutating production state.

---

## 1. High-Level AWS Architecture

```mermaid
flowchart TB
    subgraph AWS_Cloud ["AWS Cloud (Region: us-east-1)"]
        subgraph VPC ["CloudGuard VPC (10.0.0.0/16)"]
            subgraph Public_Subnets ["Public Subnets"]
                IGW[Internet Gateway]
                NAT[NAT Gateway]
                ALB[Application Load Balancer]
            end

            subgraph App_Subnets ["Private Application Subnets"]
                CG_API["CloudGuard API<br/>(ECS Fargate)"]
                DEMO_APP["Demo Banking App<br/>(ECS Fargate)"]
                WORKER["DR Validation Worker<br/>(ECS Fargate Task)"]
            end

            subgraph Isolated_DB_Subnets ["Private Isolated Database Subnets (No Internet)"]
                RDS_PRIMARY[("Primary RDS PostgreSQL 16<br/>Multi-AZ Instance")]
                RDS_SANDBOX[("Ephemeral Sandbox RDS<br/>(Created by Restore Testing)")]
            end
        end

        subgraph AWS_Managed_Services ["AWS Managed Services"]
            BACKUP["AWS Backup Vault<br/>(KMS Encrypted)"]
            RESTORE_TEST["AWS Backup Restore Testing Plan<br/>(Automated Schedules)"]
            EVENTBRIDGE["Amazon EventBridge<br/>(Restore Job State Change)"]
            S3["Amazon S3 Reports Vault<br/>(Encrypted, Versioned, TLS Only)"]
            CLOUDWATCH["Amazon CloudWatch<br/>(Metrics & SLA Breach Alarms)"]
            IAM["IAM Roles & Policies<br/>(Least-Privilege & Safety Interlocks)"]
        end
    end

    %% Flow interactions
    DEMO_APP -->|Reads / Writes| RDS_PRIMARY
    BACKUP -->|Continuous Snapshots| RDS_PRIMARY
    BACKUP -->|Triggers Restore Drill| RESTORE_TEST
    RESTORE_TEST -->|Provisions Ephemeral Target| RDS_SANDBOX
    RESTORE_TEST -->|Emits State Change Event| EVENTBRIDGE
    EVENTBRIDGE -->|Launches Task| WORKER
    WORKER -->|Validates Schema & Checksums| RDS_SANDBOX
    WORKER -->|Streams 15-Item Reports| S3
    WORKER -->|Emits RTO/RPO Metrics| CLOUDWATCH
    WORKER -->|Decommissions Sandbox| RDS_SANDBOX
    ALB --> CG_API
    CG_API --> S3
```

---

## 2. Disaster Recovery Verification Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Scheduler as EventBridge / AWS Backup
    participant RDS_Prod as Primary RDS
    participant Backup as AWS Backup Vault
    participant RDS_Test as Ephemeral Sandbox RDS
    participant Worker as ECS Validation Worker
    participant S3 as Amazon S3
    participant CW as CloudWatch
    participant Dashboard as CloudGuard Dashboard

    Scheduler->>RDS_Prod: Take Scheduled Snapshot
    RDS_Prod-->>Backup: Store Recovery Point with SHA-256 Manifest
    Scheduler->>RDS_Test: Trigger Restore Testing Plan
    Note over RDS_Test: Ephemeral Database created in isolated subnet
    Backup-->>Worker: EventBridge 'Restore Job State Change' (COMPLETED)
    
    activate Worker
    Worker->>Worker: Check Idempotency (Deduplicate Event)
    Worker->>Worker: Validate Safety Interlock (Target != Primary)
    Worker->>RDS_Test: Run DatabaseValidator (Connectivity, Schema, FKs, Checksums)
    Worker->>Worker: Run ApplicationValidator (Probes, Health, Ledger Math)
    Worker->>Worker: Compile 15-Field Compliance Report
    Worker->>S3: Upload Reports (JSON, PDF, HTML)
    Worker->>CW: Emit Telemetry (RecoveryDrillDuration, BackupFreshnessMinutes)
    Worker->>RDS_Test: Delete Ephemeral Test RDS Instance
    deactivate Worker

    Dashboard->>S3: Fetch JSON / PDF / HTML Reports
    Dashboard-->>Scheduler: Display Live RTO/RPO Benchmarks
```

---

## 3. Network Architecture & Strict Isolation

CloudGuard employs a strict 3-tier VPC architecture:
1. **Public Subnets**: Houses NAT Gateways and ALBs. No database instances are ever placed here.
2. **Private Application Subnets**: Hosts ECS Fargate tasks (`cloudguard-api`, `demo-banking-application`, `cloudguard-validation-worker`). Outbound internet access via NAT Gateway for ECR pulls.
3. **Private Isolated Database Subnets**:
   - Zero internet access.
   - Zero NAT Gateway routes.
   - Port 5432 ingress restricted strictly to the ECS task security group.
   - Both the Primary RDS instance and ephemeral restored sandbox instances reside here.

---

## 4. Safety Guardrails & Primary Protection

To prevent disastrous production data loss or accidental overwrites during DR drills, CloudGuard enforces three layers of safety interlocks:

1. **IAM Level (Hard Interlock)**:
   - The validation worker IAM policy contains an explicit `Deny` on `rds:DeleteDBInstance` targeted directly at the Primary RDS ARN:
   ```json
   {
     "Sid": "SafetyInterlockDenyPrimaryDeletion",
     "Effect": "Deny",
     "Action": ["rds:DeleteDBInstance"],
     "Resource": ["arn:aws:rds:*:*:db:cloudguard-rds-primary*"]
   }
   ```
2. **Code Level (Safety Interlock Engine)**:
   - `validate_isolated_target_safety()` compares normalized source and target URLs.
   - If target URL is identical to source URL, or target name lacks sandbox tokens (`isolated`, `test`, `sandbox`, `drill`), execution halts immediately.
3. **Naming & Tagging Policy**:
   - Ephemeral test databases are uniquely named `cloudguard-isolated-*` and tagged with `Environment=DR-Sandbox`.

---

## 5. Methodological Distinctions (SLA Definitions)

CloudGuard strictly adheres to industry DR standards:

### Recovery Time Objective (RTO)
- **Configured Target**: 300 Seconds (5 Minutes).
- **Observed Recovery Duration**: Time measured from start of sandbox restore until validation suite completion.
- **Methodological Distinction**:
  > *Observed recovery drill duration reflects synthetic sandbox restore + validation time. Actual production RTO includes DNS cutover, traffic diversion, replication catching up, and application cluster scaling.*

### Recovery Point Objective (RPO)
- **Configured Target**: 60 Minutes (1 Hour).
- **Observed Backup Age**: Elapsed time between recovery point snapshot timestamp and drill start time.
- **Methodological Distinction**:
  > *Backup age reflects snapshot freshness at drill execution. Actual RPO requires transaction log / WAL replay analysis and transaction ledger gap verification; snapshot age alone does not guarantee zero data loss.*
