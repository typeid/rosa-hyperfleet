# =============================================================================
# HyperFleet DB Module Outputs
# =============================================================================

output "endpoint" {
  description = "RDS instance endpoint (host:port)"
  value       = aws_db_instance.hyperfleet_db.endpoint
}

output "address" {
  description = "RDS instance hostname"
  value       = aws_db_instance.hyperfleet_db.address
}

output "port" {
  description = "RDS instance port"
  value       = aws_db_instance.hyperfleet_db.port
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.hyperfleet_db.db_name
}

output "dsn_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the PostgreSQL DSN"
  value       = aws_secretsmanager_secret.dsn.arn
}

output "dsn_secret_name" {
  description = "Name of the Secrets Manager secret containing the PostgreSQL DSN"
  value       = aws_secretsmanager_secret.dsn.name
}

output "master_password_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the master password"
  value       = aws_secretsmanager_secret.master.arn
}

output "security_group_id" {
  description = "Security group ID for the RDS instance"
  value       = aws_security_group.hyperfleet_db.id
}

output "kms_key_arn" {
  description = "KMS key ARN used for RDS encryption"
  value       = aws_kms_key.hyperfleet_db.arn
}

output "instance_id" {
  description = "RDS instance identifier"
  value       = aws_db_instance.hyperfleet_db.id
}
