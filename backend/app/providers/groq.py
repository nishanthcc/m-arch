import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.providers.base import BaseLLMProvider, ProviderMessage, ProviderResponse
from app.providers.redaction import redact_secrets

logger = logging.getLogger(__name__)

class GroqProvider(BaseLLMProvider):
    def __init__(self):
        self._api_key = settings.GROQ_API_KEY
        self._default_model = settings.GROQ_MODEL
        self._base_url = settings.GROQ_BASE_URL.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "Groq"

    def is_configured(self) -> bool:
        return bool(self._api_key and len(self._api_key.strip()) > 5)

    async def generate_chat(
        self,
        messages: List[ProviderMessage],
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.2,
        model: Optional[str] = None,
    ) -> ProviderResponse:
        if not self.is_configured():
            raise ValueError("Groq API key is not configured in backend/.env")

        target_model = model or self._default_model
        formatted_messages = []
        if system_prompt:
            redacted_sys, _ = redact_secrets(system_prompt)
            formatted_messages.append({"role": "system", "content": redacted_sys})

        for msg in messages:
            redacted_content, _ = redact_secrets(msg.content)
            formatted_messages.append({"role": msg.role, "content": redacted_content})

        payload = {
            "model": target_model,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        start_time = time.time()
        max_retries = settings.MAX_RETRIES
        backoff = 1.0

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        f"{self._base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                    )

                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    latency = time.time() - start_time
                    return ProviderResponse(
                        content=content,
                        provider_name=self.provider_name,
                        model_name=target_model,
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                        total_tokens=usage.get("total_tokens", 0),
                        latency_seconds=round(latency, 3),
                        fallback_used=False,
                        raw_response=data,
                    )
                elif resp.status_code in (429, 500, 502, 503, 504):
                    logger.warning(f"Groq API transient error status={resp.status_code}, attempt={attempt+1}/{max_retries}")
                    if attempt < max_retries - 1:
                        wait_time = backoff
                        if resp.status_code == 429:
                            reset_val = resp.headers.get("retry-after") or resp.headers.get("x-ratelimit-reset-tokens")
                            if reset_val:
                                try:
                                    cleaned = reset_val.rstrip("s").strip()
                                    wait_time = max(float(cleaned), backoff)
                                except ValueError:
                                    wait_time = backoff
                            wait_time = min(wait_time, 15.0)
                        logger.info(f"Retrying Groq in {wait_time:.1f}s (attempt {attempt+2}/{max_retries})...")
                        await asyncio.sleep(wait_time)
                        backoff *= settings.RETRY_BACKOFF_FACTOR
                        continue
                    resp.raise_for_status()
                else:
                    err_msg = resp.text
                    raise RuntimeError(f"Groq API error ({resp.status_code}): {err_msg}")
            except httpx.RequestError as exc:
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff)
                    backoff *= settings.RETRY_BACKOFF_FACTOR
                    continue
                raise RuntimeError(f"Groq connection failure: {exc}")

        raise RuntimeError("Groq request exceeded maximum bounded retry attempts")

    async def health_check(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "available": False,
                "configured": False,
                "error": "No API key configured in backend/.env",
                "active_model": self._default_model,
            }

        start_time = time.time()
        try:
            headers = {"Authorization": f"Bearer {self._api_key}"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self._base_url}/models", headers=headers)
                latency = (time.time() - start_time) * 1000

            if resp.status_code == 200:
                return {
                    "available": True,
                    "configured": True,
                    "latency_ms": round(latency, 1),
                    "active_model": self._default_model,
                    "error": None,
                }
            else:
                return {
                    "available": False,
                    "configured": True,
                    "latency_ms": round(latency, 1),
                    "active_model": self._default_model,
                    "error": f"HTTP {resp.status_code}: authentication or service error",
                }
        except Exception as exc:
            return {
                "available": False,
                "configured": True,
                "latency_ms": None,
                "active_model": self._default_model,
                "error": f"Connection failed: {str(exc)}",
            }
