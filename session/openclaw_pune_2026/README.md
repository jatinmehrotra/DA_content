# Designing Production-Ready Agents on AWS with AgentCore

> Demo code from the session **"Designing Production-Ready OpenClaw on AWS"** at AWS User Group Pune, August 2026.
>
> **Speaker**: Jatin Mehrotra | Developer Advocate, AWS

This repo demonstrates deploying a simple Python agent (built with [Strands Agents](https://strandsagents.com/)) to **Amazon Bedrock AgentCore**, then layering on enterprise features: **Policy** (Cedar-based authorization), **Identity**, and **Observability** - all without changing agent code.

**Key takeaway**: AgentCore is not just for OpenClaw. It works with Strands, LangGraph, Google ADK, OpenAI Agents, or any framework.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Amazon Bedrock AgentCore                       │
│                                                                   │
│  ┌──────────┐     ┌──────────────┐     ┌────────────────────┐   │
│  │  Client   │────▶│   Gateway    │────▶│  AgentCore Runtime │   │
│  │  (curl)   │     │  + Policy    │     │  (Firecracker VM)  │   │
│  └──────────┘     │  Engine      │     │                    │   │
│                    │              │     │  ┌──────────────┐  │   │
│                    │  Cedar rules │     │  │ Strands Agent │  │   │
│                    │  evaluated   │     │  │ + tools       │  │   │
│                    │  HERE        │     │  └──────────────┘  │   │
│                    └──────────────┘     └────────────────────┘   │
│                           │                        │              │
│                    ┌──────▼────────────────────────▼──────┐      │
│                    │        CloudWatch Observability       │      │
│                    │     Traces / Logs / Policy Decisions  │      │
│                    └──────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- **AWS Account** with credentials configured
- **Node.js 20+** (for AgentCore CLI)
- **Python 3.10+**
- **Python 3.12 recommended** (via `brew install python@3.12` on macOS)
- **AWS CDK** bootstrapped: `npx cdk bootstrap aws://<ACCOUNT_ID>/<REGION>`
- **Claude Sonnet 4** enabled in Amazon Bedrock console
- **IAM permissions** for AgentCore (see [docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-get-started-cli.html))

---

## Quick Start

### 0. Set up Python environment

macOS ships with Python 3.9 (Xcode CLI tools) which is too old. Use Python 3.12:

```bash
# Install Python 3.12 (if not already installed)
brew install python@3.12

# Create a virtual environment
/opt/homebrew/bin/python3.12 -m venv .venv

# Activate it
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install strands-agents "botocore[crt]" bedrock-agentcore

# Authenticate with AWS
aws login
```

> **Note**: `strands-agents` requires Python 3.10+. If you see "No matching distribution found", check your Python version with `python --version`.

### 1. Install the AgentCore CLI

```bash
npm install -g @aws/agentcore
agentcore --version
```

### 2. Create the project (scaffold)

```bash
agentcore create --name RefundAgent --framework Strands \
  --model-provider Bedrock --memory none --build CodeZip
```

### 3. Replace the agent code

Copy `app/RefundAgent/main.py` from this repo into the scaffolded project's `app/RefundAgent/main.py`.

### 4. Test locally

```bash
cd RefundAgent
agentcore dev
```

This opens the Agent Inspector in your browser. Try:
> "Process a refund of $200 for order ORD-9981, reason: defective product"

### 5. Deploy to AgentCore Runtime

```bash
agentcore deploy
```

### 6. Invoke the deployed agent

```bash
agentcore invoke --prompt "Refund $150 for order ORD-1234, item arrived damaged" --stream
```

---

## Adding Policy (Cedar Authorization)

This is the key feature. Policy enforcement happens **outside** agent code, at the Gateway boundary. Even if the LLM is tricked via prompt injection, the Gateway blocks unauthorized actions.

> **Note**: The commands below assume you are inside the `RefundAgent/` project directory (from Step 4). Paths to repo files use `../` to reference the parent (repo root).

### Step 1: Deploy the Lambda target (one-time setup)

The Lambda is the backend that processes refunds. You need it deployed first so you have an ARN for the gateway target.

```bash
# Get your AWS account ID
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"

# Create a Lambda execution role (skip if you already have one)
aws iam create-role --role-name RefundLambdaRole \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
aws iam attach-role-policy --role-name RefundLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Wait 10 seconds for IAM propagation, then deploy the Lambda (script is in repo root)
sleep 10
chmod +x ../lambda/deploy_lambda.sh
../lambda/deploy_lambda.sh arn:aws:iam::${ACCOUNT_ID}:role/RefundLambdaRole us-east-1
```

The script prints the **Lambda ARN**. Save it for the next step (or export it):

```bash
export LAMBDA_ARN=$(aws lambda get-function --function-name refund-processor --query 'Configuration.FunctionArn' --output text)
echo "Lambda ARN: $LAMBDA_ARN"
```

### Step 2: Add a Gateway + Lambda Target + Policy Engine

```bash
# Copy the tool schema into the project directory
cp ../refund_tools.json .

# Add gateway (no auth for demo simplicity)
agentcore add gateway --name RefundGateway --authorizer-type NONE --runtimes RefundAgent

# Add the Lambda as a gateway target (use the ARN from Step 1)
agentcore add gateway-target --name RefundTarget --type lambda-function-arn \
  --lambda-arn $LAMBDA_ARN \
  --tool-schema-file refund_tools.json \
  --gateway RefundGateway

# Add policy engine in ENFORCE mode
agentcore add policy-engine --name RefundPolicyEngine \
  --attach-to-gateways RefundGateway \
  --attach-mode ENFORCE

# Deploy to create the gateway
agentcore deploy
```

### Step 3: Add a Cedar policy (natural language!)

```bash
agentcore add policy --name RefundLimit \
  --engine RefundPolicyEngine \
  --generate "Only allow refunds under 1000 dollars" \
  --gateway RefundGateway

# Redeploy with policy attached
agentcore deploy
```

### Step 4: Test the policy

Get your gateway URL. The format is `https://<gateway-id>.gateway.bedrock-agentcore.<region>.amazonaws.com`.
Your gateway ID is shown in `agentcore status` (e.g., `refundagent-refundgateway-d9jafwgmey`).

```bash
export GATEWAY_URL="https://<your-gateway-id>.gateway.bedrock-agentcore.us-east-1.amazonaws.com"
```

**Allowed - $500 refund:**
```bash
curl -X POST "$GATEWAY_URL/mcp" -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"RefundTarget___process_refund","arguments":{"order_id":"ORD-5001","amount":500,"reason":"Wrong item"}}}'
```

**Denied - $2000 refund:**
```bash
curl -X POST "$GATEWAY_URL/mcp" -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"RefundTarget___process_refund","arguments":{"order_id":"ORD-5002","amount":2000,"reason":"Changed mind"}}}'
```

The $2000 request is **blocked by the Gateway** before it ever reaches the agent.

---

## Observability

Traces appear in the AgentCore console when requests go through the **agent runtime** (not direct Gateway curl calls).

### To see full end-to-end traces:

Invoke through the agent (this triggers the agent loop → tool call → Gateway → policy → Lambda):

```bash
agentcore invoke --prompt "Process a refund of 500 dollars for order ORD-5001, reason: wrong item shipped" --stream
```

This generates a full trace visible in the AgentCore console: agent reasoning → tool call → policy evaluation → Lambda execution.

### View traces and logs via CLI:

```bash
# List recent traces (from agent runtime invocations)
agentcore traces list

# Get details for a specific trace
agentcore traces get <trace-id>

# Stream runtime logs
agentcore logs --since 10m
```

### Direct Gateway curl tests vs Agent invocations:

| Method | Traces in console? | Use for |
|--------|-------------------|---------|
| `agentcore invoke --prompt "..."` | ✅ Yes (full trace) | Showing end-to-end observability |
| `curl $GATEWAY_URL/mcp` | ❌ Policy logs only | Demonstrating policy enforcement (allow/deny) |

> **Demo tip**: Use `agentcore invoke` to show observability, then switch to `curl` for the dramatic policy deny moment.

---

## Advanced: Role-Based Policies

See `policies/refund_policy_advanced.cedar` for production-style policies using JWT claims:

- Tier-1 support: up to $100
- Tier-2 support: up to $5000
- Finance team: unlimited

Enable JWT authorization on the gateway:
```bash
agentcore add gateway --name RefundGateway --authorizer-type JWT --issuer <cognito-url>
```

---

## Project Structure

```
openclaw_pune_2026/
├── README.md                              # This file
├── app/
│   └── RefundAgent/
│       ├── main.py                        # Agent code (Strands + AgentCore wrapper)
│       └── pyproject.toml                 # Python dependencies
├── lambda/
│   ├── lambda_function.py                 # Refund tool backend (Lambda)
│   └── deploy_lambda.sh                   # One-command Lambda deployment script
├── refund_tools.json                      # Tool schema for Gateway target
├── policies/
│   ├── refund_policy.cedar                # Basic: refunds < $1000
│   └── refund_policy_advanced.cedar       # Advanced: role-based access
└── .gitignore
```

---

## Key Concepts Demonstrated

| Feature | What it does | Why it matters |
|---------|-------------|----------------|
| **AgentCore Runtime** | Hosts your agent in Firecracker microVMs | Hardware isolation, serverless scaling, pay-per-use |
| **AgentCore Gateway** | Intercepts all tool calls | Single enforcement point for policies |
| **AgentCore Policy** | Cedar-based authorization rules | Deterministic, outside agent code, immune to prompt injection |
| **AgentCore Identity** | Workload identity for agents | Centralized management, OAuth 2.0, credential vault |
| **AgentCore Observability** | End-to-end tracing | Every tool call, every policy decision, logged and traced |

---

## Resources

- [Strands Agents SDK](https://strandsagents.com/)
- [Amazon Bedrock AgentCore Docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [AgentCore Policy - Getting Started](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-getting-started.html)
- [AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html)
- [Cedar Policy Language](https://www.cedarpolicy.com/)
- [AgentCore CLI on GitHub](https://github.com/aws/agentcore-cli)

---

## Clean Up

```bash
agentcore remove all
agentcore deploy
```

---

## License

This demo code is provided as-is for educational purposes. See [LICENSE](LICENSE) for details.
