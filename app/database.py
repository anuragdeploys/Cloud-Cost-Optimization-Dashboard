import sqlite3
from pathlib import Path


DATABASE_FILE = Path(__file__).parent.parent / "database" / "costs.db"


def get_connection(database_file=DATABASE_FILE):
    """Create and return a connection to the SQLite database."""
    connection = sqlite3.connect(database_file)
    return connection


def initialize_database(database_file=DATABASE_FILE):
    """Create the cost_records table if it does not already exist."""
    connection = get_connection(database_file)

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cost_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                service TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


def insert_cost_record(
    date,
    service,
    amount,
    currency,
    database_file=DATABASE_FILE,
):
    """Insert one cost record into the database."""
    connection = get_connection(database_file)

    try:
        connection.execute(
            """
            INSERT INTO cost_records (
                date,
                service,
                amount,
                currency
            )
            VALUES (?, ?, ?, ?)
            """,
            (date, service, amount, currency),
        )

        connection.commit()

    finally:
        connection.close()
