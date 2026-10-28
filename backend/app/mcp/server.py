import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from mcp.server.mcpserver import MCPServer
from app.mcp.permissions import is_tool_allowed_for_agent
from app.mcp import tools

logger = logging.getLogger(__name__)

# Official MCPServer instance for M-ARCH
mcp_server = MCPServer("m-arch-tools", version="2.0.0")

# Register read-only MCP tool handlers
@mcp_server.tool(name="list_project_sources", description="List all ingested source files for a given project")
async def mcp_list_sources(project_id: str) -> str:
    # Handler for external MCP clients
    return f"Project sources tool registered for project_id={project_id}"

@mcp_server.tool(name="search_project_code", description="Hybrid dense and keyword search over project code files")
async def mcp_search_code(project_id: str, query: str) -> str:
    return f"Project code search tool registered for query={query}"

@mcp_server.tool(name="search_security_knowledge", description="Query curated security vulnerability and compliance knowledge")
async def mcp_security_knowledge(topic: str) -> str:
    return f"Security knowledge tool registered for topic={topic}"

async def execute_mcp_tool(
    agent_id: str,
    tool_name: str,
    arguments: Dict[str, Any],
    session: AsyncSession
) -> Dict[str, Any]:
    """
    Enforces role-based permissions and dispatches execution of approved MCP tools.
    """
    if not is_tool_allowed_for_agent(agent_id, tool_name):
        raise PermissionError(
            f"Agent '{agent_id}' does not have permission to execute MCP tool '{tool_name}'"
        )

    logger.info(f"Executing MCP tool '{tool_name}' for agent '{agent_id}'")

    if tool_name == "list_project_sources":
        project_id = arguments.get("project_id", "")
        return {"result": await tools.list_project_sources(session, project_id)}

    elif tool_name == "search_project_code":
        project_id = arguments.get("project_id", "")
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 8)
        return {"result": await tools.search_project_code(session, project_id, query, top_k)}

    elif tool_name == "search_project_documents":
        project_id = arguments.get("project_id", "")
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 8)
        return {"result": await tools.search_project_documents(session, project_id, query, top_k)}

    elif tool_name == "get_source_excerpt":
        project_id = arguments.get("project_id", "")
        source_id = arguments.get("source_id", "")
        line_start = arguments.get("line_start", 1)
        line_end = arguments.get("line_end", 50)
        return {"result": await tools.get_source_excerpt(session, project_id, source_id, line_start, line_end)}

    elif tool_name == "get_dependency_manifest":
        project_id = arguments.get("project_id", "")
        return {"result": await tools.get_dependency_manifest(session, project_id)}

    elif tool_name == "get_test_inventory":
        project_id = arguments.get("project_id", "")
        return {"result": await tools.get_test_inventory(session, project_id)}

    elif tool_name == "search_security_knowledge":
        topic = arguments.get("topic", "")
        return {"result": await tools.search_security_knowledge(topic, session)}

    elif tool_name == "get_review_evidence":
        review_id = arguments.get("review_id", "")
        return {"result": await tools.get_review_evidence(session, review_id)}

    elif tool_name == "get_agent_trace":
        review_id = arguments.get("review_id", "")
        target_agent = arguments.get("agent_id", "")
        return {"result": await tools.get_agent_trace(session, review_id, target_agent)}

    else:
        raise ValueError(f"Unknown MCP tool '{tool_name}'")
