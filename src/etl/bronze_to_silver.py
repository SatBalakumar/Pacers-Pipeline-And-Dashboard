"""
Bronze to Silver ETL transformations.

Functions to transform raw data into typed Silver tables
with proper schemas.
"""

import pandas as pd
import numpy as np
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Union, Iterator, Any
from datetime import datetime, date

from .schemas import get_silver_schema
from .utils import (
    iso8601_to_minutes, to_nullable_int, coalesce, parse_height_to_inches,
    parse_jersey_number, ensure_pk_unique, ensure_fk
)
from .seed_codes import get_position_id, get_country_id, get_affiliation_id, get_game_type_id, get_event_msg_type_id, get_event_action_type_id, normalize_action_type


def parse_height_to_inches(height_str: str) -> int:
    """Parse height string (e.g., '6-2') to total inches."""
    if pd.isna(height_str) or str(height_str).strip() == '':
        return 72  # Default 6 feet
    
    try:
        height_str = str(height_str).strip()
        if '-' in height_str:
            parts = height_str.split('-')
            feet = int(parts[0]) if parts[0] else 0
            inches = int(parts[1]) if len(parts) > 1 and parts[1] else 0
            return feet * 12 + inches
        else:
            # If just a number, assume inches
            return int(float(height_str)) if height_str else 72
    except (ValueError, AttributeError):
        return 72  # Default 6 feet
from datetime import datetime, date
import hashlib

from .utils import (
    iso8601_to_minutes, to_nullable_int, coalesce, parse_height_to_inches,
    parse_jersey_number, ensure_pk_unique, ensure_fk
)
from .schemas import get_silver_schema
from .seed_codes import get_position_id, get_country_id, get_affiliation_id, get_game_type_id, get_event_msg_type_id, get_event_action_type_id


def make_venues_silver(schedule_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create venues silver table from schedule data.
    
    Args:
        schedule_df: Raw schedule DataFrame
        
    Returns:
        Venues DataFrame with schema applied
    """
    # Extract venue information
    venue_cols = ['arenaName', 'arenaState', 'arenaCity']
    available_cols = [col for col in venue_cols if col in schedule_df.columns]
    
    if not available_cols:
        # Create empty DataFrame with schema
        df = pd.DataFrame(columns=['venue_id', 'venue_name', 'venue_state', 'venue_city'])
    else:
        # Group by venue attributes and create deterministic IDs
        venue_df = schedule_df[available_cols].dropna().drop_duplicates()
        
        if venue_df.empty:
            df = pd.DataFrame(columns=['venue_id', 'venue_name', 'venue_state', 'venue_city'])
        else:
            # Create deterministic venue_id using hash of venue info
            venue_df['venue_key'] = venue_df.apply(
                lambda row: '_'.join(str(row[col]) for col in available_cols), axis=1
            )
            venue_df['venue_id'] = venue_df['venue_key'].apply(
                lambda x: int(hashlib.md5(x.encode()).hexdigest()[:8], 16) % 1000000
            )
            
            # Map columns
            df = pd.DataFrame({
                'venue_id': venue_df['venue_id'],
                'venue_name': venue_df.get('arenaName', ''),
                'venue_state': venue_df.get('arenaState', ''),
                'venue_city': venue_df.get('arenaCity', '')
            })
    
    # Apply schema
    schema = get_silver_schema('venues_silver')
    for col, dtype in schema.items():
        if col in df.columns:
            if dtype.startswith('Int'):
                bits = int(dtype[3:])
                df[col] = to_nullable_int(df[col], bits)
            else:
                df[col] = df[col].astype(dtype)
        else:
            # Add missing columns with appropriate null values
            if dtype.startswith('Int'):
                df[col] = pd.Series(dtype=dtype)
            else:
                df[col] = pd.Series(dtype=dtype)
    
    # Validate PK uniqueness
    ensure_pk_unique(df, ['venue_id'], 'venues_silver')
    
    return df.reset_index(drop=True)


from datetime import date


def parse_height_to_inches(height_str):
    """Convert height string to inches."""
    if pd.isna(height_str) or height_str == '':
        return 0
    try:
        # Handle formats like "6-10", "6'10\"", "6 ft 10 in", etc.
        height_str = str(height_str).replace('"', '').replace("'", '-').replace(' ft ', '-').replace(' in', '')
        if '-' in height_str:
            parts = height_str.split('-')
            feet = int(parts[0])
            inches = int(parts[1]) if len(parts) > 1 else 0
            return feet * 12 + inches
        else:
            # Assume it's already in inches
            return int(float(height_str))
    except:
        return 0


def get_country_id(country_name: str, countries_df: pd.DataFrame) -> int:
    """Get country_id for a given country name."""
    if pd.isna(country_name) or country_name == '' or countries_df.empty:
        return 1  # Default to USA
    
    match = countries_df[countries_df['country_name'].str.contains(country_name, case=False, na=False)]
    return int(match['country_id'].iloc[0]) if not match.empty else 1


def get_affiliation_id(affiliation_name: str, affiliations_df: pd.DataFrame) -> int:
    """Get affiliation_id for a given affiliation name."""
    if pd.isna(affiliation_name) or affiliation_name == '' or affiliations_df.empty:
        return 1  # Default affiliation
    
    match = affiliations_df[affiliations_df['affiliation_type'].str.contains(affiliation_name, case=False, na=False, regex=False)]
    return int(match['affiliation_id'].iloc[0]) if not match.empty else 1


def get_position_id(position_code: str, positions_df: pd.DataFrame) -> int:
    """Get position_id for a given position code, with NBA position mapping."""
    if pd.isna(position_code) or position_code == '' or positions_df.empty:
        return 1  # Default position
    
    # First try exact match
    exact_match = positions_df[positions_df['position_code'] == position_code]
    if not exact_match.empty:
        return int(exact_match['position_id'].iloc[0])
    
    # NBA position mapping for common abbreviations
    position_mapping = {
        'PG': 'G',      # Point Guard -> Guard
        'SG': 'G',      # Shooting Guard -> Guard  
        'SF': 'F',      # Small Forward -> Forward
        'PF': 'F',      # Power Forward -> Forward
        'C': 'C',       # Center -> Center
        'PG-SG': 'G',   # Guard hybrid
        'SG-SF': 'G-F', # Guard-Forward
        'SF-PF': 'F',   # Forward hybrid
        'PF-C': 'F-C',  # Forward-Center
        'C-PF': 'C-F'   # Center-Forward
    }
    
    # Try mapped position
    mapped_position = position_mapping.get(position_code)
    if mapped_position:
        mapped_match = positions_df[positions_df['position_code'] == mapped_position]
        if not mapped_match.empty:
            return int(mapped_match['position_id'].iloc[0])
    
    # Fallback to substring search (original logic)
    match = positions_df[positions_df['position_code'].str.contains(position_code, case=False, na=False, regex=False)]
    return int(match['position_id'].iloc[0]) if not match.empty else 1


def make_teams_silver(schedule_df: pd.DataFrame, players_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create teams silver table from schedule and players data.
    
    Args:
        schedule_df: Raw schedule DataFrame
        players_df: Raw players DataFrame
        
    Returns:
        Teams DataFrame with schema applied
    """
    teams_data = []
    
    # Extract teams from schedule (home and away)
    schedule_teams = set()
    for prefix in ['homeTeam', 'awayTeam']:
        id_col = f'{prefix}.teamId'
        name_col = f'{prefix}.teamName'
        city_col = f'{prefix}.teamCity'
        slug_col = f'{prefix}.teamSlug'
        tricode_col = f'{prefix}.teamTricode'
        
        if id_col in schedule_df.columns:
            for _, row in schedule_df.iterrows():
                team_id = row.get(id_col)
                if pd.notna(team_id) and team_id != 0:
                    # Use tricode as team_abbreviation if available
                    team_abbreviation = row.get(tricode_col, '')
                    teams_data.append({
                        'team_id': int(team_id),
                        'team_name': row.get(name_col, ''),
                        'team_city': row.get(city_col, ''),
                        'team_slug': row.get(slug_col, ''),
                        'tricode': team_abbreviation,
                        'team_abbreviation': team_abbreviation,  # Use tricode as abbreviation
                        'is_defunct': False
                    })
    
    # Extract teams from players data
    if 'TEAM_ID' in players_df.columns:
        for _, row in players_df.iterrows():
            team_id = row.get('TEAM_ID')
            if pd.notna(team_id) and team_id != 0:
                teams_data.append({
                    'team_id': int(team_id),
                    'team_name': row.get('TEAM_NAME', ''),
                    'team_city': row.get('TEAM_CITY', ''),
                    'team_slug': row.get('TEAM_SLUG', ''),
                    'tricode': row.get('TEAM_TRICODE', ''),
                    'team_abbreviation': row.get('TEAM_ABBREVIATION', ''),
                    'is_defunct': row.get('IS_DEFUNCT', False)
                })
    
    if not teams_data:
        # Create empty DataFrame with schema
        df = pd.DataFrame(columns=[
            'team_id', 'team_slug', 'team_city', 'team_name', 
            'team_abbreviation', 'is_defunct', 'tricode'
        ])
    else:
        # Create DataFrame and deduplicate by team_id
        df = pd.DataFrame(teams_data)
        
        # Aggregate team info by team_id (take first non-null values)
        agg_dict = {}
        for col in ['team_slug', 'team_city', 'team_name', 'team_abbreviation', 'tricode']:
            agg_dict[col] = lambda x: x.dropna().iloc[0] if not x.dropna().empty else ''
        agg_dict['is_defunct'] = lambda x: x.any() if x.dtype == bool else False
        
        df = df.groupby('team_id').agg(agg_dict).reset_index()
        
        # Don't filter out team_id == 0, but handle it separately below
    
    # Add a "Free Agent" team for players without a team (team_id = 0)
    free_agent_team = pd.DataFrame([{
        'team_id': 0,
        'team_slug': 'free-agents',
        'team_city': 'Free',
        'team_name': 'Free Agents',
        'team_abbreviation': 'FA',
        'tricode': 'FA',
        'is_defunct': False
    }])
    
    # Combine with existing teams
    if not df.empty:
        df = pd.concat([df, free_agent_team], ignore_index=True)
    else:
        df = free_agent_team
    
    # Apply schema
    schema = get_silver_schema('teams_silver')
    for col, dtype in schema.items():
        if col in df.columns:
            if dtype.startswith('Int'):
                bits = int(dtype[3:])
                df[col] = to_nullable_int(df[col], bits)
            elif dtype == 'boolean':
                df[col] = df[col].astype('boolean')
            else:
                df[col] = df[col].astype(dtype)
        else:
            # Add missing columns
            if dtype.startswith('Int'):
                df[col] = pd.Series(dtype=dtype)
            elif dtype == 'boolean':
                df[col] = pd.Series(dtype='boolean')
            else:
                df[col] = pd.Series(dtype=dtype)
    
    # Validate PK uniqueness
    ensure_pk_unique(df, ['team_id'], 'teams_silver')
    
    return df.reset_index(drop=True)


def make_draftpicks_silver(players_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create draft picks silver table from players data.
    
    Args:
        players_df: Raw players DataFrame
        
    Returns:
        Draft picks DataFrame with schema applied
    """
    # Filter to drafted players only - using actual column names
    draft_cols = ['draftYear', 'draftRound', 'draftNumber']
    available_cols = [col for col in draft_cols if col in players_df.columns]
    
    if not available_cols or 'playerId' not in players_df.columns:
        # Create empty DataFrame
        df = pd.DataFrame(columns=[
            'draftpick_id', 'player_id', 'draft_year', 'draft_round', 'draft_number'
        ])
    else:
        # Filter drafted players
        drafted_df = players_df[
            players_df['draftYear'].notna() & 
            (players_df['draftYear'] > 0)
        ].copy()
        
        if drafted_df.empty:
            df = pd.DataFrame(columns=[
                'draftpick_id', 'player_id', 'draft_year', 'draft_round', 'draft_number'
            ])
        else:
            # Create draftpick_id = draftYear*1000 + draftNumber
            drafted_df['draftpick_id'] = (
                drafted_df['draftYear'] * 1000 + 
                drafted_df['draftNumber'].fillna(999)
            ).astype(int)
            
            df = pd.DataFrame({
                'draftpick_id': drafted_df['draftpick_id'],
                'player_id': drafted_df['playerId'],
                'draft_year': drafted_df['draftYear'],
                'draft_round': drafted_df['draftRound'],
                'draft_number': drafted_df['draftNumber']
            })
    
    # Apply schema
    schema = get_silver_schema('draftpicks_silver')
    for col, dtype in schema.items():
        if col in df.columns:
            if dtype.startswith('Int'):
                bits = int(dtype[3:])
                df[col] = to_nullable_int(df[col], bits)
            else:
                df[col] = df[col].astype(dtype)
        else:
            if dtype.startswith('Int'):
                df[col] = pd.Series(dtype=dtype)
            else:
                df[col] = pd.Series(dtype=dtype)
    
    # Validate PK uniqueness
    ensure_pk_unique(df, ['draftpick_id'], 'draftpicks_silver')
    
    return df.reset_index(drop=True)


def make_players_silver(
    players_df: pd.DataFrame,
    positions_silver: pd.DataFrame,
    countries_silver: pd.DataFrame, 
    affiliationtypes_silver: pd.DataFrame,
    draftpicks_silver: pd.DataFrame
) -> pd.DataFrame:
    """
    Create players silver table from players data and lookup tables.
    
    Args:
        players_df: Raw players DataFrame
        positions_silver: Positions lookup table
        countries_silver: Countries lookup table
        affiliationtypes_silver: Affiliations lookup table
        draftpicks_silver: Draft picks table
        
    Returns:
        Players DataFrame with schema applied
    """
    if players_df.empty or 'playerId' not in players_df.columns:
        # Create empty DataFrame
        schema = get_silver_schema('players_silver')
        df = pd.DataFrame(columns=list(schema.keys()))
        for col, dtype in schema.items():
            if dtype.startswith('Int'):
                df[col] = pd.Series(dtype=dtype)
            elif dtype == 'boolean':
                df[col] = pd.Series(dtype='boolean')
            elif dtype == 'datetime64[ns]':
                df[col] = pd.Series(dtype='datetime64[ns]')
            else:
                df[col] = pd.Series(dtype=dtype)
        return df
    
    df = players_df.copy()
    
    # Calculate age (using June 30 as season end)
    current_season = 2024  # Adjust as needed
    season_end_date = date(current_season, 6, 30)
    
    def calculate_age(birthdate_str):
        if pd.isna(birthdate_str):
            return None
        try:
            birthdate = pd.to_datetime(birthdate_str).date()
            age = int((season_end_date - birthdate).days / 365.2422)
            return age if age >= 0 else None
        except:
            return None
    
    # Transform columns using actual column names from the data
    result_df = pd.DataFrame({
        'player_id': df['playerId'],
        'first_name': df['firstName'] if 'firstName' in df.columns else '',
        'last_name': df['lastName'] if 'lastName' in df.columns else '',
        'player_slug': df['playerSlug'] if 'playerSlug' in df.columns else '',
        'is_active': (df['rosterStatus'] == 1) if 'rosterStatus' in df.columns else True,
        'team_id': pd.to_numeric(df['teamId'] if 'teamId' in df.columns else 0, errors='coerce'),
        'jersey_num': df['jerseyNum'] if 'jerseyNum' in df.columns else '',
        'height_inches': df['height'].apply(parse_height_to_inches) if 'height' in df.columns else 0,
        'weight': pd.to_numeric(df['weight'] if 'weight' in df.columns else 0, errors='coerce'),
        'birthdate': pd.to_datetime(df['birthdate'] if 'birthdate' in df.columns else None, errors='coerce'),
        'country_id': df['country'].apply(lambda x: get_country_id(x, countries_silver)) if 'country' in df.columns else 1,
        'affiliation_id': df['lastAffiliation'].apply(lambda x: get_affiliation_id(x, affiliationtypes_silver)) if 'lastAffiliation' in df.columns else 1,
        'seasons_experience': pd.to_numeric(df['seasonExperience'] if 'seasonExperience' in df.columns else 0, errors='coerce'),
        'career_start_season': pd.to_numeric(df['fromYear'] if 'fromYear' in df.columns else current_season, errors='coerce'),
        'career_last_season': pd.to_numeric(df['toYear'] if 'toYear' in df.columns else current_season, errors='coerce'),
        'is_two_way': df['isTwoWay'] if 'isTwoWay' in df.columns else False,
        'is_ten_day': df['isTenDay'] if 'isTenDay' in df.columns else False,
        'season': current_season
    })
    
    # Calculate age using the existing calculate_age function  
    result_df['age'] = df['birthdate'].apply(calculate_age) if 'birthdate' in df.columns else 25
    
    # Map position_id using the helper function
    result_df['position_id'] = df['position'].apply(lambda x: get_position_id(x, positions_silver)) if 'position' in df.columns else 1
    
    # Map draft pick info
    result_df['draftpick_id'] = df['playerId'].apply(
        lambda pid: draftpicks_silver[draftpicks_silver['player_id'] == pid]['draftpick_id'].iloc[0]
        if not draftpicks_silver[draftpicks_silver['player_id'] == pid].empty else None
    ) if 'playerId' in df.columns and not draftpicks_silver.empty else None
    result_df['is_draft_pick'] = result_df['draftpick_id'].notna()
    
    # Handle negative seasons_experience (-1 → 0)
    result_df['seasons_experience'] = result_df['seasons_experience'].apply(
        lambda x: 0 if x < 0 else x
    )
    
    # Validate weight > 0
    result_df.loc[result_df['weight'] <= 0, 'weight'] = None
    
    # Apply schema
    schema = get_silver_schema('players_silver')
    for col, dtype in schema.items():
        if col in result_df.columns:
            if dtype.startswith('Int'):
                bits = int(dtype[3:])
                result_df[col] = to_nullable_int(result_df[col], bits)
            elif dtype == 'boolean':
                result_df[col] = result_df[col].astype('boolean')
            elif dtype == 'datetime64[ns]':
                result_df[col] = pd.to_datetime(result_df[col])
            else:
                result_df[col] = result_df[col].astype(dtype)
        else:
            # Add missing columns
            if dtype.startswith('Int'):
                result_df[col] = pd.Series(dtype=dtype)
            elif dtype == 'boolean':
                result_df[col] = pd.Series(dtype='boolean')
            elif dtype == 'datetime64[ns]':
                result_df[col] = pd.Series(dtype='datetime64[ns]')
            else:
                result_df[col] = pd.Series(dtype=dtype)
    
    # Validate PK uniqueness
    ensure_pk_unique(result_df, ['player_id'], 'players_silver')
    
    return result_df.reset_index(drop=True)


def make_games_silver(
    schedule_df: pd.DataFrame,
    boxscore_index_df: pd.DataFrame,
    venues_silver: pd.DataFrame,
    gametypes_silver: pd.DataFrame
) -> pd.DataFrame:
    """
    Create games silver table from schedule and boxscore data.
    
    Args:
        schedule_df: Raw schedule DataFrame
        boxscore_index_df: Index of boxscore files with basic game info
        venues_silver: Venues lookup table
        gametypes_silver: Game types lookup table
        
    Returns:
        Games DataFrame with schema applied
    """
    if schedule_df.empty:
        # Create empty DataFrame
        schema = get_silver_schema('games_silver')
        df = pd.DataFrame(columns=list(schema.keys()))
        for col, dtype in schema.items():
            if dtype.startswith('Int'):
                df[col] = pd.Series(dtype=dtype)
            elif dtype == 'datetime64[ns]':
                df[col] = pd.Series(dtype='datetime64[ns]')
            else:
                df[col] = pd.Series(dtype=dtype)
        return df
    
    # Parse datetime properly - use the correct column name from schedule data
    if 'gameDateTimeEst' in schedule_df.columns:
        # Use the proper datetime column from schedule data
        game_datetime_est = pd.to_datetime(schedule_df['gameDateTimeEst'], errors='coerce')
    elif 'gameTimeUTC' in schedule_df.columns:
        # Convert UTC time to EST and handle different formats
        game_datetime = pd.to_datetime(schedule_df['gameTimeUTC'], errors='coerce')
        # Convert to EST (UTC-5)
        game_datetime_est = game_datetime - pd.Timedelta(hours=5)
    elif 'gameTimeEST' in schedule_df.columns:
        game_datetime_est = pd.to_datetime(schedule_df['gameTimeEST'], errors='coerce')
    elif 'gameDate' in schedule_df.columns:
        # Handle integer date format like 20241014
        game_dates = schedule_df['gameDate'].astype(str)
        game_datetime_est = pd.to_datetime(game_dates, format='%Y%m%d', errors='coerce')
    else:
        game_datetime_est = pd.NaT
    
    result_df = pd.DataFrame({
        'game_id': pd.to_numeric(schedule_df.get('gameId', 0), errors='coerce'),
        'season': pd.to_numeric(schedule_df.get('season', 2024), errors='coerce'),
        'game_datetime_est': game_datetime_est,
        'home_team_id': pd.to_numeric(schedule_df.get('homeTeam.teamId', 0), errors='coerce'),
        'away_team_id': pd.to_numeric(schedule_df.get('awayTeam.teamId', 0), errors='coerce'),
        'game_type_id': schedule_df.get('seasonType', 'Regular Season').apply(get_game_type_id),
        'status_code': pd.to_numeric(schedule_df.get('gameStatus', 1), errors='coerce')
    })
    
    # Map venue_id - create a simple mapping based on arena name
    if 'arenaName' in schedule_df.columns and not venues_silver.empty:
        venue_map = venues_silver.set_index('venue_name')['venue_id'].to_dict()
        result_df['venue_id'] = schedule_df['arenaName'].map(venue_map)
    else:
        result_df['venue_id'] = None
    
    # Get points directly from schedule data first, then supplement with boxscore
    result_df['home_points'] = pd.to_numeric(schedule_df.get('homeTeam.score'), errors='coerce')
    result_df['away_points'] = pd.to_numeric(schedule_df.get('awayTeam.score'), errors='coerce')
    
    # Add additional points from boxscore if available and missing
    if not boxscore_index_df.empty and 'game_id' in boxscore_index_df.columns:
        boxscore_points = boxscore_index_df.set_index('game_id')[['home_points', 'away_points']].to_dict('index')
        for idx, row in result_df.iterrows():
            game_id = row['game_id']
            if game_id in boxscore_points:
                # Only use boxscore points if schedule points are missing
                if pd.isna(result_df.loc[idx, 'home_points']):
                    result_df.loc[idx, 'home_points'] = boxscore_points[game_id].get('home_points')
                if pd.isna(result_df.loc[idx, 'away_points']):
                    result_df.loc[idx, 'away_points'] = boxscore_points[game_id].get('away_points')
    
    # Filter out invalid game_ids
    result_df = result_df[result_df['game_id'].notna() & (result_df['game_id'] != 0)]
    
    # Apply schema
    schema = get_silver_schema('games_silver')
    for col, dtype in schema.items():
        if col in result_df.columns:
            if dtype.startswith('Int'):
                bits = int(dtype[3:])
                result_df[col] = to_nullable_int(result_df[col], bits)
            elif dtype == 'datetime64[ns]':
                result_df[col] = pd.to_datetime(result_df[col])
            else:
                result_df[col] = result_df[col].astype(dtype)
        else:
            if dtype.startswith('Int'):
                result_df[col] = pd.Series(dtype=dtype)
            elif dtype == 'datetime64[ns]':
                result_df[col] = pd.Series(dtype='datetime64[ns]')
            else:
                result_df[col] = pd.Series(dtype=dtype)
    
    # Validate PK uniqueness
    ensure_pk_unique(result_df, ['game_id'], 'games_silver')
    
    return result_df.reset_index(drop=True)


def load_boxscore_files(boxscore_dir: Union[str, Path]) -> Iterator[Dict]:
    """
    Load boxscore files from directory (supports .parquet and .json).
    
    Args:
        boxscore_dir: Directory containing boxscore files
        
    Yields:
        Dict containing game data from each file
    """
    boxscore_dir = Path(boxscore_dir)
    
    if not boxscore_dir.exists():
        return
    
    # Process .parquet files
    for file_path in boxscore_dir.glob('*.parquet'):
        try:
            df = pd.read_parquet(file_path)
            if len(df) == 1:  # Expected: one row per game
                yield df.iloc[0].to_dict()
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    # Process .json files
    for file_path in boxscore_dir.glob('*.json'):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                yield data
        except Exception as e:
            print(f"Error loading {file_path}: {e}")


def make_gameteamtotals_silver(boxscore_iter: Iterator[Dict]) -> pd.DataFrame:
    """
    Create game team totals silver table from boxscore data.
    
    Args:
        boxscore_iter: Iterator of boxscore game dictionaries
        
    Returns:
        Game team totals DataFrame with schema applied
    """
    team_totals_data = []
    
    for game_data in boxscore_iter:
        game_id = game_data.get('gameId')
        if not game_id:
            continue
            
        # Process home team
        home_team_id = game_data.get('homeTeam_teamId')
        if home_team_id:
            home_stats = {
                'game_id': game_id,
                'team_id': home_team_id,
                'is_home': True,
                'minutes_total': iso8601_to_minutes(game_data.get('homeTeam_statistics_minutes', 'PT240M00.00S')),
                'pts': game_data.get('homeTeam_statistics_points', 0),
                'fgm': game_data.get('homeTeam_statistics_fieldGoalsMade', 0),
                'fga': game_data.get('homeTeam_statistics_fieldGoalsAttempted', 0),
                'fg3m': game_data.get('homeTeam_statistics_threePointersMade', 0),
                'fg3a': game_data.get('homeTeam_statistics_threePointersAttempted', 0),
                'ftm': game_data.get('homeTeam_statistics_freeThrowsMade', 0),
                'fta': game_data.get('homeTeam_statistics_freeThrowsAttempted', 0),
                'oreb': game_data.get('homeTeam_statistics_reboundsOffensive', 0),
                'dreb': game_data.get('homeTeam_statistics_reboundsDefensive', 0),
                'reb': game_data.get('homeTeam_statistics_reboundsTotal', 0),
                'ast': game_data.get('homeTeam_statistics_assists', 0),
                'stl': game_data.get('homeTeam_statistics_steals', 0),
                'blk': game_data.get('homeTeam_statistics_blocks', 0),
                'tov': game_data.get('homeTeam_statistics_turnovers', 0),
                'pf': game_data.get('homeTeam_statistics_foulsPersonal', 0),
                'pitp': game_data.get('homeTeam_statistics_pointsInThePaint', 0),
                'second_chance_pts': game_data.get('homeTeam_statistics_pointsSecondChance', 0),
                'fastbreak_pts': game_data.get('homeTeam_statistics_pointsFastBreak', 0),
                'pts_off_to': game_data.get('homeTeam_statistics_pointsFromTurnovers', 0)
            }
            team_totals_data.append(home_stats)
        
        # Process away team  
        away_team_id = game_data.get('awayTeam_teamId')
        if away_team_id:
            away_stats = {
                'game_id': game_id,
                'team_id': away_team_id,
                'is_home': False,
                'minutes_total': iso8601_to_minutes(game_data.get('awayTeam_statistics_minutes', 'PT240M00.00S')),
                'pts': game_data.get('awayTeam_statistics_points', 0),
                'fgm': game_data.get('awayTeam_statistics_fieldGoalsMade', 0),
                'fga': game_data.get('awayTeam_statistics_fieldGoalsAttempted', 0),
                'fg3m': game_data.get('awayTeam_statistics_threePointersMade', 0),
                'fg3a': game_data.get('awayTeam_statistics_threePointersAttempted', 0),
                'ftm': game_data.get('awayTeam_statistics_freeThrowsMade', 0),
                'fta': game_data.get('awayTeam_statistics_freeThrowsAttempted', 0),
                'oreb': game_data.get('awayTeam_statistics_reboundsOffensive', 0),
                'dreb': game_data.get('awayTeam_statistics_reboundsDefensive', 0),
                'reb': game_data.get('awayTeam_statistics_reboundsTotal', 0),
                'ast': game_data.get('awayTeam_statistics_assists', 0),
                'stl': game_data.get('awayTeam_statistics_steals', 0),
                'blk': game_data.get('awayTeam_statistics_blocks', 0),
                'tov': game_data.get('awayTeam_statistics_turnovers', 0),
                'pf': game_data.get('awayTeam_statistics_foulsPersonal', 0),
                'pitp': game_data.get('awayTeam_statistics_pointsInThePaint', 0),
                'second_chance_pts': game_data.get('awayTeam_statistics_pointsSecondChance', 0),
                'fastbreak_pts': game_data.get('awayTeam_statistics_pointsFastBreak', 0),
                'pts_off_to': game_data.get('awayTeam_statistics_pointsFromTurnovers', 0)
            }
            team_totals_data.append(away_stats)
    
    if not team_totals_data:
        # Create empty DataFrame
        schema = get_silver_schema('gameteamtotals_silver')
        df = pd.DataFrame(columns=list(schema.keys()))
        for col, dtype in schema.items():
            if dtype.startswith('Int'):
                df[col] = pd.Series(dtype=dtype)
            elif dtype == 'boolean':
                df[col] = pd.Series(dtype='boolean')
            elif dtype == 'float32':
                df[col] = pd.Series(dtype='float32')
            else:
                df[col] = pd.Series(dtype=dtype)
        return df
    
    df = pd.DataFrame(team_totals_data)
    
    # Apply schema
    schema = get_silver_schema('gameteamtotals_silver')
    for col, dtype in schema.items():
        if col in df.columns:
            if dtype.startswith('Int'):
                bits = int(dtype[3:])
                df[col] = to_nullable_int(df[col], bits)
            elif dtype == 'boolean':
                df[col] = df[col].astype('boolean')
            elif dtype == 'float32':
                df[col] = df[col].astype('float32')
            else:
                df[col] = df[col].astype(dtype)
        else:
            if dtype.startswith('Int'):
                df[col] = pd.Series(dtype=dtype)
            elif dtype == 'boolean':
                df[col] = pd.Series(dtype='boolean')
            elif dtype == 'float32':
                df[col] = pd.Series(dtype='float32')
            else:
                df[col] = pd.Series(dtype=dtype)
    
    # Validate PK uniqueness
    ensure_pk_unique(df, ['game_id', 'team_id'], 'gameteamtotals_silver')
    
    return df.reset_index(drop=True)


def make_playerboxscore_silver(boxscore_iter: Iterator[Dict], positions_silver: pd.DataFrame, players_silver: pd.DataFrame = None) -> pd.DataFrame:
    """
    Create player boxscore silver table from boxscore data.
    
    Args:
        boxscore_iter: Iterator of boxscore game dictionaries
        positions_silver: Positions lookup table
        players_silver: Players table for position fallback lookup
        
    Returns:
        Player boxscore DataFrame with schema applied
    """
    
    def get_player_position_id(player_position: str, player_id: int) -> int:
        """Get position_id with fallback to players table if position is missing."""
        # First try the position from boxscore data
        if player_position and player_position.strip():
            return get_position_id(player_position, positions_silver)
        
        # If position is empty and we have players_silver, look it up
        if players_silver is not None and not players_silver.empty:
            player_match = players_silver[players_silver['player_id'] == player_id]
            if not player_match.empty:
                return int(player_match['position_id'].iloc[0])
        
        # Final fallback to default
        return 1
    player_stats_data = []
    
    for game_data in boxscore_iter:
        game_id = game_data.get('gameId')
        if not game_id:
            continue
            
        # Process home team players
        home_team_id = game_data.get('homeTeam_teamId')
        home_players = game_data.get('homeTeam_players', [])
        
        if isinstance(home_players, np.ndarray):
            home_players = home_players.tolist()
        
        for player in home_players or []:
            if isinstance(player, dict):
                stats = player.get('statistics', {})
                player_stat = {
                    'game_id': game_id,
                    'player_id': player.get('personId'),
                    'team_id': home_team_id,
                    'starter_flag': player.get('starter') == '1',
                    'played_flag': player.get('played') == '1',
                    'position_id': get_player_position_id(player.get('position'), player.get('personId')),
                    'minutes': iso8601_to_minutes(stats.get('minutes')),
                    'pts': stats.get('points', 0),
                    'fgm': stats.get('fieldGoalsMade', 0),
                    'fga': stats.get('fieldGoalsAttempted', 0),
                    'fg3m': stats.get('threePointersMade', 0),
                    'fg3a': stats.get('threePointersAttempted', 0),
                    'ftm': stats.get('freeThrowsMade', 0),
                    'fta': stats.get('freeThrowsAttempted', 0),
                    'oreb': stats.get('reboundsOffensive', 0),
                    'dreb': stats.get('reboundsDefensive', 0),
                    'reb': stats.get('reboundsTotal', 0),
                    'ast': stats.get('assists', 0),
                    'stl': stats.get('steals', 0),
                    'blk': stats.get('blocks', 0),
                    'tov': stats.get('turnovers', 0),
                    'pf': stats.get('foulsPersonal', 0),
                    'plusminus': stats.get('plusMinusPoints', 0),
                    'dnp_reason_code': 0 if player.get('played') == '1' else 1  # Default DNP reason
                }
                player_stats_data.append(player_stat)
        
        # Process away team players
        away_team_id = game_data.get('awayTeam_teamId')
        away_players = game_data.get('awayTeam_players', [])
        
        if isinstance(away_players, np.ndarray):
            away_players = away_players.tolist()
        
        for player in away_players or []:
            if isinstance(player, dict):
                stats = player.get('statistics', {})
                player_stat = {
                    'game_id': game_id,
                    'player_id': player.get('personId'),
                    'team_id': away_team_id,
                    'starter_flag': player.get('starter') == '1',
                    'played_flag': player.get('played') == '1',
                    'position_id': get_player_position_id(player.get('position'), player.get('personId')),
                    'minutes': iso8601_to_minutes(stats.get('minutes')),
                    'pts': stats.get('points', 0),
                    'fgm': stats.get('fieldGoalsMade', 0),
                    'fga': stats.get('fieldGoalsAttempted', 0),
                    'fg3m': stats.get('threePointersMade', 0),
                    'fg3a': stats.get('threePointersAttempted', 0),
                    'ftm': stats.get('freeThrowsMade', 0),
                    'fta': stats.get('freeThrowsAttempted', 0),
                    'oreb': stats.get('reboundsOffensive', 0),
                    'dreb': stats.get('reboundsDefensive', 0),
                    'reb': stats.get('reboundsTotal', 0),
                    'ast': stats.get('assists', 0),
                    'stl': stats.get('steals', 0),
                    'blk': stats.get('blocks', 0),
                    'tov': stats.get('turnovers', 0),
                    'pf': stats.get('foulsPersonal', 0),
                    'plusminus': stats.get('plusMinusPoints', 0),
                    'dnp_reason_code': 0 if player.get('played') == '1' else 1
                }
                player_stats_data.append(player_stat)
    
    if not player_stats_data:
        # Create empty DataFrame
        schema = get_silver_schema('playerboxscore_silver')
        df = pd.DataFrame(columns=list(schema.keys()))
        for col, dtype in schema.items():
            if dtype.startswith('Int'):
                df[col] = pd.Series(dtype=dtype)
            elif dtype == 'boolean':
                df[col] = pd.Series(dtype='boolean')
            elif dtype == 'float32':
                df[col] = pd.Series(dtype='float32')
            else:
                df[col] = pd.Series(dtype=dtype)
        return df
    
    df = pd.DataFrame(player_stats_data)
    
    # Apply schema
    schema = get_silver_schema('playerboxscore_silver')
    for col, dtype in schema.items():
        if col in df.columns:
            if dtype.startswith('Int'):
                bits = int(dtype[3:])
                df[col] = to_nullable_int(df[col], bits)
            elif dtype == 'boolean':
                df[col] = df[col].astype('boolean')
            elif dtype == 'float32':
                df[col] = df[col].astype('float32')
            else:
                df[col] = df[col].astype(dtype)
        else:
            if dtype.startswith('Int'):
                df[col] = pd.Series(dtype=dtype)
            elif dtype == 'boolean':
                df[col] = pd.Series(dtype='boolean')
            elif dtype == 'float32':
                df[col] = pd.Series(dtype='float32')
            else:
                df[col] = pd.Series(dtype=dtype)
    
    # Validate PK uniqueness
    ensure_pk_unique(df, ['game_id', 'player_id'], 'playerboxscore_silver')
    
    return df.reset_index(drop=True)


def make_pbp_silver(pbp_df: pd.DataFrame, event_types_silver: pd.DataFrame, action_types_silver: pd.DataFrame) -> pd.DataFrame:
    """
    Create play-by-play silver table from PBP data.
    
    Args:
        pbp_df: Raw play-by-play DataFrame
        event_types_silver: Event types lookup table
        action_types_silver: Action types lookup table
        
    Returns:
        PBP DataFrame with schema applied
    """
    # Create lookup dictionaries from the DataFrames
    event_types_lookup = event_types_silver.set_index('event_msg_type')['event_msg_type_id'].to_dict()
    event_actions_lookup = action_types_silver.set_index('event_action_type')['event_action_type_id'].to_dict()
    
    if pbp_df.empty:
        # Create empty DataFrame
        schema = get_silver_schema('pbp_silver')
        df = pd.DataFrame(columns=list(schema.keys()))
        for col, dtype in schema.items():
            if dtype.startswith('Int'):
                df[col] = pd.Series(dtype=dtype)
            elif dtype == 'boolean':
                df[col] = pd.Series(dtype='boolean')
            elif dtype == 'datetime64[ns]':
                df[col] = pd.Series(dtype='datetime64[ns]')
            else:
                df[col] = pd.Series(dtype=dtype)
        return df
    
    # Transform PBP data - use direct column access for DataFrame
    result_df = pd.DataFrame({
        'game_id': pd.to_numeric(pbp_df['gameId'] if 'gameId' in pbp_df.columns else 0, errors='coerce'),
        'event_num': pd.to_numeric(pbp_df['actionNumber'] if 'actionNumber' in pbp_df.columns else 0, errors='coerce'),
        'period': pd.to_numeric(pbp_df['period'] if 'period' in pbp_df.columns else 1, errors='coerce'),
        'pc_time': pbp_df['clock'] if 'clock' in pbp_df.columns else '',
        'wc_time': pd.to_datetime(pbp_df['timeActual'] if 'timeActual' in pbp_df.columns else None, errors='coerce'),
        'event_msg_type': pbp_df['actionType'].map(event_types_lookup).fillna(0) if 'actionType' in pbp_df.columns else 0,
        'event_action_type': pbp_df['subType'].fillna('').apply(normalize_action_type).map(event_actions_lookup).fillna(0) if 'subType' in pbp_df.columns else 0,
        'team_id': pd.to_numeric(pbp_df['teamId'] if 'teamId' in pbp_df.columns else 0, errors='coerce'),
        'player1_id': pd.to_numeric(pbp_df['personId'] if 'personId' in pbp_df.columns else 0, errors='coerce'),
        'player2_id': pd.to_numeric(pbp_df['assistPersonId'] if 'assistPersonId' in pbp_df.columns else 0, errors='coerce'),
        'player3_id': pd.to_numeric(pbp_df['jumpBallWonPersonId'] if 'jumpBallWonPersonId' in pbp_df.columns else 0, errors='coerce'),
        'home_description': pbp_df['description'] if 'description' in pbp_df.columns else '',
        'visitor_description': pbp_df['description'] if 'description' in pbp_df.columns else '',
        'neutral_description': pbp_df['description'] if 'description' in pbp_df.columns else '',
        'home_score': pd.to_numeric(pbp_df['scoreHome'] if 'scoreHome' in pbp_df.columns else 0, errors='coerce'),
        'away_score': pd.to_numeric(pbp_df['scoreAway'] if 'scoreAway' in pbp_df.columns else 0, errors='coerce'),
        'score_margin': (pd.to_numeric(pbp_df['scoreHome'] if 'scoreHome' in pbp_df.columns else 0, errors='coerce') - 
                        pd.to_numeric(pbp_df['scoreAway'] if 'scoreAway' in pbp_df.columns else 0, errors='coerce')),
        'shot_value': pd.to_numeric(pbp_df['pointsTotal'] if 'pointsTotal' in pbp_df.columns else 0, errors='coerce'),
        'shot_result': pbp_df['shotResult'] if 'shotResult' in pbp_df.columns else '',
        'shot_distance': pd.to_numeric(pbp_df['shotDistance'] if 'shotDistance' in pbp_df.columns else 0, errors='coerce'),
        'shot_x': pd.to_numeric(pbp_df['x'] if 'x' in pbp_df.columns else 0, errors='coerce'),
        'shot_y': pd.to_numeric(pbp_df['y'] if 'y' in pbp_df.columns else 0, errors='coerce'),
        'shot_side': pbp_df['side'] if 'side' in pbp_df.columns else '',
        'foul_type_code': pd.to_numeric(pbp_df['foulPersonalTotal'] if 'foulPersonalTotal' in pbp_df.columns else 0, errors='coerce'),
        'turnover_type_code': pd.to_numeric(pbp_df['turnoverTotal'] if 'turnoverTotal' in pbp_df.columns else 0, errors='coerce'),
        'is_substitution': (pbp_df['actionType'] == 'substitution') if 'actionType' in pbp_df.columns else False,
        'is_timeout': (pbp_df['actionType'] == 'timeout') if 'actionType' in pbp_df.columns else False
    })
    
    # Filter out invalid events
    result_df = result_df[
        result_df['game_id'].notna() & 
        (result_df['game_id'] != 0) &
        result_df['event_num'].notna() &
        (result_df['event_num'] != 0)
    ]
    
    # Apply schema
    schema = get_silver_schema('pbp_silver')
    for col, dtype in schema.items():
        if col in result_df.columns:
            if dtype.startswith('Int'):
                bits = int(dtype[3:])
                result_df[col] = to_nullable_int(result_df[col], bits)
            elif dtype == 'boolean':
                result_df[col] = result_df[col].astype('boolean')
            elif dtype == 'datetime64[ns]':
                result_df[col] = pd.to_datetime(result_df[col])
            else:
                result_df[col] = result_df[col].astype(dtype)
        else:
            if dtype.startswith('Int'):
                result_df[col] = pd.Series(dtype=dtype)
            elif dtype == 'boolean':
                result_df[col] = pd.Series(dtype='boolean')
            elif dtype == 'datetime64[ns]':
                result_df[col] = pd.Series(dtype='datetime64[ns]')
            else:
                result_df[col] = pd.Series(dtype=dtype)
    
    # Validate PK uniqueness
    ensure_pk_unique(result_df, ['game_id', 'event_num'], 'pbp_silver')
    
    return result_df.reset_index(drop=True)