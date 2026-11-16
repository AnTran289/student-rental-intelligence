import pytest
from ingestion.input_validation import validate_csv

def test_validate_csv_valid_file():
    result = validate_csv(
        "tests/fixtures/e2e_postgres_test.csv"
    )

    assert result == 3


def test_validate_csv_missing_file():
    with pytest.raises(FileNotFoundError):
        validate_csv("tests/fixtures/non_existent_file.csv")


def test_validate_csv_header_only(tmp_path):
    # Tạo một file CSV tạm chỉ có dòng header, không có dữ liệu
    header_only_csv = tmp_path / "header_only.csv"
    header_only_csv.write_text(
        "raw_record_id,source_listing_id,source_platform,"
        "suburb,weekly_rent,collected_at\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="no records found"):
        validate_csv(str(header_only_csv))