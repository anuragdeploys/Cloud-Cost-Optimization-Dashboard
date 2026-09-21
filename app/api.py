from flask import Flask, jsonify, request

from app.cost_service import (
    get_cost_summary,
    get_stored_cost_records,
)
from app.database import initialize_database


def create_app(database_file=None):
    """
    Create and configure the Flask application.
    """
    app = Flask(__name__)

    initialize_database(
        database_file=database_file
    )

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
            }
        )

    @app.get("/costs")
    def costs():
        service = request.args.get("service")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        if (start_date is None) != (end_date is None):
            return jsonify(
                {
                    "error": (
                        "start_date and end_date "
                        "must be provided together."
                    )
                }
            ), 400

        records = get_stored_cost_records(
            service=service,
            start_date=start_date,
            end_date=end_date,
            database_file=database_file,
        )

        return jsonify(
            {
                "count": len(records),
                "records": records,
            }
        )

    @app.get("/costs/summary")
    def cost_summary():
        service = request.args.get("service")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        if (start_date is None) != (end_date is None):
            return jsonify(
                {
                    "error": (
                        "start_date and end_date "
                        "must be provided together."
                    )
                }
            ), 400

        try:
            result = get_cost_summary(
                service=service,
                start_date=start_date,
                end_date=end_date,
                database_file=database_file,
            )

        except ValueError as error:
            return jsonify(
                {
                    "error": str(error),
                }
            ), 400

        return jsonify(result)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
    )
