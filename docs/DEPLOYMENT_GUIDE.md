# CloudGuard Deployment Guide

This guide details how to deploy CloudGuard in two operating modes:
1. **Local Mode**: Fully functional local development environment using Docker Compose and PostgreSQL.
2. **AWS Production Mode**: Enterprise AWS cloud environment provisioned via Terraform.

---

## 1. Prerequisites

### Local Environment
- **Docker & Docker Compose**: Docker Desktop 4.25+
- **Python**: Version 3.12+
- **Node.js**: Version 18+ and `npm`

### AWS Cloud Environment
- **AWS CLI**: Version 2.15+ authenticated via `aws configure`
- **Terraform**: Version 1.5.0+
- **IAM Permissions**: Administrator access or scoped privileges to provision VPC, RDS, Backup, EventBridge, ECS, S3, CloudWatch, and IAM.

---

## 2. Local Mode Deployment (Quickstart)

Local mode runs entirely on your local workstation without requiring an AWS account or generating cloud costs.

### Step 1: Clone and Set Up Virtual Environment
```bash
git clone https://github.com/your-org/cloudguard.git
cd cloudguard

# Create and activate Python virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies across services
pip install -r backend/requirements.txt
pip install -r report-service/requirements.txt
pip install -r demo-application/requirements.txt
pip install -r validation-engine/requirements.txt
```

### Step 2: Launch Docker Compose Services
```bash
# Starts PostgreSQL (Primary + Sandbox), Demo Banking App, and CloudGuard API
docker-compose up -d

# Verify containers are healthy
docker-compose ps
```

### Step 3: Run the React Dashboard
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`. The dashboard connects to the local FastAPI backend at `http://localhost:8000`.

---

## 3. AWS Cloud Deployment (Terraform)

Per the Phase 7 scope, **do not deploy AWS infrastructure automatically**. Follow the manual steps below when ready to deploy to your AWS account.

### Step 1: Configure AWS Credentials
Ensure your active shell has genuine AWS credentials:
```bash
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_REGION="us-east-1"
```

### Step 2: Configure Terraform Variables
Navigate to the Terraform directory and create your variable configuration:
```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
```
Edit `terraform.tfvars`:
```hcl
aws_region         = "us-east-1"
environment        = "production"
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]
db_password        = "SuperSecureP@ssw0rd2026!"
```

### Step 3: Initialize and Validate Terraform
```bash
terraform init
terraform validate
```

### Step 4: Review Execution Plan
```bash
terraform plan -out=tfplan.binary
```
Review the planned resources:
- 1 VPC with 6 subnets across 3 tiers (Public, Application, Isolated DB)
- 1 Multi-AZ RDS PostgreSQL 16 instance with automated backup retention
- 1 AWS Backup Vault with KMS CMK encryption and daily backup plan
- 1 AWS Backup Restore Testing Plan targeting ephemeral instances
- 1 EventBridge Rule capturing `Restore Job State Change` events
- 1 ECS Fargate Cluster with task definitions for API, Demo App, and Validation Worker
- 1 S3 Bucket for reports & evidence with KMS encryption and Glacier lifecycle rules
- CloudWatch Log Groups, Metric Filters, and SLA Alarms for RTO (<300s) and RPO (<60m)
- Least-privilege IAM roles with safety interlocks

### Step 5: Apply Infrastructure
```bash
terraform apply tfplan.binary
```

### Step 6: Build & Push Container Images to Amazon ECR
```bash
# Authenticate Docker to AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com

# Build and push CloudGuard API
docker build -t cloudguard-api:latest -f cloudguard-api/Dockerfile .
docker tag cloudguard-api:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/cloudguard-api:latest
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/cloudguard-api:latest

# Build and push Demo Banking Workload
docker build -t demo-banking-app:latest -f demo-application/Dockerfile .
docker tag demo-banking-app:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/demo-banking-app:latest
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/demo-banking-app:latest
```

---

## 4. Teardown and Cost Control

To avoid unnecessary cloud charges, teardown resources when not in use:

```bash
cd infrastructure/terraform
terraform destroy -auto-approve
```
*Note: Any ephemeral test RDS instances created during restore drills are automatically cleaned up by CloudGuard's worker within minutes of test completion with `SkipFinalSnapshot=True`.*
