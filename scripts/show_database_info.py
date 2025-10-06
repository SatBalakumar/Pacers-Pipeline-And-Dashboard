#!/usr/bin/env python3
"""
Show database information including tables, views, and row counts.
"""

import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.etl.sqlite_sink import SQLiteSink, create_database_summary


def main():
    """Show comprehensive database information."""
    db_path = project_root / "db" / "pacers_analytics.db"
    
    if not db_path.exists():
        print("Database not found. Run 'make build-all' first.")
        return
    
    try:
        # Create summary
        sink = SQLiteSink(str(db_path))
        summary = create_database_summary(sink)
        
        # Display information
        print(f"Database: {summary['database_path']}")
        print(f"Size: {summary['database_size_mb']} MB")
        print(f"Tables: {summary['total_tables']}")
        print(f"Views: {summary['total_views']}")
        print(f"Total Rows: {summary['total_rows']:,}")
        print()
        
        print("Table Row Counts:")
        for table, count in sorted(summary['tables'].items()):
            print(f"  {table}: {count:,}")
        
        print()
        print("Views:")
        for view in sorted(summary['views']):
            print(f"  {view}")
            
    except Exception as e:
        print(f"Error accessing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()