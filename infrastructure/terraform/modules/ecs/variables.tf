variable "environment" {
  type    = string
  default = "production"
}

variable "vpc_id" {
  type = string
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "task_execution_role_arn" {
  type        = string
  description = "IAM Role ARN for ECS task execution (pull images, write logs)"
}

variable "worker_task_role_arn" {
  type        = string
  description = "IAM Role ARN for the validation worker (access S3, RDS, CloudWatch)"
}

variable "api_image" {
  type    = string
  default = "123456789012.dkr.ecr.us-east-1.amazonaws.com/cloudguard-api:latest"
}

variable "worker_image" {
  type    = string
  default = "123456789012.dkr.ecr.us-east-1.amazonaws.com/cloudguard-worker:latest"
}

variable "demo_app_image" {
  type    = string
  default = "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo-banking-app:latest"
}

variable "s3_reports_bucket_name" {
  type = string
}

variable "rds_endpoint" {
  type = string
}
