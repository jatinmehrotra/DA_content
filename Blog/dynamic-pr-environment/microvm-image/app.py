"""
app.py — Dynamic PR Environment running inside a Lambda MicroVM.

Architecture:
- Port 8080: Main app (Flask full-stack — HTML + API + DynamoDB)
- Port 9000: Lifecycle hooks server (/run, /suspend, /resume, /terminate)

The app code is baked INTO the MicroVM image (via Dockerfile).
Each new commit → update-microvm-image → terminate old → run new.
PR metadata comes via runHookPayload (unique per MicroVM).
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
    "accent_color": "#E91E63",
    "dynamodb_table": "pr-environments",
    "microvm_id": "local",
}


def load_config():
    """Load config from file (written by /run hook)."""
    global config
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            config = json.load(f)
    return config


# =====================================================
# LIFECYCLE HOOKS SERVER (Port 9000)
# =====================================================

hooks_app = Flask("hooks")


@hooks_app.route("/aws/lambda-microvms/runtime/v1/run", methods=["POST"])
def hook_run():
    """
    /run hook — Called once when MicroVM starts from snapshot.

    Receives: {"microvmId": "...", "runHookPayload": "<json-string>"}

    Responsibilities:
    1. Parse PR metadata from runHookPayload
    2. Write config.json (app reads this on every request)
    3. Seed DynamoDB with sample data if empty
    4. Return 200 → MicroVM starts accepting external traffic
    """
    body = request.json or {}
    microvm_id = body.get("microvmId", "unknown")
    payload_str = body.get("runHookPayload", "{}")

    logger.info(f"=== /run hook fired === MicroVM: {microvm_id}")

    # Parse payload
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        payload = {}

    # Write config
    global config
    config = {
        "pr_number": payload.get("pr_number", "local"),
        "branch": payload.get("branch", "main"),
        "author": payload.get("author", "developer"),
        "accent_color": payload.get("accent_color", "#E91E63"),
        "dynamodb_table": payload.get("dynamodb_table", "pr-environments"),
        "microvm_id": microvm_id,
        "cleanup_data": payload.get("cleanup_data", False),
    }

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)

    logger.info(f"Config: PR #{config['pr_number']} | branch: {config['branch']} | color: {config['accent_color']}")

    # Seed DynamoDB with sample data (skip if data already exists from previous MicroVM)
    try:
        seed_sample_data(config)
    except Exception as e:
        logger.warning(f"Seed failed (non-fatal): {e}")

    logger.info(f"✅ /run complete — PR #{config['pr_number']} ready for traffic")
    return jsonify({"status": "ready"}), 200


@hooks_app.route("/aws/lambda-microvms/runtime/v1/resume", methods=["POST"])
def hook_resume():
    """
    /resume hook — MicroVM waking from SUSPENDED state.
    Reviewer came back to the PR environment after being idle.
    """
    load_config()
    logger.info(f"=== /resume === PR #{config['pr_number']} — reviewer returned")
    return jsonify({"status": "resumed"}), 200


@hooks_app.route("/aws/lambda-microvms/runtime/v1/suspend", methods=["POST"])
def hook_suspend():
    """
    /suspend hook — MicroVM going idle, about to be snapshotted.
    Flush any pending state.
    """
    logger.info(f"=== /suspend === PR #{config['pr_number']} — going idle")
    return jsonify({"status": "suspending"}), 200


@hooks_app.route("/aws/lambda-microvms/runtime/v1/terminate", methods=["POST"])
def hook_terminate():
    """
    /terminate hook — MicroVM being destroyed (PR closed or new version deployed).
    Only cleans DynamoDB if cleanup_data=true in config (set when PR is closed).
    On version updates (new commit), data is preserved for the next MicroVM.
    """
    logger.info(f"=== /terminate === PR #{config['pr_number']} — cleaning up")

    if config.get("cleanup_data", False):
        try:
            cleanup_dynamodb(config)
            logger.info(f"✅ Cleaned DynamoDB for PR #{config['pr_number']}")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    else:
        logger.info(f"Skipping data cleanup (version update, not PR close)")

    return jsonify({"status": "terminated"}), 200


# =====================================================
# MAIN APP SERVER (Port 8080)
# =====================================================

app = Flask("pr-env")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PR #{{ pr_number }} — Task Manager</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; }

        .pr-banner {
            background: {{ accent_color }};
            color: white;
            padding: 12px 20px;
            font-size: 13px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .pr-banner strong { font-size: 14px; }
        .pr-banner .meta { opacity: 0.9; }

        .container { max-width: 700px; margin: 40px auto; padding: 0 20px; }

        h1 { color: #232F3E; margin-bottom: 8px; }
        .subtitle { color: #666; margin-bottom: 30px; font-size: 14px; }

        .add-form { display: flex; gap: 10px; margin-bottom: 30px; }
        .add-form input {
            flex: 1; padding: 10px 14px; border: 1px solid #ddd;
            border-radius: 6px; font-size: 14px;
        }
        .add-form button {
            padding: 10px 20px; background: {{ accent_color }};
            color: white; border: none; border-radius: 6px;
            cursor: pointer; font-size: 14px; font-weight: 500;
        }
        .add-form button:hover { opacity: 0.9; }

        .task-list { list-style: none; }
        .task-item {
            background: white; padding: 14px 18px; margin-bottom: 8px;
            border-radius: 8px; border: 1px solid #eee;
            display: flex; justify-content: space-between; align-items: center;
        }
        .task-item .task-text { font-size: 14px; color: #333; }
        .task-item .task-time { font-size: 11px; color: #999; }
        .task-item .delete-btn {
            background: none; border: none; color: #D13212;
            cursor: pointer; font-size: 18px;
        }

        .empty { text-align: center; color: #999; padding: 40px; }

        .footer {
            text-align: center; margin-top: 40px; font-size: 12px; color: #999; padding: 20px;
        }
        .footer code { background: #eee; padding: 2px 6px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="pr-banner">
        <div>
            <strong>🔀 PR #{{ pr_number }}</strong> — {{ branch }}
        </div>
        <div class="meta">
            by {{ author }} | Lambda MicroVM PR Environment
        </div>
    </div>

    <div class="container">
        <h1>Task Manager</h1>
        <p class="subtitle">This is a live preview of PR #{{ pr_number }}. Any code changes in this PR are reflected here.</p>

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
def list_tasks():
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
        logger.info("Data already exists for this PR — skipping seed")
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
    """Delete all items for this PR from DynamoDB (called by /terminate hook)."""
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
# STARTUP
# =====================================================

def start_hooks_server():
    """Start lifecycle hooks server on port 9000 (Lambda talks to this)."""
    hooks_app.run(host="0.0.0.0", port=HOOKS_PORT, debug=False)


if __name__ == "__main__":
    # Start hooks server in background thread
    hooks_thread = threading.Thread(target=start_hooks_server, daemon=True)
    hooks_thread.start()
    logger.info(f"Hooks server listening on port {HOOKS_PORT}")

    # Load config if exists (from a previous /run hook)
    load_config()

    # Start main app
    logger.info(f"App server starting on port {APP_PORT}")
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
