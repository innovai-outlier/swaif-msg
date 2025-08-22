import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import logging
from dateutil.parser import parse as dateutil_parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class L2Grouper:
    """Agrupa mensagens L1 em conversas L2"""
    
    def __init__(self, database=None):
        if database:
            self.db = database
        else:
            from depths.core.database import SwaifDatabase
            self.db = SwaifDatabase()
    
    def generate_conversation_id(self, lead_phone: str, timestamp: str) -> str:
        """Gera ID único: lead_phone + data"""
        # Parse timestamp para extrair data
        if isinstance(timestamp, str):
            # Usar python-dateutil que é mais robusto e compatível
            try:
                from dateutil.parser import parse as dateutil_parse
                dt = dateutil_parse(timestamp)
            except ImportError:
                # Fallback manual para formato ISO comum
                # Remove 'Z' e microsegundos se existir
                clean_timestamp = timestamp.replace('Z', '').split('.')[0]
                dt = datetime.strptime(clean_timestamp, '%Y-%m-%dT%H:%M:%S')
        else:
            dt = timestamp
            
        date_str = dt.strftime('%Y-%m-%d')
        
        # Limpar número do telefone
        clean_phone = lead_phone.replace('@s.whatsapp.net', '').strip()
        
        return f"{clean_phone}_{date_str}"
    
    def identify_participants(self, sender: Optional[str], receiver: str) -> Dict:
        """Identifica lead e secretária na conversa"""
        
        # Limpar números
        sender_clean = self._clean_phone(sender) if sender else None
        receiver_clean = self._clean_phone(receiver)
        
        # Lógica: se sender é None, é resposta da secretária
        if sender_clean is None:
            return {
                "lead_phone": receiver_clean,
                "secretary_phone": "clinic_secretary",  # Número da clínica
                "sender_type": "secretary"
            }
        else:
            return {
                "lead_phone": sender_clean,
                "secretary_phone": receiver_clean,
                "sender_type": "lead"
            }
    
    def _clean_phone(self, phone: str) -> str:
        """Limpa número de telefone"""
        if not phone:
            return ""
        return phone.replace('@s.whatsapp.net', '').replace('@g.us', '').strip()
    
    def process_pending_messages(self) -> List[Dict]:
        """Processa mensagens L1 não agrupadas"""
        
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Buscar mensagens não processadas
            cursor = conn.execute("""
                SELECT * FROM messages_l1 
                WHERE processed = FALSE
                ORDER BY timestamp ASC
            """)
            
            messages = cursor.fetchall()
            
        if not messages:
            logger.info("No pending messages to group")
            return []
        
        # Agrupar por conversa
        conversations = self._group_into_conversations(messages)
        
        # Salvar conversas L2
        saved_conversations = []
        for conv_data in conversations.values():
            conv_id = self._save_conversation(conv_data)
            if conv_id:
                saved_conversations.append(conv_data)
                
        # Marcar mensagens como processadas
        self._mark_messages_processed([m['id'] for m in messages])
        
        logger.info(f"✅ Grouped {len(messages)} messages into {len(saved_conversations)} conversations")
        
        return saved_conversations
    
    def _group_into_conversations(self, messages: List) -> Dict:
        """Agrupa mensagens em conversas"""
        conversations = defaultdict(lambda: {
            "messages": [],
            "message_count": 0,
            "start_time": None,
            "end_time": None
        })
        
        for msg in messages:
            # Identificar participantes
            participants = self.identify_participants(
                msg['sender_phone'],
                msg['receiver_phone']
            )
            
            # Parse do timestamp para comparação
            msg_time = msg['timestamp']
            if isinstance(msg_time, str):
                msg_time = dateutil_parse(msg_time)

            # Gerar ID da conversa
            conv_id = self.generate_conversation_id(
                participants['lead_phone'],
                msg_time
            )

            # Adicionar à conversa
            conv = conversations[conv_id]
            conv["conversation_id"] = conv_id
            conv["lead_phone"] = participants['lead_phone']
            conv["secretary_phone"] = participants['secretary_phone']
            conv["messages"].append(dict(msg))
            conv["message_count"] += 1

            # Atualizar timestamps
            if not conv["start_time"] or msg_time < conv["start_time"]:
                conv["start_time"] = msg_time
            if not conv["end_time"] or msg_time > conv["end_time"]:
                conv["end_time"] = msg_time
        
        return conversations
    
    def _save_conversation(self, conv_data: Dict) -> Optional[int]:
        """Salva conversa L2 no banco"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                # Converter timestamps para string
                start_time = conv_data["start_time"]
                end_time = conv_data["end_time"]
                if isinstance(start_time, datetime):
                    start_time = start_time.isoformat()
                if isinstance(end_time, datetime):
                    end_time = end_time.isoformat()

                # Verificar se conversa já existe
                existing = conn.execute(
                    "SELECT id FROM conversations_l2 WHERE conversation_id = ?",
                    (conv_data["conversation_id"],)
                ).fetchone()
                
                if existing:
                    # Atualizar conversa existente
                    conn.execute("""
                        UPDATE conversations_l2 
                        SET message_count = message_count + ?,
                            end_time = ?
                        WHERE conversation_id = ?
                    """, (
                        conv_data["message_count"],
                        end_time,
                        conv_data["conversation_id"]
                    ))
                    return existing[0]
                else:
                    # Inserir nova conversa
                    cursor = conn.execute("""
                        INSERT INTO conversations_l2 
                        (conversation_id, lead_phone, secretary_phone, 
                         message_count, start_time, end_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        conv_data["conversation_id"],
                        conv_data["lead_phone"],
                        conv_data["secretary_phone"],
                        conv_data["message_count"],
                        start_time,
                        end_time
                    ))
                    return cursor.lastrowid
                    
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return None
    
    def _mark_messages_processed(self, message_ids: List[int]):
        """Marca mensagens L1 como processadas"""
        with sqlite3.connect(self.db.db_path) as conn:
            placeholders = ','.join('?' * len(message_ids))
            conn.execute(
                f"UPDATE messages_l1 SET processed = TRUE WHERE id IN ({placeholders})",
                message_ids
            )