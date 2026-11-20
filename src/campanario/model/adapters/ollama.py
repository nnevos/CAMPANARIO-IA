import json
import logging
import time
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


logger = logging.getLogger(__name__)


class OllamaProvider(ModelProvider):
    """Ollama adapter using only Campanario-owned types at its boundary."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 120.0,
        temperature: float = 0.35,
        think: bool | None = None,
        context_window: int | None = None,
        max_output_tokens: int | None = None,
        keep_alive: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)
        self._temperature = temperature
        self._think = think
        self._context_window = context_window
        self._max_output_tokens = max_output_tokens
        self._keep_alive = keep_alive

    def _build_payload(self, request: ModelRequest, *, stream: bool) -> dict[str, object]:
        options: dict[str, object] = {
            "temperature": self._temperature if request.temperature is None else request.temperature
        }
        max_tokens = request.max_output_tokens if request.max_output_tokens is not None else self._max_output_tokens
        window = request.context_window if request.context_window is not None else self._context_window
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if window is not None:
            options["num_ctx"] = window
        payload: dict[str, object] = {
            "model": request.model,
            "messages": [
                {"role": message.role.value, "content": message.content}
                for message in request.messages
            ],
            "stream": stream,
            "options": options,
        }
        if request.response_format:
            payload["format"] = request.response_format
        # think is a TOP-LEVEL Ollama chat API key, not an 'options' entry.
        if self._think is not None:
            payload["think"] = self._think
        if self._keep_alive is not None:
            payload["keep_alive"] = self._keep_alive
        return payload

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                return response.is_success
        except httpx.HTTPError:
            return False

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelChunk]:
        payload = self._build_payload(request, stream=True)
        start = time.perf_counter()
        first_content = None
        completed = False
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

                        if not isinstance(data, dict):
                            raise ModelResponseError("Ollama returned a non-object streaming event")
                        if data.get("error"):
                            raise ModelResponseError("Ollama reported a generation error")
                        message = data.get("message", {})
                        if message is None:  # The terminal Ollama event may omit the message.
                            message = {}
                        if not isinstance(message, dict):
                            raise ModelResponseError("Ollama returned an invalid message object")
                        text = message.get("content", "")
                        if text is None:
                            text = ""
                        if not isinstance(text, str):
                            raise ModelResponseError("Ollama returned non-text message content")
                        done = data.get("done", False)
                        if not isinstance(done, bool):
                            raise ModelResponseError("Ollama returned an invalid completion marker")
                        if text and first_content is None:
                            first_content = time.perf_counter()
                        if done:
                            logger.info(
                                "ollama_generation model=%s first_visible_ms=%s total_ms=%d "
                                "prompt_tokens=%s completion_tokens=%s",
                                request.model,
                                int((first_content - start) * 1000) if first_content else "none",
                                int((time.perf_counter() - start) * 1000),
                                data.get("prompt_eval_count", "unknown"),
                                data.get("eval_count", "unknown"),
                            )
                        if done:
                            prompt_tokens = data.get("prompt_eval_count")
                            requested_window = payload["options"].get("num_ctx")
                            # Near capacity is a diagnostic signal, not proof of truncation.
                            # Keep the user's prompt out of operational logs.
                            if (type(prompt_tokens) is int and type(requested_window) is int
                                    and requested_window > 0
                                    and prompt_tokens >= requested_window * 0.95):
                                logger.warning(
                                    "ollama_context_near_limit model=%s prompt_tokens=%d num_ctx=%d",
                                    request.model, prompt_tokens, requested_window,
                                )
                        if text or done:
                            yield ModelChunk(text=text, done=done)
                        if done:
                            completed = True
                            break
                    if not completed:
                        raise ModelResponseError("Ollama stream ended without a completion marker")
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
