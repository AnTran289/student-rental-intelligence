import os

import psycopg


def get_postgres_connection():
    """
    Create a PostgreSQL connection.

    Defaults to the local Student Rental database.
    Database name can be overridden for testing.
    """
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5433")),
        dbname=os.getenv("POSTGRES_DB", "student_rental_db"),
        user=os.getenv("POSTGRES_USER", "rental_admin"),
        password=os.environ["POSTGRES_PASSWORD"],
        autocommit=False,
    )
