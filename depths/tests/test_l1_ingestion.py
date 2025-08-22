import pytest
import json
import tempfile
from pathlib import Path
#from datetime import datetime
import sys
import os

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Sample data do seu json_test.json
SAMPLE_L1_JSON = [{
    "host_n8n": "host.docker.internal:5678",
    "evo_api_instance_name": "WAP_Diego-Menescal",
    "host_evoapi": "http://localhost:8080",
    "sender_raw_data": None,
    "receiver_raw_data": "5511998681314@s.whatsapp.net",
    "message_type": "conversation",
    "sent_message": "Teste",
    "timestamp": "2025-08-20T17:44:23.965Z"
}]

class TestL1Ingestion:
    
    def test_read_json_file(self):
        """Test: Deve ler arquivo JSON do N8N"""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(SAMPLE_L1_JSON, f)
            temp_path = f.name
        
        # Act
        from depths.layers.l1_ingestion import L1Ingestion
        ingestion = L1Ingestion()
        data = ingestion.read_json_file(temp_path)
        
        # Assert
        assert len(data) == 1
        assert data[0]["sent_message"] == "Teste"
        
        # Cleanup
        Path(temp_path).unlink()

    def test_read_json_file_missing(self):
        """Test: Deve retornar lista vazia para arquivo inexistente"""
        from depths.layers.l1_ingestion import L1Ingestion

        ingestion = L1Ingestion()
        data = ingestion.read_json_file("arquivo_que_nao_existe.json")
        assert data == []

    def test_read_json_file_malformed(self):
        """Test: Deve relançar erro para JSON malformado"""
        from depths.layers.l1_ingestion import L1Ingestion

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json}")
            temp_path = f.name

        ingestion = L1Ingestion()
        with pytest.raises(ValueError):
            ingestion.read_json_file(temp_path)

        Path(temp_path).unlink()
    
    def test_store_l1_to_database(self):
        """Test: Deve armazenar L1 no SQLite"""
        # Arrange
        from depths.core.database import SwaifDatabase
        from depths.layers.l1_ingestion import L1Ingestion
        
        db = SwaifDatabase(":memory:")  # In-memory for tests
        ingestion = L1Ingestion(database=db)
        
        try:
            # Act
            result = ingestion.process_l1_data(SAMPLE_L1_JSON[0])
            
            # Assert  
            assert result["status"] == "stored"
            assert result["message_id"] is not None
        finally:
            # Cleanup
            db.cleanup()
        
    def test_monitor_folder(self):
        """Test: Deve detectar novos arquivos JSON"""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            from depths.layers.l1_ingestion import L1Ingestion
            ingestion = L1Ingestion()
            
            # Act - criar arquivo após iniciar monitor
            test_file = Path(tmpdir) / "test_msg.json"
            test_file.write_text(json.dumps(SAMPLE_L1_JSON))

            detected_files = ingestion.scan_folder(tmpdir)

            # Assert
            assert len(detected_files) == 1
            assert "test_msg.json" in str(detected_files[0])
