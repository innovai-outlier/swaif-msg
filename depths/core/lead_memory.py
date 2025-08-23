"""Serviço de memória para conversas de leads.
Fornece funções para salvar conversas agrupadas na
memória e recuperar o histórico posteriormente.
"""

from __future__ import annotations

import sqlite3
from typing import Dict, List, Any, Union
from pathlib import Path
from dateutil.parser import parse as dateutil_parse

# Caminho do banco de dados utilizado pelo serviço.
# Deve ser ajustado pela camada que o utiliza.
DB_PATH: Union[str, Path, None] = None

# Armazena historico em memória durante a execução do processo.
_MEMORY: Dict[str, List[Dict[str, Any]]] = {}


def save_conversation(conversation_id: str) -> None:
    """Carrega mensagens da conversa e armazena em memória.

    A função usa o ``conversation_id`` para buscar as mensagens
    correspondentes no banco e mantém um cache por ``lead_phone``.
    """
    if not conversation_id:
        return

    # Garantir que o caminho do banco esteja configurado
    global DB_PATH
    if DB_PATH is None:
        try:
            from depths.core.database import SwaifDatabase

            DB_PATH = SwaifDatabase().db_path
        except Exception:
            return

    if DB_PATH is None:
        return

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        conv = conn.execute(
            """
            SELECT lead_phone, start_time, end_time
            FROM conversations_l2
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        ).fetchone()
        if not conv:
            return

        lead_phone = conv["lead_phone"]
        start_dt = dateutil_parse(conv["start_time"]) if conv["start_time"] else None
        end_dt = dateutil_parse(conv["end_time"]) if conv["end_time"] else None

        rows = conn.execute(
            """
            SELECT sender_phone, receiver_phone, content, timestamp
            FROM messages_l1
            WHERE sender_phone LIKE ? OR receiver_phone LIKE ?
            ORDER BY timestamp ASC
            """,
            (f"{lead_phone}%", f"{lead_phone}%"),
        ).fetchall()

        messages: List[Dict[str, Any]] = []
        for row in rows:
            msg_time = dateutil_parse(row["timestamp"]) if row["timestamp"] else None
            if start_dt and msg_time and msg_time < start_dt:
                continue
            if end_dt and msg_time and msg_time > end_dt:
                continue
            messages.append(dict(row))

        _MEMORY.setdefault(lead_phone, []).append(
            {"conversation_id": conversation_id, "messages": messages}
        )


def load_history(lead_phone: str) -> List[Dict[str, Any]]:
    """Retorna histórico de conversas de um lead."""
    return _MEMORY.get(lead_phone, [])
