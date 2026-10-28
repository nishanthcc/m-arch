import logging
from typing import List, Dict, Any, Optional, Literal
from app.core.config import settings
from app.providers.base import BaseLLMProvider, ProviderMessage, ProviderResponse
from app.providers.groq import GroqProvider
from app.providers.ollama import OllamaProvider
from app.providers.gemini import GeminiProvider

logger = logging.getLogger(__name__)

class ModelRouter:
    def __init__(self):
        self.groq = GroqProvider()
        self.ollama = OllamaProvider()
        self.gemini = GeminiProvider()

    def get_provider_by_name(self, name: str) -> BaseLLMProvider:
        if name.lower() == "groq":
            return self.groq
        elif name.lower() == "ollama":
            return self.ollama
        elif name.lower() == "gemini":
            return self.gemini
        raise ValueError(f"Unknown provider '{name}'")

    async def route_chat(
        self,
        messages: List[ProviderMessage],
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.2,
        agent_role: Optional[str] = None,
        override_mode: Optional[Literal["Auto", "Groq", "Ollama", "Hybrid", "Gemini"]] = None,
        override_model: Optional[str] = None,
    ) -> ProviderResponse:
        mode = override_mode or settings.AI_MODE

        # Dedicated routing rule: Code Review Agent uses Gemini Free API Key
        is_code_agent = bool(agent_role and "code" in agent_role.lower())
        if is_code_agent and self.gemini.is_configured() and override_mode not in ("Groq", "Ollama"):
            try:
                logger.info(
                    f"Routing code reviewing agent ({agent_role}) to dedicated Gemini provider ({settings.GEMINI_MODEL})"
                )
                return await self.gemini.generate_chat(
                    messages=messages,
                    system_prompt=system_prompt,
                    json_mode=json_mode,
                    temperature=temperature,
                    model=override_model or settings.GEMINI_MODEL,
                )
            except Exception as exc:
                logger.warning(
                    f"Dedicated Gemini provider failed for code agent ({exc}). Falling back to router default.",
                    exc_info=True,
                )

        # 1. Manual Gemini Mode
        if mode == "Gemini":
            if not self.gemini.is_configured():
                raise RuntimeError(
                    "Mode is set to 'Gemini', but GEMINI_API_KEY is not configured in backend/.env"
                )
            return await self.gemini.generate_chat(
                messages, system_prompt, json_mode, temperature, model=override_model
            )

        # 2. Manual Groq Mode
        elif mode == "Groq":
            if not self.groq.is_configured():
                raise RuntimeError(
                    "Mode is set to 'Groq', but GROQ_API_KEY is not configured in backend/.env"
                )
            return await self.groq.generate_chat(
                messages, system_prompt, json_mode, temperature, model=override_model
            )

        # 3. Manual Ollama Mode
        elif mode == "Ollama":
            return await self.ollama.generate_chat(
                messages, system_prompt, json_mode, temperature, model=override_model
            )

        # 3. Hybrid Mode
        elif mode == "Hybrid":
            target_provider_name = settings.AI_PRIMARY_PROVIDER
            if agent_role:
                role_lower = agent_role.lower()
                if "code" in role_lower:
                    target_provider_name = settings.HYBRID_CODE_PROVIDER
                elif "security" in role_lower:
                    target_provider_name = settings.HYBRID_SECURITY_PROVIDER
                elif "doc" in role_lower:
                    target_provider_name = settings.HYBRID_DOCS_PROVIDER
                elif "orchestrator" in role_lower:
                    target_provider_name = settings.HYBRID_ORCHESTRATOR_PROVIDER

            # If chosen hybrid provider is Groq but Groq is unconfigured, fallback to Ollama
            if target_provider_name == "Groq" and not self.groq.is_configured():
                logger.info(f"Hybrid routed to Groq for role={agent_role}, but Groq is unconfigured. Falling back to Ollama.")
                resp = await self.ollama.generate_chat(
                    messages, system_prompt, json_mode, temperature, model=override_model
                )
                resp.fallback_used = True
                return resp

            provider = self.get_provider_by_name(target_provider_name)
            return await provider.generate_chat(
                messages, system_prompt, json_mode, temperature, model=override_model
            )

        # 4. Auto Mode (Primary -> Fallback)
        else:
            primary_name = settings.AI_PRIMARY_PROVIDER
            fallback_name = settings.AI_FALLBACK_PROVIDER
            primary = self.get_provider_by_name(primary_name)
            fallback = self.get_provider_by_name(fallback_name)

            # Check if primary is Groq but not configured
            if primary_name == "Groq" and not self.groq.is_configured():
                logger.info("Auto mode: Groq is not configured. Automatically using Ollama.")
                resp = await fallback.generate_chat(
                    messages, system_prompt, json_mode, temperature, model=override_model
                )
                resp.fallback_used = True
                return resp

            try:
                return await primary.generate_chat(
                    messages, system_prompt, json_mode, temperature, model=override_model
                )
            except Exception as primary_err:
                logger.warning(
                    f"Auto mode: Primary provider '{primary_name}' failed ({primary_err}). Initiating fallback to '{fallback_name}'."
                )
                try:
                    resp = await fallback.generate_chat(
                        messages, system_prompt, json_mode, temperature, model=override_model
                    )
                    resp.fallback_used = True
                    return resp
                except Exception as fallback_err:
                    raise RuntimeError(
                        f"Both primary ('{primary_name}': {primary_err}) and fallback ('{fallback_name}': {fallback_err}) failed."
                    )

    async def get_health_status(self) -> Dict[str, Any]:
        groq_status = await self.groq.health_check()
        groq_status["name"] = "Groq"
        ollama_status = await self.ollama.health_check()
        ollama_status["name"] = "Ollama"
        gemini_status = await self.gemini.health_check()
        gemini_status["name"] = "Gemini"
        return {
            "mode": settings.AI_MODE,
            "primary_provider": settings.AI_PRIMARY_PROVIDER,
            "fallback_provider": settings.AI_FALLBACK_PROVIDER,
            "providers": {
                "Groq": groq_status,
                "Ollama": ollama_status,
                "Gemini": gemini_status,
            }
        }

model_router = ModelRouter()
