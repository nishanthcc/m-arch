import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from app.prompts.registry import get_prompt_definition
from app.services.reports.exporter import generate_markdown_report, generate_html_report, format_finding_item
from app.agents.verifier.agent import EvidenceVerifierAgent
from app.agents.orchestrator.agent import OrchestratorAgent

async def run_v1_3_verification_suite():
    print("======================================================================")
    print(" M-ARCH v1.3.0 DUAL-MODE PERSONA & QUANTITATIVE SCORING TEST SUITE")
    print("======================================================================")

    # 1. Verify Prompts
    print("\n--- TEST 1: Registered Prompts v1.3.0 ---")
    p_dual = get_prompt_definition("dual_mode_synthesis_v1_3")
    assert p_dual.version == "1.3.0"
    assert "TARGET AUDIENCE MODE" in p_dual.system_prompt
    assert "STRICT AUDIENCE CONSTRAINTS" in p_dual.system_prompt
    assert "Technical Review" in p_dual.system_prompt
    assert "Simplified Version" in p_dual.system_prompt
    print("✓ Registered prompt dual_mode_synthesis_v1_3 verified.")

    p_topo = get_prompt_definition("topology_extraction_v1_0")
    assert p_topo.version == "1.3.0"
    assert "nodes" in p_topo.required_json_keys
    assert "edges" in p_topo.required_json_keys
    print("✓ Registered prompt topology_extraction_v1_0 verified.")

    # 2. Verify Exporter Dual-Mode Formatting
    print("\n--- TEST 2: Dual-Mode Persona Exporter Strict Constraints ---")
    sample_finding = {
        "id": "fnd_sec_1",
        "title": "Hardcoded JWT Secret Token in Authentication Handler",
        "explanation": "Static inspection identified a raw cryptographic string assigned to secret_key variable.",
        "severity": "critical",
        "category": "security",
        "impact": "Attackers can forge JWT authentication signatures and impersonate administrative accounts.",
        "remediation": "Move secret_key to environment variables and validate with Pydantic BaseSettings.",
        "confidence": 0.95,
        "verification_status": "static_analysis",
        "agent_id": "security_agent",
        "evidence_items": [{
            "display_path": "backend/app/auth.py",
            "line_start": 42,
            "line_end": 44,
            "excerpt": "JWT_SECRET = 'hardcoded_production_secret_key_xyz'"
        }]
    }

    # Technical Review Mode
    tech_md = generate_markdown_report(
        project_name="Secured API",
        question="Security & Architecture Audit",
        status="completed",
        summary="Audit completed with 1 critical finding.",
        limitations="Static code inspection only.",
        findings=[sample_finding],
        tasks=[],
        mode="technical_review"
    )

    assert "Technical Architecture" in tech_md
    assert "Issue Identified" in tech_md
    assert "Technical Root Cause" in tech_md
    assert "Specific Remediation Steps" in tech_md
    assert "backend/app/auth.py:L42-44" in tech_md
    assert "JWT_SECRET = 'hardcoded_production_secret_key_xyz'" in tech_md
    print("✓ Technical Review correctly formats root cause, exact line numbers, and code excerpts.")

    # Simplified Version Mode
    simple_md = generate_markdown_report(
        project_name="Secured API",
        question="Security & Architecture Audit",
        status="completed",
        summary="A security issue was found with your system password configuration.",
        limitations="Automated check only.",
        findings=[sample_finding],
        tasks=[],
        mode="simplified_version"
    )

    assert "Simplified Plain-Language Review" in simple_md
    assert "What is the problem?" in simple_md
    assert "Why does it matter?" in simple_md
    assert "How do we fix it?" in simple_md
    # Strict Audience Constraints: zero code snippets, zero line numbers
    assert "L42-44" not in simple_md
    assert "JWT_SECRET = 'hardcoded_production_secret_key_xyz'" not in simple_md
    print("✓ Simplified Version strictly excludes code snippets and line numbers, adhering to plain language.")

    # 3. Verify Verifier Quantitative Granular Scoring (1-10)
    print("\n--- TEST 3: Verifier Quantitative Granular Scoring (1-10) ---")
    verifier = EvidenceVerifierAgent()
    candidate_findings = [sample_finding]

    verify_res = await verifier.verify_findings(
        candidate_findings=candidate_findings,
        question="Audit security",
        session=None,
        project_id="test_proj"
    )

    assert "quality_scores" in verify_res
    q_scores = verify_res["quality_scores"]
    print("Quality scores computed:", q_scores)

    for metric in [
        "security_score", "performance_score", "maintainability_score",
        "reliability_score", "test_coverage_score", "overall_architecture_score"
    ]:
        assert metric in q_scores, f"Missing metric: {metric}"
        val = q_scores[metric]
        assert isinstance(val, int), f"{metric} should be integer, got {type(val)}"
        assert 1 <= val <= 10, f"{metric} out of bounds (1-10): {val}"

    # Critical security finding should lower security score
    assert q_scores["security_score"] < 10
    print("✓ Quantitative integer scores (1-10) verified across all 6 architectural metrics.")

    # 4. Verify Topology Extraction
    print("\n--- TEST 4: Architecture Topology Extraction ---")
    orchestrator = OrchestratorAgent()
    mock_sources = [
        {"file_path": "app.py"},
        {"file_path": "routers/users.py"},
        {"file_path": "db/database.py"}
    ]
    mock_profile = {
        "frameworks": [{"name": "FastAPI", "version": "0.115.0"}],
        "database_technologies": [{"name": "SQLite"}],
        "routes": [{"path": "/users", "method": "GET"}],
        "architecture_graph": {
            "nodes": [
                {"id": "app.py", "type": "file", "label": "app.py", "status": "detected"},
                {"id": "db", "type": "database", "label": "SQLite", "status": "detected"}
            ],
            "edges": [
                {"id": "e1", "source": "app.py", "target": "db", "label": "queries", "status": "detected"}
            ]
        }
    }

    topo = await orchestrator.extract_architecture_topology(
        sources=mock_sources,
        profile_data=mock_profile
    )
    assert "nodes" in topo
    assert "edges" in topo
    assert len(topo["nodes"]) >= 2
    assert len(topo["edges"]) >= 1
    assert topo["nodes"][0]["id"] == "app.py"
    print(f"✓ Topology graph successfully extracted: {len(topo['nodes'])} nodes, {len(topo['edges'])} edges.")

    print("\n======================================================================")
    print(" ALL v1.3.0 DUAL-MODE & SCORING TESTS PASSED (100%)")
    print("======================================================================")

if __name__ == "__main__":
    asyncio.run(run_v1_3_verification_suite())
