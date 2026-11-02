variable "environment" {
  type    = string
  default = "production"
}

variable "ecs_cluster_arn" {
  type        = string
  description = "ARN of the ECS Cluster for validation worker invocation"
}

variable "task_definition_arn" {
  type        = string
  description = "ARN of the validation worker task definition"
}

variable "app_subnet_ids" {
  type        = list(string)
  description = "Private application subnet IDs for the validation worker"
}

variable "app_security_group_id" {
  type        = string
  description = "Security Group ID for the validation worker"
}

variable "eventbridge_role_arn" {
  type        = string
  description = "IAM Role ARN allowing EventBridge to run ECS tasks"
}
