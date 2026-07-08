"""Tests for shared types and models."""

from orbit_core.types.models import (
    CapabilityInfo,
    Chunk,
    Document,
    Embedding,
    EngineInfo,
    HealthStatus,
    Project,
    ProviderInfo,
    SearchResult,
    ToolInfo,
)


def test_document() -> None:
    doc = Document(path="/test", title="Test", content="Data", metadata={"key": "value"})
    assert doc.path == "/test"
    assert doc.title == "Test"
    assert doc.content == "Data"
    assert doc.metadata == {"key": "value"}


def test_chunk() -> None:
    chunk = Chunk(id="1", document="/test", section="A", title="Test", text="Data", hash="abc")
    assert chunk.id == "1"
    assert chunk.start_line == 0
    assert chunk.end_line == 0


def test_search_result() -> None:
    res = SearchResult(file="test.py", line=10, text="foo", score=0.99)
    assert res.to_dict() == {"file": "test.py", "line": 10, "text": "foo", "score": 0.9900}


def test_embedding() -> None:
    emb = Embedding(id="1", vector=[0.1, 0.2])
    assert emb.id == "1"
    assert emb.vector == [0.1, 0.2]


def test_project() -> None:
    proj = Project(name="test", root="/root")
    assert proj.name == "test"
    assert proj.root == "/root"
    assert proj.files_count == 0


def test_capability_info() -> None:
    cap = CapabilityInfo(id="c1", name="Cap 1", version="1.0")
    assert cap.id == "c1"
    assert cap.status == "unknown"


def test_health_status() -> None:
    hs = HealthStatus(status="healthy", version="1.0")
    assert hs.status == "healthy"
    assert hs.uptime == 0.0


def test_provider_info() -> None:
    pi = ProviderInfo(name="p1", type="search")
    assert pi.name == "p1"
    assert pi.healthy is True


def test_engine_info() -> None:
    ei = EngineInfo(name="e1", version="1.0")
    assert ei.name == "e1"
    assert ei.capabilities == []


def test_tool_info() -> None:
    ti = ToolInfo(name="t1", description="desc")
    assert ti.name == "t1"
    assert ti.parameters == {}
