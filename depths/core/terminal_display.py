from typing import Dict
import sqlite3
from datetime import datetime

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
            
        print("\n" + "="*50)
        print("📊 SWAIF-MSG L1 METRICS")
        print("="*50)
        print(f"Total messages: {total}")
        print(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        
        if recent:
            print("\n📱 Recent messages:")
            for i, (sender, receiver, content, ts) in enumerate(recent, 1):
                print(f"  {i}. {sender or 'Unknown'} → {receiver}")
                print(f"     💬 {content[:50]}...")
                print(f"     ⏰ {ts}\n")
        
        if total > 3:
            print(f"... and {total - 3} more messages")
        print("="*50)
        
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
            
        print("\n" + "="*50)
        print("📊 SWAIF-MSG L2 METRICS - CONVERSATIONS")
        print("="*50)
        print(f"Total conversations: {total_conv}")
        print(f"Conversations today: {today_conv}")
        print(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        
        if top_leads:
            print("\n🏆 Top Leads (by message volume):")
            for i, (phone, convs, msgs) in enumerate(top_leads, 1):
                print(f"  {i}. {phone}")
                print(f"     📱 {convs} conversations")
                print(f"     💬 {msgs} total messages\n")
        
        print("="*50)
    
    def show_all_metrics(self):
        """Mostra todas as métricas (L1 + L2)"""
        self.show_l1_metrics()
        print("")  # Espaço entre métricas
        self.show_l2_metrics()