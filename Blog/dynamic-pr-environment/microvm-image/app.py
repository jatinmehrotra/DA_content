"""
app.py — Dynamic PR Environment running inside a Lambda MicroVM.

Two servers:
- Port 9000: Lifecycle hooks (Lambda sends /ready, /run, /resume, /suspend, /terminate here)
- Port 8080: App routes (user traffic — /, /tasks, /health)

PR metadata comes via runHookPayload (delivered to /run hook at startup).
"""

import os
import json
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
import boto3
from boto3.dynamodb.conditions import Key

# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- Constants ---
CONFIG_PATH = "/app/config.json"
HOOKS_PORT = 9000
APP_PORT = 8080
REGION = os.environ.get("AWS_REGION", "us-east-1")

# --- Global config (written by /run hook, read by app) ---
config = {
    "pr_number": "local",
    "branch": "main",
    "author": "developer",
    "accent_color": "#FF9900",
    "dynamodb_table": "pr-environments",
    "microvm_id": "local",
    "cleanup_data": False,
}


def load_config():
    """Load config from file (written by /run hook)."""
    global config
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            config = json.load(f)
    return config


# =====================================================
# HOOKS SERVER (port 9000)
# =====================================================

hooks_app = Flask("hooks")


@hooks_app.route("/aws/lambda-microvms/runtime/v1/ready", methods=["GET", "POST"])
@hooks_app.route("/ready", methods=["GET", "POST"])
def hook_ready():
    """/ready hook — Called during image build. Signals app is initialized."""
    logger.info("=== /ready hook === App initialized, ready for snapshot")
    return jsonify({"status": "ready"}), 200


@hooks_app.route("/aws/lambda-microvms/runtime/v1/run", methods=["POST"])
@hooks_app.route("/run", methods=["POST"])
def hook_run():
    """
    /run hook — Called once when MicroVM starts from snapshot.
    Receives: {"microvmId": "...", "runHookPayload": "<json-string>"}
    """
    body = request.json or {}
    microvm_id = body.get("microvmId", "unknown")
    payload_str = body.get("runHookPayload", "{}")

    logger.info(f"=== /run hook fired === MicroVM: {microvm_id}")

    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        payload = {}

    global config
    config = {
        "pr_number": payload.get("pr_number", "local"),
        "branch": payload.get("branch", "main"),
        "author": payload.get("author", "developer"),
        "accent_color": payload.get("accent_color", "#FF9900"),
        "dynamodb_table": payload.get("dynamodb_table", "pr-environments"),
        "microvm_id": microvm_id,
        "cleanup_data": payload.get("cleanup_data", False),
    }

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)

    logger.info(f"Config: PR #{config['pr_number']} | branch: {config['branch']} | color: {config['accent_color']}")
    logger.info(f"✅ /run complete — PR #{config['pr_number']} ready")
    return jsonify({"status": "ready"}), 200


@hooks_app.route("/aws/lambda-microvms/runtime/v1/resume", methods=["POST"])
@hooks_app.route("/resume", methods=["POST"])
def hook_resume():
    """/resume hook — MicroVM waking from SUSPENDED state."""
    load_config()
    logger.info(f"=== /resume === PR #{config['pr_number']} — reviewer returned")
    return jsonify({"status": "resumed"}), 200


@hooks_app.route("/aws/lambda-microvms/runtime/v1/suspend", methods=["POST"])
@hooks_app.route("/suspend", methods=["POST"])
def hook_suspend():
    """/suspend hook — MicroVM going idle."""
    logger.info(f"=== /suspend === PR #{config['pr_number']} — going idle")
    return jsonify({"status": "suspending"}), 200


@hooks_app.route("/aws/lambda-microvms/runtime/v1/terminate", methods=["POST"])
@hooks_app.route("/terminate", methods=["POST"])
def hook_terminate():
    """/terminate hook — MicroVM being destroyed."""
    logger.info(f"=== /terminate === PR #{config['pr_number']}")

    if config.get("cleanup_data", False):
        try:
            cleanup_dynamodb(config)
            logger.info(f"✅ Cleaned DynamoDB for PR #{config['pr_number']}")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    else:
        logger.info("Skipping data cleanup (version update, not PR close)")

    return jsonify({"status": "terminated"}), 200


# =====================================================
# APP SERVER (port 8080) — User-facing
# =====================================================

app = Flask("app")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PR #{{ pr_number }} — Task Manager</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, sans-serif; background: #f0fdf4; color: #1a2e1a; }
        .pr-banner {
            background: linear-gradient(135deg, #16a34a 0%, #059669 100%);
            color: white; padding: 18px 28px; font-size: 15px;
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 4px solid #15803d;
        }
        .pr-banner strong { font-size: 18px; font-weight: 700; }
        .pr-banner .meta { opacity: 0.9; font-size: 13px; }
        .container { max-width: 720px; margin: 50px auto; padding: 0 24px; }
        h1 { color: #14532d; margin-bottom: 12px; font-size: 36px; font-weight: 800; }
        .subtitle { color: #4d7c4d; margin-bottom: 35px; font-size: 16px; line-height: 1.5; }
        .add-form { display: flex; gap: 12px; margin-bottom: 35px; }
        .add-form input {
            flex: 1; padding: 14px 18px; border: 2px solid #86efac;
            border-radius: 12px; font-size: 15px; background: white;
        }
        .add-form input:focus { outline: none; border-color: #16a34a; box-shadow: 0 0 0 3px rgba(22,163,74,0.1); }
        .add-form button {
            padding: 14px 28px; background: #16a34a;
            color: white; border: none; border-radius: 12px;
            cursor: pointer; font-size: 15px; font-weight: 700; text-transform: uppercase;
            letter-spacing: 1px;
        }
        .add-form button:hover { background: #15803d; transform: scale(1.02); }
        .task-list { list-style: none; }
        .task-item {
            background: white; padding: 18px 22px; margin-bottom: 12px;
            border-radius: 14px; border: 2px solid #bbf7d0;
            display: flex; justify-content: space-between; align-items: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .task-item:hover { border-color: #16a34a; box-shadow: 0 4px 12px rgba(22,163,74,0.1); }
        .task-item .task-text { font-size: 16px; color: #1a2e1a; font-weight: 500; }
        .task-item .task-time { font-size: 12px; color: #6b8f6b; margin-top: 4px; }
        .task-item .delete-btn {
            background: #fef2f2; border: none; color: #dc2626;
            cursor: pointer; font-size: 20px; width: 32px; height: 32px;
            border-radius: 50%; display: flex; align-items: center; justify-content: center;
        }
        .task-item .delete-btn:hover { background: #dc2626; color: white; }
        .empty { text-align: center; color: #6b8f6b; padding: 50px; font-size: 16px; }
        .footer {
            text-align: center; margin-top: 50px; font-size: 12px; color: #6b8f6b; padding: 20px;
        }
        .footer code { background: #dcfce7; color: #15803d; padding: 3px 8px; border-radius: 4px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="pr-banner">
        <div><strong>🔀 PR #{{ pr_number }}</strong> — {{ branch }}</div>
        <div class="meta">by {{ author }} | Lambda MicroVM PR Environment</div>
    </div>
    <div class="container">
        <h1>Task Garden 🌱</h1>
        <p class="subtitle">Grow your tasks, harvest your productivity. PR #{{ pr_number }} preview running on Lambda MicroVM with instant suspend/resume.</p>
        <div class="add-form">
            <input type="text" id="taskInput" placeholder="Add a new task..." onkeypress="if(event.key==='Enter')addTask()">
            <button onclick="addTask()">Add</button>
        </div>
        <ul class="task-list" id="taskList">
            {% for task in tasks %}
            <li class="task-item">
                <div>
                    <div class="task-text">{{ task.title }}</div>
                    <div class="task-time">{{ task.created_at }}</div>
                </div>
                <button class="delete-btn" onclick="deleteTask('{{ task.task_id }}')">&times;</button>
            </li>
            {% endfor %}
            {% if not tasks %}
            <li class="empty">No tasks yet. Add one above!</li>
            {% endif %}
        </ul>
        <div class="footer">
            <code>Lambda MicroVM</code> | Table: <code>{{ table_name }}</code> |
            Partition: <code>PR#{{ pr_number }}</code> | MicroVM: <code>{{ microvm_id }}</code>
        </div>
    </div>
    <script>
        async function addTask() {
            const input = document.getElementById('taskInput');
            const title = input.value.trim();
            if (!title) return;
            await fetch('/tasks', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title: title})
            });
            input.value = '';
            location.reload();
        }
        async function deleteTask(taskId) {
            await fetch('/tasks/' + taskId, {method: 'DELETE'});
            location.reload();
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    """Render task manager homepage."""
    load_config()
    try:
        seed_sample_data(config)
    except Exception as e:
        logger.warning(f"Seed failed: {e}")
    tasks = get_tasks()
    return render_template_string(
        HTML_TEMPLATE,
        pr_number=config["pr_number"],
        branch=config["branch"],
        author=config["author"],
        accent_color=config["accent_color"],
        table_name=config["dynamodb_table"],
        microvm_id=config.get("microvm_id", "unknown"),
        tasks=tasks,
    )


@app.route("/tasks", methods=["GET"])
def list_tasks_route():
    """API: List all tasks for this PR."""
    load_config()
    return jsonify(get_tasks())


@app.route("/tasks", methods=["POST"])
def create_task():
    """API: Create a new task."""
    load_config()
    data = request.json
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    task_id = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    item = {
        "PK": f"PR#{config['pr_number']}",
        "SK": f"TASK#{task_id}",
        "title": title,
        "task_id": task_id,
        "created_at": datetime.utcnow().isoformat(),
    }
    get_table().put_item(Item=item)
    logger.info(f"Created task: {title} (PR #{config['pr_number']})")
    return jsonify(item), 201


@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    """API: Delete a task."""
    load_config()
    get_table().delete_item(Key={"PK": f"PR#{config['pr_number']}", "SK": f"TASK#{task_id}"})
    logger.info(f"Deleted task: {task_id}")
    return jsonify({"deleted": task_id})


@app.route("/health")
def health():
    """Health check."""
    load_config()
    return jsonify({
        "status": "healthy",
        "pr": config["pr_number"],
        "branch": config["branch"],
        "microvm_id": config.get("microvm_id", "unknown"),
    })


# =====================================================
# HELPERS
# =====================================================

def get_table():
    """Get DynamoDB table resource."""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    return dynamodb.Table(config["dynamodb_table"])


def get_tasks():
    """Fetch all tasks for this PR from DynamoDB."""
    try:
        response = get_table().query(
            KeyConditionExpression=Key("PK").eq(f"PR#{config['pr_number']}")
            & Key("SK").begins_with("TASK#")
        )
        return response.get("Items", [])
    except Exception as e:
        logger.error(f"DynamoDB query failed: {e}")
        return []


def seed_sample_data(cfg):
    """Seed DynamoDB with sample tasks if none exist for this PR."""
    table = get_table()
    existing = table.query(
        KeyConditionExpression=Key("PK").eq(f"PR#{cfg['pr_number']}"),
        Limit=1,
    )
    if existing.get("Items"):
        return

    sample_tasks = [
        "Review authentication flow",
        "Test mobile responsive layout",
        "Verify API error handling",
    ]
    for i, title in enumerate(sample_tasks):
        task_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + str(i).zfill(6)
        table.put_item(Item={
            "PK": f"PR#{cfg['pr_number']}",
            "SK": f"TASK#{task_id}",
            "title": title,
            "task_id": task_id,
            "created_at": datetime.utcnow().isoformat(),
        })
    logger.info(f"Seeded {len(sample_tasks)} sample tasks for PR #{cfg['pr_number']}")


def cleanup_dynamodb(cfg):
    """Delete all items for this PR from DynamoDB."""
    table = get_table()
    response = table.query(
        KeyConditionExpression=Key("PK").eq(f"PR#{cfg['pr_number']}")
    )
    items = response.get("Items", [])
    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
    logger.info(f"Deleted {len(items)} items for PR #{cfg['pr_number']}")


# =====================================================
# STARTUP — Both servers
# =====================================================

def start_hooks_server():
    """Start the hooks server on port 9000 in a background thread."""
    logger.info(f"Starting hooks server on port {HOOKS_PORT}")
    hooks_app.run(host="0.0.0.0", port=HOOKS_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    load_config()

    # Start hooks server FIRST (Lambda sends /ready here)
    hooks_thread = threading.Thread(target=start_hooks_server, daemon=True)
    hooks_thread.start()

    # Then start app server (user traffic)
    logger.info(f"Starting app server on port {APP_PORT}")
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
