from typing import Dict, Set

# Strict permissions: give each agent only the tools required for its role
ROLE_MCP_PERMISSIONS: Dict[str, Set[str]] = {
    "code_agent": {
        "list_project_sources",
        "search_project_code",
        "get_source_excerpt",
        "get_dependency_manifest",
        "get_test_inventory",
    },
    "security_agent": {
        "list_project_sources",
        "search_project_code",
        "search_project_documents",
        "get_source_excerpt",
        "get_dependency_manifest",
        "search_security_knowledge",
    },
    "documentation_agent": {
        "list_project_sources",
        "search_project_documents",
        "get_source_excerpt",
    },
    "dependency_agent": {
        "list_project_sources",
        "get_dependency_manifest",
        "get_source_excerpt",
    },
    "evidence_verifier": {
        "get_source_excerpt",
        "get_review_evidence",
    },
    "orchestrator": {
        "list_project_sources",
        "get_review_evidence",
        "get_agent_trace",
    },
}

def is_tool_allowed_for_agent(agent_id: str, tool_name: str) -> bool:
    allowed = ROLE_MCP_PERMISSIONS.get(agent_id, set())
    return tool_name in allowed
