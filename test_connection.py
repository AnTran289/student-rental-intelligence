"""Run the Snowflake connection check from the project root."""

import runpy
from pathlib import Path


if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).resolve().parent / "tests" / "test_connection.py"),
        run_name="__main__",
    )
