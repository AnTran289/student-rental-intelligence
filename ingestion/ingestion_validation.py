def validate_ingestion_ids(records):
    """
    Validate RAW_RECORD_ID before loading into Snowflake.

    Raise ValueError if:
    - RAW_RECORD_ID is missing or blank.
    - RAW_RECORD_ID appears more than once in the batch.

    Return True if all records are valid.
    """
    seen_ids = set()

    for record in records:
        raw_id = record.get("RAW_RECORD_ID")

        # Check missing / blank
        if not isinstance(raw_id, str) or not raw_id.strip(): # Check if raw_id is not a string or is empty/whitespace
            raise ValueError(f"RAW_RECORD_ID is missing or blank in record: {record}")

        normalized_id = raw_id.strip()  # Normalize by stripping whitespace
        
        # Check duplicates using seen_ids
        if normalized_id in seen_ids:
            raise ValueError(f"Duplicate RAW_RECORD_ID found: {normalized_id}")
        
        # Add valid ID into seen_ids
        seen_ids.add(normalized_id)
    return True