from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, cast
import os


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(
        self, messages: List[Dict[str, str]], temperature: float = 0.2
    ) -> str: ...

    # Provide a safe default streaming implementation so callers can always stream
    # even if the underlying client doesn't support it natively.
    def generate_stream(self, messages: List[Dict[str, str]], temperature: float = 0.2):
        yield self.generate(messages, temperature=temperature)


class EchoLLMClient(BaseLLMClient):
    """A fallback that echoes the last user message; useful for offline testing."""

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        return f"(echo) {last_user}"

    def generate_stream(self, messages: List[Dict[str, str]], temperature: float = 0.2):
        import time

        txt = self.generate(messages, temperature=temperature)
        # Simulate token stream by words with optional delay for visibility
        delay_ms = int(os.getenv("PT_ECHO_STREAM_DELAY_MS", "0") or "0")
        for w in txt.split():
            yield w + " "
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)


# Optional OpenAI adapter. Requires `pip install openai` and env var OPENAI_API_KEY.
# Model name can come from OPENAI_MODEL (default: gpt-4o-mini or gpt-4o).
class OpenAIChatClient(BaseLLMClient):
    def __init__(self, model: Optional[str] = None):
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "OpenAI package not installed. `pip install openai`"
            ) from e
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY")
        self._client = OpenAI(api_key=api_key)
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=cast(Any, messages),
                temperature=temperature,
            )
            content = getattr(resp.choices[0].message, "content", None)
            if isinstance(content, str):
                return content
            # Fallback in case SDK returns content in unexpected shape
            return "" if content is None else str(content)
        except Exception as e:
            # Normalize errors; callers may decide to surface or fallback
            raise RuntimeError(f"OpenAI generate failed: {e}") from e


# Optional Azure OpenAI adapter (API-compatible if configured properly).
class AzureOpenAIChatClient(BaseLLMClient):
    def __init__(self, deployment: Optional[str] = None):
        try:
            from openai import AzureOpenAI  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "OpenAI package not installed. `pip install openai`"
            ) from e
        key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        if not (key and endpoint):
            raise RuntimeError("Missing AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT")
        self._client = AzureOpenAI(
            api_key=key, api_version=api_version, azure_endpoint=endpoint
        )
        self._deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "")

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=self._deployment,
                messages=cast(Any, messages),
                temperature=temperature,
            )
            content = getattr(resp.choices[0].message, "content", None)
            if isinstance(content, str):
                return content
            return "" if content is None else str(content)
        except Exception as e:
            raise RuntimeError(f"Azure OpenAI generate failed: {e}") from e

    # --- Streaming interface (optional) ---
    def generate_stream(self, messages: List[Dict[str, str]], temperature: float = 0.2):
        """Default non-streaming fallback: yield a single final chunk."""
        yield self.generate(messages, temperature=temperature)


class _OpenAIStreamMixin:
    def _stream(self, client, model, messages, temperature=0.2):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=cast(Any, messages),
                temperature=temperature,
                stream=True,
            )
            for evt in resp:
                try:
                    delta = evt.choices[0].delta.content
                except Exception:
                    delta = None
                if delta:
                    # Ensure string output
                    yield delta if isinstance(delta, str) else str(delta)
        except Exception as e:
            # Surface a single error chunk; upstream can decide how to present
            yield f"[stream error: {e}]"


# Extend OpenAIChatClient with streaming if available
try:
    from openai import OpenAI as _TestImport  # type: ignore

    _HAS_OPENAI = True
except Exception:
    _HAS_OPENAI = False

if _HAS_OPENAI:
    # Monkey-patch generate_stream onto OpenAIChatClient
    def _openai_generate_stream(self, messages, temperature: float = 0.2):
        return _OpenAIStreamMixin()._stream(
            self._client, self._model, messages, temperature=temperature
        )

    OpenAIChatClient.generate_stream = _openai_generate_stream  # type: ignore


# Custom Local LLM Client Template
class LocalLLMClient(BaseLLMClient):
    """
    Template for connecting to your own local LLM server
    Modify this to match your server's API
    """

    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or os.getenv("LOCAL_LLM_URL", "http://localhost:8000")
        self.model = model or os.getenv("LOCAL_LLM_MODEL", "your-model")

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        try:
            import requests

            # Example API call - modify for your server
            payload = {
                "messages": messages,
                "temperature": temperature,
                "model": self.model,
                "max_tokens": 1000,
            }

            # Adjust endpoint path for your server
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                # Adjust response parsing for your API format
                return (
                    result.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
            else:
                raise RuntimeError(
                    f"Local LLM API error: {response.status_code} - {response.text}"
                )

        except Exception as e:
            raise RuntimeError(f"Local LLM generate failed: {e}") from e


# Ollama-specific client (if you're using Ollama)
class OllamaClient(BaseLLMClient):
    """Ollama local LLM client"""

    def __init__(self, model: str = None):
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3:8b")

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        try:
            import requests

            # Convert messages to Ollama format
            prompt = self._messages_to_prompt(messages)

            payload = {
                "model": self.model,
                "prompt": prompt,
                "options": {"temperature": temperature, "num_predict": 1000},
                "stream": False,
            }

            response = requests.post(
                f"{self.base_url}/api/generate", json=payload, timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise RuntimeError(f"Ollama API error: {response.status_code}")

        except Exception as e:
            raise RuntimeError(f"Ollama generate failed: {e}") from e

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to a single prompt"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
