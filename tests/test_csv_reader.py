import pytest
from ingestion.csv_reader import read_rental_csv

def test_read_rental_csv_valid(tmp_path):
    csv_file = tmp_path / "rentals.csv"

    csv_file.write_text(
        "raw_record_id,suburb,weekly_rent\n"
        "S001,Wollongong,290\n"
        "S002,Figtree,250\n",
        encoding="utf-8"
    )

    required_columns = {
        "raw_record_id",
        "suburb",
        "weekly_rent"
    }

    records = read_rental_csv(csv_file, required_columns)

    assert len(records) == 2
    assert records[0]["raw_record_id"] == "S001"
    assert records[0]["weekly_rent"] == "290"
    assert records[1]["suburb"] == "Figtree"

def test_read_rental_csv_missing_columns(tmp_path):
    csv_file = tmp_path / "rentals.csv"

    csv_file.write_text(
        "raw_record_id,suburb\n"
        "S001,Wollongong\n",
        encoding="utf-8"
    )

    required_columns = {
        "raw_record_id",
        "suburb",
        "weekly_rent"
    }

    with pytest.raises(ValueError, match = "weekly_rent"):
        read_rental_csv(csv_file, required_columns)

def test_read_rental_csv_no_records(tmp_path):
    csv_file = tmp_path / "rentals.csv"

    csv_file.write_text(
        "raw_record_id,suburb,weekly_rent\n",
        encoding="utf-8"
    )

    required_columns = {
        "raw_record_id",
        "suburb",
        "weekly_rent"
    }

    records = read_rental_csv(csv_file, required_columns)

    assert records == []

def test_read_csv_extra_fields(tmp_path):
    csv_file = tmp_path / "rentals.csv"

    csv_file.write_text(
        "raw_record_id,suburb,weekly_rent\n" \
        "S001,Wollongong,290\n" \
        "S002,Figtree,250,unexpected_value\n",
        encoding="utf-8"
    )

    required_columns = {
        "raw_record_id",
        "suburb",
        "weekly_rent"
    }

    # Test that the function raises a ValueError when encountering extra fields in a record
    with pytest.raises(ValueError, match = "Line 3 contains extra CSV fields"):
        read_rental_csv(csv_file, required_columns)