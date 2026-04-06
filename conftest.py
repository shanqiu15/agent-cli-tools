"""Root pytest configuration."""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--all",
        action="store_true",
        default=False,
        help="Run all tests including those requiring external services (e.g. Google Cloud Vision)",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--all"):
        return
    skip_external = pytest.mark.skip(reason="requires --all flag to run external service tests")
    for item in items:
        if "external" in item.keywords:
            item.add_marker(skip_external)
