import sys
import asyncio
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from app.core.config import settings
from app.providers.gemini import GeminiProvider
from app.providers.router import model_router
from app.providers.base import ProviderMessage
from app.agents.code.agent import CodeTestingAgent


async def run_gemini_code_agent_tests():
    print("======================================================================")
    print(" M-ARCH: GEMINI CODE AGENT DEDICATED ROUTING VERIFICATION SUITE")
    print("======================================================================")

    # 1. Config Check
    print("\n--- TEST 1: Gemini Configuration & Key Registration ---")
    assert settings.is_gemini_configured(), "GEMINI_API_KEY must be configured"
    assert settings.GEMINI_MODEL == "gemini-3.1-flash-lite", f"Unexpected model: {settings.GEMINI_MODEL}"
    print(f"✓ Gemini configured: model={settings.GEMINI_MODEL}, base_url={settings.GEMINI_BASE_URL}")

    # 2. Direct Gemini Provider Health & Inference
    print("\n--- TEST 2: Direct Gemini Provider Connectivity & Inference ---")
    gemini = GeminiProvider()
    health = await gemini.health_check()
    assert health["available"] is True, f"Gemini health check failed: {health.get('error')}"
    print(f"✓ Gemini health check passed (latency: {health.get('latency_ms')}ms)")

    resp = await gemini.generate_chat(
        messages=[ProviderMessage(role="user", content='Respond with valid JSON: {"status": "ok", "agent": "code"}')],
        json_mode=True
    )
    assert resp.provider_name == "Gemini", f"Expected Gemini, got {resp.provider_name}"
    assert resp.model_name in ("gemini-3.1-flash-lite", "gemini-flash-lite-latest")
    assert "status" in resp.content
    print(f"✓ Direct Gemini inference succeeded: {resp.provider_name} [{resp.model_name}] tokens={resp.total_tokens}")

    # 3. Router Scoping: Code Agent MUST Route to Gemini
    print("\n--- TEST 3: ModelRouter Scoping - Code Agent to Gemini ---")
    code_resp = await model_router.route_chat(
        messages=[ProviderMessage(role="user", content='Respond with JSON: {"agent_role": "code_agent_verified"}')],
        json_mode=True,
        agent_role="code_agent"
    )
    assert code_resp.provider_name == "Gemini", f"Expected Gemini for code_agent, got {code_resp.provider_name}"
    print(f"✓ Code agent correctly routed to: {code_resp.provider_name} ({code_resp.model_name})")

    # 4. Router Scoping: Other Agents MUST NOT Route to Gemini
    print("\n--- TEST 4: ModelRouter Scoping - Other Agents Isolation ---")
    for other_role in ["security_agent", "documentation_agent", "dependency_agent", "orchestrator", "evidence_verifier"]:
        other_resp = await model_router.route_chat(
            messages=[ProviderMessage(role="user", content=f'Respond with valid JSON: {{"agent_role": "{other_role}"}}')],
            json_mode=True,
            agent_role=other_role
        )
        assert other_resp.provider_name != "Gemini", (
            f"Security/other agent '{other_role}' incorrectly routed to Gemini! "
            f"Expected Groq/Ollama, got {other_resp.provider_name}"
        )
        print(f"✓ Agent '{other_role}' correctly routed to: {other_resp.provider_name} ({other_resp.model_name})")

    # 5. Health Status Aggregation
    print("\n--- TEST 5: Health Status Aggregation in ModelRouter ---")
    all_health = await model_router.get_health_status()
    assert "Gemini" in all_health["providers"], "Gemini must be in health providers"
    assert "Groq" in all_health["providers"], "Groq must be in health providers"
    assert "Ollama" in all_health["providers"], "Ollama must be in health providers"
    assert all_health["providers"]["Gemini"]["available"] is True
    print(f"✓ Router health aggregation verified: {list(all_health['providers'].keys())}")

    # 6. CodeTestingAgent Class Verification
    print("\n--- TEST 6: CodeTestingAgent Configuration ---")
    agent = CodeTestingAgent()
    assert agent.agent_id == "code_agent"
    assert agent.name == "Code & Testing Specialist"
    print(f"✓ CodeTestingAgent initialized with agent_id='{agent.agent_id}', name='{agent.name}'")

    print("\n======================================================================")
    print(" ALL GEMINI CODE AGENT VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("======================================================================")

if __name__ == "__main__":
    asyncio.run(run_gemini_code_agent_tests())
