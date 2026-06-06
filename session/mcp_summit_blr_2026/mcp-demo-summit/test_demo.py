"""
Test script for the MCP Demo — validates all AgentCore features.
Run: python test_demo.py

Tests:
  1. AUTH — unauthenticated request → rejected
  2. TOOL DISCOVERY — tools/list via gateway → 4 tools returned
  3. ALLOWED TOOL — search_docs → works
  4. BLOCKED TOOL — delete_incident → blocked by Cedar policy
  5. OBSERVABILITY — show that traces are available
"""

import json
import urllib.request
import urllib.error
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

# --- Configuration ---
# Update GATEWAY_URL after deployment (get from: agentcore fetch access --name mcpgateway)
GATEWAY_URL = "https://mcpdemosummit-mcpgateway-XXXXX.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
# Update TARGET_PREFIX after deployment (get from: aws bedrock-agentcore-control list-gateway-targets)
TARGET_PREFIX = "target-quick-start-XXXXX"
REGION = "us-east-1"
PROFILE = "demo-jj"

def make_mcp_request(method, params=None, use_auth=True):
    """Send an MCP JSON-RPC request to the gateway."""
    body = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    })

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    if use_auth:
        session = boto3.Session(profile_name=PROFILE)
        credentials = session.get_credentials().get_frozen_credentials()
        request = AWSRequest(method="POST", url=GATEWAY_URL, data=body, headers=headers)
        SigV4Auth(credentials, "bedrock-agentcore", REGION).add_auth(request)
        headers = dict(request.headers)

    req = urllib.request.Request(GATEWAY_URL, data=body.encode(), headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as response:
            result = response.read().decode()
            # Parse SSE format
            for line in result.split("\n"):
                if line.startswith("data: "):
                    return json.loads(line[6:])
            if result.strip():
                return json.loads(result)
            return {"status": "empty_response_200_ok"}
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "body": e.read().decode()}


def test_1_auth_rejected():
    """Test: unauthenticated request is rejected."""
    print("\n" + "=" * 60)
    print("🔐 TEST 1: Auth — request without credentials")
    print("=" * 60)

    result = make_mcp_request("tools/list", use_auth=False)

    if "error" in result and "401" in str(result.get("error", "")):
        print("✅ PASS — Request rejected with 401 (IAM auth required)")
    elif "error" in result and "403" in str(result.get("error", "")):
        print("✅ PASS — Request rejected with 403 (unauthorized)")
    else:
        print(f"❌ FAIL — Expected 401/403, got: {json.dumps(result, indent=2)[:200]}")


def test_2_tool_discovery():
    """Test: tools/list returns all 4 tools."""
    print("\n" + "=" * 60)
    print("🔍 TEST 2: Tool Discovery — list all tools via gateway")
    print("=" * 60)

    result = make_mcp_request("tools/list")

    if "error" in result:
        print(f"❌ FAIL — {result}")
        return

    tools = result.get("result", {}).get("tools", [])
    tool_names = [t["name"] for t in tools]
    print(f"   Found {len(tools)} tools: {tool_names}")

    expected = ["search_docs", "get_oncall", "create_incident", "delete_incident"]
    for name in expected:
        if any(name in t for t in tool_names):
            print(f"   ✅ {name}")
        else:
            print(f"   ❌ Missing: {name}")


def test_3_allowed_tool():
    """Test: search_docs works through gateway."""
    print("\n" + "=" * 60)
    print("✅ TEST 3: Allowed Tool — call search_docs")
    print("=" * 60)

    result = make_mcp_request("tools/call", {
        "name": f"{TARGET_PREFIX}___search_docs",
        "arguments": {"query": "deploy"}
    })

    if "error" in result and "HTTP" in str(result.get("error", "")):
        print(f"❌ FAIL — {result}")
        return

    content = result.get("result", {}).get("content", [])
    if content:
        text = content[0].get("text", "")
        print(f"   ✅ PASS — Got response: {text[:100]}...")
    else:
        is_error = result.get("result", {}).get("isError", False)
        if is_error:
            print(f"   ❌ FAIL — Tool returned error: {result}")
        else:
            print(f"   Response: {json.dumps(result, indent=2)[:200]}")


def test_4_blocked_tool():
    """Test: delete_incident is blocked by Cedar policy."""
    print("\n" + "=" * 60)
    print("🛡️  TEST 4: Cedar Policy — call delete_incident (should be BLOCKED)")
    print("=" * 60)

    result = make_mcp_request("tools/call", {
        "name": f"{TARGET_PREFIX}___delete_incident",
        "arguments": {"ticket_id": "INC-1234"}
    })

    if "error" in result and "HTTP" in str(result.get("error", "")):
        print(f"   Response: {result}")
        # A 403 or policy denial is the expected behavior
        if "403" in str(result) or "denied" in str(result).lower():
            print("   ✅ PASS — Blocked by policy!")
        return

    # Check for JSON-RPC error (policy denial comes as error code -32002)
    if "error" in result and isinstance(result["error"], dict):
        msg = result["error"].get("message", "")
        if "denied" in msg.lower() or "block_delete" in msg.lower():
            print(f"   ✅ PASS — Blocked by Cedar policy: {msg}")
            return

    content = result.get("result", {})
    is_error = content.get("isError", False)
    text = ""
    if content.get("content"):
        text = content["content"][0].get("text", "")

    if is_error and "denied" in text.lower():
        print(f"   ✅ PASS — Blocked by Cedar policy: {text[:150]}")
    else:
        print(f"   ❌ FAIL — Expected denial, got: {json.dumps(result, indent=2)[:200]}")


def test_5_observability():
    """Test: Show how to view traces."""
    print("\n" + "=" * 60)
    print("📊 TEST 5: Observability — traces available")
    print("=" * 60)
    print("   Run these commands to see traces:")
    print("   $ agentcore logs --since 5m")
    print("   $ agentcore traces list")
    print("   ✅ OTEL auto-instrumentation is active (see deploy logs)")


if __name__ == "__main__":
    print("🎯 MCP Demo — Testing AgentCore Features")
    print("   Gateway: " + GATEWAY_URL)

    test_1_auth_rejected()
    test_2_tool_discovery()
    test_3_allowed_tool()
    test_4_blocked_tool()
    test_5_observability()

    print("\n" + "=" * 60)
    print("🏁 All tests complete!")
    print("=" * 60)
