import os


DEFAULT_AWS_PROFILE = "cost-dashboard"
DEFAULT_AWS_REGION = "us-east-1"


def get_aws_profile():
    """
    Return the AWS profile from the environment.

    Falls back to the project default when not configured.
    """
    return os.getenv("COST_AWS_PROFILE", DEFAULT_AWS_PROFILE)


def get_aws_region():
    """
    Return the AWS region from the environment.

    Falls back to the project default when not configured.
    """
    return os.getenv("COST_AWS_REGION", DEFAULT_AWS_REGION)
