"""
Lambda function: Refund Processing Tool Backend.

This Lambda is registered as a Gateway Target in AgentCore.
The Gateway intercepts requests, evaluates Cedar policies, and only
forwards ALLOWED requests to this function.

The Gateway passes tool arguments directly as the event payload
(not nested under an "arguments" key).
"""

import json


def handler(event, context):
    """Process a refund request.

    The AgentCore Gateway passes tool call arguments in different possible
    structures depending on configuration. We handle both cases.
    """
    # Debug: log the full event to CloudWatch (helpful during setup)
    print(f"Received event: {json.dumps(event)}")

    # Gateway may pass args directly or nested under "arguments"
    if "arguments" in event:
        args = event["arguments"]
    else:
        args = event

    order_id = args.get("order_id", "unknown")
    amount = args.get("amount", 0)
    reason = args.get("reason", "not specified")

    # In production: call your payment gateway, update database, etc.
    return {
        "status": "success",
        "message": (
            f"Refund of ${amount} processed successfully. "
            f"Order: {order_id}. Reason: {reason}."
        ),
    }
