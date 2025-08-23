import sqlite3
from pathlib import Path
from typing import Dict, List, Union


class SwaifDatabase:
    """SQLite handler para as 3 camadas"""

    def __init__(self, db_path: str = "data/swaif_msg.db"):
        self._temp_db: Union[str, None] = None
        self.db_path: Union[str, Path]
        if db_path == ":memory:":
            # Para testes, usar um arquivo temporário em vez de :memory:
            # pois :memory: não persiste entre conexões
            import tempfile
            import os

            fd, temp_path = tempfile.mkstemp(suffix=".db")
            os.close(fd)  # Fechar o file descriptor, usar apenas o path
            self.db_path = temp_path
            self._temp_db = temp_path  # Guardar o caminho para cleanup
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(exist_ok=True)
        self._init_tables()

    def cleanup(self):
        """Remove arquivo temporário (para testes)"""
        if self._temp_db:
            import os

            try:
                os.unlink(self._temp_db)
            except (FileNotFoundError, PermissionError):
                pass

    def _init_tables(self):
        """Cria tabelas L1, L2, L3"""
        with sqlite3.connect(self.db_path) as conn:
            # L1 - Mensagens brutas do N8N
            conn.execute(
                """
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
            """
            )

            # L2 - Conversas agrupadas
            conn.execute(
                """
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
            """
            )

            # Histórico das mensagens por conversa
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    sender_type TEXT,
                    content TEXT,
                    timestamp DATETIME,
                    FOREIGN KEY (conversation_id)
                        REFERENCES conversations_l2(conversation_id)
                )
            """
            )

            # Atividade por lead
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS lead_activity (
                    lead_phone TEXT PRIMARY KEY,
                    last_activity DATETIME,
                    conversation_id TEXT
                )
            """
            )

            # L3 - Análises IA
            conn.execute(
                """
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
            """
            )

            conn.commit()

    def insert_l1_message(self, data: Dict) -> int:
        """Insere mensagem L1 do N8N"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO messages_l1
                (n8n_host, evo_instance, evo_host, sender_phone,
                 receiver_phone, message_type, content, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data.get("host_n8n"),
                    data.get("evo_api_instance_name"),
                    data.get("host_evoapi"),
                    data.get("sender_raw_data"),
                    data.get("receiver_raw_data"),
                    data.get("message_type"),
                    data.get("sent_message"),
                    data.get("timestamp"),
                ),
            )
            row_id = cursor.lastrowid
            if row_id is None:
                raise RuntimeError("Failed to insert message")
            return row_id

    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Recupera o histórico de mensagens de uma conversa"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT sender_type, content, timestamp
                FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
                """,
                (conversation_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
