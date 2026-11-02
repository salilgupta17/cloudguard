variable "environment" {
  type    = string
  default = "production"
}

variable "backup_role_arn" {
  type        = string
  description = "IAM Role ARN for AWS Backup service"
}

variable "rds_resource_arn" {
  type        = string
  description = "ARN of the primary RDS instance protected by AWS Backup"
}
