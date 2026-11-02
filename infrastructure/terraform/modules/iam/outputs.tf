output "backup_role_arn" {
  value = aws_iam_role.backup_role.arn
}

output "eventbridge_role_arn" {
  value = aws_iam_role.eventbridge_role.arn
}

output "ecs_execution_role_arn" {
  value = aws_iam_role.ecs_execution_role.arn
}

output "worker_task_role_arn" {
  value = aws_iam_role.worker_task_role.arn
}
