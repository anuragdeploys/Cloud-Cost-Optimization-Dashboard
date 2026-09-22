import sqlite3
from pathlib import Path


DATABASE_FILE = Path(__file__).parent.parent / "database" / "costs.db"


def get_connection(database_file=DATABASE_FILE):
    """Create and return a connection to the SQLite database."""
    return sqlite3.connect(database_file)


def initialize_database(database_file=DATABASE_FILE):
    """Create the cost_records table and uniqueness rule."""
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

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_cost_records_unique
            ON cost_records (
                date,
                service,
                amount,
                currency
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
    """Insert one cost record unless the exact record already exists."""
    connection = get_connection(database_file)

    try:
        connection.execute(
            """
            INSERT OR IGNORE INTO cost_records (
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


def insert_cost_records(
    records,
    currency="USD",
    database_file=DATABASE_FILE,
):
    """Insert multiple normalized cost records."""
    for record in records:
        insert_cost_record(
            date=record["date"],
            service=record["service"],
            amount=record["amount"],
            currency=currency,
            database_file=database_file,
        )


def get_cost_records(
    service=None,
    start_date=None,
    end_date=None,
    database_file=DATABASE_FILE,
):
    """
    Retrieve cost records with optional filters.

    end_date is exclusive, matching the AWS Cost Explorer convention.
    """
    connection = get_connection(database_file)

    try:
        query = """
            SELECT id, date, service, amount, currency
            FROM cost_records
        """

        conditions = []
        parameters = []

        if service is not None:
            conditions.append("service = ?")
            parameters.append(service)

        if start_date is not None:
            conditions.append("date >= ?")
            parameters.append(start_date)

        if end_date is not None:
            conditions.append("date < ?")
            parameters.append(end_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY date ASC, id ASC"

        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

        return [
            {
                "id": row[0],
                "date": row[1],
                "service": row[2],
                "amount": row[3],
                "currency": row[4],
            }
            for row in rows
        ]

    finally:
        connection.close()
