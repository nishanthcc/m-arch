from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ProviderMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str

class ProviderResponse(BaseModel):
    content: str
    provider_name: str
    model_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_seconds: float = 0.0
    fallback_used: bool = False
    raw_response: Optional[Dict[str, Any]] = None

class BaseLLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def generate_chat(
        self,
        messages: List[ProviderMessage],
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.2,
        model: Optional[str] = None,
    ) -> ProviderResponse:
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Verify provider connectivity and active model availability without revealing secrets.
        """
        pass
