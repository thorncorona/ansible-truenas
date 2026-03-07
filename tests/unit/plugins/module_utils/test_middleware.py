"""Tests for the middleware module."""

from unittest.mock import patch, MagicMock

import pytest


class TestMiddleWarePickMethod:
    """Test that MiddleWare._pick_method selects the right backend."""

    def test_default_is_midclt(self):
        """With no env var set, the default method should be midclt."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("shutil.which", return_value="/usr/bin/midclt"):
                from ansible_collections.arensb.truenas.plugins.module_utils.middleware import (
                    MiddleWare,
                )
                # Remove any cached module state
                result = MiddleWare._pick_method()
                from ansible_collections.arensb.truenas.plugins.module_utils.midclt import Midclt
                assert result is Midclt

    def test_midclt_method_explicit(self):
        """Explicitly choosing midclt method."""
        with patch.dict("os.environ", {"middleware_method": "midclt"}):
            with patch("shutil.which", return_value="/usr/bin/midclt"):
                from ansible_collections.arensb.truenas.plugins.module_utils.middleware import (
                    MiddleWare,
                )
                result = MiddleWare._pick_method()
                from ansible_collections.arensb.truenas.plugins.module_utils.midclt import Midclt
                assert result is Midclt

    def test_unknown_method_raises(self):
        """Using an unknown method should raise an exception."""
        with patch.dict("os.environ", {"middleware_method": "bogus"}):
            from ansible_collections.arensb.truenas.plugins.module_utils.middleware import (
                MiddleWare,
            )
            with pytest.raises(Exception, match="Unknown middleware method"):
                MiddleWare._pick_method()
