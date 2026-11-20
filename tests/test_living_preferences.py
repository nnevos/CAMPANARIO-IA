from campanario.agents.living_preferences import LivingPreferenceService, render_living_preferences, extract_self_preferences
from campanario.runtime.experience import MemoryStatus
from campanario.storage.database import Base, build_engine, build_session_factory
from campanario.storage.repositories import SqlAlchemyExperienceRepository


def test_extract_conservative():
    assert extract_self_preferences('Eu gosto de literatura de mistério.')
    assert not extract_self_preferences('> Eu gosto de literatura de mistério.')
    assert not extract_self_preferences('Morgana: Eu gosto de literatura.')
    assert not extract_self_preferences('Se eu gosto de mistério, então...')


def test_persist_isolation_revision_and_restart(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'preferences.db'}")
    Base.metadata.create_all(engine)
    repository = SqlAlchemyExperienceRepository(build_session_factory(engine))
    service = LivingPreferenceService(repository)
    first = service.observe('morgana', 'Eu gosto de literatura de mistério.')[0]
    assert 'literatura' in render_living_preferences(repository.list(), 'morgana')
    assert not render_living_preferences(repository.list(), 'todd')
    again = service.observe('morgana', 'Eu gosto de literatura de mistério.')[0]
    assert first.id == again.id
    changed = service.observe('morgana', 'Não gosto de literatura de mistério.')[0]
    assert changed.supersedes_id == first.id
    assert repository.get(first.id).status == MemoryStatus.SUPERSEDED
    assert 'dislikes' in render_living_preferences(repository.list(), 'morgana')
    assert '"likes:' not in render_living_preferences(repository.list(), 'morgana')
    engine.dispose()
    reopened = build_engine(f"sqlite:///{tmp_path / 'preferences.db'}")
    new_repo = SqlAlchemyExperienceRepository(build_session_factory(reopened))
    assert 'dislikes' in render_living_preferences(new_repo.list(), 'morgana')
    reopened.dispose()
