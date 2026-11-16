import json
from unittest.mock import MagicMock, Mock

import psycopg
import pytest

from ingestion import pipeline_validation


@pytest.fixture
def metadata():
    endpoint = {"database": "rental_test", "host": "postgres", "port": 5432}
    ingestion = {**endpoint, "raw_record_ids": ["A", "B"], "inserted": 0, "skipped": 2}
    build = {
        **endpoint,
        "run_id": "airflow-run",
        "invocation_id": "dbt-invocation",
        "relations": {
            name: {"schema": "run_schema", "identifier": name}
            for name in pipeline_validation.REQUIRED_MODELS
        },
    }
    return ingestion, build


def validate(metadata):
    ingestion, build = metadata
    return pipeline_validation.validate_batch(
        ingestion, 2, build, run_id="airflow-run", user="test", password="test"
    )


def mock_database(monkeypatch, *, valid, rejected, database="rental_test", fact_error=False):
    connection = Mock()
    identity = Mock()
    identity.fetchone.return_value = (database,)
    fact = psycopg.errors.UndefinedTable("relation not found") if fact_error else None
    connection.execute.side_effect = [
        None, identity, fact, [(value,) for value in valid], [(value,) for value in rejected]
    ]
    connect = Mock()
    connect.return_value = MagicMock()
    connect.return_value.__enter__.return_value = connection
    monkeypatch.setattr(pipeline_validation.psycopg, "connect", connect)
    return connection, connect


def test_mixed_batch_replay_passes(monkeypatch, metadata):
    connection, connect = mock_database(monkeypatch, valid=["A"], rejected=["B"])
    result = validate(metadata)
    assert result == {
        "status": "PASS", "validated_input_count": 2, "inserted": 0, "skipped": 2,
        "valid": 1, "rejected": 1, "database": "rental_test", "schema": "run_schema",
        "dbt_invocation_id": "dbt-invocation",
    }
    assert connect.call_args.kwargs["options"] == "-c default_transaction_read_only=on"
    fact, valid, rejected = connection.execute.call_args_list[2:]
    assert fact.args[0].as_string() == 'SELECT 1 FROM "run_schema"."fct_rental_listings" LIMIT 1'
    for query in (valid, rejected):
        assert query.args[1] == (["A", "B"],)
        assert "ANY(%s)" in query.args[0].as_string()


@pytest.mark.parametrize(
    ("valid", "rejected", "message"),
    [
        (["A"], [], "missing=1"),
        (["A", "B"], ["B"], "overlap=1"),
        (["A", "A"], ["B"], "duplicate_ids=1"),
        (["A"], ["B", "B"], "duplicate_ids=1"),
        ([], ["A", "B"], "ALL_REJECTED"),
    ],
)
def test_invalid_classification_fails(monkeypatch, metadata, valid, rejected, message):
    mock_database(monkeypatch, valid=valid, rejected=rejected)
    with pytest.raises(ValueError, match=message):
        validate(metadata)


def test_wrong_connected_database_fails(monkeypatch, metadata):
    mock_database(monkeypatch, valid=[], rejected=[], database="development")
    with pytest.raises(ValueError, match="wrong PostgreSQL database"):
        validate(metadata)


def test_wrong_schema_fails(monkeypatch, metadata):
    _, build = metadata
    for relation in build["relations"].values():
        relation["schema"] = "absent_schema"
    mock_database(monkeypatch, valid=[], rejected=[], fact_error=True)
    with pytest.raises(RuntimeError, match="Cannot read required dbt outputs"):
        validate(metadata)


def test_count_mismatch_fails(metadata):
    metadata[0]["skipped"] = 1
    with pytest.raises(ValueError, match="counts do not reconcile"):
        validate(metadata)


def test_different_ingestion_database_fails(metadata):
    metadata[0]["database"] = "development"
    with pytest.raises(ValueError, match="different PostgreSQL endpoints"):
        validate(metadata)


@pytest.mark.parametrize("build", [None, {"run_id": "previous-run", "invocation_id": "old"}])
def test_missing_or_stale_build_metadata_fails(metadata, build):
    with pytest.raises(ValueError, match="Missing or stale dbt build metadata"):
        validate((metadata[0], build))


def test_build_metadata_uses_resolved_relations_and_rejects_mixed_artifacts(tmp_path):
    nodes = {
        f"model.student_rental_intelligence.{name}": {
            "database": "rental_test", "schema": "custom_schema", "alias": f"alias_{name}"
        }
        for name in pipeline_validation.REQUIRED_MODELS
    }
    kwargs = {"run_id": "current", "host": "postgres", "port": "5432", "database": "rental_test"}
    manifest = {"metadata": {"invocation_id": "current-build"}, "nodes": nodes}
    results = {
        "metadata": {"invocation_id": "previous-build"},
        "results": [{"unique_id": uid, "status": "success"} for uid in nodes],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Missing or invalid dbt build artifacts"):
        pipeline_validation.read_build_metadata(tmp_path, **kwargs)
    (tmp_path / "run_results.json").write_text(json.dumps(results), encoding="utf-8")
    with pytest.raises(ValueError, match="different invocations"):
        pipeline_validation.read_build_metadata(tmp_path, **kwargs)
    results["metadata"]["invocation_id"] = "current-build"
    (tmp_path / "run_results.json").write_text(json.dumps(results), encoding="utf-8")
    metadata = pipeline_validation.read_build_metadata(tmp_path, **kwargs)
    assert metadata["relations"]["fct_rental_listings"] == {
        "schema": "custom_schema", "identifier": "alias_fct_rental_listings",
    }
