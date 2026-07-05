# MCP Demo Server — MCP Dev Summit Bengaluru 2026

A minimal MCP (Model Context Protocol) server built for a live 30-minute presentation at MCP Dev Summit Bengaluru 2026. This demo shows how to build, test, deploy, and interact with an MCP tool runtime on AWS Bedrock AgentCore.

The server exposes four developer tools (search docs, look up on-call, create incidents, delete incidents) that any MCP client discovers automatically via the MCP protocol — no manual schema registration needed. The `delete_incident` tool is deliberately blocked by a Cedar policy on the AgentCore Gateway, demonstrating fine-grained tool-level authorization.

## Project Structure

```
mcp-demo-summit/
├── server.py          — MCP server with 4 tools (search_docs, get_oncall, create_incident, delete_incident)
├── pyproject.toml     — Python dependencies for AgentCore deployment (includes OTEL)
├── deploy.sh          — Deployment script for AgentCore (Runtime + Gateway)
├── test_demo.py       — End-to-end test script validating all AgentCore features
├── test_server.py     — Property-based and unit tests (pytest + hypothesis)
├── app.py             — Streamlit chat UI (optional, for Bedrock Agent integration)
├── guardrails.json    — Guardrail policy config (optional, for Bedrock Guardrails)
├── requirements.txt   — Python dependencies for local dev/testing
└── README.md          — This file
```

After deployment, a sibling directory is created:
```
mcpdemosummit/              — AgentCore project (created by deploy.sh)
├── server.py              — Copied from mcp-demo-summit/
├── pyproject.toml         — Copied from mcp-demo-summit/
└── agentcore/
    ├── agentcore.json     — Project config (runtimes, gateways)
    ├── aws-targets.json   — Deployment target (account + region)
    └── cdk/               — CDK infrastructure (auto-managed)
```

## Prerequisites

- **Python 3.11+**
- **AWS CLI v2** — configured with the `demo-jj` profile
- **agentcore CLI** — `npm install -g @aws/agentcore` (requires Node.js 20+)
- **demo-jj AWS profile** — must have permissions for Bedrock, IAM, and AgentCore

## Local Setup

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Run the MCP server locally:

```bash
python server.py
```

The server starts on `http://0.0.0.0:8000` using streamable-http transport. Any MCP client can connect and discover the three tools automatically.

## Running Tests

```bash
pytest test_server.py -v
```

This runs both property-based tests (via hypothesis) and unit tests. Property tests generate 100+ random inputs per test to verify universal correctness properties.

## Deploying to AgentCore

```bash
./deploy.sh
```

The deploy script packages the MCP server and deploys it to AWS Bedrock AgentCore. It handles:
1. **Project creation** — scaffolds `mcpdemosummit/` AgentCore project (interactive first time)
2. **Runtime** — adds MCP runtime with server.py as entrypoint
3. **Gateway** — adds MCP gateway with IAM auth (using `--runtimes MyAgent`)
4. **CDK fix** — patches the bundled CDK toolkit version mismatch
5. **Deploy** — runs `agentcore deploy` to provision AWS resources
6. **Observability** — configures CloudWatch log delivery

**Note:** Gateway target + Cedar policies must be configured via the AWS Console after deploy (see Post-deployment section below).

### Prerequisites for deployment

- Python 3.10+
- Node.js 20+
- AWS CLI v2 (latest — must support `bedrock-agentcore-control` with `iamCredentialProvider`)
- AgentCore CLI: `npm install -g @aws/agentcore`
- AWS profile `demo-jj` configured and authenticated (`aws login --profile demo-jj`)

### Known issue: CDK schema version mismatch

If you get `Cloud assembly schema version mismatch: Maximum schema version supported is 53.x.x, but found 54.0.0`, the agentcore CLI's bundled CDK toolkit is outdated. Fix it:

```bash
cd /opt/homebrew/lib/node_modules/@aws/agentcore
npm install @aws-cdk/toolkit-lib@latest @aws-cdk/cloud-assembly-schema@latest --legacy-peer-deps
```

### Known issue: OTEL dependencies required

AgentCore Runtime requires OpenTelemetry in the deployment package. The `pyproject.toml` must include:

```toml
dependencies = [
    "mcp",
    "opentelemetry-api",
    "opentelemetry-sdk",
    "opentelemetry-exporter-otlp-proto-http",
    "opentelemetry-distro",
    "opentelemetry-instrumentation",
]
```

### First-time deployment (interactive)

The first run of `./deploy.sh` triggers `agentcore create --protocol MCP` which requires interactive input:
- **Project name**: Must be exactly `mcpdemosummit` (hardcoded in deploy.sh, alphanumeric only)
- **Add an agent?**: Select **No** (the script adds the runtime automatically afterward via `agentcore add agent`)

### Post-deployment: Gateway Target + Cedar Policy (AWS Console)

After `deploy.sh` completes, configure the gateway target and Cedar policies via the **AWS Console**:

#### Step 0: Grant gateway role permissions

The gateway needs permission to invoke the runtime. Get the gateway role name and grant it:

```bash
GATEWAY_ROLE=$(aws cloudformation describe-stack-resources \
  --stack-name AgentCore-mcpdemosummit-default \
  --region us-east-1 --profile demo-jj \
  --query "StackResources[?contains(PhysicalResourceId, 'GatewayMcpgatewayRole')].PhysicalResourceId | [0]" \
  --output text)

aws iam put-role-policy \
  --role-name "$GATEWAY_ROLE" \
  --policy-name InvokeRuntimePolicy \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"bedrock-agentcore:*","Resource":"*"}]}' \
  --profile demo-jj
```

#### Step 1: Get the correct Runtime URL

**Important:** `agentcore status` may show a stale runtime ID. Always verify with:

```bash
aws bedrock-agentcore-control list-agent-runtimes --region us-east-1 --profile demo-jj
```

The endpoint URL format is:
```
https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3AYOUR_ACCOUNT_ID%3Aruntime%2F{RUNTIME_ID}/invocations?qualifier=DEFAULT
```

Replace `{RUNTIME_ID}` with the actual runtime ID from the command above.

#### Step 2: Add Gateway Target

1. Go to **AWS Console** → **Bedrock AgentCore** → **Gateways** → `mcpgateway`
2. Click **Add target**
3. Configure:
   - **Name**: (use default or `mcpserver`)
   - **Type**: MCP Server
   - **Endpoint**: The runtime URL from Step 1 (with `?qualifier=DEFAULT`)
   - **Outbound Auth**: Gateway IAM Role → Service: `bedrock-agentcore`
4. Wait for status: `READY`

#### Step 3: Find actual tool names

After the target is READY, the tools use the format `{targetName}___toolName`. Find the target name:

```bash
aws bedrock-agentcore-control list-gateway-targets \
  --gateway-identifier $(agentcore fetch access --name mcpgateway 2>/dev/null | grep URL | grep -o '[a-z0-9-]*\.gateway' | sed 's/.gateway//') \
  --region us-east-1 --profile demo-jj --query "items[0].name" --output text
```

Tools will be named like: `target-quick-start-XXXX___search_docs`, `target-quick-start-XXXX___delete_incident`

#### Step 4: Create Policy Engine + Policies

1. Go to **AWS Console** → **Bedrock AgentCore** → **Policy Engines** → Create
2. **Name**: `mcppolicy2`, attach to `mcpgateway` in **ENFORCE** mode
3. Add policy **allow_all** (set validation to "Ignore all findings"):
   ```cedar
   permit(principal, action, resource == AgentCore::Gateway::"arn:aws:bedrock-agentcore:us-east-1:YOUR_ACCOUNT:gateway/YOUR_GATEWAY_ID");
   ```
4. Add policy **block_delete** (set validation to "Ignore all findings"):
   ```cedar
   forbid(principal, action == AgentCore::Action::"YOUR_TARGET_NAME___delete_incident", resource == AgentCore::Gateway::"arn:aws:bedrock-agentcore:us-east-1:YOUR_ACCOUNT:gateway/YOUR_GATEWAY_ID");
   ```

Replace placeholders with values from Steps 1-3.

#### Step 5: Sync tools (if tools/call returns "Unknown tool")

If tools aren't recognized, trigger a sync:

```bash
aws bedrock-agentcore-control synchronize-gateway-targets \
  --gateway-identifier YOUR_GATEWAY_ID \
  --target-id-list YOUR_TARGET_ID \
  --region us-east-1 --profile demo-jj
```

Wait 30-60 seconds, then verify tools work.

#### Step 6: Verify

Update `GATEWAY_URL` in `test_demo.py` with the gateway URL from `agentcore fetch access --name mcpgateway`, then:

```bash
python test_demo.py
```

## Running the Streamlit UI

```bash
streamlit run app.py
```

This opens a chat interface in your browser. Before running, update the `AGENT_ID` and `AGENT_ALIAS_ID` placeholders in `app.py` with the values from your deployed Bedrock Agent.

## AgentCore Features Demonstrated

### Tool Discovery

The Bedrock Agent discovers tools automatically via the MCP `tools/list` protocol. When AgentCore connects to the MCP server, it reads the `@mcp.tool()` decorated functions — their names, docstrings (as descriptions), and type annotations (as parameter schemas). No manual JSON schema registration needed. The Python function signature IS the schema.

### Guardrails

A word-based policy (`guardrails.json`) blocks destructive prompts containing "delete", "remove", "destroy", or "drop" **before** any tool is called. The guardrail intercepts at the prompt level — the MCP server never sees the request. Users get a clear denial message explaining why the operation was blocked.

### Session Memory

The Streamlit UI passes the same `session_id` to the Bedrock Agent across all messages in a conversation. The agent stores tool call results server-side, keyed by this ID. This enables multi-turn reasoning — ask "Who is on-call for platform?" then follow up with "What's their phone number?" and the agent remembers Alice Chen from the first call.

### Observability

Every tool call produces trace data including the tool name, call latency, input parameters, and output response. Traces are emitted to CloudWatch automatically by AgentCore — no OpenTelemetry setup or custom instrumentation required. View traces after a tool call:

```bash
aws logs tail /aws/bedrock/agentcore/mcp-demo-summit \
  --since 5m --format short --profile demo-jj --region us-east-1
```

### IAM Authentication

The tool runtime uses IAM-based authentication. All requests are SigV4-signed — no API keys, no tokens, no custom auth code. The `demo-jj` profile's IAM identity must have permission to invoke the Bedrock Agent. Only authorized IAM principals can reach the deployed MCP server.

### Scaling

AgentCore handles concurrent requests automatically. The deployed tool runtime scales up to serve multiple simultaneous agent sessions without any manual configuration. You don't manage containers, load balancers, or autoscaling rules — AgentCore does it for you.

## TODO — Remaining work for the demo

### Live Demo UI (not yet implemented)

The current demo uses `test_demo.py` (a Python script) to validate all features. For the live presentation, a more visual demo is needed:

- [ ] **Option A: Streamlit Chat UI** — Update `app.py` to connect to the Gateway (not a Bedrock Agent). The UI would:
  - Send MCP tool calls via SigV4 to the gateway
  - Show tool results in chat format
  - Display policy denial when `delete_incident` is called
  - Show trace/latency info from the response

- [ ] **Option B: MCP Inspector** — Use MCP Inspector connected to the gateway. Requires OAuth/JWT auth on the gateway (currently IAM-only, which MCP Inspector doesn't support).

- [ ] **Option C: Bedrock Agent** — Create a Bedrock Agent that connects to the AgentCore Gateway as its tool source. The Streamlit UI (`app.py`) would then interact with the Bedrock Agent which routes tool calls through the gateway. This shows the full production path: User → Streamlit → Bedrock Agent → Gateway (policy) → Runtime (MCP server).

### Deployment automation (optional)

- [ ] Automate gateway target creation in `deploy.sh` (blocked by `CreateGatewayTarget` IAM permission — needs service team fix or different auth approach)
- [ ] Automate Cedar policy creation in `deploy.sh` (blocked by CDK `GetGateway` permission when policy references a gateway in the same stack)

### Observability

- [ ] Show CloudWatch observability dashboard during the live demo
- [ ] Add trace visualization to Streamlit UI (parse trace events from tool call responses)

### Cleanup

- [ ] Create `destroy.sh` script to tear down all resources cleanly


