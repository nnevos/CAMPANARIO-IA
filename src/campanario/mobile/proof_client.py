from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode, urlparse, urlunparse

import httpx
import websockets


@dataclass(slots=True)
class MobileReadinessClient:
    """Minimal remote client used to prove PF8 contracts over real HTTP/WebSocket transports.

    It deliberately has no UI toolkit, background service, GPS SDK or platform-specific code. A
    future Android/iOS shell can implement these same protocol calls without creating another
    Campanario runtime or conversation pipeline.
    """

    base_url: str
    client_id: str
    device_id: str
    device_name: str = "Campanario Mobile Proof"
    credential: str | None = None

    @property
    def websocket_base_url(self) -> str:
        parsed = urlparse(self.base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return urlunparse((scheme, parsed.netloc, "", "", "", ""))

    def _auth_headers(self) -> dict[str, str]:
        headers = {"X-Campanario-Client-Id": self.client_id}
        if self.credential:
            headers.update(
                {
                    "X-Campanario-Device-Id": self.device_id,
                    "X-Campanario-Device-Credential": self.credential,
                }
            )
        return headers

    async def register_for_pairing(self) -> dict[str, Any]:
        """Register device identity/capabilities before the one-time PF6 pairing step."""

        uri = f"{self.websocket_base_url}/ws/v1/devices"
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(self._device_hello()))
            return json.loads(await websocket.recv())

    async def pair(self) -> str:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.post(f"/api/v1/devices/{self.device_id}/pair")
            response.raise_for_status()
            self.credential = response.json()["credential"]
            return self.credential

    async def bootstrap_pair(self) -> str:
        ready = await self.register_for_pairing()
        if ready.get("frame_type") != "device_ready":
            raise RuntimeError("device registration did not complete")
        return await self.pair()

    async def open_device(self):
        """Open the authenticated device channel and return (connection, ready_frame)."""
        if not self.credential:
            raise RuntimeError("device must be paired before opening authenticated device channel")
        uri = f"{self.websocket_base_url}/ws/v1/devices"
        websocket = await websockets.connect(
            uri,
            additional_headers={"X-Campanario-Device-Credential": self.credential},
        )
        await websocket.send(json.dumps(self._device_hello()))
        ready = json.loads(await websocket.recv())
        if not ready.get("authenticated"):
            await websocket.close()
            raise RuntimeError("device channel was not authenticated")
        return websocket, ready

    async def send_location(
        self,
        websocket,
        *,
        latitude: float,
        longitude: float,
        accuracy_meters: float | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        frame: dict[str, Any] = {
            "schema_version": "1.0",
            "frame_type": "location_update",
            "latitude": latitude,
            "longitude": longitude,
        }
        if accuracy_meters is not None:
            frame["accuracy_meters"] = accuracy_meters
        if session_id is not None:
            frame["session_id"] = session_id
        await websocket.send(json.dumps(frame))
        return json.loads(await websocket.recv())

    async def publish_location(
        self,
        *,
        latitude: float,
        longitude: float,
        accuracy_meters: float | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        websocket, _ = await self.open_device()
        try:
            return await self.send_location(
                websocket,
                latitude=latitude,
                longitude=longitude,
                accuracy_meters=accuracy_meters,
                session_id=session_id,
            )
        finally:
            await websocket.close()

    async def create_session(self, title: str | None = None) -> dict[str, Any]:
        body = {} if title is None else {"title": title}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.post("/api/v1/sessions", json=body)
            response.raise_for_status()
            return response.json()

    async def messages(self, session_id: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get(f"/api/v1/sessions/{session_id}/messages")
            response.raise_for_status()
            return response.json()

    async def send_text(self, session_id: str, text: str) -> dict[str, Any]:
        if not self.credential:
            raise RuntimeError("device must be paired before sending authenticated mobile text")
        async with httpx.AsyncClient(base_url=self.base_url, timeout=180.0) as client:
            response = await client.post(
                f"/api/v1/sessions/{session_id}/turn",
                headers=self._auth_headers(),
                json={"message": text},
            )
            response.raise_for_status()
            return response.json()

    async def open_events(self, session_id: str, *, after_sequence: int = 0):
        if not self.credential:
            raise RuntimeError("device must be paired before observing authenticated mobile events")
        query = urlencode(
            {
                "session_id": session_id,
                "after_sequence": after_sequence,
                "client_id": self.client_id,
                "device_id": self.device_id,
            }
        )
        headers = {"X-Campanario-Device-Credential": self.credential}
        return await websockets.connect(
            f"{self.websocket_base_url}/ws/v1/events?{query}",
            additional_headers=headers,
        )

    def _device_hello(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "frame_type": "device_hello",
            "device_id": self.device_id,
            "name": self.device_name,
            "device_type": "mobile-proof",
            "capabilities": ["gps", "network", "screen"],
        }


async def _run_cli_async() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Campanario PF8 minimal mobile readiness client")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--client-id", default="mobile-proof-cli")
    parser.add_argument("--device-id", default="mobile-proof-cli-device")
    parser.add_argument("--credential", default=None)
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--message", default="teste do cliente mobile PF8")
    parser.add_argument("--latitude", type=float, default=-23.55052)
    parser.add_argument("--longitude", type=float, default=-46.633308)
    parser.add_argument("--accuracy", type=float, default=10.0)
    args = parser.parse_args()

    client = MobileReadinessClient(
        base_url=args.base_url,
        client_id=args.client_id,
        device_id=args.device_id,
        credential=args.credential,
    )
    if not client.credential:
        credential = await client.bootstrap_pair()
        print("PF8 pairing concluido. Guarde esta credencial para reconnect:")
        print(credential)

    session_id = args.session_id or (await client.create_session("PF8 mobile proof"))["id"]
    device_ws, ready = await client.open_device()
    try:
        print(f"device autenticado: {ready['device']['id']}")
        update = await client.send_location(
            device_ws,
            latitude=args.latitude,
            longitude=args.longitude,
            accuracy_meters=args.accuracy,
            session_id=session_id,
        )
        print(f"capability publicada: {update['capability']}")
        turn = await client.send_text(session_id, args.message)
        print(f"turno concluido: speakers={turn['speakers']} session_id={session_id}")
        history = await client.messages(session_id)
        for item in history[-4:]:
            speaker = item.get("agent_id") or item.get("client_id") or item["role"]
            print(f"{speaker}: {item['content']}")
    finally:
        await device_ws.close()


def main() -> None:
    import asyncio

    asyncio.run(_run_cli_async())
