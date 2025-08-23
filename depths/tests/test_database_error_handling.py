"""Tests for database error handling and edge cases."""

from depths.core.database import SwaifDatabase
import pytest


def test_insert_message_failure_handling(monkeypatch):
    """Test RuntimeError when cursor.lastrowid is None."""
    import sqlite3

    db = SwaifDatabase(":memory:")

    # Mock sqlite3.connect to return a connection with a cursor that has lastrowid=None
    original_connect = sqlite3.connect

    class MockCursor:
        def __init__(self):
            self.lastrowid = None

        def execute(self, *args, **kwargs):
            return self

    class MockConnection:
        def __init__(self, db_path):
            self.original_conn = original_connect(db_path)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.original_conn.close()

        def execute(self, *args, **kwargs):
            return MockCursor()

    def mock_connect(db_path):
        return MockConnection(db_path)

    monkeypatch.setattr(sqlite3, "connect", mock_connect)

    with pytest.raises(RuntimeError, match="Failed to insert message"):
        db.insert_l1_message(
            {
                "host_n8n": "test",
                "evo_api_instance_name": "test",
                "host_evoapi": "test",
                "sender_raw_data": "test",
                "receiver_raw_data": "test",
                "message_type": "test",
                "sent_message": "test",
                "timestamp": "test",
            }
        )

    db.cleanup()


def test_cleanup_file_not_found():
    """Test cleanup when temp file doesn't exist."""
    db = SwaifDatabase(":memory:")

    # Remove the file manually to simulate FileNotFoundError
    import os

    if db._temp_db:
        try:
            os.unlink(db._temp_db)
        except FileNotFoundError:
            pass

    # This should not raise an exception
    db.cleanup()


def test_cleanup_permission_error(monkeypatch):
    """Test cleanup when permission is denied."""
    db = SwaifDatabase(":memory:")

    def mock_unlink(path):
        raise PermissionError("Permission denied")

    monkeypatch.setattr("os.unlink", mock_unlink)

    # This should not raise an exception
    db.cleanup()
