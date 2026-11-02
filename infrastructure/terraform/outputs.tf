output "vpc_id" {
  description = "CloudGuard VPC ID"
  value       = module.vpc.vpc_id
}

output "primary_rds_endpoint" {
  description = "PostgreSQL primary database endpoint"
  value       = module.rds.db_endpoint
}

output "primary_rds_arn" {
  description = "ARN of primary RDS database instance"
  value       = module.rds.db_instance_arn
}

output "backup_vault_name" {
  description = "AWS Backup Vault name"
  value       = module.backup.vault_name
}

output "reports_s3_bucket" {
  description = "S3 bucket for disaster recovery compliance reports"
  value       = module.s3.bucket_name
}

output "ecs_cluster_name" {
  description = "ECS Fargate Cluster name"
  value       = module.ecs.cluster_id
}

output "eventbridge_restore_rule" {
  description = "EventBridge rule name monitoring restore events"
  value       = module.eventbridge.rule_name
}
