"""Selection, API, audit-signature and CSV edge-case regression tests."""
import math

import pytest

from exemplar_selector.selection import select_exemplars
from exemplar_selector.cli import main as selector_cli, parse_csv_bool as parse_selector_csv_bool
from cli import parse_csv_bool as parse_audit_csv_bool
from agents.base import AuditTrail


POOL = [
    {"id": "a", "input": "acute kidney injury", "output": "Compare kidney function", "domain": "clinical"},
    {"id": "b", "input": "acute kidney injury", "output": "Review fluid status", "domain": "clinical"},
    {"id": "c", "input": "apple pear fruit", "output": "Assess nutrition", "domain": "clinical"},
    {"id": "d", "input": "sort a Python list", "output": "Use sorted", "domain": "coding"},
]


def test_relevance_and_diversity():
    relevant = select_exemplars("acute kidney injury", POOL, k=2, diversity=1)
    assert [x["id"] for x in relevant["selected"]] == ["a", "b"]
    diversified = select_exemplars("acute kidney injury", POOL, k=2, diversity=0.2)
    assert diversified["selected"][0]["id"] == "a"
    assert diversified["selected"][1]["id"] in {"c", "d"}
    assert diversified["method"] == "tfidf-mmr"
    assert diversified == select_exemplars("acute kidney injury", POOL, k=2, diversity=0.2)


def test_domain_budget_and_empty_pool():
    result = select_exemplars("kidney", POOL, k=4, domain="Clinical")
    assert result["candidate_count"] == 3
    assert all(e["domain"] == "clinical" for e in result["selected"])
    assert select_exemplars("kidney", POOL, token_budget=1)["selected"] == []
    assert select_exemplars("kidney", [], k=2)["selected"] == []
    assert select_exemplars("kidney", POOL, domain="missing")["candidate_count"] == 0


@pytest.mark.parametrize("kwargs", [
    {"k": True}, {"k": 0}, {"k": 51},
    {"diversity": -0.1}, {"diversity": float("nan")},
    {"diversity": float("inf")}, {"token_budget": 0},
    {"token_budget": True}, {"domain": 1},
])
def test_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        select_exemplars("kidney", POOL, **kwargs)


@pytest.mark.parametrize("item", [
    {"id": "x", "input": "", "output": "ok"},
    {"id": "x", "input": "ok", "output": None},
    {"id": "x", "input": "ok", "output": "ok", "domain": 5},
])
def test_invalid_exemplars(item):
    with pytest.raises(ValueError):
        select_exemplars("kidney", [item])


def test_duplicate_ids_even_across_domains():
    with pytest.raises(ValueError, match="duplicate exemplar id"):
        select_exemplars("kidney", [POOL[0], dict(POOL[0], domain="coding")], domain="clinical")


@pytest.mark.parametrize("parser", [parse_csv_bool_helper for parse_csv_bool_helper in (parse_selector_csv_bool, parse_audit_csv_bool)])
def test_csv_booleans(parser):
    for value in ("False", "false", "0", "no", "", False):
        assert parser(value) is False
    for value in ("True", "yes", "1", True):
        assert parser(value) is True
    with pytest.raises(ValueError):
        parser("maybe")


def test_cli_select_json(tmp_path, capsys):
    import json
    pool = tmp_path / "pool.json"
    pool.write_text(json.dumps(POOL), encoding="utf-8")
    assert selector_cli(["select", "--pool", str(pool), "--query", "kidney injury", "-k", "2"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert len(output["selected"]) == 2
    assert output["selected"][0]["id"] == "a"


def test_full_hmac_verification_and_snapshot_isolation():
    trail = AuditTrail(secret_key="test-signing-key")
    trail.log("worker", "tier", "EVENT", {"key": "sample"})
    snapshot = trail.get_trail()
    snapshot[0]["actor"] = "malicious"
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "malicious"
    assert not trail.verify_integrity()


def test_fastapi_select_and_limits():
    from fastapi.testclient import TestClient
    from agents.api import app
    with TestClient(app) as client:
        response = client.post("/api/select", json={"query": "kidney injury", "exemplars": POOL, "k": 2})
        assert response.status_code == 200
        assert len(response.json()["selected"]) == 2
        assert client.post("/api/select", json={"query": "", "exemplars": POOL}).status_code == 422
        assert client.post("/api/select", data="x" * (1024 * 1024 + 1)).status_code == 413
        assert client.get("/").status_code == 200
        assert "selectExemplars" in client.get("/selector.js").text
