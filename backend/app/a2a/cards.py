from typing import Dict, List, Any
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from app.mcp.permissions import ROLE_MCP_PERMISSIONS

def build_agent_card(
    agent_id: str,
    name: str,
    description: str,
    skills: List[str],
    endpoint: str = ""
) -> AgentCard:
    """Builds an official A2A AgentCard instance."""
    agent_skills = [
        AgentSkill(id=f"skill_{i}", name=skill_name, description=skill_name)
        for i, skill_name in enumerate(skills)
    ]
    capabilities = AgentCapabilities(
        streaming=True,
        push_notifications=False
    )
    return AgentCard(
        name=name,
        description=description,
        version="1.1.0",
        capabilities=capabilities,
        skills=agent_skills,
        default_input_modes=["text/plain", "application/json"],
        default_output_modes=["application/json", "text/markdown"]
    )

AGENT_CARDS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "orchestrator": {
        "agent_id": "orchestrator",
        "name": "M-ARCH Orchestrator Agent",
        "role": "Orchestrator & Synthesizer",
        "description": "Decomposes project review inquiries, coordinates A2A specialist agents, resolves conflicts, and synthesizes evidence-backed reports.",
        "skills": ["Review Decomposition", "Agent Coordination", "Cross-Agent Conflict Resolution", "Executive Synthesis"],
        "allowed_mcp_tools": list(ROLE_MCP_PERMISSIONS["orchestrator"]),
        "endpoint": "/api/v1/agents/orchestrator",
        "prompt_id": "orchestrator_synthesis_v1_1",
    },
    "code_agent": {
        "agent_id": "code_agent",
        "name": "Code and Testing Specialist",
        "role": "Static Code & Test Analysis",
        "description": "Performs static inspection of source architecture, logic patterns, dependency manifests, and test inventories without executing code.",
        "skills": ["Static Code Analysis", "Test Coverage Assessment", "Dependency Inspection", "Code Architecture Review"],
        "allowed_mcp_tools": list(ROLE_MCP_PERMISSIONS["code_agent"]),
        "endpoint": "/api/v1/agents/code_agent",
        "prompt_id": "code_specialist_v1_1",
    },
    "security_agent": {
        "agent_id": "security_agent",
        "name": "Security & Vulnerability Specialist",
        "role": "Static Security & Secret Analysis",
        "description": "Scans for hard-coded credentials, insecure configurations, known CWE vulnerabilities, and flags manual review requirements.",
        "skills": ["Secret Detection", "Static Vulnerability Scanning", "CWE Security Knowledge Matching", "Compliance Review"],
        "allowed_mcp_tools": list(ROLE_MCP_PERMISSIONS["security_agent"]),
        "endpoint": "/api/v1/agents/security_agent",
        "prompt_id": "security_specialist_v1_1",
    },
    "documentation_agent": {
        "agent_id": "documentation_agent",
        "name": "Documentation & Deployment Specialist",
        "role": "Documentation & Ops Verification",
        "description": "Inspects README, API references, architecture documents, and deployment manifests for operational readiness and completeness.",
        "skills": ["Operational Readiness", "Documentation Completeness", "Deployment Manifest Review", "API Spec Validation"],
        "allowed_mcp_tools": list(ROLE_MCP_PERMISSIONS["documentation_agent"]),
        "endpoint": "/api/v1/agents/documentation_agent",
        "prompt_id": "documentation_specialist_v1_1",
    },
    "dependency_agent": {
        "agent_id": "dependency_agent",
        "name": "Dependency & Supply Chain Specialist",
        "role": "Supply Chain & Manifest Analysis",
        "description": "Inspects package manifests, lockfiles, unpinned dependencies, license compliance, and SBOM declarations.",
        "skills": ["Dependency Manifest Inspection", "Supply Chain Risk Assessment", "License Compliance Audit", "Lockfile Verification"],
        "allowed_mcp_tools": list(ROLE_MCP_PERMISSIONS["dependency_agent"]),
        "endpoint": "/api/v1/agents/dependency_agent",
        "prompt_id": "dependency_specialist_v1_1",
    },
    "evidence_verifier": {
        "agent_id": "evidence_verifier",
        "name": "Evidence & Citation Verifier",
        "role": "Pre-Synthesis Quality Gate",
        "description": "Validates candidate findings against retrieved evidence, flags overstated claims, eliminates unsupported conclusions, and surfaces contradictions.",
        "skills": ["Evidence Grounding Verification", "Citation Location Audit", "Overstatement Detection", "Discrepancy Identification"],
        "allowed_mcp_tools": list(ROLE_MCP_PERMISSIONS["evidence_verifier"]),
        "endpoint": "/api/v1/agents/evidence_verifier",
        "prompt_id": "evidence_verifier_v1_1",
    },
}

def get_official_agent_card(agent_id: str) -> AgentCard:
    meta = AGENT_CARDS_REGISTRY.get(agent_id)
    if not meta:
        raise ValueError(f"Unknown agent '{agent_id}'")
    return build_agent_card(
        agent_id=meta["agent_id"],
        name=meta["name"],
        description=meta["description"],
        skills=meta["skills"],
        endpoint=meta["endpoint"]
    )
