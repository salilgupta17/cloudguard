output "cluster_id" {
  value = aws_ecs_cluster.main.id
}

output "cluster_arn" {
  value = aws_ecs_cluster.main.arn
}

output "security_group_id" {
  value = aws_security_group.ecs.id
}

output "worker_task_definition_arn" {
  value = aws_ecs_task_definition.worker.arn
}

output "api_task_definition_arn" {
  value = aws_ecs_task_definition.api.arn
}
