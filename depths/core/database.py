import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json

class SwaifDatabase:
    """SQLite handler para as 3 camadas"""
    
    def __init__(self, db_path: str = "data/swaif_msg.db"):
        if db_path == ":memory:":
            # Para testes, usar um arquivo temporário em vez de :memory:
            # pois :memory: não persiste entre conexões
            import tempfile
            import os
            fd, self.db_path = tempfile.mkstemp(suffix='.db')
            os.close(fd)  # Fechar o file descriptor, usar apenas o path
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(exist_ok=True)
        self._init_tables()
    
    def cleanup(self):
        """Remove arquivo temporário (para testes)"""
        if hasattr(self, '_temp_db') and isinstance(self.db_path, str) and self.db_path.endswith('.db'):
            import os
            try:
                os.unlink(self.db_path)
            except (FileNotFoundError, PermissionError):
                pass
    
    def _init_tables(self):
        """Cria tabelas L1, L2, L3"""
        with sqlite3.connect(self.db_path) as conn:
            # L1 - Mensagens brutas do N8N
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages_l1 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    n8n_host TEXT,
                    evo_instance TEXT,
                    evo_host TEXT,
                    sender_phone TEXT,
                    receiver_phone TEXT,
                    message_type TEXT,
                    content TEXT,
                    timestamp DATETIME,
                    ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE
                )
            """)
            
            # L2 - Conversas agrupadas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations_l2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT UNIQUE,
                    lead_phone TEXT,
                    secretary_phone TEXT,
                    message_count INTEGER DEFAULT 0,
                    start_time DATETIME,
                    end_time DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # L3 - Análises IA
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analyses_l3 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    summary TEXT,
                    criteria JSON,
                    tasks JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) 
                        REFERENCES conversations_l2(conversation_id)
                )
            """)
            
            conn.commit()
    
    def insert_l1_message(self, data: Dict) -> int:
        """Insere mensagem L1 do N8N"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO messages_l1 
                (n8n_host, evo_instance, evo_host, sender_phone, 
                 receiver_phone, message_type, content, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("host_n8n"),
                data.get("evo_api_instance_name"),
                data.get("host_evoapi"),
                data.get("sender_raw_data"),
                data.get("receiver_raw_data"),
                data.get("message_type"),
                data.get("sent_message"),
                data.get("timestamp")
            ))
            return cursor.lastrowid