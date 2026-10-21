import pytest

from ingestion.snowflake_loader import RAW_COLUMNS, build_record_params
from ingestion.snowflake_loader import build_source_expressions
from ingestion.snowflake_loader import build_source_select
from ingestion.snowflake_loader import build_merge_sql
from unittest.mock import MagicMock
from ingestion.snowflake_loader import fetch_existing_record, RAW_COLUMNS
from ingestion.snowflake_loader import (
    merge_rental_record,
    build_merge_sql,
    build_record_params,
)
from ingestion.snowflake_loader import load_rental_batch
from unittest.mock import patch
from datetime import datetime, timezone


@pytest.mark.parametrize("microsecond", [0, 123456])
def test_build_record_params_binds_collected_at_datetime_as_string(microsecond):
    timestamp = datetime(2026, 10, 18, 10, 0, 0, microsecond)
    record = {
        "RAW_RECORD_ID": "S_DATETIME",
        "AVAILABLE_FROM": timestamp,
        "COLLECTED_AT": timestamp,
    }

    params = build_record_params(record)

    assert params[RAW_COLUMNS.index("COLLECTED_AT")] == (
        f"2026-10-18 10:00:00.{microsecond:06d}"
    )
    assert params[RAW_COLUMNS.index("AVAILABLE_FROM")] is timestamp
    assert record["COLLECTED_AT"] is timestamp


def test_build_record_params_rejects_timezone_aware_collected_at():
    record = {
        "RAW_RECORD_ID": "S_AWARE",
        "COLLECTED_AT": datetime(2026, 10, 18, tzinfo=timezone.utc),
    }

    with pytest.raises(ValueError, match="COLLECTED_AT must be timezone-naive UTC"):
        build_record_params(record)


def test_load_rental_batch_binds_normalized_timestamp_string():
    connection = MagicMock()
    cursor = connection.cursor.return_value
    cursor.fetchone.return_value = None
    record = {
        "RAW_RECORD_ID": "S_BIND",
        "COLLECTED_AT": "2026-10-18T10:00:00.123456",
    }

    assert load_rental_batch(connection, [record]) == {"inserted": 1, "skipped": 0}

    sql, params = cursor.execute.call_args.args
    assert "TO_TIMESTAMP_NTZ(%s) AS COLLECTED_AT" in sql
    assert params[RAW_COLUMNS.index("COLLECTED_AT")] == "2026-10-18 10:00:00.123456"
    assert record["COLLECTED_AT"] == "2026-10-18T10:00:00.123456"

def test_build_record_params_valid():
    record = {
        "RAW_RECORD_ID": "S001",
        "SOURCE_LISTING_ID": "L001",
        "SOURCE_PLATFORM": "PlatformA",
        "SUBURB": "Wollongong",
        "WEEKLY_RENT": 290,
        "ROOM_TYPE": "Studio",
        "PROPERTY_TYPE": "Apartment",
        "FURNISHING_STATUS": "Furnished",
        "BILLS_STATUS": "Included",
        "BATHROOM_TYPE": "Private",
        "BATHROOM_SHARE_COUNT": 0,
        "AVAILABLE_FROM": "2024-07-01",
        "COLLECTED_AT": "2024-06-01"
    }

    expected_params = (
        "S001",
        "L001",
        "PlatformA",
        "Wollongong",
        290,
        "Studio",
        "Apartment",
        "Furnished",
        "Included",
        "Private",
        0,
        "2024-07-01",
        "2024-06-01",
    )

    assert build_record_params(record) == expected_params

def test_build_record_params_missing_optional():
    record = {
        "RAW_RECORD_ID": "S002",
        "SUBURB": "Figtree",
        "WEEKLY_RENT": 250,
        "COLLECTED_AT": "2024-06-02"
    }

    expected_params = (
        record["RAW_RECORD_ID"],
        None,  # SOURCE_LISTING_ID is missing
        None,  # SOURCE_PLATFORM is missing
        record.get("SUBURB"),
        record.get("WEEKLY_RENT"),
        None,  # ROOM_TYPE is missing
        None,  # PROPERTY_TYPE is missing
        None,  # FURNISHING_STATUS is missing
        None,  # BILLS_STATUS is missing
        None,  # BATHROOM_TYPE is missing
        None,  # BATHROOM_SHARE_COUNT is missing
        None,  # AVAILABLE_FROM is missing
        record.get("COLLECTED_AT"),
    )

    assert build_record_params(record) == expected_params

def test_build_record_params_no_mutation():
    record = {
        "RAW_RECORD_ID": "S003",
        "SUBURB": "North Wollongong",
        "WEEKLY_RENT": 300,
        "COLLECTED_AT": "2024-06-03"
    }

    # Store a copy of the original record to check for mutation later
    original_record = record.copy()

    # Call the function to build record parameters
    _ = build_record_params(record)

    # Ensure the original record is not mutated
    assert record == original_record


def test_build_source_expressions_placeholder_count():

    # Ensure that the number of placeholders matches the number of columns in RAW_COLUMNS
    result = build_source_expressions()

    assert result.count("%s") == 13


def test_build_source_expressions_timestamp():

    # Ensure that the last placeholder is for a timestamp column (COLLECTED_AT)
    result = build_source_expressions()

    expressions = result.split(", ")

    assert expressions[-1] == "TO_TIMESTAMP_NTZ(%s)"
    assert all(expr == "%s" for expr in expressions[:-1])

# Confirm SQL source has correct number of placeholders and time stamp conversion for COLLECTED_AT
def test_build_source_select():
    result = build_source_select()

    assert result.startswith("SELECT ")
    assert result.count("%s") == 13
    assert "%s AS RAW_RECORD_ID" in result
    assert "TO_TIMESTAMP_NTZ(%s) AS COLLECTED_AT" in result

def test_build_merge_sql():
    result = build_merge_sql()

    assert result.strip().startswith(
    "MERGE INTO STUDENT_RENTAL_DB.RAW.RENTAL_LISTINGS AS target"
    )
    assert "ON target.RAW_RECORD_ID = source.RAW_RECORD_ID" in result
    assert "WHEN MATCHED THEN UPDATE" not in result
    assert "WHEN NOT MATCHED THEN" in result
    assert result.count("%s") == 13

# Test that merge_rental_record executes the SQL with correct parameters and does not commit
def test_merge_rental_record_executes_sql():
    connection = MagicMock()

    record = {
        "RAW_RECORD_ID": "S_TEST_001",
        "SOURCE_LISTING_ID": "SYN001",
        "SOURCE_PLATFORM": "SYNTHETIC",
        "WEEKLY_RENT": "$290",
        "COLLECTED_AT": "2026-10-18 10:00:00",
    }

    merge_rental_record(connection, record)

    cursor = connection.cursor.return_value

    # Check execute was called with expected SQL and params
    cursor.execute.assert_called_once_with(
        build_merge_sql(),
        build_record_params(record)
    )

    # Check cursor was closed
    cursor.close.assert_called_once()

    # Check function did not commit
    connection.commit.assert_not_called()

    # Help figure when number of placeholders and parameters mismatch
    sql, params = cursor.execute.call_args.args

    assert sql.count("%s") == len(params) == len(RAW_COLUMNS)


from unittest.mock import MagicMock
from ingestion.snowflake_loader import fetch_existing_record, RAW_COLUMNS

# Test fetch_existing_record returns None when no record is found
# and returns a dictionary with correct keys when a record is found
def test_fetch_existing_record_not_found():
    connection = MagicMock()
    cursor = connection.cursor.return_value

    cursor.fetchone.return_value = None

    result = fetch_existing_record(connection, "S999")

    # Verify result is None
    assert result is None

    # Verify SQL execution uses the correct ID
    sql, params = cursor.execute.call_args.args
    assert params == ("S999",)

    # Verify cursor was closed
    cursor.close.assert_called_once()

# Test fetch_existing_record returns a dictionary with correct keys when a record is found
def test_fetch_existing_record_found():
    connection = MagicMock()
    cursor = connection.cursor.return_value

    row = (
        "S001",
        "SYN001",
        "SYNTHETIC",
        "Figtree",
        "$290",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )

    cursor.fetchone.return_value = row

    result = fetch_existing_record(connection, "S001")

    # Verify returned dictionary
    assert result["RAW_RECORD_ID"] == "S001"
    assert result["WEEKLY_RENT"] == "$290"

    # Verify all 13 columns were mapped
    assert len(result) == len(RAW_COLUMNS)

# Test new observations are inserted, inserted = 1, commit() is called
def test_load_rental_batch_inserts_new_observation():
    connection = MagicMock()
    connection.cursor.return_value.fetchone.return_value = None
    records = [
        {
            "RAW_RECORD_ID": "S_NEW_001",
            "SOURCE_LISTING_ID": "SYN001",
            "SOURCE_PLATFORM": "SYNTHETIC",
            "WEEKLY_RENT": "$290",
            "COLLECTED_AT": "2026-10-18 10:00:00",
        }
    ]

    with patch('ingestion.snowflake_loader.merge_rental_record') as mock_merge:
        result = load_rental_batch(connection, records)

        # Verify that one record was inserted and none skipped
        assert result == {"inserted": 1, "skipped": 0}
        mock_merge.assert_called_once()

        # Verify that merge_rental_record was called with the correct connection and record
        actual_connection, actual_record = mock_merge.call_args.args
        assert actual_connection is connection
        assert actual_record["RAW_RECORD_ID"] == "S_NEW_001"
        assert actual_record["COLLECTED_AT"] == datetime(2026, 10, 18, 10, 0)

    # Verify that commit was called and rollback was not called
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()

# Test exact duplicate observations are skipped, skipped = 1, MERGE must not be called, commit() is called
def test_load_rental_batch_skips_exact_duplicate():
    connection = MagicMock()
    records = [
        {
            "RAW_RECORD_ID": "S_DUP_001",
            "SOURCE_LISTING_ID": "SYN001",
            "SOURCE_PLATFORM": "SYNTHETIC",
            "WEEKLY_RENT": "$290",
            "COLLECTED_AT": "2026-10-18 10:00:00",
        }
    ]

    # Simulate that the record already exists in the database
    existing_record = {
        "RAW_RECORD_ID": "S_DUP_001",
        "SOURCE_LISTING_ID": "SYN001",
        "SOURCE_PLATFORM": "SYNTHETIC",
        "WEEKLY_RENT": "$290",
        "COLLECTED_AT": datetime(2026, 10, 18, 10, 0),
    }

    # Mock fetch_existing_record to return the existing record
    connection.cursor.return_value.fetchone.return_value = tuple(
        existing_record.get(column) for column in RAW_COLUMNS
    )

    with patch('ingestion.snowflake_loader.merge_rental_record') as mock_merge:
        result = load_rental_batch(connection, records)

        # Verify that one record was skipped and none inserted
        assert result == {"inserted": 0, "skipped": 1}
        mock_merge.assert_not_called()

    # Verify that commit was called and rollback was not called
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()

# Test conflicting observations raise ValueError, rollback() is called
def test_load_rental_batch_conflicting_observation():
    connection = MagicMock()
    records = [
        {
            "RAW_RECORD_ID": "S_CONFLICT_001",
            "SOURCE_LISTING_ID": "SYN001",
            "SOURCE_PLATFORM": "SYNTHETIC",
            "WEEKLY_RENT": "$290",
            "COLLECTED_AT": "2026-10-18 10:00:00",
        }
    ]

    # Simulate that the record already exists in the database with a different WEEKLY_RENT
    existing_record = {
        "RAW_RECORD_ID": "S_CONFLICT_001",
        "SOURCE_LISTING_ID": "SYN001",
        "SOURCE_PLATFORM": "SYNTHETIC",
        "WEEKLY_RENT": "$300",  # Different rent value
        "COLLECTED_AT": datetime(2026, 10, 18, 10, 0),
    }

    # Mock fetch_existing_record to return the existing record
    connection.cursor.return_value.fetchone.return_value = tuple(
        existing_record.get(column) for column in RAW_COLUMNS
    )

    # Use patch to mock merge_rental_record and assert that it is not called due to the conflict
    with patch("ingestion.snowflake_loader.merge_rental_record") as mock_merge:
        with pytest.raises(
            ValueError,
            match="Conflicting data found for RAW_RECORD_ID"
        ):
            load_rental_batch(connection, records)

        mock_merge.assert_not_called()

    # Verify that rollback was called and commit was not called
    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
