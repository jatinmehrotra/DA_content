output "s3_bucket_name" {
  description = "S3 bucket for MicroVM code artifacts"
  value       = aws_s3_bucket.artifacts.id
}

output "dynamodb_table_name" {
  description = "DynamoDB table for PR environment data"
  value       = aws_dynamodb_table.pr_data.name
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions to assume via OIDC"
  value       = aws_iam_role.github_actions.arn
}

output "microvm_build_role_arn" {
  description = "IAM role ARN for MicroVM image builds"
  value       = aws_iam_role.microvm_build.arn
}

output "microvm_execution_role_arn" {
  description = "IAM role ARN for running MicroVMs"
  value       = aws_iam_role.microvm_execution.arn
}
