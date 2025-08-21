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