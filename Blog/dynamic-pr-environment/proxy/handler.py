"""
Auth Proxy Lambda — makes MicroVM endpoints accessible via browser.

Sits between the reviewer's browser and the MicroVM. Generates a JWE auth
token on each request and forwards it to the MicroVM endpoint.

URL pattern: https://<proxy-function-url>/<microvm-id>/<path>
Example:     https://xyz.lambda-url.us-east-1.on.aws/microvm-abc123/
             → proxies to https://<microvm-endpoint>/

The proxy looks up the MicroVM's endpoint URL, generates a short-lived token,
and forwards the browser's request with the token attached.
"""

import json
import urllib.request
import urllib.error
import boto3

lambda_client = boto3.client("lambda-microvms", region_name="us-east-1")


def handler(event, context):
    """Lambda Function URL handler — proxies requests to MicroVM."""

    # Parse path: /<microvm-id>/<rest-of-path>
    raw_path = event.get("rawPath", "/")
    path_parts = raw_path.strip("/").split("/", 1)

    if not path_parts or not path_parts[0].startswith("microvm-"):
        return response(400, "text/plain", "Usage: /<microvm-id>/path\nExample: /microvm-abc123/")

    microvm_id = path_parts[0]
    forward_path = "/" + path_parts[1] if len(path_parts) > 1 else "/"

    try:
        # Get MicroVM endpoint
        microvm_info = lambda_client.get_microvm(microvmIdentifier=microvm_id)
        endpoint = microvm_info["endpoint"]
        state = microvm_info.get("state", "UNKNOWN")

        if state not in ("RUNNING", "SUSPENDED"):
            return response(503, "text/plain", f"MicroVM is {state} — not accessible")

        # Generate auth token (short-lived, port 8080)
        token_resp = lambda_client.create_microvm_auth_token(
            microvmIdentifier=microvm_id,
            expirationInMinutes=5,
            allowedPorts=[{"port": 8080}],
        )
        token = token_resp["authToken"]["X-aws-proxy-auth"]

        # Forward request to MicroVM
        target_url = f"https://{endpoint}{forward_path}"
        headers = {
            "X-aws-proxy-auth": token,
            "X-aws-proxy-port": "8080",
        }

        # Forward query string if present
        query = event.get("rawQueryString", "")
        if query:
            target_url += f"?{query}"

        # Forward body for POST/PUT/DELETE
        method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
        body_data = None
        if event.get("body"):
            body_data = event["body"].encode("utf-8")
            if event.get("isBase64Encoded"):
                import base64
                body_data = base64.b64decode(event["body"])
            headers["Content-Type"] = event.get("headers", {}).get("content-type", "application/json")

        req = urllib.request.Request(target_url, data=body_data, headers=headers, method=method)
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read().decode("utf-8")
            content_type = resp.headers.get("Content-Type", "text/html")
            return response(resp.status, content_type, resp_body)

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else str(e)
        return response(e.code, "text/plain", body)
    except lambda_client.exceptions.ResourceNotFoundException:
        return response(404, "text/plain", f"MicroVM {microvm_id} not found")
    except Exception as e:
        return response(500, "text/plain", f"Proxy error: {str(e)}")


def response(status_code, content_type, body):
    """Build Lambda Function URL response."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": content_type},
        "body": body,
    }
