import pytest
import datetime
from ingestion.ingestion_validation import validate_ingestion_ids
from ingestion.ingestion_validation import records_match
from ingestion.ingestion_validation import normalize_collected_at

# Valid IDs
def test_validate_ingestion_ids_valid():
    records = [
        {"RAW_RECORD_ID": "S001", "suburb": "Wollongong"},
        {"RAW_RECORD_ID": "S002", "suburb": "Figtree"},
    ]

    assert validate_ingestion_ids(records) is True

# Missing ID
def test_validate_ingestion_ids_missing():
    records = [
        {"RAW_RECORD_ID": "S001", "suburb": "Wollongong"},
        {"suburb": "Figtree"},  # Missing RAW_RECORD_ID
    ]

    with pytest.raises(ValueError, match = "missing or blank"):
        validate_ingestion_ids(records)

# Duplicate ID
def test_validate_ingestion_ids_duplicate():
    records = [
        {"RAW_RECORD_ID": "S001", "suburb": "Wollongong"},
        {"RAW_RECORD_ID": "S001", "suburb": "Figtree"},  # Duplicate RAW_RECORD_ID
    ]

    with pytest.raises(ValueError, match = "Duplicate"):
        validate_ingestion_ids(records)

# Whitespace-only ID
def test_validate_ingestion_ids_whitespace():
    records = [
        {"RAW_RECORD_ID": "S001", "suburb": "Wollongong"},
        {"RAW_RECORD_ID": "   ", "suburb": "Figtree"},  # Whitespace-only RAW_RECORD_ID
    ]

    with pytest.raises(ValueError, match = "missing or blank"):
        validate_ingestion_ids(records)

# Duplicate after trimming whitespace
def test_validate_ingestion_ids_duplicate_after_trim():
    records = [
        {"RAW_RECORD_ID": "S001"},
        {"RAW_RECORD_ID": " S001 "}
    ]

    with pytest.raises(ValueError, match="Duplicate"):
        validate_ingestion_ids(records)

# 2 records match
def test_records_match_identical():
    existing_record = {
        "RAW_RECORD_ID": "S001",
        "suburb": "Wollongong",
        "WEEKLY_RENT": 290
    }

    incoming_record = {
        "RAW_RECORD_ID": "S001",
        "suburb": "Wollongong",
        "WEEKLY_RENT": 290
    }

    columns = ["RAW_RECORD_ID", "suburb", "WEEKLY_RENT"]

    assert records_match(existing_record, incoming_record, columns) is True

# Match IDs but different WEEKLY_RENT
def test_records_match_conflict():
    existing_record = {
        "RAW_RECORD_ID": "S001",
        "suburb": "Wollongong",
        "WEEKLY_RENT": 290
    }

    incoming_record = {
        "RAW_RECORD_ID": "S001",
        "suburb": "Wollongong",
        "WEEKLY_RENT": 300
    }

    columns = ["RAW_RECORD_ID", "suburb", "WEEKLY_RENT"]

    assert records_match(existing_record, incoming_record, columns) is False

# Different INGESTED_AT but other fields match
def test_records_match_ignores_ingested_at():
    existing_record = {
        "RAW_RECORD_ID": "S001",
        "suburb": "Wollongong",
        "WEEKLY_RENT": 290,
        "INGESTED_AT": "2024-01-01"
    }

    incoming_record = {
        "RAW_RECORD_ID": "S001",
        "suburb": "Wollongong",
        "WEEKLY_RENT": 290,
        "INGESTED_AT": "2024-02-01"
    }

    columns = ["RAW_RECORD_ID", "suburb", "WEEKLY_RENT"]

    assert records_match(existing_record, incoming_record, columns) is True

# test valid string timestamp
def test_normalize_collected_at_valid_string():
    timestamp_str = "2024-06-01 12:00:00"
    result = normalize_collected_at(timestamp_str)
    assert isinstance(result, datetime.datetime)
    assert result == datetime.datetime(2024, 6, 1, 12, 0, 0)

# test existing datetime
def test_normalize_collected_at_existing_datetime():
    timestamp_dt = datetime.datetime(2024, 6, 1, 12, 0, 0)
    result = normalize_collected_at(timestamp_dt)
    assert result == timestamp_dt

# test invalid string
def test_normalize_collected_at_invalid_string():
    invalid_timestamp_str = "invalid-timestamp"
    with pytest.raises(ValueError, match="Invalid COLLECTED_AT timestamp"):
        normalize_collected_at(invalid_timestamp_str)
