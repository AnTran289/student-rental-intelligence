from datetime import datetime

from airflow.sdk import dag, task


@dag(
    dag_id="student_rental_smoke_test",
    start_date=datetime(2026, 11, 1),
    schedule=None,
    catchup=False,
    tags=["student-rental", "testing"],
)
def student_rental_smoke_test():

    # Define validate_input
    @task
    def validate_input():
        print(f"Input validated")
        return True

    # Define simulate_ingestion
    @task
    def simulate_ingestion(is_valid: bool):
        if not is_valid:
            raise ValueError("Input validation failed")
        print(f"Ingestion simulated")

    # Define confirm_pipeline
    @task
    def confirm_pipeline():
        print(f"Pipeline confirmed")

    # Set task dependencies
    validation_result = validate_input()
    ingestion_result = simulate_ingestion(validation_result)
    pipeline_confirmation = confirm_pipeline()
    ingestion_result >> pipeline_confirmation


student_rental_smoke_test()