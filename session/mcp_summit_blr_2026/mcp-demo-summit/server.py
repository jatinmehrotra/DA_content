import random
from mcp.server.fastmcp import FastMCP

# FastMCP turns Python functions into MCP tools — agents discover them automatically via tools/list
mcp = FastMCP("demo-server", host="0.0.0.0", stateless_http=True)

DOCS = [  # Mock data — in production, these would be API calls to real systems
    {"title": "Deployment Guide", "content": "How to deploy services to production using CI/CD pipelines"},
    {"title": "Onboarding", "content": "New engineer onboarding checklist and setup instructions"},
    {"title": "API Reference", "content": "REST API endpoints for the payment service"},
    {"title": "Runbook: High CPU", "content": "Steps to diagnose and resolve high CPU alerts"},
    {"title": "Architecture Overview", "content": "Microservices architecture with event-driven communication"},
]
ONCALL = {
    "platform": {"name": "Alice Chen", "contact": "alice@example.com", "phone": "+1-555-0101"},
    "payments": {"name": "Bob Kumar", "contact": "bob@example.com", "phone": "+1-555-0102"},
    "frontend": {"name": "Carol Smith", "contact": "carol@example.com", "phone": "+1-555-0103"},
}

# Docstrings = tool descriptions agents read during discovery. All tools return str — simplest MCP contract.

@mcp.tool()
def search_docs(query: str) -> str:
    """Search team documentation by keyword. Provide a search query and get matching docs."""
    query = query.strip()
    results = [f"{d['title']}: {d['content']}" for d in DOCS if query.lower() in (d["title"] + d["content"]).lower()]
    return "\n".join(results) if results else f"No results found for '{query}'"

@mcp.tool()
def get_oncall(team: str) -> str:
    """Look up who is on-call for a given team. Provide the team name (e.g., 'platform')."""
    team = team.strip()
    info = ONCALL.get(team.lower())
    return f"{info['name']} — {info['contact']} — {info['phone']}" if info else f"Team '{team}' not found"

@mcp.tool()
def create_incident(title: str, severity: str) -> str:
    """Create an incident ticket. Provide title and severity (e.g., 'SEV1', 'SEV2')."""
    return f"Incident created: [INC-{random.randint(1000, 9999)}] {title} (Severity: {severity})"

@mcp.tool()
def delete_incident(ticket_id: str) -> str:
    """Delete an incident ticket. Provide the ticket ID (e.g., 'INC-1234'). Destructive operation."""
    return f"Incident {ticket_id} deleted permanently."

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
