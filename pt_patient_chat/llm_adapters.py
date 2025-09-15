
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os

class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        ...

class EchoLLMClient(BaseLLMClient):
    def generate_stream(self, messages: List[Dict[str, str]], temperature: float = 0.2):
        txt = self.generate(messages, temperature=temperature)
        # Simulate token stream by words
        for w in txt.split():
            yield w + ' '
    """A fallback that echoes the last user message; useful for offline testing."""
    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"(echo) {last_user}"

# Optional OpenAI adapter. Requires `pip install openai` and env var OPENAI_API_KEY.
# Model name can come from OPENAI_MODEL (default: gpt-4o-mini or gpt-4o).
class OpenAIChatClient(BaseLLMClient):
    def __init__(self, model: Optional[str] = None):
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:
            raise RuntimeError("OpenAI package not installed. `pip install openai`") from e
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY")
        self._client = OpenAI(api_key=api_key)
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content

# Optional Azure OpenAI adapter (API-compatible if configured properly).
class AzureOpenAIChatClient(BaseLLMClient):
    def __init__(self, deployment: Optional[str] = None):
        try:
            from openai import AzureOpenAI  # type: ignore
        except Exception as e:
            raise RuntimeError("OpenAI package not installed. `pip install openai`") from e
        key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        if not (key and endpoint):
            raise RuntimeError("Missing AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT")
        self._client = AzureOpenAI(api_key=key, api_version=api_version, azure_endpoint=endpoint)
        self._deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "")

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        resp = self._client.chat.completions.create(
            model=self._deployment,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content


    # --- Streaming interface (optional) ---
    def generate_stream(self, messages: List[Dict[str, str]], temperature: float = 0.2):
        """Default non-streaming fallback: yield a single final chunk."""
        yield self.generate(messages, temperature=temperature)

class _OpenAIStreamMixin:
    def _stream(self, client, model, messages, temperature=0.2):
        resp = client.chat.completions.create(model=model, messages=messages, temperature=temperature, stream=True)
        for evt in resp:
            try:
                delta = evt.choices[0].delta.content
            except Exception:
                delta = None
            if delta:
                yield delta

# Extend OpenAIChatClient with streaming if available
try:
    from openai import OpenAI as _TestImport  # type: ignore
    _HAS_OPENAI = True
except Exception:
    _HAS_OPENAI = False

if _HAS_OPENAI:
    # Monkey-patch generate_stream onto OpenAIChatClient
    def _openai_generate_stream(self, messages, temperature: float = 0.2):
        return _OpenAIStreamMixin()._stream(self._client, self._model, messages, temperature=temperature)
    OpenAIChatClient.generate_stream = _openai_generate_stream  # type: ignore
