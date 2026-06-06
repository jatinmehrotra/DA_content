import sys
import os
from unittest.mock import MagicMock

# Mock the mcp module before importing server — allows testing without mcp SDK installed
mock_fastmcp_module = MagicMock()
mock_mcp_instance = MagicMock()
# Make @mcp.tool() a pass-through decorator so functions remain callable
mock_mcp_instance.tool.return_value = lambda f: f
mock_fastmcp_module.FastMCP.return_value = mock_mcp_instance
sys.modules.setdefault("mcp", MagicMock())
sys.modules.setdefault("mcp.server", MagicMock())
sys.modules.setdefault("mcp.server.fastmcp", mock_fastmcp_module)

sys.path.insert(0, os.path.dirname(__file__))

from hypothesis import given, settings
from hypothesis.strategies import text, sampled_from, one_of
from server import search_docs, get_oncall, create_incident

# Mock data mirror for test verification
DOCS = [
    {"title": "Deployment Guide", "content": "How to deploy services to production using CI/CD pipelines"},
    {"title": "Onboarding", "content": "New engineer onboarding checklist and setup instructions"},
    {"title": "API Reference", "content": "REST API endpoints for the payment service"},
    {"title": "Runbook: High CPU", "content": "Steps to diagnose and resolve high CPU alerts"},
    {"title": "Architecture Overview", "content": "Microservices architecture with event-driven communication"},
]

# Known substrings that match documents (drawn from titles and content)
KNOWN_SUBSTRINGS = [
    "deploy", "Deployment", "CI/CD", "production",
    "onboarding", "checklist", "setup",
    "API", "REST", "payment",
    "Runbook", "CPU", "diagnose",
    "Architecture", "Microservices", "event-driven",
    "service",  # matches multiple docs
    "the",  # common word that may match
]


# Feature: mcp-demo-server, Property 2: Search returns all matching documents
@settings(max_examples=100)
@given(query=one_of(sampled_from(KNOWN_SUBSTRINGS), text(min_size=0, max_size=50)))
def test_property_2_search_returns_all_matching_documents(query):
    """
    For any query, verify result contains titles of ALL mock docs where query
    is a case-insensitive substring of title or content. If no matches, verify
    result contains "No results found" or similar.

    **Validates: Requirements 1.1, 1.2, 1.3**
    """
    result = search_docs(query)

    # Determine expected matching documents
    expected_matches = [
        doc for doc in DOCS
        if query.lower() in (doc["title"] + doc["content"]).lower()
    ]

    if expected_matches:
        # All matching document titles must appear in the result
        for doc in expected_matches:
            assert doc["title"] in result, (
                f"Expected title '{doc['title']}' in result for query '{query}', got: {result}"
            )
    else:
        # No matches — result should indicate no results found
        assert "No results found" in result, (
            f"Expected 'No results found' message for query '{query}', got: {result}"
        )
