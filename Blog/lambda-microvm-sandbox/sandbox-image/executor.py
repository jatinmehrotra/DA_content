"""
executor.py — Runs inside the Lambda MicroVM.

A thin HTTP server that receives code via POST, executes it as a subprocess,
and returns stdout/stderr. The security boundary is the VM, not this code.
"""

import subprocess
import os
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

WORK_DIR = "/workspace"
os.makedirs(WORK_DIR, exist_ok=True)


@app.route("/execute", methods=["POST"])
def execute():
    """Execute submitted code and return output."""
    payload = request.json
    code = payload.get("code", "")
    timeout = payload.get("timeout", 30)
    
    app.logger.info(f"=== Incoming request: {len(code)} chars, timeout: {timeout}s ===")
    app.logger.info(f"Code:\n{code}")

    # Write code to file (gives proper tracebacks with line numbers)
    code_file = os.path.join(WORK_DIR, "run.py")
    with open(code_file, "w") as f:
        f.write(code)

    try:
        result = subprocess.run(
            ["python3", code_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORK_DIR,
        )
        return jsonify(
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
        )
        app.logger.info(f"Execution complete: exit_code={result.returncode}, stdout={len(result.stdout)} chars")
        return response
    except subprocess.TimeoutExpired:
        app.logger.warning(f"Execution timed out after {timeout}s")
        return jsonify(
            {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout}s",
                "exit_code": -1,
            }
        ), 408


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint — used during image build to confirm readiness."""
    return jsonify({"status": "ready"})


@app.route("/files", methods=["GET"])
def list_files():
    """List files in the workspace — useful for debugging."""
    files = os.listdir(WORK_DIR)
    return jsonify({"workspace_files": files})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
