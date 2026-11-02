# CloudGuard Production RDS PostgreSQL Instance
# Deployed in private isolated database subnets with Multi-AZ redundancy and automated snapshots

resource "aws_db_subnet_group" "rds" {
  name       = "cloudguard-db-subnet-group-${var.environment}"
  subnet_ids = var.database_subnet_ids

  tags = {
    Name        = "cloudguard-db-subnet-group"
    Environment = var.environment
  }
}

resource "aws_security_group" "rds" {
  name        = "cloudguard-rds-sg-${var.environment}"
  description = "Allows PostgreSQL ingress strictly from ECS application and validation worker"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from application and DR worker"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "cloudguard-rds-sg"
    Environment = var.environment
  }
}

resource "aws_db_instance" "primary" {
  identifier                  = "cloudguard-rds-primary-${var.environment}"
  engine                      = "postgres"
  engine_version              = "16.1"
  instance_class              = var.instance_class
  allocated_storage           = var.allocated_storage
  max_allocated_storage       = 100
  storage_type                = "gp3"
  storage_encrypted           = true
  multi_az                    = true
  publicly_accessible         = false
  auto_minor_version_upgrade  = true
  allow_major_version_upgrade = false

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Sun:04:30-Sun:05:30"
  deletion_protection     = false # Set true in strict enterprise production
  skip_final_snapshot     = true

  tags = {
    Name        = "cloudguard-rds-primary"
    Environment = var.environment
    ProtectedBy = "AWSBackup"
    Tier        = "MissionCritical"
  }
}
