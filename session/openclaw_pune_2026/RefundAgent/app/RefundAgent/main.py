"""
Refund Processing Agent - Deployed to Amazon Bedrock AgentCore Runtime.

A simple Strands Agent that processes customer refunds.
Demonstrates that AgentCore works with ANY agent framework, not just OpenClaw.

Author: Jatin Mehrotra | Developer Advocate, AWS
Session: Designing Production-Ready OpenClaw on AWS
"""

from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()


@tool
def process_refund(order_id: str, amount: int, reason: str) -> str:
    """Process a customer refund for a given order.

    Args:
        order_id: The order ID to refund (e.g., ORD-1234)
        amount: The refund amount in dollars
        reason: Reason for the refund

    Returns:
        Confirmation message with refund details
    """
    if amount <= 0:
        return f"Error: Invalid refund amount ${amount}. Amount must be positive."

    # In production, this would call your payment gateway / database
    return (
        f"Refund of ${amount} processed successfully.\n"
        f"Order: {order_id}\n"
        f"Reason: {reason}\n"
        f"Status: COMPLETED"
    )


agent = Agent(
    tools=[process_refund],
    system_prompt=(
        "You are a customer service agent that processes refunds. "
        "Always confirm the order ID, amount, and reason before processing. "
        "Be concise and professional."
    ),
)


@app.entrypoint
def invoke(payload, context):
    """Handler for agent invocation via AgentCore Runtime."""
    prompt = payload.get("prompt", "")
    if not isinstance(prompt, str) or not prompt.strip():
        return {"error": "Invalid input: 'prompt' must be a non-empty string"}

    result = agent(prompt)
    return {"response": str(result.message)}


if __name__ == "__main__":
    app.run()
