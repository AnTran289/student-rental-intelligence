from ingestion.snowflake_loader import RAW_COLUMNS, build_record_params
from ingestion.snowflake_loader import build_source_expressions
from ingestion.snowflake_loader import build_source_select
from ingestion.snowflake_loader import build_merge_sql
from unittest.mock import MagicMock
from ingestion.snowflake_loader import (
    merge_rental_record,
    build_merge_sql,
    build_record_params,
)

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

