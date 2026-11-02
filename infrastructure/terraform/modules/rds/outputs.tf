output "db_instance_id" {
  value = aws_db_instance.primary.identifier
}

output "db_instance_arn" {
  value = aws_db_instance.primary.arn
}

output "db_endpoint" {
  value = aws_db_instance.primary.endpoint
}

output "db_address" {
  value = aws_db_instance.primary.address
}

output "db_security_group_id" {
  value = aws_security_group.rds.id
}
