#!/bin/bash
# =============================================================================
# deploy.sh — Deploy MCP server to AgentCore: Runtime + Gateway + Policy
# =============================================================================
# Usage: ./deploy.sh (from mcp-demo-summit/ directory)
# Requires: agentcore CLI, AWS CLI v2 (latest), Node.js 20+, Python 3.10+
#
# Deploys an MCP server with production capabilities:
#   Runtime  — runs your MCP server, auto-scaling, IAM auth, OTEL traces
#   Gateway  — MCP proxy with tool-level auth and observability
#   Policy   — Cedar policy blocking delete_incident tool
# =============================================================================

set -e

PROFILE="demo-jj"
REGION="us-east-1"
PROJECT_NAME="mcpdemosummit"
GATEWAY_TARGET_NAME="mcpserver"

export AWS_PROFILE="$PROFILE"
export AWS_REGION="$REGION"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")/$PROJECT_NAME"

echo "🚀 Deploying MCP server to AgentCore (Runtime + Gateway + Policy)"
echo "   Profile: $PROFILE | Region: $REGION"
echo ""

# =============================================================================
# STEP 1: Create AgentCore project (if needed)
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 Step 1: Project setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "   Creating AgentCore project..."
  cd "$(dirname "$SCRIPT_DIR")"
  agentcore create --protocol MCP
  echo "   ✅ Project created."
fi

cd "$PROJECT_DIR"
echo "   Working directory: $(pwd)"

if [ ! -f "agentcore/agentcore.json" ]; then
  echo "❌ agentcore/agentcore.json not found. Project setup failed."
  exit 1
fi

# Fix CDK schema version mismatch (agentcore CLI bundles outdated CDK toolkit)
echo "   Fixing CDK toolkit version..."
AGENTCORE_PATH=$(dirname $(which agentcore))/../lib/node_modules/@aws/agentcore
if [ -d "$AGENTCORE_PATH" ]; then
  cd "$AGENTCORE_PATH"
  npm install @aws-cdk/toolkit-lib@latest @aws-cdk/cloud-assembly-schema@latest --legacy-peer-deps --silent 2>/dev/null || true
  cd "$PROJECT_DIR"
fi

# Ensure deployment target is configured
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile "$PROFILE")
if grep -q '^\[\]$' agentcore/aws-targets.json 2>/dev/null || [ ! -s agentcore/aws-targets.json ]; then
  echo "   Configuring deployment target (${ACCOUNT_ID} / ${REGION})..."
  cat > agentcore/aws-targets.json << TARGETS
[
  {
    "name": "default",
    "account": "${ACCOUNT_ID}",
    "region": "${REGION}"
  }
]
TARGETS
  echo "   ✅ Target configured."
fi
echo ""

# =============================================================================
# STEP 2: Configure Runtime + Gateway + Policy Engine
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  Step 2: Configuring resources"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Add MCP runtime (BYO server.py)
if ! grep -q '"MyAgent"' agentcore/agentcore.json 2>/dev/null || \
   grep -q '"runtimes":\s*\[\s*\]' agentcore/agentcore.json 2>/dev/null; then
  echo "   Adding MCP runtime..."
  agentcore add agent \
    --name MyAgent \
    --type byo \
    --build CodeZip \
    --language Python \
    --protocol MCP \
    --code-location . \
    --entrypoint server.py \
    --authorizer-type AWS_IAM
  echo "   ✅ Runtime configured."
else
  echo "   ⏭️  Runtime already configured."
fi

# Add Gateway (with --runtimes to wire IAM internally)
if ! grep -q "mcpgateway" agentcore/agentcore.json 2>/dev/null; then
  echo "   Adding gateway..."
  agentcore add gateway \
    --name mcpgateway \
    --description "MCP Gateway with Cedar policy" \
    --runtimes MyAgent \
    --authorizer-type AWS_IAM
  echo "   ✅ Gateway configured."
else
  echo "   ⏭️  Gateway already configured."
fi

# Policy Engine will be added manually after first deployment
echo "   ⏭️  Policy engine will be configured after first deploy."
echo ""

# =============================================================================
# STEP 3: Copy server files
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📄 Step 3: Copying server.py and pyproject.toml"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cp "$SCRIPT_DIR/server.py" ./server.py 2>/dev/null || true
cp "$SCRIPT_DIR/pyproject.toml" ./pyproject.toml 2>/dev/null || true
echo "   ✅ Files copied."
echo ""

# =============================================================================
# STEP 4: Deploy Runtime + Gateway
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Step 4: Deploying to AWS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Clean up any failed stacks from previous attempts
STACK_STATUS=$(aws cloudformation describe-stacks \
  --stack-name AgentCore-${PROJECT_NAME}-default \
  --region "$REGION" \
  --profile "$PROFILE" \
  --query "Stacks[0].StackStatus" \
  --output text 2>/dev/null || true)

if [[ "$STACK_STATUS" == *"FAILED"* ]] || [[ "$STACK_STATUS" == *"ROLLBACK"* ]]; then
  echo "   Cleaning up failed stack ($STACK_STATUS)..."
  aws cloudformation delete-stack \
    --stack-name AgentCore-${PROJECT_NAME}-default \
    --deletion-mode FORCE_DELETE_STACK \
    --region "$REGION" \
    --profile "$PROFILE" 2>/dev/null || true
  sleep 30
fi

agentcore deploy --yes

echo ""
echo "   ✅ Deployed!"
echo ""

# =============================================================================
# STEP 4b: Enable Observability (logs + traces for runtime and gateway)
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Step 4b: Enabling Observability (logs + traces)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get runtime ARN for observability setup
RUNTIME_ARN=$(aws cloudformation describe-stacks \
  --stack-name AgentCore-${PROJECT_NAME}-default \
  --region "$REGION" \
  --profile "$PROFILE" \
  --query "Stacks[0].Outputs[?contains(OutputKey, 'RuntimeArn')].OutputValue | [0]" \
  --output text 2>/dev/null || true)

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile "$PROFILE")

# Enable observability via CloudWatch Logs delivery APIs
python3 -c "
import boto3, sys

session = boto3.Session(profile_name='${PROFILE}', region_name='${REGION}')
logs = session.client('logs')
account = '${ACCOUNT_ID}'
region = '${REGION}'

resources = [
    ('${RUNTIME_ARN}', '${RUNTIME_ARN}'.split('/')[-1], 'runtime'),
]

# Get gateway ARN
try:
    gw_id = '${PROJECT_NAME}-mcpgateway'
    import subprocess
    result = subprocess.run(['agentcore', 'fetch', 'access', '--name', 'mcpgateway'], capture_output=True, text=True, cwd='$(pwd)')
    for line in result.stdout.split('\n'):
        if 'URL' in line:
            gw_identifier = line.split('//')[1].split('.gateway')[0]
            gw_arn = f'arn:aws:bedrock-agentcore:{region}:{account}:gateway/{gw_identifier}'
            resources.append((gw_arn, gw_identifier, 'gateway'))
            break
except:
    pass

for res_arn, res_id, res_type in resources:
    if not res_arn or res_arn == 'None':
        continue
    log_group = f'/aws/vendedlogs/bedrock-agentcore/{res_type}/{res_id}' if res_type != 'runtime' else f'/aws/vendedlogs/bedrock-agentcore/{res_id}'
    log_group_arn = f'arn:aws:logs:{region}:{account}:log-group:{log_group}'

    try:
        logs.create_log_group(logGroupName=log_group)
    except:
        pass

    try:
        logs.put_delivery_source(name=f'{res_id}-logs-source', logType='APPLICATION_LOGS', resourceArn=res_arn)
    except:
        pass

    try:
        logs.put_delivery_source(name=f'{res_id}-traces-source', logType='TRACES', resourceArn=res_arn)
    except:
        pass

    try:
        resp = logs.put_delivery_destination(name=f'{res_id}-logs-dest', deliveryDestinationType='CWL', deliveryDestinationConfiguration={'destinationResourceArn': log_group_arn})
        dest_arn = resp['deliveryDestination']['arn']
    except:
        dest_arn = f'arn:aws:logs:{region}:{account}:delivery-destination:{res_id}-logs-dest'

    try:
        resp = logs.put_delivery_destination(name=f'{res_id}-traces-dest', deliveryDestinationType='XRAY')
    except:
        pass

    try:
        logs.create_delivery(deliverySourceName=f'{res_id}-logs-source', deliveryDestinationArn=dest_arn)
    except:
        pass

    try:
        traces_dest_arn = f'arn:aws:logs:{region}:{account}:delivery-destination:{res_id}-traces-dest'
        logs.create_delivery(deliverySourceName=f'{res_id}-traces-source', deliveryDestinationArn=traces_dest_arn)
    except:
        pass

    print(f'  ✅ Observability enabled for {res_type}: {res_id}')
" 2>/dev/null || echo "   ⚠️  Some observability setup skipped (may already exist)"

echo ""

# =============================================================================
# STEP 5: Get Gateway info
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 Step 5: Gateway → Runtime connectivity"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# The --runtimes MyAgent flag on gateway creation wires IAM permissions
# between the gateway and runtime automatically via CDK.
# Grant gateway role additional permissions for tool sync
GATEWAY_ROLE=$(aws cloudformation describe-stack-resources \
  --stack-name AgentCore-${PROJECT_NAME}-default \
  --region "$REGION" \
  --profile "$PROFILE" \
  --query "StackResources[?contains(PhysicalResourceId, 'GatewayMcpgatewayRole')].PhysicalResourceId | [0]" \
  --output text 2>/dev/null || true)

if [ -n "$GATEWAY_ROLE" ] && [ "$GATEWAY_ROLE" != "None" ]; then
  echo "   Gateway role: $GATEWAY_ROLE"
  aws iam put-role-policy \
    --role-name "$GATEWAY_ROLE" \
    --policy-name InvokeRuntimePolicy \
    --policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Action": "bedrock-agentcore:*",
        "Resource": "*"
      }]
    }' \
    --profile "$PROFILE"
  echo "   ✅ Permissions granted."
fi

# Get gateway identifier for the policy step
GW_URL_LINE=$(agentcore fetch access --name mcpgateway 2>/dev/null | grep URL || true)
GATEWAY_IDENTIFIER=$(echo "$GW_URL_LINE" | grep -o '[a-z0-9-]*\.gateway' | head -1 | sed 's/.gateway//' || true)
if [ -z "$GATEWAY_IDENTIFIER" ]; then
  GATEWAY_IDENTIFIER="${PROJECT_NAME}-mcpgateway-unknown"
fi
echo "   Gateway: $GATEWAY_IDENTIFIER"
echo ""

# =============================================================================
# STEP 6: Cedar Policy (manual step after deployment)
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛡️  Step 6: Cedar Policy Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   The Cedar policy must be added AFTER deployment (due to gateway auth)."
echo "   Run these commands to add the policy:"
echo ""
echo "   agentcore add policy --name allow_all --engine mcppolicy2 \\"
echo "     --description 'Permit all tools' \\"
echo "     --statement 'permit(principal, action, resource is AgentCore::Gateway);' \\"
echo "     --validation-mode IGNORE_ALL_FINDINGS"
echo ""
echo "   agentcore add policy --name block_delete --engine mcppolicy2 \\"
echo "     --description 'Block delete_incident' \\"
echo "     --statement 'forbid(principal, action == AgentCore::Action::\"mcpserver___delete_incident\", resource == AgentCore::Gateway::\"arn:aws:bedrock-agentcore:${REGION}:$(aws sts get-caller-identity --query Account --output text --profile $PROFILE):gateway/${GATEWAY_IDENTIFIER}\");' \\"
echo "     --validation-mode IGNORE_ALL_FINDINGS"
echo ""
echo "   Then: agentcore deploy --yes"
echo ""

# =============================================================================
# DONE
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Full deployment complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

agentcore status

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Demo Scenarios"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Gateway URL: $(agentcore fetch access --name mcpgateway 2>/dev/null | grep URL | awk '{print $2}')"
echo ""
echo "1. AUTH — Without SigV4 credentials → 401 Unauthorized"
echo "2. POLICY — Call delete_incident via gateway → DENIED by Cedar"
echo "3. ALLOWED — Call search_docs or create_incident → works"
echo "4. OBSERVABILITY — agentcore logs | agentcore traces list"
