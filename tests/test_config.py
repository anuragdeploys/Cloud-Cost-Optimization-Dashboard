import os
from pathlib import Path

from app.config import (
    DEFAULT_DATABASE_FILE,
    get_aws_profile,
    get_aws_region,
    get_database_file,
)


def test_default_aws_profile(monkeypatch):
    monkeypatch.delenv("COST_AWS_PROFILE", raising=False)

    assert get_aws_profile() == "cost-dashboard"


def test_custom_aws_profile(monkeypatch):
    monkeypatch.setenv(
        "COST_AWS_PROFILE",
        "test-profile",
    )

    assert get_aws_profile() == "test-profile"


def test_default_aws_region(monkeypatch):
    monkeypatch.delenv("COST_AWS_REGION", raising=False)

    assert get_aws_region() == "us-east-1"


def test_custom_aws_region(monkeypatch):
    monkeypatch.setenv(
        "COST_AWS_REGION",
        "eu-west-1",
    )

    assert get_aws_region() == "eu-west-1"


def test_default_database_file(monkeypatch):
    monkeypatch.delenv(
        "COST_DATABASE_FILE",
        raising=False,
    )

    assert get_database_file() == DEFAULT_DATABASE_FILE


def test_custom_database_file(monkeypatch):
    monkeypatch.setenv(
        "COST_DATABASE_FILE",
        "/tmp/custom-costs.db",
    )

    assert get_database_file() == Path(
        "/tmp/custom-costs.db"
    )


def test_database_file_expands_home_directory(monkeypatch):
    monkeypatch.setenv(
        "COST_DATABASE_FILE",
        "~/custom-costs.db",
    )

    expected = Path("~/custom-costs.db").expanduser()

    assert get_database_file() == expected

def test_aws_collection_disabled_by_default(monkeypatch):
    monkeypatch.delenv(
        "ENABLE_AWS_COLLECTION",
        raising=False,
    )

    from app.config import is_aws_collection_enabled

    assert is_aws_collection_enabled() is False


def test_aws_collection_enabled_when_configured(monkeypatch):
    monkeypatch.setenv(
        "ENABLE_AWS_COLLECTION",
        "true",
    )

    from app.config import is_aws_collection_enabled

    assert is_aws_collection_enabled() is True    
