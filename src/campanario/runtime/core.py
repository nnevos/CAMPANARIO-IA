from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from campanario.chat.models import ChatSession
from campanario.chat.service import ChatService
from campanario.model.protocol import ModelProvider
from campanario.runtime.capabilities import CapabilityRegistry
from campanario.runtime.clients import ClientSessionRegistry
from campanario.runtime.devices import DeviceRegistry
from campanario.runtime.events import RuntimeEventBus
from campanario.runtime.permissions import PermissionPolicy, TrustManager
from campanario.runtime.mobile import MobileCapabilityState
from campanario.runtime.voice import VoiceCallRegistry
from campanario.runtime.telemetry import RuntimeTelemetry
from campanario.runtime.experience import ExperienceLayer
from campanario.runtime.presence import PresenceManager
from campanario.runtime.media import VoiceMediaRuntime, unconfigured_voice_media


class RuntimeNotRunningError(RuntimeError):
    """Raised when a runtime-owned operation is requested outside the running lifecycle."""


@dataclass(frozen=True, slots=True)
class RuntimeState:
    runtime_id: UUID
    created_at: datetime
    started_at: datetime | None
    stopped_at: datetime | None
    status: str


class ChatSessionManager:
    """Client-independent session facade over the shared conversation service."""

    def __init__(self, runtime: CampanarioRuntime, conversation: ChatService) -> None:
        self._runtime = runtime
        self._conversation = conversation

    def create_session(self, title: str | None = None, primary_agent_id: str | None = None) -> ChatSession:
        self._runtime.ensure_running()
        return self._conversation.create_session(title, primary_agent_id)

    def list_sessions(self) -> list[ChatSession]:
        self._runtime.ensure_running()
        return self._conversation.list_sessions()


class CampanarioRuntime:
    """Logical Campanario runtime, independent from FastAPI, browser and native hosting.

    PF1b gives the logical boundary an explicit lifecycle. Native Windows service/tray concerns stay
    out of this class; a process host may keep the runtime alive without changing its semantics.
    """

    def __init__(
        self,
        conversation: ChatService,
        model_provider: ModelProvider,
        *,
        runtime_id: UUID | None = None,
        event_bus: RuntimeEventBus | None = None,
        devices: DeviceRegistry | None = None,
        tools: CapabilityRegistry | None = None,
        trust: TrustManager | None = None,
        permissions: PermissionPolicy | None = None,
        clients: ClientSessionRegistry | None = None,
        mobile: MobileCapabilityState | None = None,
        calls: VoiceCallRegistry | None = None,
        telemetry: RuntimeTelemetry | None = None,
        experience: ExperienceLayer | None = None,
        presence: PresenceManager | None = None,
        voice_media: VoiceMediaRuntime | None = None,
    ) -> None:
        self._conversation = conversation
        self._model_provider = model_provider
        now = datetime.now(UTC)
        self._state = RuntimeState(
            runtime_id=runtime_id or uuid4(),
            created_at=now,
            started_at=None,
            stopped_at=None,
            status="stopped",
        )
        self._sessions = ChatSessionManager(self, conversation)
        self._event_bus = event_bus or RuntimeEventBus(self._state.runtime_id)
        self._devices = devices
        self._tools = tools
        self._trust = trust
        self._permissions = permissions
        self._clients = clients or ClientSessionRegistry()
        self._mobile = mobile or MobileCapabilityState()
        self._calls = calls or VoiceCallRegistry()
        self._telemetry = telemetry or RuntimeTelemetry(self._state.runtime_id)
        self._experience = experience
        self._presence = presence or PresenceManager(self._event_bus)
        self._voice_media = voice_media or unconfigured_voice_media()

    def start(self) -> CampanarioRuntime:
        """Start the logical runtime. Repeated calls are intentionally idempotent."""
        if self._state.status == "running":
            return self
        now = datetime.now(UTC)
        self._state = RuntimeState(
            runtime_id=self._state.runtime_id,
            created_at=self._state.created_at,
            started_at=now,
            stopped_at=None,
            status="running",
        )
        return self

    def stop(self) -> None:
        """Stop accepting runtime-owned work without imposing a native process strategy."""
        if self._state.status == "stopped":
            return
        self._state = RuntimeState(
            runtime_id=self._state.runtime_id,
            created_at=self._state.created_at,
            started_at=self._state.started_at,
            stopped_at=datetime.now(UTC),
            status="stopped",
        )

    def ensure_running(self) -> None:
        if self._state.status != "running":
            raise RuntimeNotRunningError("Campanario runtime is not running")

    @property
    def state(self) -> RuntimeState:
        return self._state

    @property
    def conversation(self) -> ChatService:
        self.ensure_running()
        return self._conversation

    @property
    def sessions(self) -> ChatSessionManager:
        self.ensure_running()
        return self._sessions

    @property
    def events(self) -> RuntimeEventBus:
        self.ensure_running()
        return self._event_bus

    @property
    def model_provider(self) -> ModelProvider:
        self.ensure_running()
        return self._model_provider

    @property
    def tools(self) -> CapabilityRegistry:
        self.ensure_running()
        if self._tools is None:
            raise RuntimeError("Capability / Tool Registry is not configured")
        return self._tools

    @property
    def capabilities(self) -> CapabilityRegistry:
        return self.tools

    @property
    def devices(self) -> DeviceRegistry:
        self.ensure_running()
        if self._devices is None:
            raise RuntimeError("Device Registry is not configured")
        return self._devices
    @property
    def clients(self) -> ClientSessionRegistry:
        self.ensure_running()
        return self._clients

    @property
    def mobile(self) -> MobileCapabilityState:
        self.ensure_running()
        return self._mobile

    @property
    def calls(self) -> VoiceCallRegistry:
        self.ensure_running()
        return self._calls



    @property
    def presence(self) -> PresenceManager:
        self.ensure_running()
        return self._presence

    @property
    def voice_media(self) -> VoiceMediaRuntime:
        self.ensure_running()
        return self._voice_media

    def configure_voice_media(self, media: VoiceMediaRuntime) -> None:
        self.ensure_running()
        self._voice_media = media

    @property
    def experience(self) -> ExperienceLayer:
        self.ensure_running()
        if self._experience is None:
            raise RuntimeError("Experience / Learning Layer is not configured")
        return self._experience

    @property
    def telemetry(self) -> RuntimeTelemetry:
        self.ensure_running()
        return self._telemetry

    @property
    def trust(self) -> TrustManager:
        self.ensure_running()
        if self._trust is None:
            raise RuntimeError("Trust Manager is not configured")
        return self._trust

    @property
    def permissions(self) -> PermissionPolicy:
        self.ensure_running()
        if self._permissions is None:
            raise RuntimeError("Permission Policy is not configured")
        return self._permissions

