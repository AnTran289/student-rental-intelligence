from ingestion.validators import validate_schema

def test_validate_schema_valid():
    actual_columns = [
        "raw_record_id",
        "source_platform",
        "weekly_rent",
        "suburb"
    ]

    required_columns = {
        "raw_record_id",
        "weekly_rent",
        "suburb"
    }

    result = validate_schema(actual_columns, required_columns)

    assert result["is_valid"] is True
    assert result["missing_columns"] == []

def test_validate_schema_missing_columns():
    actual_columns = [
        "raw_record_id",
        "suburb"
    ]

    required_columns = {
        "raw_record_id",
        "suburb",
        "weekly_rent",
        "collected_at"
    }

    result = validate_schema(actual_columns, required_columns)
    assert result["is_valid"] is False
    assert result["missing_columns"] == ["collected_at", "weekly_rent"]

def test_validate_schema_empty():
    actual_columns = []

    required_columns = {
        "raw_record_id",
        "weekly_rent",
    }

    result = validate_schema(actual_columns, required_columns)
    assert result["is_valid"] is False
    assert result["missing_columns"] == ["raw_record_id", "weekly_rent"]