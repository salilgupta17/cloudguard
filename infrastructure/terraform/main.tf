terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Platform    = "CloudGuard"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# 1. Network Infrastructure (VPC, Subnets, NAT)
module "vpc" {
  source             = "./modules/vpc"
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}

# 2. S3 Disaster Recovery Reports & Evidence Vault
module "s3" {
  source      = "./modules/s3"
  environment = var.environment
}

# 3. CloudWatch Observability & SLA Breach Alarms
module "cloudwatch" {
  source      = "./modules/cloudwatch"
  environment = var.environment
}

# 4. IAM Roles & Least-Privilege Guardrails
module "iam" {
  source                = "./modules/iam"
  environment           = var.environment
  s3_reports_bucket_arn = module.s3.bucket_arn
  primary_rds_arn       = module.rds.db_instance_arn
}

# 5. RDS PostgreSQL 16 Primary Database
module "rds" {
  source                = "./modules/rds"
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  database_subnet_ids   = module.vpc.database_subnet_ids
  app_security_group_id = module.ecs.security_group_id
  db_password           = var.db_password
}

# 6. AWS Backup & Restore Testing
module "backup" {
  source           = "./modules/backup"
  environment      = var.environment
  backup_role_arn  = module.iam.backup_role_arn
  rds_resource_arn = module.rds.db_instance_arn
}

# 7. ECS Fargate Cluster & Validation Worker Task
module "ecs" {
  source                  = "./modules/ecs"
  environment             = var.environment
  vpc_id                  = module.vpc.vpc_id
  aws_region              = var.aws_region
  task_execution_role_arn = module.iam.ecs_execution_role_arn
  worker_task_role_arn    = module.iam.worker_task_role_arn
  s3_reports_bucket_name  = module.s3.bucket_name
  rds_endpoint            = module.rds.db_endpoint
}

# 8. EventBridge Restore Event Integration
module "eventbridge" {
  source                 = "./modules/eventbridge"
  environment            = var.environment
  ecs_cluster_arn        = module.ecs.cluster_arn
  task_definition_arn    = module.ecs.worker_task_definition_arn
  app_subnet_ids         = module.vpc.app_subnet_ids
  app_security_group_id  = module.ecs.security_group_id
  eventbridge_role_arn   = module.iam.eventbridge_role_arn
}
