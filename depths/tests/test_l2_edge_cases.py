"""Tests for l2_grouper dateutil import fallback."""

from depths.layers.l2_grouper import L2Grouper
from depths.core.database import SwaifDatabase
import builtins


def test_generate_conversation_id_import_error():
    """Test generate_conversation_id when dateutil import fails."""
    db = SwaifDatabase(":memory:")
    grouper = L2Grouper(db)

    # Mock the import to fail
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if "dateutil" in name:
            raise ImportError("No module named 'dateutil'")
        return original_import(name, *args, **kwargs)

    builtins.__import__ = mock_import

    try:
        # This should use the fallback manual parsing
        result = grouper.generate_conversation_id(
            "5511999887766@s.whatsapp.net", "2025-01-14T10:30:00.000Z"
        )
        assert result == "5511999887766_2025-01-14"
    finally:
        builtins.__import__ = original_import
        db.cleanup()


def test_generate_conversation_id_already_datetime():
    """Test generate_conversation_id when timestamp is already datetime."""
    from datetime import datetime

    db = SwaifDatabase(":memory:")
    grouper = L2Grouper(db)

    dt = datetime(2025, 1, 14, 10, 30, 0)
    result = grouper.generate_conversation_id("5511999887766@s.whatsapp.net", dt)
    assert result == "5511999887766_2025-01-14"

    db.cleanup()
