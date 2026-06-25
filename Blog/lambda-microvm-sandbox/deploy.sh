#!/bin/bash
# deploy.sh — Create IAM roles (if needed) + Build and deploy the MicroVM sandbox image
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - S3 bucket created (update S3_BUCKET below)

set -e

# --- Configuration (UPDATE THESE) ---
S3_BUCKET="lambda-microvms-jatin-test"
IMAGE_NAME="python-sandbox"
REGION="us-east-1"
STACK_NAME="microvm-sandbox-roles"

# --- Step 0: Deploy IAM roles via CloudFormation ---
echo "🔐 Deploying IAM roles (CloudFormation)..."
aws cloudformation deploy \
  --template-file iam-roles.yaml \
  --stack-name ${STACK_NAME} \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides S3BucketName=${S3_BUCKET} \
  --region ${REGION} \
  --no-fail-on-empty-changeset

# Fetch role ARNs from stack outputs
BUILD_ROLE_ARN=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} \
  --query 'Stacks[0].Outputs[?OutputKey==`BuildRoleArn`].OutputValue' --output text)

echo "   Build Role: ${BUILD_ROLE_ARN}"
echo ""

# --- Package sandbox image code ---
echo "📦 Packaging sandbox image..."
cd sandbox-image
zip -r ../sandbox-code.zip Dockerfile executor.py requirements.txt
cd ..

# --- Upload to S3 ---
echo "☁️  Uploading to S3..."
aws s3 cp sandbox-code.zip s3://${S3_BUCKET}/lambda-microvm-sandbox/sandbox-code.zip

# --- Create or Update MicroVM Image ---
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
IMAGE_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:microvm-image:${IMAGE_NAME}"

# Check if image already exists
if aws lambda-microvms get-microvm-image --image-identifier ${IMAGE_ARN} --region ${REGION} > /dev/null 2>&1; then
  echo "🔨 Updating existing MicroVM image (new version)..."
  aws lambda-microvms update-microvm-image \
    --image-identifier ${IMAGE_ARN} \
    --code-artifact uri=s3://${S3_BUCKET}/lambda-microvm-sandbox/sandbox-code.zip \
    --base-image-arn arn:aws:lambda:${REGION}:aws:microvm-image:al2023-1 \
    --build-role-arn ${BUILD_ROLE_ARN} \
    --region ${REGION}
else
  echo "🔨 Creating new MicroVM image..."
  aws lambda-microvms create-microvm-image \
    --name ${IMAGE_NAME} \
    --code-artifact uri=s3://${S3_BUCKET}/lambda-microvm-sandbox/sandbox-code.zip \
    --base-image-arn arn:aws:lambda:${REGION}:aws:microvm-image:al2023-1 \
    --build-role-arn ${BUILD_ROLE_ARN} \
    --region ${REGION}
fi

echo ""
echo "✅ Image creation started!"
echo ""
echo "Check build status with:"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "  aws lambda-microvms get-microvm-image \\"
echo "    --image-identifier arn:aws:lambda:${REGION}:${ACCOUNT_ID}:microvm-image:${IMAGE_NAME} \\"
echo "    --region ${REGION}"
echo ""
echo "Build logs at:"
echo "  CloudWatch → /aws/lambda-microvms/${IMAGE_NAME}"
echo ""
echo "Once status is SUCCESSFUL, run the agent:"
echo "  cd agent && pip install -r requirements.txt && python agent.py"

# Cleanup
rm -f sandbox-code.zip
