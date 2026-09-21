from flask import Flask, jsonify, render_template, request

from app.aws_cost_collector import validate_date_range
from app.cost_service import (
    get_cost_insights,
    get_cost_summary,
    get_stored_cost_records,
)
from app.database import DATABASE_FILE, initialize_database


def create_app(database_file=None):
    """
    Create and configure the Flask application.
    """
    effective_database_file = (
        DATABASE_FILE
        if database_file is None
        else database_file
    )

    initialize_database(
        database_file=effective_database_file
    )

    app = Flask(__name__)

    def validate_request_dates(start_date, end_date):
        """
        Validate optional API date parameters.
        """
        if (start_date is None) != (end_date is None):
            return (
                "start_date and end_date "
                "must be provided together."
            )

        if start_date is not None and end_date is not None:
            try:
                validate_date_range(
                    start_date,
                    end_date,
                )
            except ValueError as error:
                return str(error)

        return None

    @app.get("/")
    def dashboard():
        return render_template("index.html")

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

        date_error = validate_request_dates(
            start_date,
            end_date,
        )

        if date_error:
            return jsonify(
                {
                    "error": date_error,
                }
            ), 400

        records = get_stored_cost_records(
            service=service,
            start_date=start_date,
            end_date=end_date,
            database_file=effective_database_file,
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

        date_error = validate_request_dates(
            start_date,
            end_date,
        )

        if date_error:
            return jsonify(
                {
                    "error": date_error,
                }
            ), 400

        result = get_cost_summary(
            service=service,
            start_date=start_date,
            end_date=end_date,
            database_file=effective_database_file,
        )

        return jsonify(result)

    @app.get("/costs/insights")
    def cost_insights():
        service = request.args.get("service")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        date_error = validate_request_dates(
            start_date,
            end_date,
        )

        if date_error:
            return jsonify(
                {
                    "error": date_error,
                }
            ), 400

        result = get_cost_insights(
            service=service,
            start_date=start_date,
            end_date=end_date,
            database_file=effective_database_file,
        )

        return jsonify(result)

    return app


if __name__ == "__main__":
    app = create_app()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
    )
