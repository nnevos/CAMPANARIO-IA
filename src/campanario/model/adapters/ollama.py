import json
from collections.abc import AsyncIterator

import httpx

from campanario.model.protocol import (
    ModelChunk,
    ModelProvider,
    ModelRequest,
    ModelResponseError,
    ModelTimeoutError,
    ModelUnavailableError,
)


class OllamaProvider(ModelProvider):
    """Ollama adapter using only Campanario-owned types at its boundary."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 120.0,
        temperature: float = 0.35,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)
        self._temperature = temperature

    def _build_payload(self, request: ModelRequest, *, stream: bool) -> dict[str, object]:
        return {
            "model": request.model,
            "messages": [
                {"role": message.role.value, "content": message.content}
                for message in request.messages
            ],
            "stream": stream,
            "options": {"temperature": self._temperature},
        }

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                return response.is_success
        except httpx.HTTPError:
            return False

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelChunk]:
        payload = self._build_payload(request, stream=True)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self._base_url}/api/chat",
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError as exc:
                            raise ModelResponseError("Ollama returned invalid streaming JSON") from exc

                        message = data.get("message") or {}
                        text = message.get("content") or ""
                        done = bool(data.get("done", False))
                        if text or done:
                            yield ModelChunk(text=text, done=done)
        except httpx.TimeoutException as exc:
            raise ModelTimeoutError("Ollama request timed out") from exc
        except httpx.ConnectError as exc:
            raise ModelUnavailableError("Ollama is unavailable") from exc
        except httpx.HTTPStatusError as exc:
            raise ModelResponseError(
                f"Ollama returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ModelUnavailableError("Ollama request failed") from exc
