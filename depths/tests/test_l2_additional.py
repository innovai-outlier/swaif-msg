import sqlite3
from datetime import datetime

from depths.core.database import SwaifDatabase
from depths.layers.l2_grouper import L2Grouper


class TestL2Additional:
    def setup_method(self):
        self.db = SwaifDatabase(":memory:")
        self.grouper = L2Grouper(self.db, tolerance_hours=1)

    def teardown_method(self):
        self.db.cleanup()

    def _insert(self, sender, receiver, content, ts):
        self.db.insert_l1_message(
            {
                "host_n8n": "t",
                "evo_api_instance_name": "t",
                "host_evoapi": "t",
                "sender_raw_data": sender,
                "receiver_raw_data": receiver,
                "message_type": "conversation",
                "sent_message": content,
                "timestamp": ts,
            }
        )

    def test_tolerance_same_conversation_within_1h(self):
        lead = "5511999887766@s.whatsapp.net"
        sec = "5511998681314@s.whatsapp.net"
        self._insert(lead, sec, "msg1", "2025-01-14T10:00:00Z")
        self._insert(lead, sec, "msg2", "2025-01-14T10:30:00Z")

        conversations = self.grouper.process_pending_messages()
        assert len(conversations) == 1
        assert conversations[0]["message_count"] == 2
        assert conversations[0]["conversation_id"] == "5511999887766_2025-01-14"

    def test_tolerance_new_conversation_over_1h(self):
        lead = "5511999887766@s.whatsapp.net"
        sec = "5511998681314@s.whatsapp.net"
        self._insert(lead, sec, "msg1", "2025-01-14T10:00:00Z")
        self._insert(lead, sec, "msg2", "2025-01-14T12:30:00Z")

        conversations = self.grouper.process_pending_messages()
        # two separate conversations (same date string but new conv id chosen on 2nd due to > tolerance)
        assert len(conversations) == 2
        ids = [c["conversation_id"] for c in conversations]
        assert ids.count("5511999887766_2025-01-14") >= 1

    def test_generate_conversation_id_accepts_datetime(self):
        conv_id = self.grouper.generate_conversation_id(
            "5511999887766@s.whatsapp.net", datetime(2025, 1, 14, 10, 0, 0)
        )
        assert conv_id == "5511999887766_2025-01-14"

    def test_clean_phone_group_chat(self):
        assert self.grouper._clean_phone("5511999887766@g.us") == "5511999887766"
