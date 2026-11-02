# CloudGuard CloudWatch Observability & SLA Alarms

# 1. Log Groups
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/cloudguard-api-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "cloudguard-api-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/cloudguard-validation-worker-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "cloudguard-worker-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "demo_app" {
  name              = "/ecs/demo-banking-app-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "cloudguard-demo-app-logs"
    Environment = var.environment
  }
}

# 2. SLA Alarms
# RTO Breach Alarm: Triggers if recovery duration exceeds 300 seconds
resource "aws_cloudwatch_metric_alarm" "rto_breach" {
  alarm_name          = "CloudGuard-RTO-SLABreach-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "RecoveryDrillDuration"
  namespace           = "CloudGuard/DisasterRecovery"
  period              = 300
  statistic           = "Maximum"
  threshold           = 300 # 300 seconds Target RTO
  alarm_description   = "Alarm triggered when isolated disaster recovery drill duration exceeds 300s SLA"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApplicationName = "demo-banking-application"
    Environment     = var.environment
  }

  tags = {
    Name        = "cloudguard-rto-alarm"
    Environment = var.environment
  }
}

# RPO Breach Alarm: Triggers if backup snapshot age exceeds 60 minutes
resource "aws_cloudwatch_metric_alarm" "rpo_breach" {
  alarm_name          = "CloudGuard-RPO-SLABreach-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "BackupFreshnessMinutes"
  namespace           = "CloudGuard/DisasterRecovery"
  period              = 300
  statistic           = "Maximum"
  threshold           = 60 # 60 minutes Target RPO
  alarm_description   = "Alarm triggered when backup snapshot age exceeds 60 minutes SLA"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApplicationName = "demo-banking-application"
    Environment     = var.environment
  }

  tags = {
    Name        = "cloudguard-rpo-alarm"
    Environment = var.environment
  }
}

# Drill Failure Alarm: Triggers if any verification check fails
resource "aws_cloudwatch_metric_alarm" "drill_failure" {
  alarm_name          = "CloudGuard-DrillFailure-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ValidationChecksFailed"
  namespace           = "CloudGuard/DisasterRecovery"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alarm triggered when one or more DR validation checks fail during an isolated drill"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApplicationName = "demo-banking-application"
    Environment     = var.environment
  }

  tags = {
    Name        = "cloudguard-failure-alarm"
    Environment = var.environment
  }
}
