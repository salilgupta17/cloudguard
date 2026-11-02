# CloudGuard EventBridge Automation
# Captures AWS Backup Restore Job events and triggers VPC-internal validation worker

resource "aws_cloudwatch_event_rule" "restore_event" {
  name        = "cloudguard-backup-restore-event-${var.environment}"
  description = "Captures AWS Backup restore job completion and failure events"

  event_pattern = jsonencode({
    source      = ["aws.backup"],
    detail-type = ["Restore Job State Change"],
    detail = {
      status = ["COMPLETED", "FAILED"]
    }
  })

  tags = {
    Name        = "cloudguard-restore-rule"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "ecs_worker" {
  rule      = aws_cloudwatch_event_rule.restore_event.name
  target_id = "cloudguard-validation-worker-target"
  arn       = var.ecs_cluster_arn
  role_arn  = var.eventbridge_role_arn

  ecs_target {
    task_count          = 1
    task_definition_arn = var.task_definition_arn
    launch_type         = "FARGATE"
    platform_version    = "LATEST"

    network_configuration {
      subnets          = var.app_subnet_ids
      security_groups  = [var.app_security_group_id]
      assign_public_ip = false
    }
  }
}
