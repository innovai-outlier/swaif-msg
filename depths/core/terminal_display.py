from typing import Dict
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TerminalDisplay:
    """Exibe métricas no terminal"""
    
    def __init__(self, db_path="data/swaif_msg.db"):
        self.db_path = db_path
    
    def show_l1_metrics(self):
        """Mostra métricas L1"""
        with sqlite3.connect(self.db_path) as conn:
            # Total mensagens
            total = conn.execute(
                "SELECT COUNT(*) FROM messages_l1"
            ).fetchone()[0]
            
            # Últimas 3 mensagens
            recent = conn.execute("""
                SELECT sender_phone, receiver_phone, content, timestamp
                FROM messages_l1
                ORDER BY ingested_at DESC
                LIMIT 3
            """).fetchall()
            
        logger.info("\n" + "="*50)
        logger.info("📊 SWAIF-MSG L1 METRICS")
        logger.info("="*50)
        logger.info(f"Total messages: {total}")
        logger.info(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        
        if recent:
            logger.info("\n📱 Recent messages:")
            for i, (sender, receiver, content, ts) in enumerate(recent, 1):
                logger.info(f"  {i}. {sender or 'Unknown'} → {receiver}")
                logger.info(f"     💬 {content[:50]}...")
                logger.info(f"     ⏰ {ts}\n")
        
        if total > 3:
            logger.info(f"... and {total - 3} more messages")
        logger.info("="*50)
        
    def show_l2_metrics(self):
        """Mostra métricas L2 - Conversas"""
        with sqlite3.connect(self.db_path) as conn:
            # Total conversas
            total_conv = conn.execute(
                "SELECT COUNT(*) FROM conversations_l2"
            ).fetchone()[0]
            
            # Conversas hoje
            today = datetime.now().strftime('%Y-%m-%d')
            today_conv = conn.execute(
                "SELECT COUNT(*) FROM conversations_l2 WHERE date(start_time) = ?",
                (today,)
            ).fetchone()[0]
            
            # Top leads (mais mensagens)
            top_leads = conn.execute("""
                SELECT lead_phone, COUNT(*) as conv_count, 
                       SUM(message_count) as total_messages
                FROM conversations_l2
                GROUP BY lead_phone
                ORDER BY total_messages DESC
                LIMIT 3
            """).fetchall()
            
        logger.info("\n" + "="*50)
        logger.info("📊 SWAIF-MSG L2 METRICS - CONVERSATIONS")
        logger.info("="*50)
        logger.info(f"Total conversations: {total_conv}")
        logger.info(f"Conversations today: {today_conv}")
        logger.info(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        
        if top_leads:
            logger.info("\n🏆 Top Leads (by message volume):")
            for i, (phone, convs, msgs) in enumerate(top_leads, 1):
                logger.info(f"  {i}. {phone}")
                logger.info(f"     📱 {convs} conversations")
                logger.info(f"     💬 {msgs} total messages\n")

        logger.info("="*50)
    
    def show_all_metrics(self):
        """Mostra todas as métricas (L1 + L2)"""
        self.show_l1_metrics()
        print("")  # Espaço entre métricas
        self.show_l2_metrics()
