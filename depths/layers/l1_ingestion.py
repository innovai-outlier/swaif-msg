import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class L1Ingestion:
    """Monitora pasta N8N e ingere JSONs L1"""
    
    def __init__(self, database=None, watch_folder="docker/n8n/data"):
        self.watch_folder = Path(watch_folder)
        self.processed_files = set()
        
        if database:
            self.db = database
        else:
            from depths.core.database import SwaifDatabase
            self.db = SwaifDatabase()
    
    def read_json_file(self, filepath: str) -> List[Dict]:
        """Lê arquivo JSON do N8N"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            return []
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in {filepath}: {e}"
            logger.error(msg)
            raise ValueError(msg) from e
    
    def process_l1_data(self, message_data: Dict) -> Dict:
        """Processa e armazena mensagem L1"""
        try:
            message_id = self.db.insert_l1_message(message_data)
            logger.info(f"✅ L1 stored: ID {message_id}")
            return {
                "status": "stored",
                "message_id": message_id,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Error storing L1: {e}")
            return {"status": "error", "error": str(e)}
    
    def scan_folder(self, folder_path=None) -> List[Path]:
        """Escaneia pasta por novos JSONs"""
        folder = Path(folder_path or self.watch_folder)
        return list(folder.glob("*.json"))
    
    def monitor_continuous(self, interval=5):
        """Monitor contínuo da pasta N8N"""
        logger.info(f"👁️ Monitoring {self.watch_folder}")
        
        while True:
            try:
                json_files = self.scan_folder()
                
                for file_path in json_files:
                    if file_path not in self.processed_files:
                        logger.info(f"📄 New file: {file_path.name}")
                        
                        # Processar arquivo
                        messages = self.read_json_file(file_path)
                        for msg in messages:
                            self.process_l1_data(msg)
                        
                        self.processed_files.add(file_path)
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("⏹️ Monitor stopped")
                break
            except Exception as e:
                logger.error(f"Error in monitor: {e}")
                time.sleep(interval)
