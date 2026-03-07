"""Tests for the setup module.

These tests mock the middleware calls since we can't connect to a real
TrueNAS host in CI.
"""

import re
from unittest.mock import patch, MagicMock

import pytest
from packaging import version


class TestGetTnVersion:
    """Test version detection and parsing logic."""

    def _make_mock_mw(self, mocker, product_type, full_version, product_name=None):
        """Create a mock middleware client with canned responses."""
        mock_mw = MagicMock()

        def mock_call(method, *args, **kwargs):
            if method == "system.product_type":
                return product_type
            elif method == "system.version":
                return full_version
            elif method == "system.product_name":
                if product_name is not None:
                    return product_name
                raise Exception("Not available")
            raise Exception(f"Unexpected call: {method}")

        mock_mw.call = mock_call
        return mock_mw

    def test_parse_scale_version(self, mocker):
        """Test parsing a TrueNAS SCALE version string."""
        import ansible_collections.arensb.truenas.plugins.module_utils.setup as setup_mod
        setup_mod.tn_version = None  # Reset memoization

        mock_mw = self._make_mock_mw(
            mocker, "SCALE", "TrueNAS-SCALE-24.10.0"
        )
        mocker.patch(
            "ansible_collections.arensb.truenas.plugins.module_utils.middleware.MiddleWare.client",
            return_value=mock_mw,
        )

        result = setup_mod.get_tn_version()
        assert result["name"] == "TrueNAS"
        assert result["type"] == "SCALE"
        assert result["version"] == version.parse("24.10.0")

    def test_parse_core_version(self, mocker):
        """Test parsing a TrueNAS CORE version string.

        Note: CORE version strings like '13.0-U5' are not PEP 440 compliant,
        so packaging.version.parse() raises InvalidVersion. This test documents
        that known behavior.
        """
        from packaging.version import InvalidVersion
        import ansible_collections.arensb.truenas.plugins.module_utils.setup as setup_mod
        setup_mod.tn_version = None

        mock_mw = self._make_mock_mw(
            mocker, "CORE", "TrueNAS-13.0-U5", product_name="TrueNAS"
        )
        mocker.patch(
            "ansible_collections.arensb.truenas.plugins.module_utils.middleware.MiddleWare.client",
            return_value=mock_mw,
        )

        with pytest.raises(InvalidVersion):
            setup_mod.get_tn_version()

        # Clean up memoization
        setup_mod.tn_version = None

    def test_parse_core_numeric_version(self, mocker):
        """Test parsing a TrueNAS CORE version with a PEP 440-compatible string."""
        import ansible_collections.arensb.truenas.plugins.module_utils.setup as setup_mod
        setup_mod.tn_version = None

        mock_mw = self._make_mock_mw(
            mocker, "CORE", "TrueNAS-13.0.5", product_name="TrueNAS"
        )
        mocker.patch(
            "ansible_collections.arensb.truenas.plugins.module_utils.middleware.MiddleWare.client",
            return_value=mock_mw,
        )

        result = setup_mod.get_tn_version()
        assert result["name"] == "TrueNAS"
        assert result["type"] == "CORE"
        assert result["version"] == version.parse("13.0.5")

    def test_memoization(self, mocker):
        """Test that get_tn_version returns cached data on subsequent calls."""
        import ansible_collections.arensb.truenas.plugins.module_utils.setup as setup_mod

        cached = {
            "name": "TrueNAS",
            "type": "SCALE",
            "version": version.parse("24.10.0"),
        }
        setup_mod.tn_version = cached

        result = setup_mod.get_tn_version()
        assert result is cached

        # Clean up
        setup_mod.tn_version = None

    def test_version_regex_pattern(self):
        """Test the regex used to parse version strings independently."""
        pattern = r'^(?:(\w+)-)(?:(\w+)-)?(\d.*)'

        # SCALE format
        match = re.match(pattern, "TrueNAS-SCALE-24.10.0")
        assert match[1] == "TrueNAS"
        assert match[2] == "SCALE"
        assert match[3] == "24.10.0"

        # CORE format
        match = re.match(pattern, "TrueNAS-13.0-U5")
        assert match[1] == "TrueNAS"
        assert match[2] is None
        assert match[3] == "13.0-U5"

    def test_version_comparison(self):
        """Test that parsed versions compare correctly."""
        v1 = version.parse("24.04.0")
        v2 = version.parse("24.10.0")
        v3 = version.parse("25.04.0")

        assert v1 < v2 < v3
        assert v2 > v1
