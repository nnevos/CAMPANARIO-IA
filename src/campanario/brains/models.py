"""Separate V9 state. No cascading deletion of chat, identities or memories."""
from __future__ import annotations
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from campanario.storage.database import Base


class AgentBuildRow(Base):
    __tablename__ = 'agent_builds'
    agent_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ArchetypeDefinitionRow(Base):
    __tablename__ = 'archetype_definitions'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version: Mapped[str] = mapped_column(String(24), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class TalentDefinitionRow(Base):
    __tablename__ = 'talent_definitions'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version: Mapped[str] = mapped_column(String(24), nullable=False)
    definition: Mapped[dict] = mapped_column(JSON, nullable=False)


class AgentTalentRow(Base):
    __tablename__ = 'agent_talents'
    agent_id: Mapped[str] = mapped_column(String(64), ForeignKey('agent_builds.agent_id', ondelete='CASCADE'), primary_key=True)
    talent_id: Mapped[str] = mapped_column(String(64), ForeignKey('talent_definitions.id'), primary_key=True)


class BrainRegistryRow(Base):
    __tablename__ = 'brain_registry'
    brain_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)


class BrainRunRow(Base):
    __tablename__ = 'brain_runs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    trace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    brain_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    operations: Mapped[list] = mapped_column(JSON, nullable=False)
    error: Mapped[str | None] = mapped_column(String(90), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
