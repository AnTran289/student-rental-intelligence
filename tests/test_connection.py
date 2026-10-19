from ingestion.snowflake_connection import get_snowflake_connection

def main():
    conn = get_snowflake_connection()

    try:
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE()")
            print(cursor.fetchone())
        finally:
            cursor.close()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
