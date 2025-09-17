from depths.core import lead_memory
from depths.core.database import SwaifDatabase
from depths.layers.l1_ingestion import L1Ingestion
from depths.layers.l2_grouper import L2Grouper
from depths.layers.l3_ai import L3AI


def test_end_to_end_pipeline():
    db = SwaifDatabase(":memory:")
    try:
        lead_memory.DB_PATH = db.db_path
        lead_memory._MEMORY.clear()

        l1 = L1Ingestion(database=db)
        l2 = L2Grouper(database=db)
        l3 = L3AI()

        msgs = [
            {
                "host_n8n": "t",
                "evo_api_instance_name": "t",
                "host_evoapi": "t",
                "sender_raw_data": "5511999887766@s.whatsapp.net",
                "receiver_raw_data": "5511998681314@s.whatsapp.net",
                "message_type": "conversation",
                "sent_message": "Oi",
                "timestamp": "2025-01-14T10:00:00.000Z",
            },
            {
                "host_n8n": "t",
                "evo_api_instance_name": "t",
                "host_evoapi": "t",
                "sender_raw_data": None,
                "receiver_raw_data": "5511999887766@s.whatsapp.net",
                "message_type": "conversation",
                "sent_message": "Olá!",
                "timestamp": "2025-01-14T10:05:00.000Z",
            },
        ]

        for m in msgs:
            assert l1.process_l1_data(m)["status"] == "stored"

        conversations = l2.process_pending_messages()
        assert len(conversations) == 1
        conv_id = conversations[0]["conversation_id"]

        history = l3.get_history("5511999887766")
        assert history
        assert history[0]["conversation_id"] == conv_id
        assert [m["content"] for m in history[0]["messages"]] == ["Oi", "Olá!"]
    finally:
        db.cleanup()
