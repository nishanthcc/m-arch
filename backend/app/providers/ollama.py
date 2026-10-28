import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.providers.base import BaseLLMProvider, ProviderMessage, ProviderResponse

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    def __init__(self):
        self._base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self._default_model = settings.OLLAMA_MODEL

    @property
    def provider_name(self) -> str:
        return "Ollama"

    def is_configured(self) -> bool:
        return True  # Local endpoint is always eligible to be probed

    async def generate_chat(
        self,
        messages: List[ProviderMessage],
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.2,
        model: Optional[str] = None,
    ) -> ProviderResponse:
        target_model = model or self._default_model

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": target_model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        if json_mode:
            payload["format"] = "json"

        start_time = time.time()
        timeout = float(settings.AGENT_TIMEOUT_SECONDS)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(f"{self._base_url}/api/chat", json=payload)

            if resp.status_code == 200:
                data = resp.json()
                content = data.get("message", {}).get("content", "")
                latency = time.time() - start_time
                prompt_eval_count = data.get("prompt_eval_count", 0)
                eval_count = data.get("eval_count", 0)
                return ProviderResponse(
                    content=content,
                    provider_name=self.provider_name,
                    model_name=target_model,
                    prompt_tokens=prompt_eval_count,
                    completion_tokens=eval_count,
                    total_tokens=prompt_eval_count + eval_count,
                    latency_seconds=round(latency, 3),
                    fallback_used=False,
                    raw_response=data,
                )
            else:
                raise RuntimeError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self._base_url}. Ensure Ollama is running (`ollama serve`)."
            )
        except httpx.TimeoutException:
            raise RuntimeError(f"Ollama inference timed out after {timeout} seconds.")

    async def health_check(self) -> Dict[str, Any]:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                latency = (time.time() - start_time) * 1000

            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                model_found = any(self._default_model in m for m in models)
                return {
                    "available": True,
                    "configured": True,
                    "latency_ms": round(latency, 1),
                    "active_model": self._default_model,
                    "installed_models": models,
                    "model_available": model_found,
                    "error": None if model_found else f"Model '{self._default_model}' not found in Ollama tags. Run `ollama pull {self._default_model}`",
                }
            else:
                return {
                    "available": False,
                    "configured": True,
                    "latency_ms": round(latency, 1),
                    "active_model": self._default_model,
                    "error": f"Ollama HTTP {resp.status_code}",
                }
        except Exception as exc:
            return {
                "available": False,
                "configured": True,
                "latency_ms": None,
                "active_model": self._default_model,
                "error": f"Ollama service offline or unreachable at {self._base_url}",
            }
