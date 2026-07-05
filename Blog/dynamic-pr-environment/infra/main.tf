terraform {
  required_version = ">= 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}

# =============================================================================
# S3 BUCKET — Stores MicroVM code artifacts (Dockerfile + app.py zip)
# =============================================================================

resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.project_name}-artifacts-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project = var.project_name
  }
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

# =============================================================================
# DYNAMODB TABLE — Shared table for all PR environments (partitioned by PR#)
# =============================================================================

resource "aws_dynamodb_table" "pr_data" {
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  tags = {
    Project = var.project_name
  }
}

# =============================================================================
# GITHUB OIDC — Allows GitHub Actions to assume IAM role without secrets
# =============================================================================

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]

  tags = {
    Project = var.project_name
  }
}

# =============================================================================
# IAM ROLE — GitHub Actions assumes this to manage MicroVMs
# =============================================================================

resource "aws_iam_role" "github_actions" {
  name = "${var.project_name}-github-actions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
        }
      }
    }]
  })

  tags = {
    Project = var.project_name
  }
}

resource "aws_iam_role_policy" "github_actions" {
  name = "${var.project_name}-github-actions-policy"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Artifacts"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.artifacts.arn}/*"
      },
      {
        Sid    = "MicroVMManage"
        Effect = "Allow"
        Action = [
          "lambda:CreateMicrovmImage",
          "lambda:UpdateMicrovmImage",
          "lambda:GetMicrovmImage",
          "lambda:GetMicrovmImageVersion",
          "lambda:RunMicrovm",
          "lambda:GetMicrovm",
          "lambda:ListMicrovms",
          "lambda:TerminateMicrovm",
          "lambda:CreateMicrovmAuthToken"
        ]
        Resource = "*"
      },
      {
        Sid    = "PassRoles"
        Effect = "Allow"
        Action = "iam:PassRole"
        Resource = [
          aws_iam_role.microvm_build.arn,
          aws_iam_role.microvm_execution.arn
        ]
      }
    ]
  })
}

# =============================================================================
# MICROVM BUILD ROLE — Used during create/update-microvm-image
# =============================================================================

resource "aws_iam_role" "microvm_build" {
  name = "${var.project_name}-microvm-build"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = ["sts:AssumeRole", "sts:TagSession"]
    }]
  })

  tags = {
    Project = var.project_name
  }
}

resource "aws_iam_role_policy" "microvm_build" {
  name = "${var.project_name}-microvm-build-policy"
  role = aws_iam_role.microvm_build.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadArtifacts"
        Effect = "Allow"
        Action = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.artifacts.arn}/*"
      },
      {
        Sid    = "BuildLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# =============================================================================
# MICROVM EXECUTION ROLE — Used at runtime by the running MicroVM
# =============================================================================

resource "aws_iam_role" "microvm_execution" {
  name = "${var.project_name}-microvm-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = ["sts:AssumeRole", "sts:TagSession"]
    }]
  })

  tags = {
    Project = var.project_name
  }
}

resource "aws_iam_role_policy" "microvm_execution" {
  name = "${var.project_name}-microvm-execution-policy"
  role = aws_iam_role.microvm_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDB"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:DeleteItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = aws_dynamodb_table.pr_data.arn
      },
      {
        Sid    = "RuntimeLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}
