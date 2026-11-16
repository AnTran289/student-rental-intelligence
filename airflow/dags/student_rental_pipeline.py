from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from airflow.sdk import dag, get_current_context, task
from ingestion.input_validation import validate_csv
from ingestion.pipeline_validation import read_build_metadata, validate_batch

from run_ingestion import run_ingestion

import logging
import os
import subprocess

logger = logging.getLogger(__name__)


@dag(
    dag_id="student_rental_pipeline",
    start_date=datetime(2026, 11, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["student-rental", "data-engineering"],
)
def student_rental_pipeline():

    CSV_PATH = (
        "/opt/airflow/student-rental/"
        "tests/fixtures/e2e_postgres_test.csv"
    )

    @task
    def validate_input():
        record_count = validate_csv(csv_path=CSV_PATH)

        print(f"CSV validation passed: {record_count} records")


        return record_count

    """
    Ingest rental data from a CSV file into PostgreSQL.
    """
    @task(retries=1)
    def ingest_rentals():
        # Call run_ingestion() with recent CSV path
        summary = run_ingestion(CSV_PATH, include_batch_metadata=True)

        # Log numbers of records inserted and skipped
        logger.info(
            "Ingestion completed for %s | Inserted: %s | Skipped: %s",
            CSV_PATH,
            summary["inserted"],
            summary["skipped"],
        )

        # Return ingestion summary (Automatically update into XCom)
        return summary

    """
    Run dbt build to transform the ingested data."""
    @task(retries=1)
    def dbt_build():
        env = os.environ.copy()
        artifact_root = Path(env["DBT_TARGET_PATH"])
        artifact_root.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="airflow-build-", dir=artifact_root) as artifact_dir:
            env["DBT_TARGET_PATH"] = artifact_dir
            result = subprocess.run(
                [
                    "/opt/dbt-venv/bin/dbt",
                    "build",
                    "--project-dir", env["DBT_PROJECT_DIR"],
                    "--profiles-dir", env["DBT_PROFILES_DIR"],
                    "--target", "local",
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            for output, log in ((result.stdout, logger.info), (result.stderr, logger.warning)):
                if output:
                    for variable in ("RENTAL_DB_PASSWORD", "RENTAL_DB_USER"):
                        secret = env.get(variable)
                        if secret:
                            output = output.replace(secret, "[redacted]")
                    log("%s", output.rstrip())
            if result.returncode:
                raise RuntimeError(f"dbt build exited with code {result.returncode}")
            return read_build_metadata(
                Path(artifact_dir),
                run_id=get_current_context()["run_id"],
                host=env["RENTAL_DB_HOST"],
                port=env["RENTAL_DB_PORT"],
                database=env["RENTAL_DB_NAME"],
            )

    @task
    def validate_pipeline():
        context = get_current_context()
        ti = context["ti"]
        summary = validate_batch(
            ti.xcom_pull(task_ids="ingest_rentals"),
            ti.xcom_pull(task_ids="validate_input"),
            ti.xcom_pull(task_ids="dbt_build"),
            run_id=context["run_id"],
            user=os.environ["RENTAL_DB_USER"],
            password=os.environ["RENTAL_DB_PASSWORD"],
        )
        logger.info("Pipeline validation passed: %s", str(summary))
        return summary

    validation = validate_input()
    ingestion = ingest_rentals()
    transformation = dbt_build()
    pipeline_check = validate_pipeline()
    validation >> ingestion >> transformation >> pipeline_check


student_rental_pipeline()
