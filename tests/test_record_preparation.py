from ingestion.record_preparation import prepare_records


def test_prepare_records_multiple():
    records = [
        {"raw_record_id": "S001", "weekly_rent": "$290"},
        {"raw_record_id": "S002", "weekly_rent": "-$250"}
    ]
    expected_records = [
        {"RAW_RECORD_ID": "S001", "WEEKLY_RENT": "$290"},
        {"RAW_RECORD_ID": "S002", "WEEKLY_RENT": "-$250"}
    ]
    assert prepare_records(records) == expected_records

def test_prepare_records_empty():
    records = []
    expected_records = []
    assert prepare_records(records) == expected_records

def test_prepare_records_no_mutation():
    records = [
        {"raw_record_id": "S001", "weekly_rent": None}
    ]
    expected_records = [
        {"raw_record_id": "S001", "weekly_rent": None}
    ]
    
    result = prepare_records(records)

    # Input must remain unchanged
    assert records == expected_records

    # Output must be transformed correctly
    assert result == [{"RAW_RECORD_ID": "S001", "WEEKLY_RENT": None}]

    # Output should be a separate object
    assert result is not records
    assert result[0] is not records[0]
