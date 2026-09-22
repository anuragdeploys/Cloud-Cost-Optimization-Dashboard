import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_AWS_PROFILE = "cost-dashboard"
DEFAULT_AWS_REGION = "us-east-1"
DEFAULT_DATABASE_FILE = PROJECT_ROOT / "database" / "costs.db"


def get_aws_profile():
    """
    Return the AWS profile from the environment.

    Falls back to the project default when not configured.
    """
    return os.getenv(
        "COST_AWS_PROFILE",
        DEFAULT_AWS_PROFILE,
    )


def get_aws_region():
    """
    Return the AWS region from the environment.

    Falls back to the project default when not configured.
    """
    return os.getenv(
        "COST_AWS_REGION",
        DEFAULT_AWS_REGION,
    )


def get_database_file():
    """
    Return the SQLite database path from the environment.

    Falls back to the project default database path.
    """
    configured_path = os.getenv("COST_DATABASE_FILE")

    if configured_path:
        return Path(configured_path).expanduser()

    return DEFAULT_DATABASE_FILE

def is_aws_collection_enabled():
    """
    Return whether scheduled AWS collection is enabled.

    Collection is disabled by default to avoid unintended
    Cost Explorer API requests.
    """
    return os.getenv(
        "ENABLE_AWS_COLLECTION",
        "false",
    ).lower() == "true"
