#!/usr/bin/env python3
"""
SWAIF-MSG Depths - Processamento Local
Monitora N8N output e processa L1, L2, L3
"""

import argparse
import sys
from pathlib import Path

# Add depths to path
sys.path.append(str(Path(__file__).parent.parent))

from depths.layers.l1_ingestion import L1Ingestion
from depths.core.terminal_display import TerminalDisplay

def main():
    parser = argparse.ArgumentParser(description="SWAIF-MSG Depths")
    parser.add_argument("--monitor", action="store_true", 
                       help="Monitor N8N folder continuously")
    parser.add_argument("--metrics", action="store_true",
                       help="Show L1 metrics")
    parser.add_argument("--test", action="store_true",
                       help="Test with json_test.json")
    
    args = parser.parse_args()
    
    if args.monitor:
        print("🚀 Starting SWAIF-MSG Depths Monitor...")
        ingestion = L1Ingestion()
        ingestion.monitor_continuous()
    
    elif args.metrics:
        display = TerminalDisplay()
        display.show_l1_metrics()
    
    elif args.test:
        # Testar com json_test.json
        ingestion = L1Ingestion()
        test_data = ingestion.read_json_file("docker/n8n/data/json_test.json")
        for msg in test_data:
            result = ingestion.process_l1_data(msg)
            print(f"Processed: {result}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()