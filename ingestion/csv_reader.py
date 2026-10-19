import csv
from ingestion.validators import validate_schema


def read_rental_csv(file_path, required_columns):
    """
    Read csv file about rental info and return a list of dictionary.
    Automatically validate schema with required_columns.
    If invalid, raise ValueError. If valid, return list of dicts.
    """

    # Use utf-8-sig to remove Byte Order Mark (BOM)
    with open(file_path, mode = 'r', encoding = 'utf-8-sig') as file:
        # Use DictReader so every lines of data could automatically map into a dictionary
        reader = csv.DictReader(file)

        # Use reader.fieldnames to get the CSV headers list safely
        # If file is empty (no header included), fieldnames will be None
        actual_headers = reader.fieldnames if reader.fieldnames is not None else []

        # Call validate_schema() to check headers
        validation_result = validate_schema(actual_headers, required_columns)

        # If schema is INVALID, raise ValueError including list of missing columns
        if not validation_result["is_valid"]:
            missing = validation_result["missing_columns"]
            raise ValueError(f"Schema validation failed! Missing columns: {missing}")

        # If schema is valid, read the records into a list of dictionaries
        records = []

        for line_number, record in enumerate(reader, start = 2):  # Start from line 2 because line 1 is header
            # Check if record has None 
            if None in record:
                raise ValueError(f"Line {line_number} contains extra CSV fields: {record[None]}")
            records.append(record)

        return records