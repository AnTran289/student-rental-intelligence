import pytest
from ingestion.ingestion_validation import validate_ingestion_ids

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