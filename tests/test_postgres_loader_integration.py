
import os
import uuid

import psycopg
import pytest

from ingestion.postgres_loader import load_rental_batch


@pytest.fixture
def connection():
    conn = psycopg.connect(
        host="127.0.0.1",
        port=5433,
        dbname="student_rental_test_db",
        user="rental_admin",
        password=os.environ["POSTGRES_PASSWORD"],
    )

    assert conn.info.dbname == "student_rental_test_db"

    yield conn
    conn.close()


def make_record(raw_id, rent="$290"):
    return {
        "raw_record_id": raw_id,
        "source_listing_id": "TEST001",
        "source_platform": "integration_test",
        "suburb": "Wollongong",
        "weekly_rent": rent,
        "collected_at": "2026-11-12T10:30:00",
    }


def test_insert_skip_conflict_rollback(connection):
    prefix = f"PGTEST_{uuid.uuid4().hex[:10]}"

    first = make_record(f"{prefix}_001")

    # INSERT
    result = load_rental_batch(connection, [first])
    assert result == {"inserted": 1, "skipped": 0}

    # SKIP
    result = load_rental_batch(connection, [first])
    assert result == {"inserted": 0, "skipped": 1}

    # CONFLICT
    with pytest.raises(ValueError, match="Conflicting data"):
        load_rental_batch(
            connection,
            [make_record(f"{prefix}_001", "$999")]
        )

    # ROLLBACK
    with pytest.raises(ValueError):
        load_rental_batch(
            connection,
            [
                make_record(f"{prefix}_002"),
                make_record(f"{prefix}_001", "$999"),
            ]
        )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM raw.rental_listings
            WHERE raw_record_id = %s
            """,
            (f"{prefix}_002",),
        )
        assert cursor.fetchone()[0] == 0
