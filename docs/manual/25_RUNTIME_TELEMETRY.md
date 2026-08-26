# Runtime Telemetry — F3 closure

Campanario exposes recent architectural timing points at `GET /api/v1/runtime/telemetry?limit=200`.

This endpoint is diagnostic. It reports milestone names, timestamps and provenance identifiers; it does not expose prompts or transcript content. The journal is process-local and bounded, so restarting the runtime clears it.

Use correlation IDs to group timing points belonging to the same turn. `first_token` measures the provider's first generated token; `first_usable_output` measures when output is ready for the client after runtime response guards. The distinction is intentional for future Call latency work.
