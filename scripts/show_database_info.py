#!/usr/bin/env python3
"""
Show database information including tables, views, and row counts.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.etl.sqlite_sink import SQLiteSink, create_database_summary

# Configure logging
logs_dir = project_root / "logs"
logs_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = logs_dir / f"database_info_{timestamp}.log"

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
    """Show comprehensive database information."""
    db_path = project_root / "db" / "pacers_analytics.db"
    
    if not db_path.exists():
        logger.error("Database not found. Run 'make build-all' first.")
        return
    
    try:
        # Create summary
        sink = SQLiteSink(str(db_path))
        summary = create_database_summary(sink)
        
        # Display information
        logger.info(f"Database: {summary['database_path']}")
        logger.info(f"Size: {summary['database_size_mb']} MB")
        logger.info(f"Tables: {summary['total_tables']}")
        logger.info(f"Views: {summary['total_views']}")
        logger.info(f"Total Rows: {summary['total_rows']:,}")
        logger.info("")
        
        logger.info("Table Row Counts:")
        for table, count in sorted(summary['tables'].items()):
            logger.info(f"  {table}: {count:,}")
        
        logger.info("")
        logger.info("Views:")
        for view in sorted(summary['views']):
            logger.info(f"  {view}")
            
    except Exception as e:
        logger.error(f"Error accessing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()