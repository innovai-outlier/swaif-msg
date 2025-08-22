import pytest
import logging
import sqlite3
import builtins
from datetime import datetime, timedelta
from depths.core.database import SwaifDatabase
from depths.layers.l2_grouper import L2Grouper


class TestL2Grouping:
    def setup_method(self):
        """Setup com banco in-memory para cada teste"""
        self.db = SwaifDatabase(":memory:")
        self.grouper = L2Grouper(self.db)

    def teardown_method(self):
        self.db.cleanup()
        
    def test_identify_conversation_id(self):
        """Test: Deve gerar ID único para conversa (lead + data)"""
        # Arrange
        lead_phone = "5511999887766"
        timestamp = "2025-01-14T10:30:00.000Z"

        # Act
        conv_id = self.grouper.generate_conversation_id(lead_phone, timestamp)

        # Assert
        assert conv_id == "5511999887766_2025-01-14"

    def test_group_messages_same_day(self):
        """Test: Deve agrupar mensagens do mesmo lead no mesmo dia"""
        # Arrange - inserir mensagens L1
        messages = [
            {
                "sender_raw_data": "5511999887766@s.whatsapp.net",
                "receiver_raw_data": "5511998681314@s.whatsapp.net",
                "sent_message": "Olá, gostaria de agendar",
                "timestamp": "2025-01-14T10:00:00.000Z",
            },
            {
                "sender_raw_data": "5511999887766@s.whatsapp.net",
                "receiver_raw_data": "5511998681314@s.whatsapp.net",
                "sent_message": "Para amanhã seria possível?",
                "timestamp": "2025-01-14T10:05:00.000Z",
            },
            {
                "sender_raw_data": None,  # Resposta da secretária
                "receiver_raw_data": "5511999887766@s.whatsapp.net",
                "sent_message": "Sim, temos horário às 14h",
                "timestamp": "2025-01-14T10:10:00.000Z",
            },
        ]

        for msg in messages:
            self.db.insert_l1_message(
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

        # Act
        conversations = self.grouper.process_pending_messages()

        # Assert
        assert len(conversations) == 1
        assert conversations[0]["message_count"] == 3
        assert conversations[0]["lead_phone"] == "5511999887766"

        # Histórico deve conter as mensagens salvas
        history = self.db.get_conversation_history(conversations[0]["conversation_id"])
        assert len(history) == 3
        assert [m["content"] for m in history] == [
            "Olá, gostaria de agendar",
            "Para amanhã seria possível?",
            "Sim, temos horário às 14h",
        ]
        assert history[0]["sender_type"] == "lead"
        assert history[-1]["sender_type"] == "secretary"

    def test_separate_conversations_different_days(self):
        """Test: Deve separar conversas de dias diferentes"""
        # Arrange
        messages_day1 = {
            "sender_raw_data": "5511999887766@s.whatsapp.net",
            "timestamp": "2025-01-14T10:00:00.000Z",
            "sent_message": "Mensagem dia 14",
        }

        messages_day2 = {
            "sender_raw_data": "5511999887766@s.whatsapp.net",
            "timestamp": "2025-01-15T10:00:00.000Z",
            "sent_message": "Mensagem dia 15",
        }

        # Inserir mensagens
        for msg in [messages_day1, messages_day2]:
            self.db.insert_l1_message(
                {
                    "host_n8n": "test",
                    "evo_api_instance_name": "test",
                    "host_evoapi": "test",
                    "sender_raw_data": msg["sender_raw_data"],
                    "receiver_raw_data": "5511998681314@s.whatsapp.net",
                    "message_type": "conversation",
                    "sent_message": msg["sent_message"],
                    "timestamp": msg["timestamp"],
                }
            )

        # Act
        conversations = self.grouper.process_pending_messages()

        # Assert
        assert len(conversations) == 2
        assert (
            conversations[0]["conversation_id"] == "5511999887766_2025-01-14"
        )
        assert (
            conversations[1]["conversation_id"] == "5511999887766_2025-01-15"
        )

    def test_messages_across_midnight_within_tolerance(self):
        """Testa mensagens após a meia-noite dentro da tolerância"""

        messages = [
            {
                "sender_raw_data": "5511999887766@s.whatsapp.net",
                "receiver_raw_data": "5511998681314@s.whatsapp.net",
                "sent_message": "Mensagem antes da meia-noite",
                "timestamp": "2025-01-14T23:50:00.000Z",
            },
            {
                "sender_raw_data": "5511999887766@s.whatsapp.net",
                "receiver_raw_data": "5511998681314@s.whatsapp.net",
                "sent_message": "Mensagem após a meia-noite",
                "timestamp": "2025-01-15T00:30:00.000Z",
            },
        ]

        for msg in messages:
            self.db.insert_l1_message(
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

        conversations = self.grouper.process_pending_messages()

        assert len(conversations) == 1
        assert conversations[0]["conversation_id"] == "5511999887766_2025-01-14"
        assert conversations[0]["message_count"] == 2

    def test_identify_lead_and_secretary(self):
        """Test: Deve identificar corretamente lead e secretária"""
        # Act
        result = self.grouper.identify_participants(
            sender="5511999887766@s.whatsapp.net",
            receiver="5511998681314@s.whatsapp.net",
        )

        # Assert
        assert result["lead_phone"] == "5511999887766"
        assert result["secretary_phone"] == "5511998681314"
        assert result["sender_type"] == "lead"

    def test_custom_secretary_phone(self):
        """Test: Deve aceitar número de secretária customizado"""
        custom_phone = "551100000000"
        grouper = L2Grouper(self.db, secretary_phone=custom_phone)

        self.db.insert_l1_message(
            {
                "host_n8n": "test",
                "evo_api_instance_name": "test",
                "host_evoapi": "test",
                "sender_raw_data": None,
                "receiver_raw_data": "5511999887766@s.whatsapp.net",
                "message_type": "conversation",
                "sent_message": "Olá",
                "timestamp": "2025-01-14T10:00:00.000Z",
            }
        )

        conversations = grouper.process_pending_messages()

        assert len(conversations) == 1
        assert conversations[0]["secretary_phone"] == custom_phone
        assert conversations[0]["lead_phone"] == "5511999887766"
        assert conversations[0]["message_count"] == 1

    def test_mark_messages_processed_empty(self):
        """Test: Deve executar sem erro com lista vazia"""
        self.grouper._mark_messages_processed([])
        assert True

    def test_process_pending_messages_no_messages(self, caplog):
        """Test: Deve retornar lista vazia quando não há mensagens pendentes"""
        with caplog.at_level(logging.INFO):
            result = self.grouper.process_pending_messages()
        assert result == []
        assert "No pending messages to group" in caplog.text

    def test_clean_phone_empty(self):
        """Test: Deve limpar telefone vazio"""
        assert self.grouper._clean_phone(None) == ""

    def test_save_conversation_existing_updates(self):
        """Test: Deve atualizar conversa existente"""
        conv_data = {
            "conversation_id": "123_2025-01-14",
            "lead_phone": "123",
            "secretary_phone": "sec",
            "message_count": 1,
            "start_time": datetime(2025, 1, 14, 10, 0, 0),
            "end_time": datetime(2025, 1, 14, 10, 0, 0),
            "messages": [
                {
                    "sender_phone": "123@s.whatsapp.net",
                    "receiver_phone": "sec@s.whatsapp.net",
                    "content": "hi",
                    "timestamp": datetime(2025, 1, 14, 10, 0, 0),
                }
            ],
        }
        row_id = self.grouper._save_conversation(conv_data)
        assert row_id is not None

        conv_update = {
            "conversation_id": "123_2025-01-14",
            "lead_phone": "123",
            "secretary_phone": "sec",
            "message_count": 1,
            "start_time": datetime(2025, 1, 14, 10, 0, 0),
            "end_time": datetime(2025, 1, 14, 10, 10, 0),
            "messages": [
                {
                    "sender_phone": None,
                    "receiver_phone": "123@s.whatsapp.net",
                    "content": "reply",
                    "timestamp": datetime(2025, 1, 14, 10, 10, 0),
                }
            ],
        }
        row_id2 = self.grouper._save_conversation(conv_update)
        assert row_id2 == row_id

        with sqlite3.connect(self.db.db_path) as conn:
            data = conn.execute(
                "SELECT message_count, end_time FROM conversations_l2 WHERE conversation_id=?",
                ("123_2025-01-14",),
            ).fetchone()
        assert data[0] == 2
        assert data[1] == "2025-01-14T10:10:00"

        history = self.db.get_conversation_history("123_2025-01-14")
        assert len(history) == 2

    def test_save_conversation_handles_exception(self, monkeypatch):
        """Test: Deve retornar None se ocorrer erro ao salvar"""
        def fail_connect(*args, **kwargs):
            raise Exception("db error")
        monkeypatch.setattr(sqlite3, "connect", fail_connect)
        conv_data = {
            "conversation_id": "x",
            "lead_phone": "l",
            "secretary_phone": "s",
            "message_count": 0,
            "start_time": datetime.now(),
            "end_time": datetime.now(),
            "messages": [],
        }
        assert self.grouper._save_conversation(conv_data) is None

def test_generate_conversation_id_fallback(monkeypatch):
    """Test: Deve usar parse manual quando dateutil não estiver disponível"""
    real_import = builtins.__import__
    def fake_import(name, *args, **kwargs):
        if name == "dateutil.parser":
            raise ImportError
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", fake_import)
    grouper = L2Grouper()
    conv_id = grouper.generate_conversation_id("5511@s.whatsapp.net", "2025-01-14T10:30:00Z")
    assert conv_id == "5511_2025-01-14"
    Path(grouper.db.db_path).unlink(missing_ok=True)

def test_init_without_database():
    """Test: Instancia sem banco explícito"""
    grouper = L2Grouper()
    assert grouper.db is not None
    Path(grouper.db.db_path).unlink(missing_ok=True)
