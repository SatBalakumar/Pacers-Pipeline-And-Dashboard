#!/usr/bin/env python3
"""
Script to display the normalized event actions lookup table.
"""

import pandas as pd
import sqlite3
from pathlib import Path

def show_normalized_actions():
    """Show the normalized event actions lookup table."""
    
    db_path = Path(__file__).parent / "db" / "pacers_analytics.db"
    conn = sqlite3.connect(db_path)
    
    try:
        # Get the normalized lookup table
        actions_df = pd.read_sql_query(
            "SELECT * FROM event_actions_silver ORDER BY event_action_type_id", 
            conn
        )
        
        print("🎯 Normalized Event Actions Lookup Table")
        print("=" * 50)
        print(f"Total entries: {len(actions_df)} (was 67 before normalization)")
        print()
        
        # Show all entries
        for _, row in actions_df.iterrows():
            action_id = int(row['event_action_type_id'])
            action_type = row['event_action_type']
            print(f"{action_id:2d}: {action_type}")
        
        print("\n✅ Normalization eliminated duplicates like:")
        print("   - '1 of 1' and '1of1' → both now '1of1'")
        print("   - 'shot clock' and 'shotclock' → both now 'shotclock'")
        print("   - 'out-of-bounds' and 'outofbounds' → both now 'outofbounds'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    show_normalized_actions()