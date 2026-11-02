output "rule_name" {
  value = aws_cloudwatch_event_rule.restore_event.name
}

output "rule_arn" {
  value = aws_cloudwatch_event_rule.restore_event.arn
}
