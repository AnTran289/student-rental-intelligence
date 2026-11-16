from pathlib import Path
from ingestion.csv_reader import read_rental_csv
from run_ingestion import REQUIRED_COLUMNS

def validate_csv(csv_path: str) -> int:
    path = Path(csv_path)

    # Check whether the file exists.
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found at path: {csv_path}")

    # Read CSV using existing reader.
    records = read_rental_csv(str(path), REQUIRED_COLUMNS)

    # Reject empty CSV.
    if not records:
        raise ValueError(f"CSV file is empty (no records found): {csv_path}")

    # Return number of records.
    return len(records)