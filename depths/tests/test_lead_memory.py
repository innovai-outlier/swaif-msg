from depths.core import lead_memory
from depths.core.database import SwaifDatabase
from depths.layers.l2_grouper import L2Grouper
from depths.layers.l3_ai import L3AI


class TestLeadMemory:
    def setup_method(self):
        self.db = SwaifDatabase(":memory:")
        lead_memory.DB_PATH = self.db.db_path
        lead_memory._MEMORY.clear()
        self.grouper = L2Grouper(self.db)

    def teardown_method(self):
        self.db.cleanup()
        lead_memory._MEMORY.clear()

    def _insert_msg(self, sender, receiver, content, timestamp):
        self.db.insert_l1_message(
            {
                "host_n8n": "t",
                "evo_api_instance_name": "t",
                "host_evoapi": "t",
                "sender_raw_data": sender,
                "receiver_raw_data": receiver,
                "message_type": "conversation",
                "sent_message": content,
                "timestamp": timestamp,
            }
        )

    def test_save_and_load_history(self):
        self._insert_msg("5511999887766@s.whatsapp.net", "5511998681314@s.whatsapp.net", "Oi", "2025-01-14T10:00:00.000Z")
        self._insert_msg("5511999887766@s.whatsapp.net", "5511998681314@s.whatsapp.net", "Tudo bem?", "2025-01-14T10:05:00.000Z")
        self._insert_msg(None, "5511999887766@s.whatsapp.net", "Olá!", "2025-01-14T10:10:00.000Z")

        self.grouper.process_pending_messages()

        history = lead_memory.load_history("5511999887766")
        assert len(history) == 1
        assert len(history[0]["messages"]) == 3

        ai = L3AI()
        history_l3 = ai.get_history("5511999887766")
        assert history_l3 == history
