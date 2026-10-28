import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.providers.base import BaseLLMProvider, ProviderMessage, ProviderResponse
from app.providers.redaction import redact_secrets

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    """
    Dedicated Google Gemini Provider.
    Configured specifically for the Code Reviewing Agent with free-tier models.
    """

    FALLBACK_MODELS = [
        "gemini-flash-lite-latest",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.5-flash-lite",
    ]

    def __init__(self):
        self._api_key = settings.GEMINI_API_KEY
        self._default_model = settings.GEMINI_MODEL
        self._base_url = settings.GEMINI_BASE_URL.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "Gemini"

    def is_configured(self) -> bool:
        return bool(self._api_key and len(self._api_key.strip()) > 5)

    async def generate_chat(
        self,
        messages: List[ProviderMessage],
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.1,
        model: Optional[str] = None,
    ) -> ProviderResponse:
        if not self.is_configured():
            raise ValueError("Gemini API key is not configured in backend/.env")

        target_model = model or self._default_model

        # Build redacted payload
        formatted_contents = []
        system_instruction = None

        if system_prompt:
            redacted_sys, _ = redact_secrets(system_prompt)
            system_instruction = {"parts": [{"text": redacted_sys}]}

        for msg in messages:
            redacted_content, _ = redact_secrets(msg.content)
            role = "model" if msg.role in ("assistant", "model") else "user"
            formatted_contents.append({
                "role": role,
                "parts": [{"text": redacted_content}]
            })

        # Ensure at least one content part
        if not formatted_contents:
            formatted_contents.append({"role": "user", "parts": [{"text": "Review request"}]})

        payload: Dict[str, Any] = {
            "contents": formatted_contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }

        if system_instruction:
            payload["system_instruction"] = system_instruction

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        start_time = time.time()
        max_retries = settings.MAX_RETRIES
        backoff = 1.0
        candidate_models = [target_model] + [m for m in self.FALLBACK_MODELS if m != target_model]

        last_error = None

        for current_model in candidate_models:
            for attempt in range(max_retries):
                url = f"{self._base_url}/models/{current_model}:generateContent?key={self._api_key}"
                try:
                    async with httpx.AsyncClient(timeout=90.0) as client:
                        resp = await client.post(url, json=payload)

                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            raise RuntimeError(f"Gemini returned empty candidates list: {data}")

                        parts = candidates[0].get("content", {}).get("parts", [])
                        if not parts:
                            raise RuntimeError(f"Gemini candidate has no parts: {candidates[0]}")

                        content = parts[0].get("text", "")
                        usage = data.get("usageMetadata", {})
                        latency = time.time() - start_time

                        return ProviderResponse(
                            content=content,
                            provider_name=self.provider_name,
                            model_name=current_model,
                            prompt_tokens=usage.get("promptTokenCount", 0),
                            completion_tokens=usage.get("candidatesTokenCount", 0),
                            total_tokens=usage.get("totalTokenCount", 0),
                            latency_seconds=round(latency, 3),
                            fallback_used=(current_model != target_model),
                            raw_response=data,
                        )

                    elif resp.status_code in (429, 500, 502, 503, 504):
                        logger.warning(
                            f"Gemini API transient status={resp.status_code} on {current_model}, "
                            f"attempt={attempt+1}/{max_retries}"
                        )
                        if attempt < max_retries - 1:
                            await asyncio.sleep(backoff)
                            backoff *= settings.RETRY_BACKOFF_FACTOR
                            continue
                        last_error = f"Gemini {resp.status_code}: {resp.text[:200]}"
                        # Try next fallback model
                        break
                    else:
                        err_text = resp.text[:300]
                        raise RuntimeError(f"Gemini API error ({resp.status_code}): {err_text}")

                except httpx.RequestError as exc:
                    logger.warning(f"Gemini connection error on {current_model}: {exc}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(backoff)
                        backoff *= settings.RETRY_BACKOFF_FACTOR
                        continue
                    last_error = str(exc)
                    break

        raise RuntimeError(f"Gemini request failed across models {candidate_models}: {last_error}")

    async def health_check(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "available": False,
                "configured": False,
                "error": "No Gemini API key configured in backend/.env",
                "active_model": self._default_model,
            }

        start_time = time.time()
        try:
            url = f"{self._base_url}/models?key={self._api_key}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                latency = (time.time() - start_time) * 1000

            if resp.status_code == 200:
                data = resp.json()
                raw_models = data.get("models", [])
                gemini_models = [
                    m.get("name", "").replace("models/", "")
                    for m in raw_models
                    if "gemini" in m.get("name", "").lower() and "generatecontent" in [
                        method.lower() for method in m.get("supportedGenerationMethods", [])
                    ]
                ]
                return {
                    "available": True,
                    "configured": True,
                    "latency_ms": round(latency, 1),
                    "active_model": self._default_model,
                    "error": None,
                    "installed_models": gemini_models[:8],
                    "model_available": any(self._default_model in m for m in gemini_models),
                }
            else:
                return {
                    "available": False,
                    "configured": True,
                    "latency_ms": round(latency, 1),
                    "active_model": self._default_model,
                    "error": f"HTTP {resp.status_code}: {resp.text[:120]}",
                }
        except Exception as exc:
            return {
                "available": False,
                "configured": True,
                "latency_ms": None,
                "active_model": self._default_model,
                "error": f"Connection failed: {str(exc)}",
            }

