#!/usr/bin/env python3
"""Debug script for players_silver table creation."""

import sys
from pathlib import Path
import pandas as pd

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from etl.bronze_to_silver import make_players_silver
from etl.sqlite_sink import SQLiteSink

def main():
    """Debug players_silver table creation."""
    data_dir = project_root / "data"
    db_path = project_root / "db" / "pacers_analytics.db"
    
    # Load data
    print("Loading players data...")
    players_path = data_dir / "raw" / "players" / "2024_NBA_Players.parquet"
    players_df = pd.read_parquet(players_path)
    print(f"Loaded players: {len(players_df)} rows")
    print(f"Sample columns: {list(players_df.columns)[:10]}")
    
    # Load reference tables
    print("Loading reference tables...")
    sink = SQLiteSink(str(db_path))
    positions_silver = sink.execute_query("SELECT * FROM positions_silver")
    countries_silver = sink.execute_query("SELECT * FROM countries_silver") 
    affiliationtypes_silver = sink.execute_query("SELECT * FROM affiliationtypes_silver")
    
    print(f"Positions: {len(positions_silver)} rows")
    print(f"Countries: {len(countries_silver)} rows")
    print(f"Affiliations: {len(affiliationtypes_silver)} rows")
    
    # Try to create players_silver
    print("Creating players_silver...")
    try:
        players_silver = make_players_silver(
            players_df, 
            positions_silver, 
            countries_silver, 
            affiliationtypes_silver
        )
        print(f"✅ Created players_silver: {len(players_silver)} rows")
        print(f"Columns: {list(players_silver.columns)}")
        
        # Show sample data
        if len(players_silver) > 0:
            print("\nSample data:")
            print(players_silver.head(2).to_string())
            
    except Exception as e:
        print(f"❌ Error creating players_silver: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()