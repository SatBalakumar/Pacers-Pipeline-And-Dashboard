#!/usr/bin/env python3
"""Debug script to identify exact conversion errors."""

import pandas as pd
import sys
from pathlib import Path
import traceback

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def debug_players_error():
    """Debug players_silver conversion error."""
    print("🔍 DEBUGGING PLAYERS_SILVER ERROR")
    print("=" * 50)
    
    try:
        from etl.bronze_to_silver import make_players_silver
        from etl.seed_codes import build_positions_silver, build_countries_silver, build_affiliationtypes_silver
        
        # Load players data
        players_df = pd.read_parquet('data/raw/players/2024_NBA_Players.parquet')
        print(f"✅ Loaded players data: {len(players_df)} rows")
        
        # Build seed tables
        positions_silver = build_positions_silver(players_df)
        countries_silver = build_countries_silver(players_df)
        affiliationtypes_silver = build_affiliationtypes_silver(players_df)
        
        # Try to build players_silver
        players_silver = make_players_silver(
            players_df,
            positions_silver,
            countries_silver,
            affiliationtypes_silver,
            pd.DataFrame()  # empty draftpicks for now
        )
        print(f"✅ Created players_silver: {len(players_silver)} rows")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Full traceback:")
        traceback.print_exc()


def debug_pbp_error():
    """Debug pbp_silver conversion error."""
    print("\n🔍 DEBUGGING PBP_SILVER ERROR")
    print("=" * 50)
    
    try:
        from etl.bronze_to_silver import make_pbp_silver
        
        # Load and concatenate PBP data like the ETL does
        pbp_dir = Path('data/raw/PBP')
        pbp_files = list(pbp_dir.glob('*.parquet'))
        
        pbp_list = []
        for file in pbp_files:
            df = pd.read_parquet(file)
            pbp_list.append(df)
        
        combined_pbp = pd.concat(pbp_list, ignore_index=True)
        print(f"✅ Loaded PBP data: {len(combined_pbp)} rows")
        
        # Try to build pbp_silver
        pbp_silver = make_pbp_silver(combined_pbp)
        print(f"✅ Created pbp_silver: {len(pbp_silver)} rows")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Full traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    debug_players_error()
    debug_pbp_error()