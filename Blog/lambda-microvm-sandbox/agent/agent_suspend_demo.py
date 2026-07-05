"""
agent_suspend_demo.py — Demonstrates MicroVM suspend/resume state preservation.

Same as agent.py but with a 1-minute idle timeout so you can actually see
the suspend → resume cycle without waiting 5 minutes.

Usage:
    python agent_suspend_demo.py

Test flow:
    1. Ask the agent to create a file (it creates a sandbox + writes file)
    2. Wait ~70 seconds (MicroVM auto-suspends after 60s idle)
    3. Ask the agent to read that file back (MicroVM auto-resumes, file still there)
"""

import boto3
import requests
import time
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
print()
print("⚠️  This demo uses 60-second idle timeout for suspend.")
print("    After running code, wait ~70 seconds, then run more code.")
print("    The MicroVM will suspend and resume with state intact.")
print()

lambda_client = boto3.client("lambda-microvms", region_name=REGION)


# --- Tools ---


@tool
def create_sandbox() -> dict:
    """Create an isolated MicroVM sandbox with 1-minute suspend timeout.
    Returns sandbox_id and endpoint URL."""
    try:
        response = lambda_client.run_microvm(
            imageIdentifier=SANDBOX_IMAGE_ARN,
            executionRoleArn=SANDBOX_ROLE_ARN,
            idlePolicy={
                "maxIdleDurationSeconds": 60,       # Suspend after 1 min idle
                "suspendedDurationSeconds": 1800,   # Keep suspended state for 30 min
                "autoResumeEnabled": True,           # Auto-resume on next request
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
    """Execute Python code in the sandbox. State persists — even across suspend/resume."""
    try:
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
def check_sandbox_state(sandbox_id: str) -> dict:
    """Check the current state of the sandbox (RUNNING, SUSPENDED, etc.)."""
    try:
        response = lambda_client.get_microvm(microvmIdentifier=sandbox_id)
        return {"state": response["state"], "sandbox_id": sandbox_id}
    except Exception as e:
        return {"error": str(e)}


@tool
def destroy_sandbox(sandbox_id: str) -> str:
    """Terminate the sandbox. All memory, disk, and processes destroyed."""
    try:
        lambda_client.terminate_microvm(microvmIdentifier=sandbox_id)
    except Exception as e:
        return f"Error terminating: {e}"
    return "Sandbox terminated. All state destroyed."


# --- Agent ---

SYSTEM_PROMPT = """You are a coding assistant demonstrating MicroVM state preservation.

When the user asks you to run code:
1. Create a sandbox with create_sandbox() — it has a 1-minute idle suspend timeout
2. Execute code with run_code()
3. You can call run_code() multiple times — state persists between calls
4. You can check sandbox state with check_sandbox_state() to show RUNNING/SUSPENDED
5. When finished, destroy the sandbox with destroy_sandbox()

IMPORTANT: If the user says "wait" or asks about suspend/resume, tell them to wait
70 seconds and then ask you to run code again. The MicroVM will auto-suspend after
60 seconds of idle and auto-resume when the next request arrives.

Always run code in the sandbox. Never just describe what code would do."""

agent = Agent(
    model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    system_prompt=SYSTEM_PROMPT,
    tools=[create_sandbox, run_code, check_sandbox_state, destroy_sandbox],
)


# --- Entry point ---

if __name__ == "__main__":
    print("Lambda MicroVM Suspend/Resume Demo")
    print("=" * 40)
    print()
    print("Try this flow:")
    print('  1. "Write a file /workspace/state.txt with the current timestamp"')
    print('  2. Wait 70 seconds (watch it suspend)')
    print('  3. "Read /workspace/state.txt and print its contents"')
    print('  4. The file survives suspend/resume!')
    print()
    print("Type your request (or 'quit' to exit):\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ("quit", "exit", "q"):
            break
        response = agent(user_input)
        print(f"\nAgent: {response}\n")
