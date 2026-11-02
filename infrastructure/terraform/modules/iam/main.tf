# CloudGuard Least-Privilege IAM Roles & Security Guardrails

# 1. AWS Backup Service Role
resource "aws_iam_role" "backup_role" {
  name = "cloudguard-aws-backup-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = { Service = "backup.amazonaws.com" },
        Action    = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "cloudguard-backup-role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "backup_policy" {
  role       = aws_iam_role.backup_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "restore_policy" {
  role       = aws_iam_role.backup_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

# 2. EventBridge Invocation Role for ECS
resource "aws_iam_role" "eventbridge_role" {
  name = "cloudguard-eventbridge-ecs-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = { Service = "events.amazonaws.com" },
        Action    = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "cloudguard-eventbridge-role"
    Environment = var.environment
  }
}

resource "aws_iam_policy" "eventbridge_run_task" {
  name        = "cloudguard-eventbridge-run-task-policy-${var.environment}"
  description = "Allows EventBridge to launch CloudGuard validation worker tasks"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["ecs:RunTask"],
        Resource = ["*"]
      },
      {
        Effect   = "Allow",
        Action   = ["iam:PassRole"],
        Resource = ["*"]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eventbridge_attach" {
  role       = aws_iam_role.eventbridge_role.name
  policy_arn = aws_iam_policy.eventbridge_run_task.arn
}

# 3. ECS Task Execution Role (Pull images, CloudWatch logs)
resource "aws_iam_role" "ecs_execution_role" {
  name = "cloudguard-ecs-execution-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = { Service = "ecs-tasks.amazonaws.com" },
        Action    = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "cloudguard-ecs-execution-role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_attach" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# 4. Validation Worker Task Role (Least Privilege with Safety Guardrail)
resource "aws_iam_role" "worker_task_role" {
  name = "cloudguard-worker-task-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = { Service = "ecs-tasks.amazonaws.com" },
        Action    = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "cloudguard-worker-task-role"
    Environment = var.environment
  }
}

resource "aws_iam_policy" "worker_policy" {
  name        = "cloudguard-worker-least-privilege-policy-${var.environment}"
  description = "Allows S3 report writing, CloudWatch emission, and ephemeral sandbox cleanup with safety interlock"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      # S3 Access
      {
        Sid    = "S3ReportsAccess",
        Effect = "Allow",
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ],
        Resource = [
          var.s3_reports_bucket_arn,
          "${var.s3_reports_bucket_arn}/*"
        ]
      },
      # CloudWatch Telemetry
      {
        Sid    = "CloudWatchMetricsAndLogs",
        Effect = "Allow",
        Action = [
          "cloudwatch:PutMetricData",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      },
      # AWS Backup Job Inspection
      {
        Sid    = "BackupInspection",
        Effect = "Allow",
        Action = [
          "backup:DescribeRestoreJob",
          "backup:GetRecoveryPointRestoreMetadata"
        ],
        Resource = "*"
      },
      # Ephemeral Sandbox Teardown (Allowed only for isolated instances)
      {
        Sid    = "SandboxRDSDescribe",
        Effect = "Allow",
        Action = [
          "rds:DescribeDBInstances"
        ],
        Resource = "*"
      },
      {
        Sid    = "SandboxRDSDelete",
        Effect = "Allow",
        Action = [
          "rds:DeleteDBInstance"
        ],
        Resource = ["arn:aws:rds:*:*:db:cloudguard-isolated-*"]
      },
      # SAFETY INTERLOCK: Explicitly DENY deletion of the primary production RDS instance
      {
        Sid       = "SafetyInterlockDenyPrimaryDeletion",
        Effect    = "Deny",
        Action    = ["rds:DeleteDBInstance"],
        Resource  = [var.primary_rds_arn]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "worker_policy_attach" {
  role       = aws_iam_role.worker_task_role.name
  policy_arn = aws_iam_policy.worker_policy.arn
}
