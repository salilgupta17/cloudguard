variable "environment" {
  type        = string
  default     = "production"
}

variable "vpc_id" {
  type = string
}

variable "database_subnet_ids" {
  type = list(string)
}

variable "app_security_group_id" {
  type        = string
  description = "Security Group ID of ECS Application & Validation Worker tasks"
}

variable "db_name" {
  type    = string
  default = "cloudguard_primary"
}

variable "db_username" {
  type    = string
  default = "cloudguard_admin"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "allocated_storage" {
  type    = number
  default = 20
}

variable "instance_class" {
  type    = string
  default = "db.t4g.micro"
}
