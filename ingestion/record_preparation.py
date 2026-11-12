def _normalize_record_keys(records, normalize_key):
    prepared_records = []
    for record in records:
        normalized = {}
        for key, value in record.items():
            normalized_key = normalize_key(key)
            if normalized_key in ("RAW_RECORD_ID", "raw_record_id") and normalized_key in normalized:
                raise ValueError("Ambiguous RAW_RECORD_ID: multiple ID keys in record")
            normalized[normalized_key] = value
        prepared_records.append(normalized)
    return prepared_records


def prepare_records(records):
    """Return records with uppercase keys for Snowflake."""
    return _normalize_record_keys(records, str.upper)


def prepare_postgres_records(records):
    """Return records with lowercase keys for PostgreSQL."""
    return _normalize_record_keys(records, str.lower)
