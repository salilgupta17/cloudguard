# CloudGuard ECS Fargate Infrastructure
# Orchestrates API, Workload, and VPC-internal Disaster Recovery Validation Worker

resource "aws_ecs_cluster" "main" {
  name = "cloudguard-dr-cluster-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "cloudguard-ecs-cluster"
    Environment = var.environment
  }
}

# ECS Security Group (Application & Validation Worker)
resource "aws_security_group" "ecs" {
  name        = "cloudguard-ecs-tasks-sg-${var.environment}"
  description = "Security Group for ECS Fargate API, Banking Workload and Validation Worker"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP ingress from VPC or internal ALB"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    description = "Outbound to VPC endpoints, NAT Gateway and RDS"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "cloudguard-ecs-sg"
    Environment = var.environment
  }
}

# 1. Validation Worker Task Definition (Invoked by EventBridge)
resource "aws_ecs_task_definition" "worker" {
  family                   = "cloudguard-validation-worker-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.worker_task_role_arn

  container_definitions = jsonencode([
    {
      name      = "validation-worker"
      image     = var.worker_image
      essential = true
      command   = ["python", "-m", "app.dr.aws_worker"]

      environment = [
        { name = "APP_ENV", value = var.environment },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "AWS_S3_REPORTS_BUCKET", value = var.s3_reports_bucket_name },
        { name = "DATABASE_URL", value = "postgresql://cloudguard_admin@${var.rds_endpoint}/cloudguard_primary" }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/cloudguard-validation-worker-${var.environment}"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "worker"
        }
      }
    }
  ])

  tags = {
    Name        = "cloudguard-validation-worker-task"
    Environment = var.environment
  }
}

# 2. CloudGuard API Task Definition
resource "aws_ecs_task_definition" "api" {
  family                   = "cloudguard-api-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.worker_task_role_arn

  container_definitions = jsonencode([
    {
      name      = "cloudguard-api"
      image     = var.api_image
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
        }
      ]
      environment = [
        { name = "APP_ENV", value = var.environment },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "AWS_S3_REPORTS_BUCKET", value = var.s3_reports_bucket_name },
        { name = "DATABASE_URL", value = "postgresql://cloudguard_admin@${var.rds_endpoint}/cloudguard_primary" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/cloudguard-api-${var.environment}"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }
    }
  ])

  tags = {
    Name        = "cloudguard-api-task"
    Environment = var.environment
  }
}
