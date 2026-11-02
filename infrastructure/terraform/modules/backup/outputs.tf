output "vault_name" {
  value = aws_backup_vault.vault.name
}

output "vault_arn" {
  value = aws_backup_vault.vault.arn
}

output "backup_plan_id" {
  value = aws_backup_plan.plan.id
}

output "restore_testing_plan_name" {
  value = aws_backup_restore_testing_plan.restore_test_plan.name
}
