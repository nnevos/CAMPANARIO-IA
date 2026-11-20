"""Safe declarative .campagent format. Never imports executable assets/permissions."""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
from pathlib import PurePosixPath
from zipfile import ZipFile, ZIP_STORED, BadZipFile

from pydantic import BaseModel, ConfigDict, Field

from campanario.brains.builds import AgentBuild

_MAX_PACKAGE = 4_000_000
_ALLOWED_ASSET_EXTENSIONS = {'.png', '.webp', '.jpg', '.jpeg'}


class AgentPackageManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    format: str = Field(pattern=r'^campagent/1$')
    build: AgentBuild
    assets: dict[str, str] = Field(default_factory=dict)


def export_package(build: AgentBuild) -> bytes:
    # Export declarative public configuration ONLY. Never profile personality,
    # memory, credentials, documents, real permission scopes or file paths.
    manifest = AgentPackageManifest(format='campagent/1', build=build)
    data = json.dumps(manifest.model_dump(mode='json'), ensure_ascii=False,
                      sort_keys=True).encode('utf-8')
    with BytesIO() as buf:
        with ZipFile(buf, 'w', compression=ZIP_STORED) as out:
            out.writestr('manifest.json', data)
        return buf.getvalue()


def import_package(raw: bytes) -> AgentBuild:
    if len(raw) > _MAX_PACKAGE:
        raise ValueError('Pacote excede 4 MB')
    try:
        with ZipFile(BytesIO(raw)) as archive:
            infos = archive.infolist()
            names = [i.filename for i in infos]
            if len(infos) > 18 or len(names) != len(set(names)) or 'manifest.json' not in names:
                raise ValueError('Manifesto ausente, duplicação ou excesso de arquivos')
            if sum(i.file_size for i in infos) > _MAX_PACKAGE:
                raise ValueError('Pacote descompactado excede 4 MB')
            for info in infos:
                name = info.filename
                path = PurePosixPath(name)
                if (not name or '\\' in name or name.startswith('/') or '..' in path.parts
                        or '\x00' in name or info.is_dir() or info.flag_bits & 1
                        or ((info.external_attr >> 16) & 0o170000) == 0o120000):
                    raise ValueError('Caminho perigoso ou link em pacote')
                if name != 'manifest.json' and (len(path.parts) != 2 or
                        path.parts[0] != 'assets' or path.suffix.lower() not in _ALLOWED_ASSET_EXTENSIONS):
                    raise ValueError('Arquivo não permitido em pacote')
            manifest = AgentPackageManifest.model_validate_json(archive.read('manifest.json'))
            assets = set(names) - {'manifest.json'}
            if assets != set(manifest.assets):
                raise ValueError('Arquivos e hashes do manifesto divergem')
            for name in assets:
                if sha256(archive.read(name)).hexdigest() != manifest.assets[name]:
                    raise ValueError('Checksum inválido')
            return manifest.build
    except (OSError, BadZipFile, KeyError, json.JSONDecodeError) as exc:
        raise ValueError('Pacote .campagent inválido') from exc
