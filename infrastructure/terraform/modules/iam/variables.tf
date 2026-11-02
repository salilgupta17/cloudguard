variable "environment" {
  type    = string
  default = "production"
}

variable "s3_reports_bucket_arn" {
  type        = string
  description = "ARN of the S3 Disaster Recovery reports bucket"
}

variable "primary_rds_arn" {
  type        = string
  description = "ARN of the primary production RDS instance (protected by explicit Deny guardrail)"
}
