#import pytest
from datetime import datetime, timedelta
from pathlib import Path
from depths.core.database import SwaifDatabase
from depths.layers.l2_grouper import L2Grouper

class TestL2Grouping:
    
    def setup_method(self):
        """Setup com banco in-memory para cada teste"""
        self.db = SwaifDatabase(":memory:")
        self.grouper = L2Grouper(self.db)

    def teardown_method(self):
        db_path = self.db.db_path
        self.db.cleanup()
        assert not Path(db_path).exists()
        
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
                "timestamp": "2025-01-14T10:00:00.000Z"
            },
            {
                "sender_raw_data": "5511999887766@s.whatsapp.net",
                "receiver_raw_data": "5511998681314@s.whatsapp.net",
                "sent_message": "Para amanhã seria possível?",
                "timestamp": "2025-01-14T10:05:00.000Z"
            },
            {
                "sender_raw_data": None,  # Resposta da secretária
                "receiver_raw_data": "5511999887766@s.whatsapp.net",
                "sent_message": "Sim, temos horário às 14h",
                "timestamp": "2025-01-14T10:10:00.000Z"
            }
        ]
        
        for msg in messages:
            self.db.insert_l1_message({
                "host_n8n": "test",
                "evo_api_instance_name": "test",
                "host_evoapi": "test",
                "sender_raw_data": msg["sender_raw_data"],
                "receiver_raw_data": msg["receiver_raw_data"],
                "message_type": "conversation",
                "sent_message": msg["sent_message"],
                "timestamp": msg["timestamp"]
            })
        
        # Act
        conversations = self.grouper.process_pending_messages()
        
        # Assert
        assert len(conversations) == 1
        assert conversations[0]["message_count"] == 3
        assert conversations[0]["lead_phone"] == "5511999887766"
        
    def test_separate_conversations_different_days(self):
        """Test: Deve separar conversas de dias diferentes"""
        # Arrange
        messages_day1 = {
            "sender_raw_data": "5511999887766@s.whatsapp.net",
            "timestamp": "2025-01-14T10:00:00.000Z",
            "sent_message": "Mensagem dia 14"
        }
        
        messages_day2 = {
            "sender_raw_data": "5511999887766@s.whatsapp.net", 
            "timestamp": "2025-01-15T10:00:00.000Z",
            "sent_message": "Mensagem dia 15"
        }
        
        # Inserir mensagens
        for msg in [messages_day1, messages_day2]:
            self.db.insert_l1_message({
                "host_n8n": "test",
                "evo_api_instance_name": "test",
                "host_evoapi": "test",
                "sender_raw_data": msg["sender_raw_data"],
                "receiver_raw_data": "5511998681314@s.whatsapp.net",
                "message_type": "conversation",
                "sent_message": msg["sent_message"],
                "timestamp": msg["timestamp"]
            })
        
        # Act
        conversations = self.grouper.process_pending_messages()
        
        # Assert
        assert len(conversations) == 2
        assert conversations[0]["conversation_id"] == "5511999887766_2025-01-14"
        assert conversations[1]["conversation_id"] == "5511999887766_2025-01-15"
        
    def test_identify_lead_and_secretary(self):
        """Test: Deve identificar corretamente lead e secretária"""
        # Act
        result = self.grouper.identify_participants(
            sender="5511999887766@s.whatsapp.net",
            receiver="5511998681314@s.whatsapp.net"
        )
        
        # Assert
        assert result["lead_phone"] == "5511999887766"
        assert result["secretary_phone"] == "5511998681314"
        assert result["sender_type"] == "lead"