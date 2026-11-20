"""Persistence for V9 builds and observed brain runs, separate from chat/memory."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import delete, select

from campanario.brains.builds import AgentBuild
from campanario.brains.models import AgentBuildRow, AgentTalentRow, BrainRunRow, TalentDefinitionRow
from campanario.brains.builds import TALENTS


class BuildConflict(ValueError):
    pass


class BuildStore:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def get(self, agent_id: str) -> AgentBuild:
        with self._session_factory() as db:
            row = db.get(AgentBuildRow, agent_id)
            return AgentBuild.model_validate(row.config) if row else AgentBuild(agent_id=agent_id)

    def list_builds(self) -> list[AgentBuild]:
        with self._session_factory() as db:
            return [AgentBuild.model_validate(row.config)
                    for row in db.scalars(select(AgentBuildRow)).all()]

    def save(self, build: AgentBuild, *, expected_revision: int | None = None) -> AgentBuild:
        with self._session_factory.begin() as db:
            row = db.get(AgentBuildRow, build.agent_id)
            revision = row.revision if row is not None else 1
            if expected_revision is not None and revision != expected_revision:
                raise BuildConflict('A ficha foi alterada em outra sessão; recarregue a Forja.')
            updated = build.model_copy(update={'revision': revision + 1})
            if row is None:
                db.add(AgentBuildRow(agent_id=updated.agent_id, revision=updated.revision,
                                     config=updated.model_dump(mode='json'), updated_at=datetime.now(UTC)))
            else:
                row.revision = updated.revision
                row.config = updated.model_dump(mode='json')
                row.updated_at = datetime.now(UTC)
            db.execute(delete(AgentTalentRow).where(AgentTalentRow.agent_id == updated.agent_id))
            for talent_id in updated.talents:
                if db.get(TalentDefinitionRow, talent_id) is None:
                    definition = TALENTS[talent_id]
                    db.add(TalentDefinitionRow(id=definition.id, version=definition.version,
                                               definition=definition.model_dump(mode='json')))
                db.add(AgentTalentRow(agent_id=updated.agent_id, talent_id=talent_id))
            return updated

    def record_run(self, *, record, request):
        with self._session_factory.begin() as db:
            db.add(BrainRunRow(id=str(uuid4()), request_id=str(request.request_id),
                               trace_id=str(record.trace_id), brain_id=record.brain_id,
                               status=record.status.value, latency_ms=record.elapsed_ms,
                               evidence_count=len(record.evidence_refs),
                               operations=list(record.operations), error=record.error,
                               created_at=datetime.now(UTC)))

    def runs(self, limit: int = 30) -> list[dict]:
        with self._session_factory() as db:
            rows = db.scalars(select(BrainRunRow).order_by(BrainRunRow.created_at.desc()).limit(min(limit, 100))).all()
            return [{'trace_id': row.trace_id, 'brain_id': row.brain_id,
                     'request_id': row.request_id, 'status': row.status,
                     'latency_ms': row.latency_ms, 'evidence_count': row.evidence_count,
                     'operations': row.operations, 'error': row.error,
                     'created_at': row.created_at.isoformat()} for row in rows]
