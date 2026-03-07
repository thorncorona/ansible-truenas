"""Tests for the exceptions module."""

import pytest
from ansible_collections.arensb.truenas.plugins.module_utils.exceptions import (
    MethodNotFoundError,
)


class TestMethodNotFoundError:
    def test_basic_creation(self):
        exc = MethodNotFoundError("system.bogus")
        assert exc.method == "system.bogus"
        assert exc.errmsg == ""

    def test_creation_with_message(self):
        exc = MethodNotFoundError("system.bogus", "Service not found")
        assert exc.method == "system.bogus"
        assert exc.errmsg == "Service not found"

    def test_str_representation(self):
        exc = MethodNotFoundError("system.bogus", "Service not found")
        result = str(exc)
        assert "system.bogus" in result
        assert "Service not found" in result

    def test_is_exception(self):
        exc = MethodNotFoundError("system.bogus")
        assert isinstance(exc, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(MethodNotFoundError) as exc_info:
            raise MethodNotFoundError("pool.query", "Method not available")
        assert exc_info.value.method == "pool.query"
