# CloudGuard AWS Backup and Automated Restore Testing
# Orchestrates regular snapshots and automated sandbox restoration drills

resource "aws_kms_key" "backup_vault" {
  description             = "KMS Key for CloudGuard AWS Backup Vault encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name        = "cloudguard-backup-kms-key"
    Environment = var.environment
  }
}

resource "aws_backup_vault" "vault" {
  name        = "cloudguard-dr-backup-vault-${var.environment}"
  kms_key_arn = aws_kms_key.backup_vault.arn

  tags = {
    Name        = "cloudguard-dr-backup-vault"
    Environment = var.environment
  }
}

# AWS Backup Plan
resource "aws_backup_plan" "plan" {
  name = "cloudguard-dr-backup-plan-${var.environment}"

  rule {
    rule_name         = "daily-snapshot-rule"
    target_vault_name = aws_backup_vault.vault.name
    schedule          = "cron(0 3 * * ? *)" # Daily 03:00 UTC

    start_window      = 60
    completion_window = 180

    lifecycle {
      cold_storage_after = 30
      delete_after       = 365
    }

    recovery_point_tags = {
      Environment = var.environment
      Service     = "CloudGuard"
    }
  }

  tags = {
    Name        = "cloudguard-dr-backup-plan"
    Environment = var.environment
  }
}

# AWS Backup Selection (Selects RDS primary database)
resource "aws_backup_selection" "rds" {
  iam_role_arn = var.backup_role_arn
  name         = "cloudguard-rds-selection-${var.environment}"
  plan_id      = aws_backup_plan.plan.id

  resources = [
    var.rds_resource_arn
  ]
}

# AWS Backup Restore Testing Plan
# Automatically executes restore drills to verify recovery objectives (RTO/RPO)
resource "aws_backup_restore_testing_plan" "restore_test_plan" {
  name = "cloudguard-restore-testing-plan-${var.environment}"

  schedule_expression = "cron(0 6 ? * SUN *)" # Weekly Sunday at 06:00 UTC
  start_window_hours  = 4

  recovery_point_selection {
    algorithm      = "LATEST_WITHIN_WINDOW"
    recovery_point_types = ["SNAPSHOT"]
    selection_window_days = 7
  }

  tags = {
    Name        = "cloudguard-restore-testing-plan"
    Environment = var.environment
  }
}

# Assign RDS resource to the Restore Testing Plan
resource "aws_backup_restore_testing_selection" "rds_test_selection" {
  name                      = "cloudguard-restore-test-selection-${var.environment}"
  restore_testing_plan_name = aws_backup_restore_testing_plan.restore_test_plan.name
  protected_resource_type   = "RDS"
  iam_role_arn              = var.backup_role_arn

  protected_resource_arns = [
    var.rds_resource_arn
  ]

  restore_metadata_overrides = {
    "DBInstanceClass"         = "db.t4g.micro"
    "MultiAZ"                 = "false"
    "PubliclyAccessible"      = "false"
    "AutoMinorVersionUpgrade" = "false"
  }
}
