# Lambda MicroVM Sandbox — Ephemeral Code Execution for AI Agents

An AI coding assistant that creates isolated Firecracker-based sandboxes on demand, executes generated code inside them, and destroys them when done. Built with [Strands Agents SDK](https://github.com/strands-agents/sdk-python) and [AWS Lambda MicroVMs](https://aws.amazon.com/lambda/lambda-microvms/).

## Architecture

```
┌──────────────────────────────────────────────────────┐
│   Strands Agent (agent.py)                            │
│                                                       │
│   @tool create_sandbox()  ─── boto3 ──▶ Lambda API   │
│   @tool run_code()        ─── HTTPS ──▶ MicroVM      │
│   @tool destroy_sandbox() ─── boto3 ──▶ Lambda API   │
└──────────────────────────────────────────────────────┘
                                              │
                  ┌───────────────────────────▼──────────┐
                  │  Firecracker MicroVM (per session)   │
                  │  • Own kernel, memory, disk          │
                  │  • executor.py listens on :8080      │
                  │  • Receives code → runs → returns    │
                  └─────────────────────────────────────┘
```

## Project Structure

```
lambda-microvm-sandbox/
├── sandbox-image/          # What runs INSIDE the MicroVM
│   ├── Dockerfile          # Builds the sandbox environment
│   ├── requirements.txt    # Packages available to generated code
│   ├── executor.py         # HTTP server that receives and runs code
│   └── requirements.txt    # Packages available to generated code
├── agent/                  # Your application (runs OUTSIDE)
│   ├── agent.py            # Strands agent with 3 tools
│   └── requirements.txt    # Agent dependencies
├── sample-data/            # Test data for the demo
│   └── sales.csv
├── deploy.sh               # Build + deploy script
├── iam-roles.yaml          # CloudFormation: creates both IAM roles
├── test.sh                 # Manual test: run → execute code → terminate
└── README.md
```

## Prerequisites

- AWS account with access to a supported region (us-east-1, us-east-2, us-west-2, ap-northeast-1, eu-west-1)
- AWS CLI v2.35.11 or later (`aws --version` to check; update with `pip install awscli --upgrade` or `brew upgrade awscli`)
- Python 3.12+
- An S3 bucket for uploading the code artifact
- Two IAM roles (see [IAM Setup](#iam-setup) below)

## Quick Start

Navigate to the project directory:

```bash
cd lambda-microvm-sandbox
```

### 1. Create IAM Roles (Automated)

Deploy the CloudFormation stack to create both roles:

```bash
aws cloudformation deploy \
  --template-file iam-roles.yaml \
  --stack-name microvm-sandbox-roles \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides S3BucketName=your-bucket-name
```

Get the ARNs:

```bash
aws cloudformation describe-stacks --stack-name microvm-sandbox-roles \
  --query 'Stacks[0].Outputs' --output table
```

⚠️ **Note:** The Execution Role has `AdministratorAccess` for demo purposes.

**Why?** The Execution Role controls what **AWS API calls** the code inside the MicroVM can make (S3, DynamoDB, Bedrock, etc.) — it does NOT restrict code execution itself (Python, packages, file I/O all work regardless).

**For production, scope it down based on your use case:**

| Use Case | Execution Role Needs |
|----------|---------------------|
| Pure compute sandbox (pandas, numpy, charts) | CloudWatch Logs only — code never calls AWS APIs |
| Code needs to read from S3 | Logs + `s3:GetObject` on specific buckets |
| Code needs to call Bedrock | Logs + `bedrock:InvokeModel` |
| Demo / testing | `AdministratorAccess` (what we're using) |

**Security tip:** For untrusted code, the safest pattern is to pass data INTO the sandbox via the HTTP request body rather than giving the sandbox credentials to fetch it from AWS services directly.

### 2. Deploy the MicroVM Image

Update the variables in `deploy.sh`:

```bash
S3_BUCKET="your-bucket-name"
```

Then deploy:

```bash
chmod +x deploy.sh
./deploy.sh
```

Wait for the image build to complete (2-5 minutes):

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws lambda-microvms get-microvm-image \
  --image-identifier arn:aws:lambda:us-east-1:${ACCOUNT_ID}:microvm-image:python-sandbox --region us-east-1
# Wait until State shows "SUCCESSFUL"
```

### 3. Test Manually (before running the agent)

Update the ARNs in `test.sh`, then:

```bash
chmod +x test.sh
./test.sh
```

This runs through the full lifecycle:
1. `run-microvm` → launches a MicroVM from your image
2. Waits for RUNNING state
3. Creates an auth token
4. Sends a health check request
5. Executes Python code via the `/execute` endpoint
6. Tests state persistence between calls
7. `terminate-microvm` → destroys the sandbox

If all steps pass, your image is working correctly.

### 4. Run the Agent

```bash
cd agent
pip install -r requirements.txt
python agent.py
```

The agent auto-fetches the Image ARN and Execution Role ARN from your AWS account and CloudFormation stack — no manual configuration needed.

Try these prompts:

```
You: What's the memory usage of a Python list with 1 million integers vs a numpy array?

You: Read /data/sales.csv and tell me the top 3 products by revenue

You: Install the tabulate package and print the sales data as a formatted table
```

## How It Works

1. **Image Build (one-time):** `deploy.sh` packages the Dockerfile + executor, uploads to S3, and creates a MicroVM image. Lambda runs the Dockerfile, starts the executor, and takes a Firecracker snapshot of the fully initialized state.

2. **At Runtime:** The agent calls `create_sandbox()` → Lambda restores from the snapshot (sub-second) → returns a dedicated HTTPS endpoint.

3. **Code Execution:** Agent sends generated code via POST to the endpoint → executor writes it to a file → runs `python3` on it → returns stdout/stderr.

4. **State Persists:** Variables, imported packages, and files created in step N are still there in step N+1. Same MicroVM, same process space.

5. **Cleanup:** Agent calls `destroy_sandbox()` → MicroVM terminated → all state gone permanently.

## Cost

| State | You Pay |
|-------|---------|
| Running (executing code) | Baseline compute |
| Suspended (user idle) | Snapshot storage only |
| Terminated | Nothing |

MicroVMs auto-suspend after 5 minutes of inactivity (configurable). Resume is sub-second when traffic returns.

## Security Notes

- Each sandbox is a Firecracker VM — separate kernel, no shared resources
- The Execution Role has only CloudWatch Logs permissions — no access to your S3, DynamoDB, etc.
- Auth tokens are short-lived (5 min), port-scoped, and per-MicroVM
- Code runs as a subprocess, not `eval()` — proper process isolation within the VM

## Regions

Lambda MicroVMs is available in: us-east-1, us-east-2, us-west-2, ap-northeast-1, eu-west-1.

## Blog Post

This repo accompanies the blog post: [The Hardest Part of Running Someone Else's Code — Solved Without Managing VMs](#)

## License

MIT
