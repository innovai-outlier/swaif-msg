import sqlite3
from depths.core.database import SwaifDatabase
from depths.layers.l2_grouper import L2Grouper


def test_get_conversation_history_empty_returns_empty_list():
    db = SwaifDatabase(":memory:")
    assert db.get_conversation_history("nonexistent") == []
    db.cleanup()


def test_conversation_history_persistence_and_message_processing(tmp_path):
    db_file = tmp_path / "test.db"
    db = SwaifDatabase(str(db_file))
    grouper = L2Grouper(db)

    messages = [
        {
            "sender_raw_data": "5511999887766@s.whatsapp.net",
            "receiver_raw_data": "5511998681314@s.whatsapp.net",
            "sent_message": "Oi",
            "timestamp": "2025-01-14T10:00:00.000Z",
        },
        {
            "sender_raw_data": None,
            "receiver_raw_data": "5511999887766@s.whatsapp.net",
            "sent_message": "Olá",
            "timestamp": "2025-01-14T10:05:00.000Z",
        },
    ]

    for msg in messages:
        db.insert_l1_message(
            {
                "host_n8n": "test",
                "evo_api_instance_name": "test",
                "host_evoapi": "test",
                "sender_raw_data": msg["sender_raw_data"],
                "receiver_raw_data": msg["receiver_raw_data"],
                "message_type": "conversation",
                "sent_message": msg["sent_message"],
                "timestamp": msg["timestamp"],
            }
        )

    conversations = grouper.process_pending_messages()
    conv_id = conversations[0]["conversation_id"]

    db2 = SwaifDatabase(str(db_file))
    history = db2.get_conversation_history(conv_id)
    assert [m["content"] for m in history] == ["Oi", "Olá"]
    assert history[0]["sender_type"] == "lead"
    assert history[1]["sender_type"] == "secretary"

    with sqlite3.connect(db_file) as conn:
        processed = [
            row[0] for row in conn.execute("SELECT processed FROM messages_l1")
        ]
        assert all(processed)

    db.cleanup()
    db2.cleanup()
