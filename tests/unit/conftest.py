"""Shared fixtures for unit tests."""

import pytest


@pytest.fixture
def mock_middleware(mocker):
    """Mock the MiddleWare client to avoid needing a live TrueNAS host."""
    mock_mw = mocker.MagicMock()
    mocker.patch(
        "ansible_collections.arensb.truenas.plugins.module_utils.middleware.MiddleWare.client",
        return_value=mock_mw,
    )
    return mock_mw
