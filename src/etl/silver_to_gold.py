"""
Silver to Gold ETL transformations.

Functions to create Gold tables from Silver tables with joins and aggregations.
"""

import pandas as pd
from typing import Dict

from .utils import to_nullable_int, ensure_pk_unique
from .schemas import get_silver_schema


def make_gold_games(
    games_silver: pd.DataFrame,
    gameteamtotals_silver: pd.DataFrame, 
    teams_silver: pd.DataFrame
) -> pd.DataFrame:
    """
    Create gold_games table (2 rows per game - one for each team).
    
    Args:
        games_silver: Games silver table
        gameteamtotals_silver: Game team totals silver table
        teams_silver: Teams silver table
        
    Returns:
        Gold games DataFrame with team perspective and opponent info
    """
    if games_silver.empty or gameteamtotals_silver.empty or teams_silver.empty:
        return pd.DataFrame()
    
    # Join games with team totals
    gold_games = games_silver.merge(
        gameteamtotals_silver,
        on='game_id',
        how='inner'
    )
    
    # Join with teams info for team details
    gold_games = gold_games.merge(
        teams_silver.add_suffix('_team'),
        left_on='team_id',
        right_on='team_id_team',
        how='left'
    )
    
    # Add opponent team info via self-join
    # For each team's row, find the opponent team in the same game
    opponent_mapping = []
    for game_id in gold_games['game_id'].unique():
        game_teams = gold_games[gold_games['game_id'] == game_id][['team_id', 'is_home']].drop_duplicates()
        if len(game_teams) == 2:
            team1, team2 = game_teams.iloc[0], game_teams.iloc[1]
            opponent_mapping.append({
                'game_id': game_id,
                'team_id': team1['team_id'],
                'opp_team_id': team2['team_id']
            })
            opponent_mapping.append({
                'game_id': game_id,
                'team_id': team2['team_id'],
                'opp_team_id': team1['team_id']
            })
    
    if opponent_mapping:
        opp_df = pd.DataFrame(opponent_mapping)
        gold_games = gold_games.merge(opp_df, on=['game_id', 'team_id'], how='left')
        
        # Add opponent team details
        gold_games = gold_games.merge(
            teams_silver.add_suffix('_opp'),
            left_on='opp_team_id',
            right_on='team_id_opp',
            how='left'
        )
    else:
        gold_games['opp_team_id'] = None
        for col in teams_silver.columns:
            gold_games[f'{col}_opp'] = None
    
    # Clean up column names and select relevant columns
    result_cols = [
        'game_id', 'season', 'game_datetime_est', 'venue_id', 'game_type_id', 'status_code',
        'team_id', 'team_name_team', 'team_city_team', 'team_abbreviation_team', 
        'opp_team_id', 'team_name_opp', 'team_city_opp', 'team_abbreviation_opp',
        'is_home', 'minutes_total', 'pts', 'fgm', 'fga', 'fg3m', 'fg3a', 
        'ftm', 'fta', 'oreb', 'dreb', 'reb', 'ast', 'stl', 'blk', 'tov', 'pf',
        'pitp', 'second_chance_pts', 'fastbreak_pts', 'pts_off_to'
    ]
    
    available_cols = [col for col in result_cols if col in gold_games.columns]
    gold_games = gold_games[available_cols].copy()
    
    return gold_games.reset_index(drop=True)


def make_gold_game_summary(games_silver: pd.DataFrame, teams_silver: pd.DataFrame) -> pd.DataFrame:
    """
    Create gold_game_summary table (1 row per game).
    
    Args:
        games_silver: Games silver table
        teams_silver: Teams silver table
        
    Returns:
        Gold game summary DataFrame
    """
    if games_silver.empty or teams_silver.empty:
        return pd.DataFrame()
    
    # Join with home team info
    summary = games_silver.merge(
        teams_silver.add_suffix('_home'),
        left_on='home_team_id',
        right_on='team_id_home',
        how='left'
    )
    
    # Join with away team info
    summary = summary.merge(
        teams_silver.add_suffix('_away'),
        left_on='away_team_id', 
        right_on='team_id_away',
        how='left'
    )
    
    # Select and rename columns
    result_df = pd.DataFrame({
        'game_id': summary['game_id'],
        'season': summary['season'],
        'game_datetime_est': summary['game_datetime_est'],
        'venue_id': summary['venue_id'],
        'game_type_id': summary['game_type_id'],
        'status_code': summary['status_code'],
        'home_team_id': summary['home_team_id'],
        'home_team_name': summary['team_name_home'],
        'home_team_city': summary['team_city_home'],
        'home_team_abbreviation': summary['team_abbreviation_home'],
        'home_points': summary['home_points'],
        'away_team_id': summary['away_team_id'],
        'away_team_name': summary['team_name_away'],
        'away_team_city': summary['team_city_away'],
        'away_team_abbreviation': summary['team_abbreviation_away'],
        'away_points': summary['away_points'],
        'point_differential': summary['home_points'] - summary['away_points'],
        'total_points': summary['home_points'] + summary['away_points']
    })
    
    return result_df.reset_index(drop=True)


def make_gold_player_info(
    players_silver: pd.DataFrame,
    teams_silver: pd.DataFrame,
    positions_silver: pd.DataFrame,
    countries_silver: pd.DataFrame,
    draftpicks_silver: pd.DataFrame
) -> pd.DataFrame:
    """
    Create gold_player_info table with all player details joined.
    
    Args:
        players_silver: Players silver table
        teams_silver: Teams silver table
        positions_silver: Positions silver table
        countries_silver: Countries silver table
        draftpicks_silver: Draft picks silver table
        
    Returns:
        Gold player info DataFrame
    """
    if players_silver.empty:
        return pd.DataFrame()
    
    result = players_silver.copy()
    
    # Join with teams
    if not teams_silver.empty:
        result = result.merge(
            teams_silver[['team_id', 'team_name', 'team_city', 'team_abbreviation']].add_suffix('_team'),
            left_on='team_id',
            right_on='team_id_team',
            how='left'
        )
    
    # Join with positions
    if not positions_silver.empty:
        result = result.merge(
            positions_silver,
            on='position_id',
            how='left'
        )
    
    # Join with countries
    if not countries_silver.empty:
        result = result.merge(
            countries_silver,
            on='country_id',
            how='left'
        )
    
    # Join with draft picks
    if not draftpicks_silver.empty:
        result = result.merge(
            draftpicks_silver[['draftpick_id', 'draft_year', 'draft_round', 'draft_number']],
            on='draftpick_id',
            how='left'
        )
    
    # Add full name
    result['full_name'] = result['first_name'] + ' ' + result['last_name']
    
    return result.reset_index(drop=True)


def make_gold_player_boxscore(
    playerboxscore_silver: pd.DataFrame,
    games_silver: pd.DataFrame,
    teams_silver: pd.DataFrame,
    positions_silver: pd.DataFrame
) -> pd.DataFrame:
    """
    Create gold_player_boxscore table with game and team context.
    
    Args:
        playerboxscore_silver: Player boxscore silver table
        games_silver: Games silver table
        teams_silver: Teams silver table
        positions_silver: Positions silver table
        
    Returns:
        Gold player boxscore DataFrame
    """
    if playerboxscore_silver.empty or games_silver.empty:
        return pd.DataFrame()
    
    # Join with games for context
    result = playerboxscore_silver.merge(
        games_silver[['game_id', 'season', 'game_datetime_est', 'home_team_id', 'away_team_id']],
        on='game_id',
        how='left'
    )
    
    # Determine if player's team was home
    result['is_home'] = result['team_id'] == result['home_team_id']
    
    # Add opponent team ID
    result['opp_team_id'] = result.apply(
        lambda row: row['away_team_id'] if row['is_home'] else row['home_team_id'],
        axis=1
    )
    
    # Join with team info
    if not teams_silver.empty:
        result = result.merge(
            teams_silver[['team_id', 'team_name', 'team_abbreviation']].add_suffix('_team'),
            left_on='team_id',
            right_on='team_id_team',
            how='left'
        )
        
        result = result.merge(
            teams_silver[['team_id', 'team_name', 'team_abbreviation']].add_suffix('_opp'),
            left_on='opp_team_id',
            right_on='team_id_opp',
            how='left'
        )
    
    # Join with positions
    if not positions_silver.empty:
        result = result.merge(
            positions_silver,
            on='position_id',
            how='left'
        )
    
    # Calculate shooting percentages
    result['fg_pct'] = result['fgm'] / result['fga'].replace(0, 1)
    result['fg3_pct'] = result['fg3m'] / result['fg3a'].replace(0, 1) 
    result['ft_pct'] = result['ftm'] / result['fta'].replace(0, 1)
    
    # Replace inf with 0
    result['fg_pct'] = result['fg_pct'].replace([float('inf'), -float('inf')], 0)
    result['fg3_pct'] = result['fg3_pct'].replace([float('inf'), -float('inf')], 0)
    result['ft_pct'] = result['ft_pct'].replace([float('inf'), -float('inf')], 0)
    
    return result.reset_index(drop=True)


def make_gold_player_averages(gold_player_boxscore: pd.DataFrame) -> pd.DataFrame:
    """
    Create gold_player_averages table with season aggregations.
    
    Args:
        gold_player_boxscore: Gold player boxscore table
        
    Returns:
        Gold player averages DataFrame
    """
    if gold_player_boxscore.empty:
        return pd.DataFrame()
    
    # Filter to played games only
    played_games = gold_player_boxscore[gold_player_boxscore['played_flag'] == True].copy()
    
    if played_games.empty:
        return pd.DataFrame()
    
    # Group by player and season
    agg_dict = {
        'game_id': 'count',  # Games played
        'minutes': 'mean',   # Minutes per game
        'pts': 'mean',       # Points per game
        'reb': 'mean',       # Rebounds per game
        'ast': 'mean',       # Assists per game
        'stl': 'mean',       # Steals per game
        'blk': 'mean',       # Blocks per game
        'tov': 'mean',       # Turnovers per game
        'fgm': 'sum',        # Total field goals made
        'fga': 'sum',        # Total field goals attempted
        'fg3m': 'sum',       # Total 3-pointers made
        'fg3a': 'sum',       # Total 3-pointers attempted
        'ftm': 'sum',        # Total free throws made
        'fta': 'sum'         # Total free throws attempted
    }
    
    averages = played_games.groupby(['player_id', 'season']).agg(agg_dict).reset_index()
    
    # Rename count column
    averages.columns = [
        'player_id', 'season', 'gp', 'mpg', 'ppg', 'rpg', 'apg', 'spg', 'bpg', 'tpg',
        'fgm_total', 'fga_total', 'fg3m_total', 'fg3a_total', 'ftm_total', 'fta_total'
    ]
    
    # Calculate shooting percentages
    averages['fg_pct'] = averages['fgm_total'] / averages['fga_total'].replace(0, 1)
    averages['three_pct'] = averages['fg3m_total'] / averages['fg3a_total'].replace(0, 1)
    averages['ft_pct'] = averages['ftm_total'] / averages['fta_total'].replace(0, 1)
    
    # Replace inf with 0
    for col in ['fg_pct', 'three_pct', 'ft_pct']:
        averages[col] = averages[col].replace([float('inf'), -float('inf')], 0)
    
    # Round to reasonable precision
    for col in ['mpg', 'ppg', 'rpg', 'apg', 'spg', 'bpg', 'tpg', 'fg_pct', 'three_pct', 'ft_pct']:
        averages[col] = averages[col].round(2)
    
    return averages.reset_index(drop=True)


def create_gold_views_sql() -> Dict[str, str]:
    """
    Create SQL for Gold views.
    
    Returns:
        Dictionary of view names and their SQL definitions
    """
    views = {
        'gold_preseason_games': """
            CREATE VIEW IF NOT EXISTS gold_preseason_games AS
            SELECT * FROM gold_games 
            WHERE game_type_id = 0
        """,
        
        'gold_regular_season_games': """
            CREATE VIEW IF NOT EXISTS gold_regular_season_games AS
            SELECT * FROM gold_games 
            WHERE game_type_id = 1
        """,
        
        'gold_playoff_games': """
            CREATE VIEW IF NOT EXISTS gold_playoff_games AS
            SELECT * FROM gold_games 
            WHERE game_type_id = 3
        """,
        
        'gold_pacers_games': """
            CREATE VIEW IF NOT EXISTS gold_pacers_games AS
            SELECT * FROM gold_games 
            WHERE team_abbreviation_team = 'IND'
        """,
        
        'gold_pacers_home_games': """
            CREATE VIEW IF NOT EXISTS gold_pacers_home_games AS
            SELECT * FROM gold_games 
            WHERE team_abbreviation_team = 'IND' AND is_home = 1
        """,
        
        'gold_pacers_away_games': """
            CREATE VIEW IF NOT EXISTS gold_pacers_away_games AS
            SELECT * FROM gold_games 
            WHERE team_abbreviation_team = 'IND' AND is_home = 0
        """,
        
        'gold_pacers_players': """
            CREATE VIEW IF NOT EXISTS gold_pacers_players AS
            SELECT * FROM gold_player_info 
            WHERE team_abbreviation_team = 'IND'
        """,
        
        'gold_pacers_player_stats': """
            CREATE VIEW IF NOT EXISTS gold_pacers_player_stats AS
            SELECT * FROM gold_player_boxscore 
            WHERE team_abbreviation_team = 'IND'
        """,
        
        'gold_pacers_season_averages': """
            CREATE VIEW IF NOT EXISTS gold_pacers_season_averages AS
            SELECT pa.*, pi.first_name, pi.last_name, pi.full_name, pi.position_code
            FROM gold_player_averages pa
            JOIN gold_player_info pi ON pa.player_id = pi.player_id
            WHERE pi.team_abbreviation_team = 'IND'
        """,
        
        'gold_games_with_status': """
            CREATE VIEW IF NOT EXISTS gold_games_with_status AS
            SELECT gg.*, sc.status_name
            FROM gold_games gg
            LEFT JOIN status_codes_silver sc ON gg.status_code = sc.status_code
        """,
        
        'gold_game_summary_with_status': """
            CREATE VIEW IF NOT EXISTS gold_game_summary_with_status AS
            SELECT gs.*, sc.status_name
            FROM gold_game_summary gs
            LEFT JOIN status_codes_silver sc ON gs.status_code = sc.status_code
        """,
        
        'gold_pacers_player_stats': """
            CREATE VIEW IF NOT EXISTS gold_pacers_player_stats AS
            SELECT * FROM gold_player_boxscore 
            WHERE team_abbreviation_team = 'IND'
        """,
        
        'gold_pacers_season_averages': """
            CREATE VIEW IF NOT EXISTS gold_pacers_season_averages AS
            SELECT pa.*, pi.first_name, pi.last_name, pi.full_name, pi.position_code
            FROM gold_player_averages pa
            JOIN gold_player_info pi ON pa.player_id = pi.player_id
            WHERE pi.team_abbreviation_team = 'IND'
        """,
        
        'gold_team_standings': """
            CREATE VIEW IF NOT EXISTS gold_team_standings AS
            SELECT 
                team_id,
                team_name_team,
                team_abbreviation_team,
                season,
                COUNT(*) as games_played,
                SUM(CASE WHEN pts > (
                    SELECT pts FROM gold_games g2 
                    WHERE g2.game_id = gold_games.game_id 
                    AND g2.team_id != gold_games.team_id
                ) THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN pts < (
                    SELECT pts FROM gold_games g2 
                    WHERE g2.game_id = gold_games.game_id 
                    AND g2.team_id != gold_games.team_id
                ) THEN 1 ELSE 0 END) as losses,
                AVG(pts) as avg_points_for,
                AVG((
                    SELECT pts FROM gold_games g2 
                    WHERE g2.game_id = gold_games.game_id 
                    AND g2.team_id != gold_games.team_id
                )) as avg_points_against
            FROM gold_games
            WHERE game_type_id = 1  -- Regular season only
            GROUP BY team_id, team_name_team, team_abbreviation_team, season
            ORDER BY wins DESC, avg_points_for DESC
        """
    }
    
    return views


def validate_gold_data(
    gold_games: pd.DataFrame,
    gold_player_boxscore: pd.DataFrame,
    games_silver: pd.DataFrame,
    teams_silver: pd.DataFrame
) -> None:
    """
    Validate Gold data integrity.
    
    Args:
        gold_games: Gold games table
        gold_player_boxscore: Gold player boxscore table
        games_silver: Games silver table (for FK validation)
        teams_silver: Teams silver table (for FK validation)
        
    Raises:
        ValueError: If validation fails
    """
    # Validate gold_games foreign keys
    if not gold_games.empty and not games_silver.empty:
        # Check game_id exists in games_silver
        missing_games = gold_games[~gold_games['game_id'].isin(games_silver['game_id'])]
        if not missing_games.empty:
            raise ValueError(f"gold_games has game_ids not in games_silver: {missing_games['game_id'].unique()}")
    
    if not gold_games.empty and not teams_silver.empty:
        # Check team_id exists in teams_silver
        missing_teams = gold_games[~gold_games['team_id'].isin(teams_silver['team_id'])]
        if not missing_teams.empty:
            raise ValueError(f"gold_games has team_ids not in teams_silver: {missing_teams['team_id'].unique()}")
    
    # Validate gold_player_boxscore foreign keys
    if not gold_player_boxscore.empty and not games_silver.empty:
        missing_games = gold_player_boxscore[~gold_player_boxscore['game_id'].isin(games_silver['game_id'])]
        if not missing_games.empty:
            raise ValueError(f"gold_player_boxscore has game_ids not in games_silver: {missing_games['game_id'].unique()}")
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info("✅ Gold data validation passed")