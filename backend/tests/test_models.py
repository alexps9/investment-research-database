"""Unit tests for model validation (no DB required)."""
import pytest
from app.models import VALID_RELATION_TYPES
from app.schemas import (
    SourceCreate, SignalCreate, EntityCreate,
    EntityRelationCreate, PipelineRunCreate,
)


def test_valid_relation_types_not_empty():
    assert len(VALID_RELATION_TYPES) > 0
    assert "WORKS_AT" in VALID_RELATION_TYPES
    assert "RELEASED" in VALID_RELATION_TYPES


def test_source_schema_defaults():
    s = SourceCreate(name="Test")
    assert s.source_type == "person"
    assert s.activity_status == "unknown"
    assert s.importance_score == 0.5
    assert s.is_active is True


def test_signal_schema_defaults():
    sig = SignalCreate(title="Test Paper", url="https://example.com/p1")
    assert sig.signal_type == "other"
    assert sig.status == "collected"
    assert sig.language == "en"


def test_entity_schema_defaults():
    e = EntityCreate(name="GPT-4", canonical_name="GPT-4", entity_type="model")
    assert e.metadata == {}


def test_pipeline_schema_defaults():
    p = PipelineRunCreate(run_type="collect")
    assert p.status == "success"
    assert p.total_items == 0
