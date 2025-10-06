"""
Seed code/lookup table builders.

Functions to create normalized lookup tables from raw data.
"""

import pandas as pd
from typing import Dict
from .utils import to_nullable_int


def build_gametypes_silver(schedule_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build game types lookup table from schedule data.
    
    Args:
        schedule_df: Raw schedule DataFrame
        
    Returns:
        DataFrame with game_type_id and game_type columns
    """
    # Define game type mapping
    game_type_mapping = {
        "Pre Season": 0,
        "Regular Season": 1, 
        "All-Star": 2,
        "Playoffs": 3
    }
    
    # Get unique season types from schedule
    if 'seasonType' in schedule_df.columns:
        unique_types = schedule_df['seasonType'].dropna().unique()
    else:
        # Fallback to all known types
        unique_types = list(game_type_mapping.keys())
    
    # Create lookup table
    game_types_data = []
    for game_type in unique_types:
        if game_type in game_type_mapping:
            game_types_data.append({
                'game_type_id': game_type_mapping[game_type],
                'game_type': game_type
            })
    
    # Add any missing standard types
    for game_type, type_id in game_type_mapping.items():
        if not any(row['game_type_id'] == type_id for row in game_types_data):
            game_types_data.append({
                'game_type_id': type_id,
                'game_type': game_type
            })
    
    df = pd.DataFrame(game_types_data)
    
    # Apply schema
    df['game_type_id'] = to_nullable_int(df['game_type_id'], 8)
    df['game_type'] = df['game_type'].astype('string')
    
    return df.sort_values('game_type_id').reset_index(drop=True)


def build_positions_silver(players_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build positions lookup table from players data.
    
    Args:
        players_df: Raw players DataFrame
        
    Returns:
        DataFrame with position_id and position_code columns
    """
    # Get unique positions
    position_col = None
    for col in ['position', 'POSITION', 'pos']:
        if col in players_df.columns:
            position_col = col
            break
    
    if position_col is None:
        # Default positions if no data available - include both general and specific NBA positions
        unique_positions = ['C', 'PF', 'SF', 'SG', 'PG', 'F', 'G', 'C-F', 'F-C', 'F-G', 'G-F']
    else:
        unique_positions = players_df[position_col].dropna().unique()
    
    # Standard NBA positions with consistent ordering (most specific first)
    standard_positions = ['C', 'PF', 'SF', 'SG', 'PG', 'F', 'G', 'C-F', 'F-C', 'F-G', 'G-F']
    
    # Combine and deduplicate, preserving standard order
    all_positions = []
    for pos in standard_positions:
        if pos in unique_positions:
            all_positions.append(pos)
    
    # Add any additional positions not in standard list
    for pos in unique_positions:
        if pos not in all_positions:
            all_positions.append(pos)
    
    # Create lookup table
    positions_data = []
    for i, position in enumerate(all_positions, 1):
        positions_data.append({
            'position_id': i,
            'position_code': position
        })
    
    df = pd.DataFrame(positions_data)
    
    # Apply schema
    df['position_id'] = to_nullable_int(df['position_id'], 8)
    df['position_code'] = df['position_code'].astype('string')
    
    return df


def normalize_country_name(country: str) -> str:
    """
    Normalize country names for consistency.
    
    Args:
        country: Raw country name
        
    Returns:
        Normalized country name
    """
    if pd.isna(country) or country == '':
        return 'United States'  # Default
    
    country = str(country).strip()
    
    # Normalize specific countries
    country_normalizations = {
        'USA': 'United States',
        'US': 'United States',
        'United States of America': 'United States',
        # Keep other countries as-is for NBA purposes
        # Puerto Rico stays separate (NBA territory)
        # DRC stays as abbreviation (common usage)
        # UK would become United Kingdom if it appeared
        'UK': 'United Kingdom',
        'Great Britain': 'United Kingdom'
    }
    
    return country_normalizations.get(country, country)


def build_countries_silver(players_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build countries lookup table from players data with normalized names.
    
    Args:
        players_df: Raw players DataFrame
        
    Returns:
        DataFrame with country_id and country_name columns
    """
    # Get unique countries
    country_col = None
    for col in ['country', 'COUNTRY', 'birthCountry', 'birth_country']:
        if col in players_df.columns:
            country_col = col
            break
    
    if country_col is None:
        # Default to United States if no data available
        unique_countries = ['United States']
    else:
        # Normalize country names and get unique values
        normalized_countries = players_df[country_col].dropna().apply(normalize_country_name).unique()
        unique_countries = list(normalized_countries)
    
    # Sort countries with United States first
    countries_list = sorted(unique_countries)
    if 'United States' in countries_list:
        countries_list.remove('United States')
        countries_list.insert(0, 'United States')
    
    # Create lookup table
    countries_data = []
    for i, country in enumerate(countries_list, 1):
        countries_data.append({
            'country_id': i,
            'country_name': country
        })
    
    df = pd.DataFrame(countries_data)
    
    # Apply schema
    df['country_id'] = to_nullable_int(df['country_id'], 16)
    df['country_name'] = df['country_name'].astype('string')
    
    return df


def build_affiliationtypes_silver(players_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build affiliation types lookup table from players data.
    
    Args:
        players_df: Raw players DataFrame
        
    Returns:
        DataFrame with affiliation_id and affiliation_type columns
    """
    # Get unique affiliations
    affiliation_col = None
    for col in ['lastAffiliation', 'last_affiliation', 'affiliation', 'college']:
        if col in players_df.columns:
            affiliation_col = col
            break
    
    if affiliation_col is None:
        # Default affiliations if no data available
        unique_affiliations = ['None', 'High School', 'College']
    else:
        unique_affiliations = players_df[affiliation_col].dropna().unique()
    
    # Clean and sort affiliations
    affiliations_list = []
    for affiliation in unique_affiliations:
        clean_affiliation = str(affiliation).strip()
        if clean_affiliation and clean_affiliation.lower() not in ['nan', 'none', '']:
            affiliations_list.append(clean_affiliation)
    
    # Add standard entries if not present
    standard_affiliations = ['None', 'High School', 'International']
    for std_aff in standard_affiliations:
        if std_aff not in affiliations_list:
            affiliations_list.append(std_aff)
    
    affiliations_list = sorted(set(affiliations_list))
    
    # Create lookup table
    affiliations_data = []
    for i, affiliation in enumerate(affiliations_list, 1):
        affiliations_data.append({
            'affiliation_id': i,
            'affiliation_type': affiliation
        })
    
    df = pd.DataFrame(affiliations_data)
    
    # Apply schema
    df['affiliation_id'] = to_nullable_int(df['affiliation_id'], 16)
    df['affiliation_type'] = df['affiliation_type'].astype('string')
    
    return df


def build_dnp_reason_codes():
    """
    Build DNP reason codes lookup table.
    Maps dnp_reason_code to human-readable reason.
    """
    dnp_codes = [
        (0, "Played"),
        (1, "Coach Decision"),  # Most common DNP
        (2, "Injury"),
        (3, "Rest"),
        (4, "Personal Reasons"),
        (5, "Suspension"),
        (6, "Illness"),
        (7, "Load Management"),
        (8, "Not With Team"),
        (9, "G League Assignment"),
        (10, "Other")
    ]
    
    return pd.DataFrame(dnp_codes, columns=['dnp_reason_code', 'dnp_reason_name'])


def build_status_codes():
    """
    Build status codes lookup table.
    Maps status_code to human-readable game status.
    Based on NBA API documentation.
    """
    status_codes = [
        (1, "Scheduled"),
        (2, "In Progress"),
        (3, "Final"),
        (4, "Postponed"), 
        (5, "Cancelled")
    ]
    
    return pd.DataFrame(status_codes, columns=['status_code', 'status_name'])


def build_event_types_silver(pbp_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Build event message types lookup table for PBP data.
    
    Args:
        pbp_df: Raw PBP DataFrame (optional)
        
    Returns:
        DataFrame with event_msg_type_id and event_msg_type columns
    """
    # Standard NBA event types based on analysis
    event_types = [
        '2pt', '3pt', 'block', 'foul', 'freethrow', 'game', 
        'instantreplay', 'jumpball', 'memo', 'period', 'rebound', 
        'steal', 'substitution', 'timeout', 'turnover', 'violation'
    ]
    
    # If pbp_df provided, get unique values from actual data
    if pbp_df is not None and not pbp_df.empty and 'actionType' in pbp_df.columns:
        unique_from_data = pbp_df['actionType'].dropna().unique().tolist()
        # Combine with standard list, maintaining order
        all_types = event_types.copy()
        for event_type in unique_from_data:
            if event_type not in all_types:
                all_types.append(event_type)
        event_types = all_types
    
    # Create lookup table
    event_types_data = []
    for i, event_type in enumerate(sorted(event_types), 1):
        event_types_data.append({
            'event_msg_type_id': i,
            'event_msg_type': event_type
        })
    
    df = pd.DataFrame(event_types_data)
    
    # Apply schema
    df['event_msg_type_id'] = to_nullable_int(df['event_msg_type_id'], 8)
    df['event_msg_type'] = df['event_msg_type'].astype('string')
    
    return df


def normalize_action_type(action_type: str) -> str:
    """
    Normalize action type strings to canonical form.
    
    Args:
        action_type: Raw action type string
        
    Returns:
        Normalized action type string
    """
    if pd.isna(action_type) or action_type == '':
        return ''
    
    # Convert to lowercase and remove extra spaces
    normalized = str(action_type).lower().strip()
    
    # Normalize spacing and formatting variants
    normalizations = {
        # Free throw patterns - remove spaces
        '1 of 1': '1of1',
        '1 of 2': '1of2', 
        '1 of 3': '1of3',
        '2 of 2': '2of2',
        '2 of 3': '2of3',
        '3 of 3': '3of3',
        
        # Compound words - remove spaces and hyphens
        'bad pass': 'badpass',
        'defensive goaltending': 'defensivegoaltending',
        'delay-of-game': 'delayofgame',
        'delay of game': 'delayofgame',
        'kicked ball': 'kickedball',
        'lost ball': 'lostball',
        'offensive foul': 'offensivefoul',
        'out-of-bounds': 'outofbounds',
        'out of bounds': 'outofbounds',
        'shot clock': 'shotclock',
        
        # Violation types - standardize format
        '5secviolation': '5secviolation',
        '8-second-violation': '8secviolation', 
        '8 second violation': '8secviolation',
        
        # Shot types - standardize case
        'dunk': 'dunk',
        'jump shot': 'jumpshot',
        'layup': 'layup',
        'hook': 'hook'
    }
    
    return normalizations.get(normalized, normalized)


def build_event_actions_silver(pbp_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Build event action types lookup table for PBP data with normalized values.
    
    Args:
        pbp_df: Raw PBP DataFrame (optional)
        
    Returns:
        DataFrame with event_action_type_id and event_action_type columns
    """
    # Standard NBA action types (normalized canonical forms)
    action_types = [
        '', '1of1', '1of2', '1of3', '2of2', '2of3', '3of3', 'altercationrequest',
        'badpass', 'challenge', 'defensive', 'delayofgame', 'dunk', 'end', 'full',
        'hook', 'in', 'jumpshot', 'kickedball', 'lane', 'layup', 'lostball',
        'offensive', 'offensivefoul', 'offensivegoaltending', 'out', 'outofbounds',
        'personal', 'recovered', 'request', 'shotclock', 'start', 'technical', 'traveling'
    ]
    
    # If pbp_df provided, get unique values from actual data and normalize them
    if pbp_df is not None and not pbp_df.empty and 'subType' in pbp_df.columns:
        unique_from_data = pbp_df['subType'].dropna().apply(normalize_action_type).unique().tolist()
        # Combine with standard list, maintaining order
        all_types = action_types.copy()
        for action_type in unique_from_data:
            if action_type not in all_types:
                all_types.append(action_type)
        action_types = list(dict.fromkeys(all_types))  # Remove duplicates while preserving order
    
    # Create lookup table with normalized canonical forms
    action_types_data = []
    for i, action_type in enumerate(sorted(action_types), 0):  # Start from 0 for empty string
        action_types_data.append({
            'event_action_type_id': i,
            'event_action_type': action_type
        })
    
    df = pd.DataFrame(action_types_data)
    
    # Apply schema
    df['event_action_type_id'] = to_nullable_int(df['event_action_type_id'], 8)
    df['event_action_type'] = df['event_action_type'].astype('string')
    
    return df


def get_game_type_id(season_type: str) -> int:
    """
    Get game type ID for a season type string.
    
    Args:
        season_type: Season type string
        
    Returns:
        Game type ID (0-3)
    """
    mapping = {
        "Preseason": 0,           # Fixed: was "Pre Season" 
        "Pre Season": 0,          # Keep both variants for safety
        "Regular Season": 1,
        "All-Star": 2, 
        "Playoffs": 3,
        "PlayIn": 3,              # Added: Play-in games are playoff-related
        "IST Championship": 1     # Added: In-Season Tournament treated as regular season
    }
    
    return mapping.get(season_type, 1)  # Default to Regular Season


def get_event_msg_type_id(action_type: str, event_types_df: pd.DataFrame) -> int:
    """
    Get event message type ID for an action type string.
    
    Args:
        action_type: Action type string (e.g., 'jumpball', '3pt')
        event_types_df: Event types lookup DataFrame
        
    Returns:
        Event message type ID
    """
    if pd.isna(action_type) or action_type == '' or event_types_df.empty:
        return 1  # Default event type
    
    match = event_types_df[event_types_df['event_msg_type'] == action_type]
    return int(match['event_msg_type_id'].iloc[0]) if not match.empty else 1


def get_event_action_type_id(sub_type: str, action_types_df: pd.DataFrame) -> int:
    """
    Get event action type ID for a sub type string.
    
    Args:
        sub_type: Sub type string (e.g., 'jumpshot', 'personal')
        action_types_df: Action types lookup DataFrame
        
    Returns:
        Event action type ID
    """
    if pd.isna(sub_type) or action_types_df.empty:
        sub_type = ''  # Handle null as empty string
    
    match = action_types_df[action_types_df['event_action_type'] == sub_type]
    return int(match['event_action_type_id'].iloc[0]) if not match.empty else 0


def get_position_id(position_code: str, positions_df: pd.DataFrame) -> int:
    """
    Get position ID for a position code.
    
    Args:
        position_code: Position code string (e.g., 'PG', 'SG')
        positions_df: Positions lookup DataFrame
        
    Returns:
        Position ID or None if not found
    """
    if pd.isna(position_code):
        return None
        
    match = positions_df[positions_df['position_code'] == position_code]
    if not match.empty:
        return match.iloc[0]['position_id']
    
    return None


def get_country_id(country_name: str, countries_df: pd.DataFrame) -> int:
    """
    Get country ID for a country name.
    
    Args:
        country_name: Country name string
        countries_df: Countries lookup DataFrame
        
    Returns:
        Country ID or None if not found
    """
    if pd.isna(country_name):
        return None
        
    match = countries_df[countries_df['country_name'] == country_name]
    if not match.empty:
        return match.iloc[0]['country_id']
    
    return None


def get_affiliation_id(affiliation_type: str, affiliations_df: pd.DataFrame) -> int:
    """
    Get affiliation ID for an affiliation type.
    
    Args:
        affiliation_type: Affiliation type string
        affiliations_df: Affiliations lookup DataFrame
        
    Returns:
        Affiliation ID or None if not found
    """
    if pd.isna(affiliation_type):
        return None
        
    # Try exact match first
    match = affiliations_df[affiliations_df['affiliation_type'] == affiliation_type]
    if not match.empty:
        return match.iloc[0]['affiliation_id']
    
    # Try case-insensitive match
    match = affiliations_df[affiliations_df['affiliation_type'].str.lower() == str(affiliation_type).lower()]
    if not match.empty:
        return match.iloc[0]['affiliation_id']
    
    # Default to 'None' if available
    none_match = affiliations_df[affiliations_df['affiliation_type'] == 'None']
    if not none_match.empty:
        return none_match.iloc[0]['affiliation_id']
    
    return None