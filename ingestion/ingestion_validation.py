from datetime import datetime

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

def records_match(existing_record, incoming_record, columns):
    """
    Return True if two observations contain
    the same business data.
    """
    for column in columns:
        # Get value from existing_record
        existing_value = existing_record.get(column)

        # Get value from imcoming_record
        incoming_value = incoming_record.get(column)

        # Return False if values differ
        if existing_value != incoming_value:
            return False

    return True

def normalize_collected_at(value):
    """
    Convert COLLECTED_AT into Python datetime.
    Reject missing or invalid timestamp
    """
    if isinstance(value, datetime):
        return value

    if not isinstance(value, str) or not value.strip():
        raise ValueError("COLLECTED_AT is missing or invalid")

    try:
        # Convert ISO-format string into datetime
        return datetime.fromisoformat(value)
    
    except ValueError:
        raise ValueError("Invalid COLLECTED_AT timestamp")
