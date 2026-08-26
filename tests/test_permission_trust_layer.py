from uuid import UUID

import pytest
from fastapi.testclient import TestClient

import campanario.api as api_module
from campanario.composition import build_runtime
from campanario.config import Settings
from campanario.main import app
from campanario.runtime.capabilities import CallbackCapabilityProvider, CapabilityDefinition, CapabilityProvenance, CapabilityProviderKind
from campanario.runtime.devices import DeviceAnnouncement
from campanario.runtime.permissions import AuthorizationContext, PermissionConfirmationRequired, PermissionDeniedError, PermissionMode


def _runtime(tmp_path):
    return build_runtime(Settings(), database_url=f"sqlite:///{tmp_path / 'pf6.db'}", create_schema=True)


def _register(runtime, permission="camera.capture"):
    provider = CallbackCapabilityProvider("camera-mock", lambda capability, arguments: {"ok": True})
    runtime.tools.register_provider(provider)
    runtime.tools.register(CapabilityDefinition(name="camera.inspect", description="test", provider_id=provider.provider_id, permissions=(permission,), provenance=CapabilityProvenance(provider_kind=CapabilityProviderKind.MOCK, provider_id=provider.provider_id)))


def test_pairing_hashes_credential_and_revocation_survives_registry(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.devices.connect(DeviceAnnouncement(device_id="phone", name="Phone", type="mobile", capabilities=("camera",)))
    token = runtime.trust.pair("phone")
    state = runtime.trust._repository.get_trust("phone")
    assert state["trusted"] is True
    assert state["credential_hash"] and state["credential_hash"] != token
    assert runtime.trust.authenticate("phone", token) is True
    runtime.trust.revoke("phone")
    assert runtime.trust.authenticate("phone", token) is False
    state = runtime.trust._repository.get_trust("phone")
    assert state["trusted"] is False
    assert state["revoked_at"] is not None


@pytest.mark.asyncio
async def test_untrusted_device_is_blocked_before_provider_runs(tmp_path):
    runtime = _runtime(tmp_path); _register(runtime)
    called = False
    # replace provider to observe execution
    async def handler(capability, arguments):
        nonlocal called; called = True; return {"ok": True}
    runtime.tools.register_provider(CallbackCapabilityProvider("camera-mock", handler))
    auth = AuthorizationContext(principal_kind="device", principal_id="phone", device_id="phone", session_active=True)
    with pytest.raises(PermissionDeniedError):
        await runtime.tools.execute("camera.inspect", {}, authorization=auth)
    assert called is False


@pytest.mark.asyncio
async def test_confirmation_is_one_time_and_scoped_to_principal(tmp_path):
    runtime = _runtime(tmp_path); _register(runtime)
    runtime.devices.connect(DeviceAnnouncement(device_id="phone", name="Phone", type="mobile"))
    runtime.trust.pair("phone")
    auth = AuthorizationContext(principal_kind="device", principal_id="phone", device_id="phone", session_active=True)
    with pytest.raises(PermissionConfirmationRequired) as exc:
        await runtime.tools.execute("camera.inspect", {}, authorization=auth)
    token = runtime.permissions.approve(exc.value.confirmation_id, principal_id="phone")
    approved = auth.model_copy(update={"confirmation_token": token})
    result = await runtime.tools.execute("camera.inspect", {}, authorization=approved)
    assert result.output == {"ok": True}
    with pytest.raises(PermissionConfirmationRequired):
        await runtime.tools.execute("camera.inspect", {}, authorization=approved)


@pytest.mark.asyncio
async def test_allow_while_session_requires_active_session(tmp_path):
    runtime = _runtime(tmp_path); _register(runtime, "location.read")
    runtime.devices.connect(DeviceAnnouncement(device_id="phone", name="Phone", type="mobile")); runtime.trust.pair("phone")
    inactive = AuthorizationContext(principal_kind="device", principal_id="phone", device_id="phone", session_active=False)
    with pytest.raises(PermissionDeniedError):
        await runtime.tools.execute("camera.inspect", {}, authorization=inactive)
    active = inactive.model_copy(update={"session_active": True})
    assert (await runtime.tools.execute("camera.inspect", {}, authorization=active)).output["ok"] is True


def test_pair_revoke_and_audit_api_never_expose_hash(monkeypatch, tmp_path):
    runtime = _runtime(tmp_path)
    runtime.devices.connect(DeviceAnnouncement(device_id="phone", name="Phone", type="mobile"))
    monkeypatch.setattr(api_module, "get_runtime", lambda: runtime)
    client = TestClient(app)
    paired = client.post("/api/v1/devices/phone/pair")
    assert paired.status_code == 200 and paired.json()["credential"]
    device = client.get("/api/v1/devices/phone").json()
    assert device["trusted"] is True and "credential_hash" not in device
    assert client.post("/api/v1/devices/phone/revoke").json()["revoked"] is True
    audit = client.get("/api/v1/security/audit").json()
    assert any(item["action"] == "device.revoked" for item in audit)
    assert "credential_hash" not in str(audit)
