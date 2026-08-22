#!/bin/bash
# Deploy the refund Lambda function using AWS CLI.
# Run this BEFORE adding the gateway target.
#
# Prerequisites:
#   - AWS CLI configured (run `aws login` first)
#   - An IAM role for Lambda (basic execution role)
#
# Usage: ./deploy_lambda.sh <ROLE_ARN> <REGION>

set -e

ROLE_ARN=${1:?"Usage: ./deploy_lambda.sh <LAMBDA_ROLE_ARN> <REGION>"}
REGION=${2:-"us-east-1"}
FUNCTION_NAME="refund-processor"

echo "📦 Packaging Lambda..."
zip -j function.zip lambda_function.py

echo "🚀 Creating Lambda function..."
aws lambda create-function \
  --function-name $FUNCTION_NAME \
  --runtime python3.12 \
  --handler lambda_function.handler \
  --role $ROLE_ARN \
  --zip-file fileb://function.zip \
  --region $REGION \
  --architectures arm64

echo "✅ Lambda created!"
echo ""

# Get the ARN
LAMBDA_ARN=$(aws lambda get-function \
  --function-name $FUNCTION_NAME \
  --region $REGION \
  --query 'Configuration.FunctionArn' \
  --output text)

echo "Lambda ARN (use this in agentcore add gateway-target):"
echo "  $LAMBDA_ARN"
echo ""
echo "Next step:"
echo "  agentcore add gateway-target --name RefundTarget --type lambda-function-arn \\"
echo "    --lambda-arn $LAMBDA_ARN \\"
echo "    --tool-schema-file refund_tools.json \\"
echo "    --gateway RefundGateway"

# Cleanup
rm -f function.zip
