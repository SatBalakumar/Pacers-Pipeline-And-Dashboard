#!/usr/bin/env python3
"""
Run complete ETL pipeline: Bronze → Silver → Gold
All console output will be logged to timestamped files in logs/ directory.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logs_dir = project_root / "logs"
logs_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = logs_dir / f"etl_pipeline_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also output to console
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run the complete ETL pipeline."""
    try:
        logger.info("🚀 Starting ETL Pipeline")
        logger.info(f"📝 Logs will be saved to: {log_file}")
        
        # Import and run Silver ETL
        logger.info("📊 Building Silver tables...")
        from scripts.build_silver import main as build_silver
        build_silver()
        
        # Import and run Gold ETL  
        logger.info("🏆 Building Gold tables...")
        from scripts.build_gold import main as build_gold
        build_gold()
        
        logger.info("✅ ETL Pipeline completed successfully!")
        logger.info(f"📝 Full logs saved to: {log_file}")
        
    except Exception as e:
        logger.error(f"❌ ETL Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()