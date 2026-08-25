from collections.abc import AsyncIterator

from campanario.model.protocol import ModelChunk, ModelProvider, ModelRequest
from campanario.response.pipeline import ResponseContractPipeline


class BehaviorResponseGuardProvider(ModelProvider):
    """Compatibility adapter around the v1.6 Response Contract Pipeline.

    Kept under the historical class name so bootstrap/API callers do not need to change while
    generation, validation, repair and finalization are now explicit pipeline stages.
    """

    def __init__(self, inner: ModelProvider) -> None:
        self._pipeline = ResponseContractPipeline(inner)

    async def health(self) -> bool:
        return await self._pipeline.health()

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelChunk]:
        result = await self._pipeline.execute(request)
        if result.text:
            yield ModelChunk(text=result.text)
        yield ModelChunk(text="", done=True)
