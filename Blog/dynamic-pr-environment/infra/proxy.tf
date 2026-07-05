# =============================================================================
# AUTH PROXY LAMBDA — Makes MicroVM endpoints accessible via browser
# =============================================================================
# One proxy Lambda serves ALL PR environments.
# URL pattern: https://<proxy-url>/<microvm-id>/path

data "archive_file" "proxy" {
  type        = "zip"
  source_file = "${path.module}/../proxy/handler.py"
  output_path = "${path.module}/../proxy/handler.zip"
}

resource "aws_iam_role" "proxy" {
  name = "${var.project_name}-proxy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = { Project = var.project_name }
}

resource "aws_iam_role_policy" "proxy" {
  name = "${var.project_name}-proxy-policy"
  role = aws_iam_role.proxy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "MicroVMAccess"
        Effect = "Allow"
        Action = [
          "lambda:GetMicrovm",
          "lambda:CreateMicrovmAuthToken"
        ]
        Resource = "*"
      },
      {
        Sid    = "Logs"
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

resource "aws_lambda_function" "proxy" {
  function_name = "${var.project_name}-auth-proxy"
  role          = aws_iam_role.proxy.arn
  handler       = "handler.handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 128

  filename         = data.archive_file.proxy.output_path
  source_code_hash = data.archive_file.proxy.output_base64sha256

  tags = { Project = var.project_name }
}

resource "aws_lambda_function_url" "proxy" {
  function_name      = aws_lambda_function.proxy.function_name
  authorization_type = "NONE" # Public — reviewer can click the link

  cors {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE"]
    allow_headers = ["*"]
  }
}
