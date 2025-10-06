#!/usr/bin/env python3
"""
Gold Table Normalization Analysis

This script analyzes each Gold table for potential normalization and deduplication opportunities.
"""

import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def analyze_gold_tables():
    """
    Systematic analysis of Gold tables for normalization opportunities.
    """
    print("🏀 Gold Table Normalization Analysis")
    print("=" * 60)
    
    # Based on code review, here are the Gold tables and their characteristics:
    tables = {
        'gold_games': {
            'description': 'Team-centric view (2 rows per game - one for each team)',
            'source': 'games_silver + gameteamtotals_silver + teams_silver',
            'potential_issues': [
                'Team name/city/abbreviation duplication (from teams lookup)',
                'Opponent team info duplication'
            ]
        },
        'gold_game_summary': {
            'description': 'Game-centric view (1 row per game)',
            'source': 'games_silver + teams_silver',
            'potential_issues': [
                'Home/away team name/city/abbreviation duplication',
                'Calculated fields (point_differential, total_points) could be computed'
            ]
        },
        'gold_player_info': {
            'description': 'Enriched player data with team, position, country, draft info',
            'source': 'players_silver + teams_silver + positions_silver + countries_silver + draftpicks_silver',
            'potential_issues': [
                'Team name/city/abbreviation duplication',
                'Full name concatenation (could be computed)',
                'Position/country names (already normalized via lookup tables)'
            ]
        },
        'gold_player_boxscore': {
            'description': 'Enriched boxscore data with game/team context',
            'source': 'playerboxscore_silver + games_silver + teams_silver + positions_silver',
            'potential_issues': [
                'Team/opponent team name duplication',
                'Calculated shooting percentages (fg_pct, fg3_pct, ft_pct)',
                'Position name duplication'
            ]
        },
        'gold_player_averages': {
            'description': 'Season aggregations from boxscore data',
            'source': 'gold_player_boxscore (aggregated)',
            'potential_issues': [
                'Calculated fields (all averages and percentages)',
                'No denormalization issues (pure aggregation table)'
            ]
        },
        'pacers_games': {
            'description': 'Filtered view of gold_games for Pacers only',
            'source': 'gold_games (filtered)',
            'potential_issues': [
                'Duplicate of existing data with filter',
                'Could be replaced with view or query'
            ]
        },
        'pacers_players': {
            'description': 'Filtered view of gold_player_info for Pacers only',
            'source': 'gold_player_info (filtered)',
            'potential_issues': [
                'Duplicate of existing data with filter',
                'Could be replaced with view or query'
            ]
        },
        'pacers_player_stats': {
            'description': 'Filtered view of gold_player_boxscore for Pacers only',
            'source': 'gold_player_boxscore (filtered)',
            'potential_issues': [
                'Duplicate of existing data with filter',
                'Could be replaced with view or query'
            ]
        },
        'pacers_season_averages': {
            'description': 'Pacers player averages with player names joined',
            'source': 'gold_player_averages + gold_player_info (filtered and joined)',
            'potential_issues': [
                'Player name duplication from join',
                'Could be replaced with view or query'
            ]
        }
    }
    
    print("\n📊 Table Analysis:")
    for table_name, info in tables.items():
        print(f"\n🔍 {table_name.upper()}")
        print(f"   Description: {info['description']}")
        print(f"   Source: {info['source']}")
        print("   Potential Issues:")
        for issue in info['potential_issues']:
            print(f"      • {issue}")
    
    print("\n🎯 NORMALIZATION RECOMMENDATIONS:")
    print("=" * 60)
    
    print("\n1. CALCULATED FIELDS (Can be computed at query time):")
    print("   • gold_game_summary: point_differential, total_points")
    print("   • gold_player_info: full_name (first_name + last_name)")
    print("   • gold_player_boxscore: fg_pct, fg3_pct, ft_pct")
    print("   • gold_player_averages: all percentage calculations")
    
    print("\n2. TEAM INFORMATION DENORMALIZATION:")
    print("   • Team names/cities/abbreviations repeated across multiple tables")
    print("   • Already normalized via team_id FK to teams_silver")
    print("   • Gold tables include denormalized team info for analytical convenience")
    print("   • RECOMMENDATION: Keep as-is for analytics performance")
    
    print("\n3. PACERS-SPECIFIC TABLES:")
    print("   • pacers_games, pacers_players, pacers_player_stats, pacers_season_averages")
    print("   • These are filtered subsets of main Gold tables")
    print("   • RECOMMENDATION: Convert to SQL views instead of physical tables")
    
    print("\n4. POSITION/COUNTRY INFORMATION:")
    print("   • Already properly normalized via position_id -> positions_silver")
    print("   • Already properly normalized via country_id -> countries_silver")
    print("   • Gold tables include denormalized names for convenience")
    print("   • RECOMMENDATION: Keep as-is for analytics performance")
    
    print("\n5. LOOKUP TABLE OPPORTUNITIES:")
    print("   • DNP reasons already implemented for playerboxscore")
    print("   • Status codes could benefit from lookup table")
    print("   • Game types could benefit from lookup table")
    
    return tables

if __name__ == "__main__":
    analyze_gold_tables()