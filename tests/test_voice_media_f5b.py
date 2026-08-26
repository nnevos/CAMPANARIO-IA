from __future__ import annotations

import asyncio
from fastapi.testclient import TestClient

import campanario.api as api_module
import campanario.gateway.call as call_gateway_module
import campanario.gateway.devices as device_gateway_module
from campanario.composition import build_runtime
from campanario.config import Settings
from campanario.main import app
from campanario.model.protocol import FakeModelProvider
from campanario.runtime.devices import DeviceAnnouncement
from campanario.runtime.media import EnergyVad, VoiceMediaRuntime
from campanario.runtime.voice import SttSegment, TtsChunk


class ProofStt:
    def __init__(self): self.finals = 0
    async def push(self, audio: bytes, *, final: bool = False):
        if final:
            self.finals += 1
            return SttSegment(text="Campanario, teste de audio", final=True, confidence=.99)
        return None
    async def reset(self): return None


class ProofTts:
    def __init__(self): self.cancelled = 0
    async def synthesize(self, text: str, *, agent_id: str):
        yield TtsChunk(agent_id=agent_id, audio=(agent_id+":"+text).encode(), final=True)
    async def cancel(self): self.cancelled += 1


def install(monkeypatch, tmp_path):
    rt=build_runtime(Settings(), database_url=f"sqlite:///{tmp_path/'media.db'}", create_schema=True)
    fake=FakeModelProvider("resposta audivel")
    rt.conversation._model_provider=fake; rt.conversation._participation._provider=fake
    rt.conversation._default_model="fake"; rt.conversation._participation._model="fake"
    rt.configure_voice_media(VoiceMediaRuntime(stt=ProofStt(),tts=ProofTts(),vad=EnergyVad(threshold=100),silence_frames_to_finalize=2,min_speech_ms=20))
    for mod in (api_module,device_gateway_module,call_gateway_module): monkeypatch.setattr(mod,"get_runtime",lambda:rt)
    return rt


def test_binary_pcm_to_stt_conversation_tts_audio_e2e(monkeypatch,tmp_path):
    rt=install(monkeypatch,tmp_path); client=TestClient(app)
    sid=client.post('/api/v1/sessions',json={}).json()['id']
    rt.devices.connect(DeviceAnnouncement(device_id='pc',name='pc',type='desktop',capabilities=('microphone','speaker')))
    cred=rt.trust.pair('pc')
    url=f'/ws/v1/call?session_id={sid}&client_id=desktop&device_id=pc'
    with client.websocket_connect(url,headers={'X-Campanario-Device-Credential':cred}) as ws:
        assert ws.receive_json()['frame_type']=='call_ready'
        ws.send_bytes(b'\xff\x7f'*320)
        ws.send_bytes(b'\x00\x00'*320); ws.send_bytes(b'\x00\x00'*320)
        saw_final=saw_text=saw_audio=False
        for _ in range(40):
            msg=ws.receive()
            if msg.get('bytes') is not None:
                assert b'morgana:resposta audivel' in msg['bytes']; saw_audio=True
            elif msg.get('text'):
                import json; frame=json.loads(msg['text'])
                saw_final |= frame.get('frame_type')=='stt_final'
                saw_text |= frame.get('frame_type')=='tts_text'
            if saw_final and saw_text and saw_audio: break
        assert saw_final and saw_text and saw_audio
        history=rt.conversation.get_messages(__import__('uuid').UUID(sid))
        assert history[0].content=='teste de audio'
        assert history[1].content=='resposta audivel'


def test_barge_in_cancels_tts_adapter(monkeypatch,tmp_path):
    rt=install(monkeypatch,tmp_path); client=TestClient(app)
    sid=client.post('/api/v1/sessions',json={}).json()['id']
    rt.devices.connect(DeviceAnnouncement(device_id='pc',name='pc',type='desktop',capabilities=('microphone','speaker')))
    cred=rt.trust.pair('pc')
    with client.websocket_connect(f'/ws/v1/call?session_id={sid}&client_id=desktop&device_id=pc',headers={'X-Campanario-Device-Credential':cred}) as ws:
        ws.receive_json(); ws.send_json({'schema_version':'1.0','frame_type':'interrupt','agent_id':'morgana'})
        for _ in range(10):
            if ws.receive_json().get('frame_type')=='interrupt_ack': break
        assert rt.voice_media.tts.cancelled >= 1


def test_unconfigured_runtime_audio_returns_contract_error_instead_of_crashing(monkeypatch, tmp_path):
    rt = build_runtime(Settings(_env_file=None), database_url=f"sqlite:///{tmp_path/'no-stt.db'}", create_schema=True)
    for mod in (api_module, device_gateway_module, call_gateway_module):
        monkeypatch.setattr(mod, "get_runtime", lambda: rt)
    client = TestClient(app)
    sid = client.post('/api/v1/sessions', json={}).json()['id']
    rt.devices.connect(DeviceAnnouncement(device_id='pc', name='pc', type='desktop', capabilities=('microphone','speaker')))
    cred = rt.trust.pair('pc')
    with client.websocket_connect(
        f'/ws/v1/call?session_id={sid}&client_id=desktop&device_id=pc',
        headers={'X-Campanario-Device-Credential': cred},
    ) as ws:
        assert ws.receive_json()['frame_type'] == 'call_ready'
        ws.send_bytes(b'\xff\x7f' * 320)
        frame = ws.receive_json()
        assert frame['frame_type'] == 'error'
        assert frame['error'] == 'voice_stt_not_configured'


def test_utterance_buffer_preserves_preroll_soft_frames_and_hangover() -> None:
    from campanario.runtime.media import UtteranceBuffer

    buffer = UtteranceBuffer(preroll_frames=2, silence_frames_to_finalize=2)
    quiet1 = b"a" * 4
    quiet2 = b"b" * 4
    loud1 = b"c" * 4
    soft_middle = b"d" * 4
    loud2 = b"e" * 4
    tail1 = b"f" * 4
    tail2 = b"g" * 4

    assert buffer.push(quiet1, speaking=False) is None
    assert buffer.push(quiet2, speaking=False) is None
    assert buffer.push(loud1, speaking=True) is None
    # A low-energy syllable/pause after speech start must not be deleted.
    assert buffer.push(soft_middle, speaking=False) is None
    assert buffer.push(loud2, speaking=True) is None
    assert buffer.push(tail1, speaking=False) is None
    utterance = buffer.push(tail2, speaking=False)
    assert utterance == quiet1 + quiet2 + loud1 + soft_middle + loud2 + tail1 + tail2
