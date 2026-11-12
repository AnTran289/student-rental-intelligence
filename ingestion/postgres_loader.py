
from datetime import datetime

from ingestion.ingestion_validation import (
    validate_ingestion_ids,
    records_match,
    normalize_collected_at,
)


RAW_COLUMNS = [
    "raw_record_id",
    "source_listing_id",
    "source_platform",
    "suburb",
    "weekly_rent",
    "room_type",
    "property_type",
    "furnishing_status",
    "bills_status",
    "bathroom_type",
    "bathroom_share_count",
    "available_from",
    "collected_at",
]


def build_record_params(record):
    """Build parameters matching RAW_COLUMNS order."""
    params = []

    for column in RAW_COLUMNS:
        value = (
            record[column]
            if column == "raw_record_id"
            else record.get(column)
        )

        if column == "collected_at" and isinstance(value, datetime):
            if value.tzinfo is not None:
                raise ValueError(
                    "collected_at must be timezone-naive UTC"
                )

        params.append(value)

    return tuple(params)


def build_insert_sql():
    """Build a parameterized PostgreSQL INSERT."""
    columns_sql = ", ".join(RAW_COLUMNS)
    placeholders = ", ".join(["%s"] * len(RAW_COLUMNS))

    return f"""
        INSERT INTO raw.rental_listings ({columns_sql})
        VALUES ({placeholders})
    """


def insert_rental_record(connection, record):
    """Insert one rental observation without committing."""
    sql = build_insert_sql()
    params = build_record_params(record)

    with connection.cursor() as cursor:
        cursor.execute(sql, params)


def fetch_existing_record(connection, raw_record_id):
    """Fetch an existing observation by raw_record_id."""
    columns_sql = ", ".join(RAW_COLUMNS)

    sql = f"""
        SELECT {columns_sql}
        FROM raw.rental_listings
        WHERE raw_record_id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, (raw_record_id,))
        row = cursor.fetchone()

    if row is None:
        return None

    return dict(zip(RAW_COLUMNS, row))


def load_rental_batch(connection, records):
    """
    Atomically load rental observations.

    New ID       -> INSERT
    Same ID/data -> SKIP
    Same ID/different data -> ERROR + ROLLBACK

    Assumes a non-autocommit connection and a single writer.
    """
    validate_ingestion_ids(records)

    prepared_records = []

    for record in records:
        normalized = record.copy()

        timestamp = normalize_collected_at(
            normalized.get("collected_at")
        )

        if timestamp.tzinfo is not None:
            raise ValueError(
                "collected_at must be timezone-naive UTC"
            )

        normalized["collected_at"] = timestamp
        normalized["raw_record_id"] = (
            normalized["raw_record_id"].strip()
        )

        prepared_records.append(normalized)

    inserted = 0
    skipped = 0

    try:
        for record in prepared_records:
            existing = fetch_existing_record(
                connection,
                record["raw_record_id"]
            )

            if existing is None:
                insert_rental_record(connection, record)
                inserted += 1

            else:
                existing["collected_at"] = (
                    normalize_collected_at(
                        existing["collected_at"]
                    )
                )

                if records_match(
                    existing,
                    record,
                    RAW_COLUMNS
                ):
                    skipped += 1
                else:
                    raise ValueError(
                        "Conflicting data found for "
                        f"raw_record_id: {record['raw_record_id']}"
                    )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    return {
        "inserted": inserted,
        "skipped": skipped,
    }
