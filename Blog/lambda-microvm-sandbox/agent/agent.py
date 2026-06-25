"""
agent.py — Strands Agent with Lambda MicroVM sandbox tools.

The agent creates isolated sandboxes on demand, executes AI-generated
code inside them, and tears them down when done.
"""

import boto3
import requests
import json
from strands import Agent
from strands.tools import tool

# --- Configuration ---
REGION = "us-east-1"
IMAGE_NAME = "python-sandbox"
STACK_NAME = "microvm-sandbox-roles"

# Auto-fetch ARNs from AWS
sts_client = boto3.client("sts", region_name=REGION)
cfn_client = boto3.client("cloudformation", region_name=REGION)

ACCOUNT_ID = sts_client.get_caller_identity()["Account"]
SANDBOX_IMAGE_ARN = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:microvm-image:{IMAGE_NAME}"

stack_outputs = cfn_client.describe_stacks(StackName=STACK_NAME)["Stacks"][0]["Outputs"]
SANDBOX_ROLE_ARN = next(
    o["OutputValue"] for o in stack_outputs if o["OutputKey"] == "ExecutionRoleArn"
)

print(f"Image ARN: {SANDBOX_IMAGE_ARN}")
print(f"Execution Role: {SANDBOX_ROLE_ARN}")

lambda_client = boto3.client("lambda-microvms", region_name=REGION)


# --- Tools ---


@tool
def create_sandbox() -> dict:
    """Create an isolated MicroVM sandbox for executing code.
    Returns sandbox_id and endpoint URL."""
    try:
        response = lambda_client.run_microvm(
            imageIdentifier=SANDBOX_IMAGE_ARN,
            executionRoleArn=SANDBOX_ROLE_ARN,
            idlePolicy={
                "maxIdleDurationSeconds": 300,
                "suspendedDurationSeconds": 1800,
                "autoResumeEnabled": True,
            },
        )
    except Exception as e:
        return {"error": str(e)}
    return {
        "sandbox_id": response["microvmId"],
        "endpoint": f"https://{response['endpoint']}",
    }


@tool
def run_code(sandbox_id: str, endpoint: str, code: str) -> dict:
    """Execute Python code in the isolated sandbox.
    State persists between calls — variables, packages, and files carry over."""
    try:
        # Generate short-lived auth token using the sandbox_id (microvmId)
        token_response = lambda_client.create_microvm_auth_token(
            microvmIdentifier=sandbox_id,
            expirationInMinutes=5,
            allowedPorts=[{"port": 8080}],
        )
        token = token_response["authToken"]["X-aws-proxy-auth"]

        resp = requests.post(
            f"{endpoint}/execute",
            headers={
                "X-aws-proxy-auth": token,
                "X-aws-proxy-port": "8080",
            },
            json={"code": code, "timeout": 60},
            timeout=90,
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e), "stdout": "", "stderr": str(e), "exit_code": -1}


@tool
def destroy_sandbox(sandbox_id: str) -> str:
    """Terminate the sandbox. All memory, disk, and processes are destroyed permanently."""
    try:
        lambda_client.terminate_microvm(microvmIdentifier=sandbox_id)
    except Exception as e:
        return f"Error terminating: {e}"
    return "Sandbox terminated. All state destroyed."


# --- Agent ---

SYSTEM_PROMPT = """You are a coding assistant. When the user asks you to
analyze data, write code, or compute anything:

1. Create a sandbox with create_sandbox()
2. Write Python code and execute it with run_code()
3. You can call run_code() multiple times — state persists between calls
   (variables, installed packages, and files carry over)
4. When finished, destroy the sandbox with destroy_sandbox()

Always run code in the sandbox. Never just describe what code would do — execute it.
If an execution fails, read the error, fix your code, and retry."""

agent = Agent(
    model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    system_prompt=SYSTEM_PROMPT,
    tools=[create_sandbox, run_code, destroy_sandbox],
)


# --- Entry point ---

if __name__ == "__main__":
    print("Lambda MicroVM Sandbox Agent")
    print("=" * 40)
    print("Type your request (or 'quit' to exit):\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ("quit", "exit", "q"):
            break
        response = agent(user_input)
        print(f"\nAgent: {response}\n")
