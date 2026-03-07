"""Tests for the midclt module.

These tests focus on the pure utility methods that don't require
a live TrueNAS host or the 'midclt' command.
"""

import json
import subprocess
from unittest.mock import patch, MagicMock

import pytest


# We can't import Midclt directly at module level because its class body
# checks for the midclt binary via shutil.which(). We patch that check
# when we need to instantiate or test the class.


@pytest.fixture
def midclt_class():
    """Import and return the Midclt class with shutil.which patched."""
    with patch("shutil.which", return_value="/usr/bin/midclt"):
        from ansible_collections.arensb.truenas.plugins.module_utils.midclt import (
            Midclt,
        )
        yield Midclt


@pytest.fixture
def midclt_error_class():
    """Import and return the MidcltError class."""
    from ansible_collections.arensb.truenas.plugins.module_utils.midclt import (
        MidcltError,
    )
    return MidcltError


class TestMidcltToJson:
    """Tests for Midclt._to_json static method."""

    def test_parse_json_object(self, midclt_class):
        result = midclt_class._to_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_array(self, midclt_class):
        result = midclt_class._to_json('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_parse_json_string(self, midclt_class):
        result = midclt_class._to_json('"hello"')
        assert result == "hello"

    def test_parse_json_number(self, midclt_class):
        result = midclt_class._to_json("42")
        assert result == 42

    def test_parse_json_null(self, midclt_class):
        result = midclt_class._to_json("null")
        assert result is None

    def test_parse_true_string(self, midclt_class):
        """midclt sometimes prints 'True' (Python-style) instead of 'true' (JSON)."""
        result = midclt_class._to_json("True")
        assert result is True

    def test_parse_false_string(self, midclt_class):
        """midclt sometimes prints 'False' (Python-style) instead of 'false' (JSON)."""
        result = midclt_class._to_json("False")
        assert result is False

    def test_parse_bytes_input(self, midclt_class):
        result = midclt_class._to_json(b'{"key": "value"}')
        assert result == {"key": "value"}

    def test_strip_whitespace(self, midclt_class):
        result = midclt_class._to_json('  {"key": "value"}  \n')
        assert result == {"key": "value"}

    def test_invalid_json_raises(self, midclt_class):
        with pytest.raises(json.JSONDecodeError):
            midclt_class._to_json("not valid json")


class TestMidcltCall:
    """Tests for Midclt.call static method."""

    def test_simple_call(self, midclt_class):
        with patch("subprocess.check_output") as mock_sub:
            mock_sub.return_value = b'{"hostname": "truenas"}'
            result = midclt_class.call("network.configuration.config")

        mock_sub.assert_called_once_with(
            ["midclt", "call", "network.configuration.config"],
            stderr=subprocess.STDOUT,
        )
        assert result == {"hostname": "truenas"}

    def test_call_with_args(self, midclt_class):
        with patch("subprocess.check_output") as mock_sub:
            mock_sub.return_value = b'[{"username": "root"}]'
            result = midclt_class.call(
                "user.query",
                [["username", "=", "root"]],
            )

        args = mock_sub.call_args[0][0]
        assert args[0] == "midclt"
        assert args[1] == "call"
        assert args[2] == "user.query"
        # The filter arg should be JSON-encoded
        assert json.loads(args[3]) == [["username", "=", "root"]]

    def test_call_with_str_output(self, midclt_class):
        with patch("subprocess.check_output") as mock_sub:
            mock_sub.return_value = b"TrueNAS-SCALE-24.10\n"
            result = midclt_class.call("system.version", output="str")

        assert result == "TrueNAS-SCALE-24.10"

    def test_call_invalid_output_format(self, midclt_class):
        with patch("subprocess.check_output") as mock_sub:
            mock_sub.return_value = b"something"
            with pytest.raises(Exception, match="Invalid output format"):
                midclt_class.call("system.version", output="xml")

    def test_call_method_not_found(self, midclt_class):
        from ansible_collections.arensb.truenas.plugins.module_utils.exceptions import (
            MethodNotFoundError,
        )

        with patch("subprocess.check_output") as mock_sub:
            mock_sub.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["midclt", "call", "bogus.method"],
                output=b"[ENOMETHOD] Method bogus.method not found",
            )
            with pytest.raises(MethodNotFoundError):
                midclt_class.call("bogus.method")

    def test_call_generic_error(self, midclt_class):
        with patch("subprocess.check_output") as mock_sub:
            mock_sub.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["midclt", "call", "some.method"],
                output=b"Some other error",
            )
            with pytest.raises(Exception, match="exited with status 1"):
                midclt_class.call("some.method")


class TestMidcltError:
    def test_basic_error(self, midclt_error_class):
        err = midclt_error_class("something went wrong")
        assert err.value == "something went wrong"
        assert err.progress is None
        assert err.error is None
        assert err.exception is None

    def test_error_with_details(self, midclt_error_class):
        err = midclt_error_class(
            "fail",
            progress={"percent": 50},
            error="disk error",
            exception="traceback here",
        )
        assert err.progress == {"percent": 50}
        assert err.error == "disk error"
        assert err.exception == "traceback here"

    def test_str_representation(self, midclt_error_class):
        err = midclt_error_class("value", error="disk error")
        result = str(err)
        assert "disk error" in result
