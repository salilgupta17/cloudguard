output "api_log_group_name" {
  value = aws_cloudwatch_log_group.api.name
}

output "worker_log_group_name" {
  value = aws_cloudwatch_log_group.worker.name
}

output "rto_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.rto_breach.arn
}

output "rpo_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.rpo_breach.arn
}
