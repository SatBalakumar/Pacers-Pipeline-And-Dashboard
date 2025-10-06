"""
Schema definitions for Silver and Gold tables.

Contains pandas dtype definitions and SQLite DDL for all tables in the pipeline.
"""

from typing import Dict, Any

# =============================================================================
# SILVER TABLE SCHEMAS (Pandas dtypes)
# =============================================================================

venues_silver_schema: Dict[str, str] = {
    'venue_id': 'Int32',
    'venue_name': 'string',
    'venue_state': 'string', 
    'venue_city': 'string'
}

teams_silver_schema: Dict[str, str] = {
    'team_id': 'Int64',           # PK
    'team_slug': 'string',
    'team_city': 'string',
    'team_name': 'string',
    'team_abbreviation': 'string',
    'is_defunct': 'boolean',
    'tricode': 'string'
}

positions_silver_schema: Dict[str, str] = {
    'position_id': 'Int8',        # PK
    'position_code': 'string'
}

countries_silver_schema: Dict[str, str] = {
    'country_id': 'Int16',        # PK
    'country_name': 'string'
}

draftpicks_silver_schema: Dict[str, str] = {
    'draftpick_id': 'Int32',      # PK
    'player_id': 'Int64',
    'draft_year': 'Int16',
    'draft_round': 'Int8',
    'draft_number': 'Int16'
}

gametypes_silver_schema: Dict[str, str] = {
    'game_type_id': 'Int8',       # PK
    'game_type': 'string'
}

affiliationtypes_silver_schema: Dict[str, str] = {
    'affiliation_id': 'Int16',     # PK
    'affiliation_type': 'string'
}

dnp_reasons_silver_schema = {
    'dnp_reason_code': 'int64',
    'dnp_reason_name': 'object'
}

status_codes_silver_schema = {
    'status_code': 'int64',
    'status_name': 'object'
}

players_silver_schema: Dict[str, str] = {
    'player_id': 'Int64',         # PK
    'first_name': 'string',
    'last_name': 'string',
    'player_slug': 'string',
    'is_active': 'boolean',
    'team_id': 'Int64',
    'jersey_num': 'Int8',
    'position_id': 'Int8',
    'height_inches': 'Int16',
    'weight': 'Int16',
    'birthdate': 'datetime64[ns]',
    'age': 'Int8',
    'country_id': 'Int16',
    'affiliation_id': 'Int16',
    'is_draft_pick': 'boolean',
    'draftpick_id': 'Int32',
    'seasons_experience': 'Int8',
    'career_start_season': 'Int16',
    'career_last_season': 'Int16',
    'is_two_way': 'boolean',
    'is_ten_day': 'boolean',
    'season': 'Int16'
}

games_silver_schema: Dict[str, str] = {
    'game_id': 'Int64',           # PK
    'season': 'Int16',
    'game_datetime_est': 'datetime64[ns]',
    'home_team_id': 'Int64',
    'away_team_id': 'Int64',
    'venue_id': 'Int32',
    'home_points': 'Int16',
    'away_points': 'Int16',
    'game_type_id': 'Int8',
    'status_code': 'Int8'
}

gameteamtotals_silver_schema: Dict[str, str] = {
    'game_id': 'Int64',           # PK part 1
    'team_id': 'Int64',           # PK part 2
    'is_home': 'boolean',
    'minutes_total': 'float32',
    'pts': 'Int16',
    'fgm': 'Int16',
    'fga': 'Int16',
    'fg3m': 'Int16',
    'fg3a': 'Int16',
    'ftm': 'Int16',
    'fta': 'Int16',
    'oreb': 'Int16',
    'dreb': 'Int16',
    'reb': 'Int16',
    'ast': 'Int16',
    'stl': 'Int16',
    'blk': 'Int16',
    'tov': 'Int16',
    'pf': 'Int16',
    'pitp': 'Int16',
    'second_chance_pts': 'Int16',
    'fastbreak_pts': 'Int16',
    'pts_off_to': 'Int16'
}

playerboxscore_silver_schema: Dict[str, str] = {
    'game_id': 'Int64',           # PK part 1
    'player_id': 'Int64',         # PK part 2
    'team_id': 'Int64',
    'starter_flag': 'boolean',
    'played_flag': 'boolean',
    'position_id': 'Int8',
    'minutes': 'float32',
    'pts': 'Int16',
    'fgm': 'Int16',
    'fga': 'Int16',
    'fg3m': 'Int16',
    'fg3a': 'Int16',
    'ftm': 'Int16',
    'fta': 'Int16',
    'oreb': 'Int16',
    'dreb': 'Int16',
    'reb': 'Int16',
    'ast': 'Int16',
    'stl': 'Int16',
    'blk': 'Int16',
    'tov': 'Int16',
    'pf': 'Int16',
    'plusminus': 'Int16',
    'dnp_reason_code': 'Int8'
}

pbp_silver_schema: Dict[str, str] = {
    'game_id': 'Int64',           # PK part 1
    'event_num': 'Int32',         # PK part 2
    'period': 'Int8',
    'pc_time': 'string',
    'wc_time': 'datetime64[ns]',
    'event_msg_type': 'Int8',
    'event_action_type': 'Int8',
    'team_id': 'Int64',
    'player1_id': 'Int64',
    'player2_id': 'Int64',
    'player3_id': 'Int64',
    'home_description': 'string',
    'visitor_description': 'string',
    'neutral_description': 'string',
    'home_score': 'Int16',
    'away_score': 'Int16',
    'score_margin': 'Int16',
    'shot_value': 'Int8',
    'shot_result': 'string',
    'shot_distance': 'float32',
    'shot_x': 'float32',
    'shot_y': 'float32',
    'shot_side': 'string',
    'foul_type_code': 'Int8',
    'turnover_type_code': 'Int8',
    'is_substitution': 'boolean',
    'is_timeout': 'boolean'
}

# =============================================================================
# SQLITE DDL DEFINITIONS
# =============================================================================

sqlite_ddl: Dict[str, str] = {
    'venues_silver': """
        CREATE TABLE IF NOT EXISTS venues_silver (
            venue_id INTEGER PRIMARY KEY,
            venue_name TEXT,
            venue_state TEXT,
            venue_city TEXT
        )
    """,
    
    'teams_silver': """
        CREATE TABLE IF NOT EXISTS teams_silver (
            team_id INTEGER PRIMARY KEY,
            team_slug TEXT,
            team_city TEXT,
            team_name TEXT,
            team_abbreviation TEXT,
            is_defunct INTEGER,
            tricode TEXT
        )
    """,
    
    'positions_silver': """
        CREATE TABLE IF NOT EXISTS positions_silver (
            position_id INTEGER PRIMARY KEY,
            position_code TEXT
        )
    """,
    
    'countries_silver': """
        CREATE TABLE IF NOT EXISTS countries_silver (
            country_id INTEGER PRIMARY KEY,
            country_name TEXT
        )
    """,
    
    'draftpicks_silver': """
        CREATE TABLE IF NOT EXISTS draftpicks_silver (
            draftpick_id INTEGER PRIMARY KEY,
            player_id INTEGER,
            draft_year INTEGER,
            draft_round INTEGER,
            draft_number INTEGER
        )
    """,
    
    'gametypes_silver': """
        CREATE TABLE IF NOT EXISTS gametypes_silver (
            game_type_id INTEGER PRIMARY KEY,
            game_type TEXT
        )
    """,
    
    'affiliationtypes_silver': """
        CREATE TABLE IF NOT EXISTS affiliationtypes_silver (
            affiliation_id INTEGER PRIMARY KEY,
            affiliation_type TEXT
        )
    """,
    
    'dnp_reasons_silver': """
        CREATE TABLE IF NOT EXISTS dnp_reasons_silver (
            dnp_reason_code INTEGER PRIMARY KEY,
            dnp_reason_name TEXT NOT NULL
        );
    """,
    
    'status_codes_silver': """
        CREATE TABLE IF NOT EXISTS status_codes_silver (
            status_code INTEGER PRIMARY KEY,
            status_name TEXT NOT NULL
        );
    """,
    
    'players_silver': """
        CREATE TABLE IF NOT EXISTS players_silver (
            player_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            player_slug TEXT,
            is_active INTEGER,
            team_id INTEGER,
            jersey_num INTEGER,
            position_id INTEGER,
            height_inches INTEGER,
            weight INTEGER,
            birthdate TEXT,
            age INTEGER,
            country_id INTEGER,
            affiliation_id INTEGER,
            is_draft_pick INTEGER,
            draftpick_id INTEGER,
            seasons_experience INTEGER,
            career_start_season INTEGER,
            career_last_season INTEGER,
            is_two_way INTEGER,
            is_ten_day INTEGER,
            season INTEGER,
            FOREIGN KEY (team_id) REFERENCES teams_silver(team_id),
            FOREIGN KEY (position_id) REFERENCES positions_silver(position_id),
            FOREIGN KEY (country_id) REFERENCES countries_silver(country_id),
            FOREIGN KEY (affiliation_id) REFERENCES affiliationtypes_silver(affiliation_id),
            FOREIGN KEY (draftpick_id) REFERENCES draftpicks_silver(draftpick_id)
        )
    """,
    
    'games_silver': """
        CREATE TABLE IF NOT EXISTS games_silver (
            game_id INTEGER PRIMARY KEY,
            season INTEGER,
            game_datetime_est TEXT,
            home_team_id INTEGER,
            away_team_id INTEGER,
            venue_id INTEGER,
            home_points INTEGER,
            away_points INTEGER,
            game_type_id INTEGER,
            status_code INTEGER,
            FOREIGN KEY (home_team_id) REFERENCES teams_silver(team_id),
            FOREIGN KEY (away_team_id) REFERENCES teams_silver(team_id),
            FOREIGN KEY (venue_id) REFERENCES venues_silver(venue_id),
            FOREIGN KEY (game_type_id) REFERENCES gametypes_silver(game_type_id)
        )
    """,
    
    'gameteamtotals_silver': """
        CREATE TABLE IF NOT EXISTS gameteamtotals_silver (
            game_id INTEGER,
            team_id INTEGER,
            is_home INTEGER,
            minutes_total REAL,
            pts INTEGER,
            fgm INTEGER,
            fga INTEGER,
            fg3m INTEGER,
            fg3a INTEGER,
            ftm INTEGER,
            fta INTEGER,
            oreb INTEGER,
            dreb INTEGER,
            reb INTEGER,
            ast INTEGER,
            stl INTEGER,
            blk INTEGER,
            tov INTEGER,
            pf INTEGER,
            pitp INTEGER,
            second_chance_pts INTEGER,
            fastbreak_pts INTEGER,
            pts_off_to INTEGER,
            PRIMARY KEY (game_id, team_id),
            FOREIGN KEY (game_id) REFERENCES games_silver(game_id),
            FOREIGN KEY (team_id) REFERENCES teams_silver(team_id)
        )
    """,
    
    'playerboxscore_silver': """
        CREATE TABLE IF NOT EXISTS playerboxscore_silver (
            game_id INTEGER,
            player_id INTEGER,
            team_id INTEGER,
            starter_flag INTEGER,
            played_flag INTEGER,
            position_id INTEGER,
            minutes REAL,
            pts INTEGER,
            fgm INTEGER,
            fga INTEGER,
            fg3m INTEGER,
            fg3a INTEGER,
            ftm INTEGER,
            fta INTEGER,
            oreb INTEGER,
            dreb INTEGER,
            reb INTEGER,
            ast INTEGER,
            stl INTEGER,
            blk INTEGER,
            tov INTEGER,
            pf INTEGER,
            plusminus INTEGER,
            dnp_reason_code INTEGER,
            PRIMARY KEY (game_id, player_id),
            FOREIGN KEY (game_id) REFERENCES games_silver(game_id),
            FOREIGN KEY (player_id) REFERENCES players_silver(player_id),
            FOREIGN KEY (team_id) REFERENCES teams_silver(team_id),
            FOREIGN KEY (position_id) REFERENCES positions_silver(position_id)
        )
    """,
    
    'pbp_silver': """
        CREATE TABLE IF NOT EXISTS pbp_silver (
            game_id INTEGER,
            event_num INTEGER,
            period INTEGER,
            pc_time TEXT,
            wc_time TEXT,
            event_msg_type INTEGER,
            event_action_type INTEGER,
            team_id INTEGER,
            player1_id INTEGER,
            player2_id INTEGER,
            player3_id INTEGER,
            home_description TEXT,
            visitor_description TEXT,
            neutral_description TEXT,
            home_score INTEGER,
            away_score INTEGER,
            score_margin INTEGER,
            shot_value INTEGER,
            shot_result TEXT,
            shot_distance REAL,
            shot_x REAL,
            shot_y REAL,
            shot_side TEXT,
            foul_type_code INTEGER,
            turnover_type_code INTEGER,
            is_substitution INTEGER,
            is_timeout INTEGER,
            PRIMARY KEY (game_id, event_num),
            FOREIGN KEY (game_id) REFERENCES games_silver(game_id),
            FOREIGN KEY (team_id) REFERENCES teams_silver(team_id),
            FOREIGN KEY (player1_id) REFERENCES players_silver(player_id),
            FOREIGN KEY (player2_id) REFERENCES players_silver(player_id),
            FOREIGN KEY (player3_id) REFERENCES players_silver(player_id)
        )
    """
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_silver_schema(table_name: str) -> Dict[str, str]:
    """Get pandas dtype schema for a silver table."""
    schema_map = {
        'venues_silver': venues_silver_schema,
        'teams_silver': teams_silver_schema,
        'positions_silver': positions_silver_schema,
        'countries_silver': countries_silver_schema,
        'draftpicks_silver': draftpicks_silver_schema,
        'gametypes_silver': gametypes_silver_schema,
        'affiliationtypes_silver': affiliationtypes_silver_schema,
        'dnp_reasons_silver': dnp_reasons_silver_schema,
        'players_silver': players_silver_schema,
        'games_silver': games_silver_schema,
        'gameteamtotals_silver': gameteamtotals_silver_schema,
        'playerboxscore_silver': playerboxscore_silver_schema,
        'pbp_silver': pbp_silver_schema
    }
    
    if table_name not in schema_map:
        raise ValueError(f"Unknown table: {table_name}")
    
    return schema_map[table_name]


def get_sqlite_ddl(table_name: str) -> str:
    """Get SQLite DDL for a table."""
    if table_name not in sqlite_ddl:
        raise ValueError(f"Unknown table: {table_name}")
    
    return sqlite_ddl[table_name]


def get_all_silver_tables() -> list:
    """Get list of all silver table names."""
    return [
        'venues_silver',
        'teams_silver', 
        'positions_silver',
        'countries_silver',
        'draftpicks_silver',
        'gametypes_silver',
        'affiliationtypes_silver',
        'dnp_reasons_silver',
        'players_silver',
        'games_silver',
        'gameteamtotals_silver',
        'playerboxscore_silver',
        'pbp_silver'
    ]