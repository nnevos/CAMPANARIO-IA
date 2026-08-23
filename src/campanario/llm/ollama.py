from collections.abc import AsyncIterator

from campanario.llm.provider import ModelChunk, ModelProvider, ModelRequest


class OllamaProvider(ModelProvider):
    """Adapter Ollama.

    A implementação HTTP real entra no próximo incremento.
    Manter todos os detalhes específicos do Ollama dentro deste módulo.
    """

    async def health(self) -> bool:
        raise NotImplementedError("Ollama integration is scheduled for Phase 1.")

    def stream(self, request: ModelRequest) -> AsyncIterator[ModelChunk]:
        raise NotImplementedError("Ollama streaming is scheduled for Phase 1.")
