from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from campanario.agents.profiles import default_agent_registry
from campanario.chat.behavior import BehaviorContextManager
from campanario.chat.context import SummarizingContextManager
from campanario.chat.service import ChatService
from campanario.config import Settings
from campanario.model.protocol import ModelProvider
from campanario.model.runtime import build_model_provider
from campanario.response.guard import BehaviorResponseGuardProvider
from campanario.runtime.capabilities import CapabilityRegistry
from campanario.runtime.core import CampanarioRuntime
from campanario.runtime.devices import DeviceRegistry
from campanario.runtime.events import RuntimeEventBus
from campanario.runtime.experience import ExperienceLayer
from campanario.runtime.permissions import PermissionMode, PermissionPolicy, TrustManager
from campanario.runtime.telemetry import RuntimeTelemetry
from campanario.runtime.presence import PresenceManager
from campanario.runtime.host_voice import build_host_voice_media
from campanario.response.prompt_safety import PromptLeakGuardProvider
from campanario.storage.database import Base, build_engine, build_session_factory
from campanario.storage.repositories import (
    SqlAlchemyChatSessionRepository, SqlAlchemyContextSummaryRepository, SqlAlchemyDeviceRepository, SqlAlchemyMessageRepository, SqlAlchemyTrustRepository, SqlAlchemyExperienceRepository,
)

def build_chat_stack(
    settings: Settings,
    *,
    database_url: str | None = None,
    create_schema: bool = False,
    event_bus: RuntimeEventBus | None = None,
    session_factory=None,
    telemetry: RuntimeTelemetry | None = None,
    experience: ExperienceLayer | None = None,
) -> tuple[ChatService, ModelProvider]:
    """Canonical composition root for API and E2E.

    Returns the chat service plus the raw provider for health/profiling. Model family names never
    enter behavior modules; they remain in Settings/ModelRuntimeConfig.
    """
    if session_factory is None:
        engine = build_engine(database_url) if database_url else build_engine()
        if create_schema:
            Base.metadata.create_all(engine)
        session_factory = build_session_factory(engine)
    runtime = settings.model_runtime
    raw_provider = build_model_provider(runtime)
    safe_provider = PromptLeakGuardProvider(raw_provider)
    response_provider = BehaviorResponseGuardProvider(safe_provider)
    service = ChatService(
        sessions=SqlAlchemyChatSessionRepository(session_factory),
        messages=SqlAlchemyMessageRepository(session_factory),
        model_provider=response_provider,
        context_manager=BehaviorContextManager(
            SummarizingContextManager(
                max_messages=settings.context_max_messages,
                summaries=SqlAlchemyContextSummaryRepository(session_factory),
                model_provider=safe_provider,
                model=runtime.model,
                max_summary_chars=settings.context_summary_max_chars,
            )
        ),
        default_model=runtime.model,
        agent_registry=default_agent_registry(),
        participation_provider=safe_provider,
        event_bus=event_bus,
        telemetry=telemetry,
        experience=experience,
    )
    return service, raw_provider


def build_runtime(
    settings: Settings,
    *,
    database_url: str | None = None,
    create_schema: bool = False,
    autostart: bool = True,
) -> CampanarioRuntime:
    """Canonical Campanario runtime composition root, independent from API/UI hosting."""
    runtime_id = uuid4()
    event_bus = RuntimeEventBus(runtime_id)
    telemetry = RuntimeTelemetry(runtime_id)
    telemetry.bind_event_bus(event_bus)
    engine = build_engine(database_url) if database_url else build_engine()
    if create_schema:
        Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    experience = ExperienceLayer(SqlAlchemyExperienceRepository(session_factory), event_bus)
    service, raw_provider = build_chat_stack(
        settings,
        event_bus=event_bus,
        session_factory=session_factory,
        telemetry=telemetry,
        experience=experience,
    )
    devices = DeviceRegistry(SqlAlchemyDeviceRepository(session_factory), event_bus)
    trust_repository = SqlAlchemyTrustRepository(session_factory)
    trust = TrustManager(trust_repository, devices)
    permissions = PermissionPolicy(trust, trust_repository)
    permissions.set_rule("location.read", PermissionMode.ALLOW_WHILE_SESSION)
    permissions.set_rule("camera.capture", PermissionMode.ASK)
    permissions.set_rule("message.send", PermissionMode.CONFIRM)
    permissions.set_rule("file.delete", PermissionMode.CONFIRM)
    permissions.set_rule("computer.execute", PermissionMode.SCOPED_CONFIRM)
    permissions.set_rule("microphone.listen", PermissionMode.ALLOW_WHILE_CALL)
    tools = CapabilityRegistry(event_bus, permissions)
    presence = PresenceManager(event_bus)
    host_voice_media = build_host_voice_media(settings)
    runtime = CampanarioRuntime(
        service, raw_provider, runtime_id=runtime_id, event_bus=event_bus, devices=devices, tools=tools, trust=trust, permissions=permissions, telemetry=telemetry, experience=experience, presence=presence, voice_media=host_voice_media
    )
    if autostart:
        runtime.start()
    return runtime
