#!/usr/bin/env python3
"""
Quick script to check PBP event type data quality.
"""

import pandas as pd
import sqlite3
from pathlib import Path

def check_pbp_events():
    """Check PBP event type data quality."""
    
    db_path = Path(__file__).parent / "db" / "pacers_analytics.db"
    
    if not db_path.exists():
        print("❌ Database not found")
        return
        
    conn = sqlite3.connect(db_path)
    
    try:
        # Check PBP event types
        print("🏀 Checking PBP Event Type Data")
        print("=" * 50)
        
        # Get basic stats
        pbp_df = pd.read_sql_query("SELECT * FROM pbp_silver LIMIT 1000", conn)
        
        print(f"📊 PBP Sample: {len(pbp_df)} rows")
        print()
        
        # Check event_msg_type values
        event_msg_type_stats = pbp_df['event_msg_type'].value_counts()
        print("🎯 Event Message Types:")
        print(event_msg_type_stats.head(10))
        
        null_event_msg = pbp_df['event_msg_type'].isnull().sum()
        zero_event_msg = (pbp_df['event_msg_type'] == 0).sum()
        
        print(f"\n❓ Null event_msg_type: {null_event_msg} ({null_event_msg/len(pbp_df)*100:.1f}%)")
        print(f"⚪ Zero event_msg_type: {zero_event_msg} ({zero_event_msg/len(pbp_df)*100:.1f}%)")
        print()
        
        # Check event_action_type values  
        event_action_type_stats = pbp_df['event_action_type'].value_counts()
        print("🎯 Event Action Types:")
        print(event_action_type_stats.head(10))
        
        null_action_type = pbp_df['event_action_type'].isnull().sum()
        zero_action_type = (pbp_df['event_action_type'] == 0).sum()
        
        print(f"\n❓ Null event_action_type: {null_action_type} ({null_action_type/len(pbp_df)*100:.1f}%)")
        print(f"⚪ Zero event_action_type: {zero_action_type} ({zero_action_type/len(pbp_df)*100:.1f}%)")
        print()
        
        # Check lookup tables
        event_types_df = pd.read_sql_query("SELECT * FROM event_types_silver", conn)
        print(f"📋 Event Types Lookup: {len(event_types_df)} entries")
        print(event_types_df.head())
        print()
        
        event_actions_df = pd.read_sql_query("SELECT * FROM event_actions_silver", conn)  
        print(f"📋 Event Actions Lookup: {len(event_actions_df)} entries")
        print(event_actions_df.head())
        
        print(f"\n✅ PBP event type validation complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_pbp_events()