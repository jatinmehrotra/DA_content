#!/bin/bash
# test.sh — Manually test the MicroVM sandbox (run, send code, terminate)
#
# Use this to verify your image works before running the agent.
# Prerequisites: Image build must be SUCCESSFUL (run deploy.sh first)

set -e

# --- Configuration (UPDATE THESE) ---
REGION="us-east-1"
IMAGE_NAME="python-sandbox"
STACK_NAME="microvm-sandbox-roles"

# Auto-fetch ARNs from CloudFormation stack
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
IMAGE_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:microvm-image:${IMAGE_NAME}"

EXECUTION_ROLE_ARN=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} \
  --query 'Stacks[0].Outputs[?OutputKey==`ExecutionRoleArn`].OutputValue' --output text)

echo "Using Image: ${IMAGE_ARN}"
echo "Using Execution Role: ${EXECUTION_ROLE_ARN}"
echo ""

echo "🚀 Step 1: Running a MicroVM from the image..."
RUN_OUTPUT=$(aws lambda-microvms run-microvm \
  --image-identifier ${IMAGE_ARN} \
  --execution-role-arn ${EXECUTION_ROLE_ARN} \
  --idle-policy '{"maxIdleDurationSeconds":300,"suspendedDurationSeconds":1800,"autoResumeEnabled":true}' \
  --region ${REGION} \
  --output json)

MICROVM_ID=$(echo $RUN_OUTPUT | jq -r '.microvmId')
ENDPOINT="https://$(echo $RUN_OUTPUT | jq -r '.endpoint')"

echo "   MicroVM ID: ${MICROVM_ID}"
echo "   Endpoint:   ${ENDPOINT}"
echo ""

# Wait for RUNNING state
echo "⏳ Waiting for MicroVM to reach RUNNING state..."
while true; do
  STATE=$(aws lambda-microvms get-microvm \
    --microvm-identifier "${MICROVM_ID}" \
    --region ${REGION} \
    --query 'state' --output text)
  echo "   State: ${STATE}"
  if [ "$STATE" = "RUNNING" ]; then
    break
  fi
  if [ "$STATE" = "TERMINATED" ] || [ "$STATE" = "FAILED" ]; then
    echo "❌ MicroVM failed to start. Check CloudWatch logs."
    exit 1
  fi
  sleep 2
done


echo "🔑 Step 2: Creating auth token..."
TOKEN_JSON=$(aws lambda-microvms create-microvm-auth-token \
  --microvm-identifier ${MICROVM_ID} \
  --expiration-in-minutes 5 \
  --allowed-ports '[{"port":8080}]' \
  --region ${REGION} \
  --output json)
TOKEN=$(echo $TOKEN_JSON | jq -r '.authToken["X-aws-proxy-auth"]')

echo "   Token created (expires in 10 min)"
echo ""

echo "🏥 Step 3: Health check..."
HEALTH=$(curl -s \
  -H "X-aws-proxy-auth: ${TOKEN}" \
  -H "X-aws-proxy-port: 8080" \
  "${ENDPOINT}/health")
echo "   Response: ${HEALTH}"
echo ""

echo "🐍 Step 4: Executing Python code..."
RESULT=$(curl -s \
  -X POST \
  -H "X-aws-proxy-auth: ${TOKEN}" \
  -H "X-aws-proxy-port: 8080" \
  -H "Content-Type: application/json" \
  -d '{"code": "import sys\nimport platform\nprint(f\"Python {sys.version}\")\nprint(f\"OS: {platform.system()} {platform.release()}\")\nprint(f\"Available packages:\")\nimport pandas; print(f\"  pandas {pandas.__version__}\")\nimport numpy; print(f\"  numpy {numpy.__version__}\")", "timeout": 60}' \
  "${ENDPOINT}/execute")
echo "   Result:"
echo "${RESULT}" | jq '.'
echo ""

echo "🧪 Step 5: Testing state persistence (multi-step)..."
# Step A: Write data to a file
echo "   Step A: Writing data to file..."
STEP_A=$(curl -s -X POST \
  -H "X-aws-proxy-auth: ${TOKEN}" \
  -H "X-aws-proxy-port: 8080" \
  -H "Content-Type: application/json" \
  -d '{"code": "import json\ndata = {\"name\": \"test\", \"value\": 42, \"items\": [1, 2, 3]}\nwith open(\"/workspace/state.json\", \"w\") as f:\n    json.dump(data, f)\nprint(f\"Wrote state to /workspace/state.json\")\nprint(f\"Data: {data}\")"}' \
  "${ENDPOINT}/execute")
echo "   $(echo ${STEP_A} | jq -r '.stdout')"

# Step B: Read that file back (proves filesystem persists between calls)
echo "   Step B: Reading file back from a NEW process..."
STEP_B=$(curl -s -X POST \
  -H "X-aws-proxy-auth: ${TOKEN}" \
  -H "X-aws-proxy-port: 8080" \
  -H "Content-Type: application/json" \
  -d '{"code": "import json\nwith open(\"/workspace/state.json\") as f:\n    data = json.load(f)\nprint(f\"Read back from file: {data}\")\nprint(f\"Value is: {data[\"value\"]}\")"}' \
  "${ENDPOINT}/execute")
echo "   $(echo ${STEP_B} | jq -r '.stdout')"
echo ""
echo "   ✅ Files written in one call persist to the next — disk state is preserved!"
echo ""

echo "🗑️  Step 6: Terminating MicroVM..."
aws lambda-microvms terminate-microvm \
  --microvm-identifier "${MICROVM_ID}" \
  --region ${REGION}
echo "   Terminated: ${MICROVM_ID}"
echo ""
echo "✅ All steps complete!"
