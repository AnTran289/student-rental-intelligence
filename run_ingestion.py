import argparse
import logging

from ingestion.csv_reader import read_rental_csv
from ingestion.record_preparation import prepare_records
from ingestion.ingestion_validation import validate_ingestion_ids
from ingestion.postgres_connection import get_postgres_connection
from ingestion.postgres_loader import load_rental_batch


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


REQUIRED_COLUMNS = [
    "raw_record_id",
    "source_listing_id",
    "source_platform",
    "suburb",
    "weekly_rent",
    "collected_at",
]


def run_ingestion(csv_path, *, include_batch_metadata=False):
    logger.info("Starting rental ingestion: %s", csv_path)

    # 1. Read and validate CSV schema
    records = read_rental_csv(csv_path, REQUIRED_COLUMNS)
    logger.info("Read %d records", len(records))

    # 2. Normalize dictionary keys
    prepared_records = prepare_records(records)

    # 3. Validate observation IDs
    validate_ingestion_ids(prepared_records)

    # 4. Skip database connection for empty files
    if not prepared_records:
        logger.info("No records to ingest")
        result = {"inserted": 0, "skipped": 0}
        if include_batch_metadata:
            result["raw_record_ids"] = []
        return result

    # 5. Load into PostgreSQL
    connection = get_postgres_connection()

    try:
        result = load_rental_batch(connection, prepared_records)
        if include_batch_metadata:
            result.update(
                raw_record_ids=[record["raw_record_id"].strip() for record in prepared_records],
                database=connection.info.dbname,
                host=connection.info.host,
                port=connection.info.port,
            )
    finally:
        connection.close()

    logger.info(
        "Ingestion complete | inserted=%d | skipped=%d",
        result["inserted"],
        result["skipped"],
    )

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest rental observations into PostgreSQL"
    )

    parser.add_argument(
        "--file",
        required=True,
        help="Path to rental CSV file",
    )

    args = parser.parse_args()

    run_ingestion(args.file)
