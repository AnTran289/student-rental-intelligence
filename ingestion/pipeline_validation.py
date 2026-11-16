"""Validate the current batch against the relations built by dbt."""

import json
from collections import Counter

import psycopg
from psycopg import sql


REQUIRED_MODELS = (
    "int_valid_rental_listings",
    "int_rejected_rental_listings",
    "fct_rental_listings",
)


def read_build_metadata(artifact_dir, *, run_id, host, port, database):
    """Read metadata from the fresh artifact directory of a successful build."""
    try:
        manifest = json.loads((artifact_dir / "manifest.json").read_text(encoding="utf-8"))
        results = json.loads((artifact_dir / "run_results.json").read_text(encoding="utf-8"))
        invocation = manifest["metadata"]["invocation_id"]
        if not invocation or invocation != results["metadata"]["invocation_id"]:
            raise ValueError("dbt artifacts belong to different invocations")

        successful = {
            entry["unique_id"] for entry in results["results"] if entry["status"] == "success"
        }
        relations = {}
        for name in REQUIRED_MODELS:
            model_id = f"model.student_rental_intelligence.{name}"
            node = manifest["nodes"][model_id]
            if model_id not in successful:
                raise ValueError(f"Required dbt model did not build successfully: {name}")
            if node["database"] != database:
                raise ValueError("dbt artifact database differs from configured target")
            relations[name] = {"schema": node["schema"], "identifier": node["alias"]}
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("Missing or invalid dbt build artifacts") from error

    return {
        "run_id": run_id,
        "invocation_id": invocation,
        "database": database,
        "host": host,
        "port": int(port),
        "relations": relations,
    }


def validate_batch(ingestion, validated_count, build, *, run_id, user, password):
    """Reconcile this run's observations using one read-only PostgreSQL snapshot."""
    if not build or build.get("run_id") != run_id or not build.get("invocation_id"):
        raise ValueError("Missing or stale dbt build metadata")
    if not ingestion or not isinstance(validated_count, int):
        raise ValueError("Missing input count or ingestion metadata")
    try:
        database, host, port = (build[key] for key in ("database", "host", "port"))
        relations = {
            name: (build["relations"][name]["schema"], build["relations"][name]["identifier"])
            for name in REQUIRED_MODELS
        }
    except (KeyError, TypeError) as error:
        raise ValueError("Incomplete dbt build metadata") from error
    if (
        not all(isinstance(value, str) and value for pair in relations.values() for value in pair)
        or len({schema for schema, _ in relations.values()}) != 1
        or len(set(relations.values())) != len(REQUIRED_MODELS)
    ):
        raise ValueError("Invalid dbt output schema or relation metadata")
    if (database, host, port) != (ingestion.get("database"), ingestion.get("host"), ingestion.get("port")):
        raise ValueError("Ingestion and dbt target different PostgreSQL endpoints")

    ids = ingestion["raw_record_ids"]
    inserted, skipped = ingestion["inserted"], ingestion["skipped"]
    if validated_count <= 0 or len(ids) != validated_count or inserted + skipped != validated_count:
        raise ValueError("Input and ingestion counts do not reconcile")
    expected = set(ids)
    if len(expected) != len(ids):
        raise ValueError("Duplicate observation IDs in ingestion metadata")

    valid_name, rejected_name, fact_name = REQUIRED_MODELS
    try:
        with psycopg.connect(
            dbname=database, host=host, port=port, user=user, password=password,
            options="-c default_transaction_read_only=on",
        ) as connection:
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            if connection.execute("SELECT current_database()").fetchone()[0] != database:
                raise ValueError("Connected to the wrong PostgreSQL database")
            connection.execute(
                sql.SQL("SELECT 1 FROM {} LIMIT 1").format(sql.Identifier(*relations[fact_name]))
            )
            counts = []
            for name in (valid_name, rejected_name):
                query = sql.SQL("SELECT raw_record_id FROM {} WHERE raw_record_id = ANY(%s)")
                rows = connection.execute(query.format(sql.Identifier(*relations[name])), (ids,))
                counts.append(Counter(row[0] for row in rows))
    except psycopg.Error as error:
        raise RuntimeError(f"Cannot read required dbt outputs (SQLSTATE {error.sqlstate or 'unknown'})") from None

    valid, rejected = counts
    duplicates = sum(count > 1 for branch in counts for count in branch.values())
    overlap = len(valid.keys() & rejected.keys())
    missing = len(expected - (valid.keys() | rejected.keys()))
    if duplicates or overlap or missing:
        raise ValueError(
            f"Batch classification mismatch (missing={missing}, duplicate_ids={duplicates}, overlap={overlap})"
        )
    if not valid:
        raise ValueError(f"ALL_REJECTED: all {len(ids)} batch observations were rejected")

    return {
        "status": "PASS",
        "validated_input_count": validated_count,
        "inserted": inserted,
        "skipped": skipped,
        "valid": len(valid),
        "rejected": len(rejected),
        "database": database,
        "schema": relations[fact_name][0],
        "dbt_invocation_id": build["invocation_id"],
    }
