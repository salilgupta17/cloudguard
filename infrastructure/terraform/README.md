# CloudGuard Infrastructure as Code (Terraform)

This directory houses the AWS Infrastructure as Code (IaC) definitions for CloudGuard production deployments.

## Modules Structure:
- `modules/rds/`: AWS RDS PostgreSQL Multi-AZ instance definitions with automated backup retention
- `modules/s3/`: S3 Disaster Recovery Vault bucket with KMS customer-managed key encryption and versioning
- `modules/ecs/`: ECS Fargate task definitions for `cloudguard-api` and `demo-application`
- `modules/iam/`: Least-privilege IAM roles for CloudGuard audit and snapshot verification
- `modules/cloudwatch/`: CloudWatch alarms for RTO/RPO SLA breaches

*Note: Per Phase 1 requirements, AWS provisioning is deferred to avoid unapproved cloud expenditures.*
