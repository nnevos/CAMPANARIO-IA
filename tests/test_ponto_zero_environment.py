from pathlib import Path

import pytest
from pydantic import ValidationError

from campanario.config import Settings


def test_memory_environments_are_separate(tmp_path: Path):
    dev = Settings(_env_file=None, data_dir=tmp_path, memory_environment='desenvolvimento')
    prod = Settings(_env_file=None, data_dir=tmp_path, memory_environment='producao')
    assert dev.database_path == tmp_path / 'desenvolvimento' / 'campanario.db'
    assert prod.database_path == tmp_path / 'producao' / 'campanario.db'
    assert dev.database_path != prod.database_path


def test_invalid_memory_environment_rejected(tmp_path: Path):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, data_dir=tmp_path, memory_environment='producao/../desenvolvimento')
