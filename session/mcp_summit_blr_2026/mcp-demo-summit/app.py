"""
Streamlit Chat UI for MCP Demo — MCP Dev Summit Bengaluru 2026

This app connects to a Bedrock Agent backed by an AgentCore-hosted MCP tool runtime.
It demonstrates:
  - Tool Discovery: The agent auto-discovers tools via MCP tools/list — no manual schema needed
  - Session Memory: The agent remembers prior tool results via session_id
  - Observability: Trace events show tool name, input, output, and latency
  - Guardrails: Destructive prompts are blocked before reaching any tool
"""

import streamlit as st
import boto3
import uuid
import time

# --- Configuration ---
# Placeholder IDs — replace with actual values after deploying the agent and tool runtime
AGENT_ID = "AGENT_ID"
AGENT_ALIAS_ID = "ALIAS_ID"

# boto3 session with IAM profile — SigV4 signing handles auth automatically, no API keys needed
session = boto3.Session(profile_name="demo-jj")
client = session.client("bedrock-agent-runtime", region_name="us-east-1")

# --- Streamlit Page Setup ---
st.set_page_config(page_title="MCP Demo — DevOps Agent", page_icon="🤖")
st.title("🤖 MCP DevOps Agent")
st.caption("Powered by Bedrock Agent + AgentCore MCP Tool Runtime")

# --- Session State Initialization ---
# Session memory: Bedrock Agent remembers context from prior tool calls via session_id.
# Same session_id = same conversation memory. New ID = fresh start.
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


def invoke_agent(prompt: str) -> dict:
    """
    Send a prompt to the Bedrock Agent and stream the response.

    The agent automatically discovers tools from the MCP tool runtime (via tools/list)
    and selects which tool to call based on the prompt. No manual tool registration needed.

    Session memory is enabled by passing the same session_id across calls — the agent
    recalls prior tool results (e.g., "who is on-call?" followed by "send them a message").

    enableTrace=True requests trace data in the response stream for observability.
    """
    start_time = time.time()

    response = client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=st.session_state.session_id,  # Session memory — same ID = same conversation
        inputText=prompt,
        enableTrace=True,  # Observability — request trace events in response stream
    )

    result_text = ""
    traces = []
    guardrail_triggered = False

    # Stream response chunks and parse trace events for observability
    for event in response["completion"]:
        # --- Response text chunks ---
        if "chunk" in event:
            result_text += event["chunk"]["bytes"].decode()

        # --- Trace events: tool name, input, output, latency ---
        if "trace" in event:
            trace = event["trace"]["trace"]

            # Guardrail trace — destructive operation was blocked before reaching any tool
            if "guardrailTrace" in trace:
                guardrail_triggered = True

            # Orchestration trace — tool invocation details for observability
            if "orchestrationTrace" in trace:
                orch = trace["orchestrationTrace"]

                # Tool invocation input — which tool was called and with what parameters
                if "invocationInput" in orch:
                    inv = orch["invocationInput"]
                    if "actionGroupInvocationInput" in inv:
                        action = inv["actionGroupInvocationInput"]
                        traces.append({
                            "tool": action.get("function", "unknown"),
                            "input": action.get("parameters", {}),
                        })

                # Tool invocation output — what the tool returned
                if "observation" in orch:
                    obs = orch["observation"]
                    if "actionGroupInvocationOutput" in obs:
                        if traces:
                            traces[-1]["output"] = obs["actionGroupInvocationOutput"].get("text", "")

    latency_ms = round((time.time() - start_time) * 1000)

    return {
        "text": result_text,
        "traces": traces,
        "latency_ms": latency_ms,
        "guardrail_triggered": guardrail_triggered,
    }


# --- Chat History Display ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat Input ---
if prompt := st.chat_input("Ask the DevOps agent..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Invoke agent and display response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = invoke_agent(prompt)

        # Show guardrail warning if a destructive operation was blocked
        if result["guardrail_triggered"]:
            st.warning("🛡️ Guardrail activated — destructive operation blocked")

        # Display the agent's response
        st.markdown(result["text"])

        # Observability: Show trace details (tool name, input, output, latency)
        # Traces are emitted by AgentCore automatically — no custom instrumentation needed
        if result["traces"]:
            with st.expander("🔍 Trace Details"):
                st.json(result["traces"])
                st.metric("Total Latency", f"{result['latency_ms']} ms")

    # Save assistant response to conversation history
    st.session_state.messages.append({"role": "assistant", "content": result["text"]})

# --- Sidebar: Session Info ---
with st.sidebar:
    st.subheader("Session Info")
    st.code(st.session_state.session_id, language=None)
    if st.button("🔄 New Conversation"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
