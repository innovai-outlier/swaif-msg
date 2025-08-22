#!/usr/bin/env python3
"""
SWAIF-MSG Depths - Processamento Local
Monitora N8N output e processa L1, L2, L3
"""

import argparse
import sys
import time
from pathlib import Path
import logging

# Add depths to path
sys.path.append(str(Path(__file__).parent.parent))

from depths.layers.l1_ingestion import L1Ingestion
from depths.layers.l2_grouper import L2Grouper
from depths.core.terminal_display import TerminalDisplay

logger = logging.getLogger(__name__)

def process_l2_batch():
    """Processa L2 em batch"""
    logger.info("🔄 Processing L2 - Grouping conversations...")
    
    grouper = L2Grouper()
    conversations = grouper.process_pending_messages()
    
    logger.info(f"✅ Grouped into {len(conversations)} conversations")
    
    for conv in conversations:
        logger.info(f"  📱 {conv['conversation_id']}: {conv['message_count']} messages")
    
    return conversations

def continuous_pipeline(interval=5):
    """Pipeline contínuo L1 -> L2"""
    logger.info("🚀 Starting continuous pipeline (L1 -> L2)...")
    
    ingestion = L1Ingestion()
    grouper = L2Grouper()
    display = TerminalDisplay()
    
    while True:
        try:
            # L1: Ingerir novos JSONs
            json_files = ingestion.scan_folder()
            new_messages = 0
            
            for file_path in json_files:
                if file_path not in ingestion.processed_files:
                    messages = ingestion.read_json_file(file_path)
                    for msg in messages:
                        ingestion.process_l1_data(msg)
                        new_messages += 1
                    ingestion.processed_files.add(file_path)
            
            if new_messages > 0:
                logger.info(f"📥 L1: Ingested {new_messages} new messages")
                
                # L2: Agrupar em conversas
                conversations = grouper.process_pending_messages()
                if conversations:
                    logger.info(f"🔗 L2: Created/updated {len(conversations)} conversations")
            
            # Exibir métricas
            logger.info("\n" + "-"*30)
            display.show_all_metrics()
            logger.info("-"*30 + "\n")
            
            time.sleep(interval)
            
        except KeyboardInterrupt:
            logger.info("\n⏹️ Pipeline stopped")
            break
        except Exception as e:
            logger.error(f"❌ Error in pipeline: {e}")
            time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description="SWAIF-MSG Depths")
    parser.add_argument("--monitor", action="store_true", 
                       help="Monitor N8N folder continuously (L1 only)")
    parser.add_argument("--pipeline", action="store_true",
                       help="Run full pipeline (L1 -> L2)")
    parser.add_argument("--process-l2", action="store_true",
                       help="Process L2 grouping once")
    parser.add_argument("--metrics", action="store_true",
                       help="Show all metrics")
    parser.add_argument("--test", action="store_true",
                       help="Test with json_test.json")
    
    args = parser.parse_args()
    
    if args.pipeline:
        continuous_pipeline()
    
    elif args.process_l2:
        process_l2_batch()
    
    elif args.monitor:
        logger.info("🚀 Starting L1 Monitor...")
        ingestion = L1Ingestion()
        ingestion.monitor_continuous()
    
    elif args.metrics:
        display = TerminalDisplay()
        display.show_all_metrics()
    
    elif args.test:
        # Testar pipeline completo com json_test.json
        logger.info("🧪 Testing full pipeline...")
        
        # L1
        ingestion = L1Ingestion()
        test_data = ingestion.read_json_file("docker/n8n/data/json_test.json")
        for msg in test_data:
            result = ingestion.process_l1_data(msg)
            logger.info(f"L1 Processed: {result}")
        
        # L2
        grouper = L2Grouper()
        conversations = grouper.process_pending_messages()
        logger.info(f"L2 Grouped: {len(conversations)} conversations")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()