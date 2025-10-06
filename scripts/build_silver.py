#!/usr/bin/env python3
"""
Build Silver tables from Bronze data.

This script processes Bronze parquet files and creates Silver tables
with proper schemas, validation, and data quality checks.
"""

import pandas as pd
import sys
from pathlib import Path
import logging
from typing import Dict

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.etl.bronze_to_silver import (
    make_venues_silver,
    make_teams_silver, 
    make_games_silver,
    make_players_silver,
    make_draftpicks_silver,
    make_playerboxscore_silver,
    make_gameteamtotals_silver,
    make_pbp_silver
)
from src.etl.seed_codes import (
    build_event_types_silver,
    build_event_actions_silver, 
    build_gametypes_silver,
    build_positions_silver,
    build_countries_silver,
    build_affiliationtypes_silver,
    build_dnp_reason_codes,
    build_status_codes,
    normalize_action_type,
    normalize_country_name
)
from src.etl.sqlite_sink import SQLiteSink
from src.etl.utils import ensure_pk_unique, ensure_fk


# Configure logging
from datetime import datetime

# Create logs directory if it doesn't exist
project_root = Path(__file__).parent.parent
logs_dir = project_root / "logs"
logs_dir.mkdir(exist_ok=True)

# Generate timestamped log filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = logs_dir / f"build_silver_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also output to console
    ]
)
logger = logging.getLogger(__name__)


def load_bronze_data(data_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Load all Bronze data from parquet files.
    
    Args:
        data_dir: Path to data directory
        
    Returns:
        Dictionary of DataFrames with Bronze data
    """
    bronze_data = {}
    
    # Load schedule data
    schedule_path = data_dir / "raw" / "schedule" / "2024_NBA_Schedule.parquet"
    if schedule_path.exists():
        bronze_data['schedule'] = pd.read_parquet(schedule_path)
        logger.info(f"Loaded schedule data: {len(bronze_data['schedule'])} rows")
    else:
        logger.warning(f"Schedule file not found: {schedule_path}")
        bronze_data['schedule'] = pd.DataFrame()
    
    # Load players data  
    players_path = data_dir / "raw" / "players" / "2024_NBA_Players.parquet"
    if players_path.exists():
        bronze_data['players'] = pd.read_parquet(players_path)
        logger.info(f"Loaded players data: {len(bronze_data['players'])} rows")
    else:
        logger.warning(f"Players file not found: {players_path}")
        bronze_data['players'] = pd.DataFrame()
    
    # Load boxscore data
    boxscore_dir = data_dir / "raw" / "Boxscores"
    if boxscore_dir.exists():
        boxscore_files = list(boxscore_dir.glob("*.parquet"))
        if boxscore_files:
            boxscore_list = []
            for file in boxscore_files:
                try:
                    df = pd.read_parquet(file)
                    boxscore_list.append(df)
                    logger.debug(f"Loaded boxscore file: {file.name}")
                except Exception as e:
                    logger.error(f"Failed to load {file.name}: {e}")
            
            if boxscore_list:
                bronze_data['boxscores'] = pd.concat(boxscore_list, ignore_index=True)
                logger.info(f"Loaded boxscores data: {len(bronze_data['boxscores'])} rows")
            else:
                bronze_data['boxscores'] = pd.DataFrame()
        else:
            logger.warning(f"No boxscore files found in: {boxscore_dir}")
            bronze_data['boxscores'] = pd.DataFrame()
    else:
        logger.warning(f"Boxscores directory not found: {boxscore_dir}")
        bronze_data['boxscores'] = pd.DataFrame()
    
    # Load PBP data
    pbp_dir = data_dir / "raw" / "PBP"
    if pbp_dir.exists():
        pbp_files = list(pbp_dir.glob("*.parquet"))
        if pbp_files:
            pbp_list = []
            for file in pbp_files:
                try:
                    df = pd.read_parquet(file)
                    pbp_list.append(df)
                    logger.debug(f"Loaded PBP file: {file.name}")
                except Exception as e:
                    logger.error(f"Failed to load {file.name}: {e}")
            
            if pbp_list:
                bronze_data['pbp'] = pd.concat(pbp_list, ignore_index=True)
                logger.info(f"Loaded PBP data: {len(bronze_data['pbp'])} rows")
            else:
                bronze_data['pbp'] = pd.DataFrame()
        else:
            logger.warning(f"No PBP files found in: {pbp_dir}")
            bronze_data['pbp'] = pd.DataFrame()
    else:
        logger.warning(f"PBP directory not found: {pbp_dir}")
        bronze_data['pbp'] = pd.DataFrame()
    
    # Load PBP data
    pbp_dir = data_dir / "raw" / "PBP"
    if pbp_dir.exists():
        pbp_files = list(pbp_dir.glob("*.parquet"))
        if pbp_files:
            pbp_list = []
            for file in pbp_files:
                try:
                    df = pd.read_parquet(file)
                    pbp_list.append(df)
                    logger.debug(f"Loaded PBP file: {file.name}")
                except Exception as e:
                    logger.error(f"Failed to load {file.name}: {e}")
            
            if pbp_list:
                bronze_data['pbp'] = pd.concat(pbp_list, ignore_index=True)
                logger.info(f"Loaded PBP data: {len(bronze_data['pbp'])} rows")
            else:
                bronze_data['pbp'] = pd.DataFrame()
        else:
            logger.warning(f"No PBP files found in: {pbp_dir}")
            bronze_data['pbp'] = pd.DataFrame()
    else:
        logger.warning(f"PBP directory not found: {pbp_dir}")
        bronze_data['pbp'] = pd.DataFrame()
    
    return bronze_data


def build_silver_tables(bronze_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Build all Silver tables from Bronze data.
    
    Args:
        bronze_data: Dictionary of Bronze DataFrames
        
    Returns:
        Dictionary of Silver DataFrames
    """
    silver_tables = {}
    
    logger.info("Building Silver tables...")
    
    # Build seed/lookup tables first
    logger.info("Building seed tables...")
    silver_tables['gametypes_silver'] = build_gametypes_silver(bronze_data['schedule'])
    silver_tables['positions_silver'] = build_positions_silver(bronze_data['players'])
    silver_tables['countries_silver'] = build_countries_silver(bronze_data['players'])
    silver_tables['affiliationtypes_silver'] = build_affiliationtypes_silver(bronze_data['players'])
    silver_tables['event_types_silver'] = build_event_types_silver(bronze_data['pbp'])
    silver_tables['event_actions_silver'] = build_event_actions_silver(bronze_data['pbp'])
    silver_tables['dnp_reasons_silver'] = build_dnp_reason_codes()
    silver_tables['status_codes_silver'] = build_status_codes()
    
    # Build dimension tables
    logger.info("Building dimension tables...")
    
    # Venues from schedule
    if not bronze_data['schedule'].empty:
        silver_tables['venues_silver'] = make_venues_silver(bronze_data['schedule'])
        logger.info(f"Built venues_silver: {len(silver_tables['venues_silver'])} rows")
    else:
        silver_tables['venues_silver'] = pd.DataFrame()
    
    # Teams from players and schedule
    if not bronze_data['players'].empty or not bronze_data['schedule'].empty:
        silver_tables['teams_silver'] = make_teams_silver(
            bronze_data['schedule'], 
            bronze_data['players']
        )
        logger.info(f"Built teams_silver: {len(silver_tables['teams_silver'])} rows")
    else:
        silver_tables['teams_silver'] = pd.DataFrame()
    
    # Games from schedule
    if not bronze_data['schedule'].empty:
        # Create boxscore index for points data
        boxscore_index = pd.DataFrame()  # Will be populated when we have boxscore data
        if not bronze_data['boxscores'].empty:
            # Extract points from boxscore data
            boxscore_points = []
            for _, row in bronze_data['boxscores'].iterrows():
                boxscore_points.append({
                    'game_id': int(row['gameId']) if 'gameId' in row else None,
                    'home_points': row.get('homeTeam_statistics_points'),
                    'away_points': row.get('awayTeam_statistics_points')
                })
            boxscore_index = pd.DataFrame(boxscore_points)
        
        silver_tables['games_silver'] = make_games_silver(
            bronze_data['schedule'],
            boxscore_index,
            silver_tables['venues_silver'],
            silver_tables['gametypes_silver']
        )
        logger.info(f"Built games_silver: {len(silver_tables['games_silver'])} rows")
    else:
        silver_tables['games_silver'] = pd.DataFrame()
    
    # Players and draft picks
    if not bronze_data['players'].empty:
        try:
            silver_tables['draftpicks_silver'] = make_draftpicks_silver(bronze_data['players'])
            logger.info(f"Built draftpicks_silver: {len(silver_tables['draftpicks_silver'])} rows")
        except Exception as e:
            logger.error(f"Error building draftpicks_silver: {e}")
            silver_tables['draftpicks_silver'] = pd.DataFrame()
        
        try:
            silver_tables['players_silver'] = make_players_silver(
                bronze_data['players'],
                silver_tables['positions_silver'],
                silver_tables['countries_silver'],
                silver_tables['affiliationtypes_silver'],
                silver_tables['draftpicks_silver']
            )
            logger.info(f"Built players_silver: {len(silver_tables['players_silver'])} rows")
        except Exception as e:
            logger.error(f"Error building players_silver: {e}")
            silver_tables['players_silver'] = pd.DataFrame()
    else:
        silver_tables['draftpicks_silver'] = pd.DataFrame()
        silver_tables['players_silver'] = pd.DataFrame()
    
    # Boxscore-derived tables
    if not bronze_data['boxscores'].empty:
        # Convert boxscore DataFrame to iterator of dictionaries
        boxscore_iter = (row.to_dict() for _, row in bronze_data['boxscores'].iterrows())
        
        # Player boxscores
        silver_tables['playerboxscore_silver'] = make_playerboxscore_silver(
            boxscore_iter,
            silver_tables['positions_silver'],
            silver_tables['players_silver']
        )
        logger.info(f"Built playerboxscore_silver: {len(silver_tables['playerboxscore_silver'])} rows")
        
        # Need to recreate the iterator for the next function
        boxscore_iter = (row.to_dict() for _, row in bronze_data['boxscores'].iterrows())
        
        # Game team totals
        silver_tables['gameteamtotals_silver'] = make_gameteamtotals_silver(
            boxscore_iter
        )
        logger.info(f"Built gameteamtotals_silver: {len(silver_tables['gameteamtotals_silver'])} rows")
        
        # Note: Substitutions and Officials tables not implemented yet
        # These would require additional parsing of boxscore data
        logger.info("Substitutions and Officials tables not implemented in this version")
    else:
        silver_tables['playerboxscore_silver'] = pd.DataFrame()
        silver_tables['gameteamtotals_silver'] = pd.DataFrame()
    
    # PBP-derived table
    if not bronze_data['pbp'].empty:
        try:
            silver_tables['pbp_silver'] = make_pbp_silver(
                bronze_data['pbp'],
                silver_tables['event_types_silver'],
                silver_tables['event_actions_silver']
            )
            logger.info(f"Built pbp_silver: {len(silver_tables['pbp_silver'])} rows")
        except Exception as e:
            logger.error(f"Error building pbp_silver: {e}")
            silver_tables['pbp_silver'] = pd.DataFrame()
    else:
        silver_tables['pbp_silver'] = pd.DataFrame()
        logger.info("PBP data not available - pbp_silver will be empty")
    
    logger.info("Silver tables built successfully")
    return silver_tables


def save_silver_tables(silver_tables: Dict[str, pd.DataFrame], data_dir: Path) -> None:
    """
    Save Silver tables to parquet files.
    
    Args:
        silver_tables: Dictionary of Silver DataFrames
        data_dir: Path to data directory
    """
    silver_dir = data_dir / "silver"
    silver_dir.mkdir(parents=True, exist_ok=True)
    
    for table_name, df in silver_tables.items():
        if not df.empty:
            output_path = silver_dir / f"{table_name}.parquet"
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved {table_name}: {len(df)} rows to {output_path}")
        else:
            logger.warning(f"Skipping empty table: {table_name}")


def load_to_sqlite(silver_tables: Dict[str, pd.DataFrame], db_path: Path) -> None:
    """
    Load Silver tables into SQLite database.
    
    Args:
        silver_tables: Dictionary of Silver DataFrames
        db_path: Path to SQLite database
    """
    sink = SQLiteSink(str(db_path))
    
    logger.info("Creating SQLite tables...")
    sink.create_tables()
    
    logger.info("Loading data into SQLite...")
    
    # Define insertion order to respect foreign key constraints
    # Lookup tables must be inserted before tables that reference them
    insertion_order = [
        'gametypes_silver',
        'positions_silver', 
        'countries_silver',
        'affiliationtypes_silver',
        'venues_silver',
        'teams_silver',
        'players_silver',
        'draftpicks_silver',
        'games_silver',
        'playerboxscore_silver',
        'gameteamtotals_silver',
        'pbp_silver'
    ]
    
    # Insert tables in the correct order
    for table_name in insertion_order:
        if table_name in silver_tables and not silver_tables[table_name].empty:
            sink.insert_dataframe(silver_tables[table_name], table_name, if_exists='replace')
        elif table_name in silver_tables:
            logger.warning(f"Skipping empty table for SQLite: {table_name}")
    
    # Insert any remaining tables not in the order list
    for table_name, df in silver_tables.items():
        if table_name not in insertion_order and not df.empty:
            sink.insert_dataframe(df, table_name, if_exists='replace')
        elif table_name not in insertion_order:
            logger.warning(f"Skipping empty table for SQLite: {table_name}")
    
    # Get database summary
    from src.etl.sqlite_sink import create_database_summary
    summary = create_database_summary(sink)
    
    logger.info("SQLite Database Summary:")
    logger.info(f"  Database size: {summary['database_size_mb']} MB")
    logger.info(f"  Total tables: {summary['total_tables']}")
    logger.info(f"  Total rows: {summary['total_rows']}")
    
    for table, count in summary['tables'].items():
        logger.info(f"    {table}: {count} rows")


def validate_silver_data(silver_tables: Dict[str, pd.DataFrame]) -> None:
    """
    Validate Silver data integrity.
    
    Args:
        silver_tables: Dictionary of Silver DataFrames
    """
    logger.info("Validating Silver data...")
    
    validation_errors = []
    
    # Validate primary key uniqueness
    pk_checks = {
        'venues_silver': 'venue_id',
        'teams_silver': 'team_id', 
        'gametypes_silver': 'game_type_id',
        'positions_silver': 'position_id',
        'countries_silver': 'country_id',
        'games_silver': 'game_id',
        'players_silver': 'player_id',
        'draftpicks_silver': 'draftpick_id',
        'officials_silver': 'official_id'
    }
    
    for table_name, pk_col in pk_checks.items():
        if table_name in silver_tables and not silver_tables[table_name].empty:
            try:
                ensure_pk_unique(silver_tables[table_name], [pk_col], table_name)
                logger.info(f"✅ {table_name} PK validation passed")
            except ValueError as e:
                validation_errors.append(f"{table_name}: {e}")
                logger.error(f"❌ {table_name} PK validation failed: {e}")
    
    # Validate foreign key relationships
    fk_checks = [
        ('games_silver', 'venue_id', 'venues_silver', 'venue_id'),
        ('games_silver', 'home_team_id', 'teams_silver', 'team_id'),
        ('games_silver', 'away_team_id', 'teams_silver', 'team_id'),
        ('players_silver', 'team_id', 'teams_silver', 'team_id'),
        ('players_silver', 'position_id', 'positions_silver', 'position_id'),
        ('playerboxscore_silver', 'game_id', 'games_silver', 'game_id'),
        ('playerboxscore_silver', 'player_id', 'players_silver', 'player_id'),
    ]
    
    for child_table, child_col, parent_table, parent_col in fk_checks:
        if (child_table in silver_tables and parent_table in silver_tables and 
            not silver_tables[child_table].empty and not silver_tables[parent_table].empty):
            try:
                ensure_fk(
                    silver_tables[child_table],
                    child_col,
                    silver_tables[parent_table],
                    parent_col,
                    child_table,
                    parent_table
                )
                logger.info(f"✅ {child_table}.{child_col} → {parent_table}.{parent_col} FK validation passed")
            except ValueError as e:
                validation_errors.append(f"{child_table}.{child_col} → {parent_table}.{parent_col}: {e}")
                logger.error(f"❌ FK validation failed: {e}")
    
    if validation_errors:
        logger.error(f"Data validation failed with {len(validation_errors)} errors:")
        for error in validation_errors:
            logger.error(f"  - {error}")
        raise ValueError(f"Data validation failed with {len(validation_errors)} errors")
    else:
        logger.info("✅ All Silver data validation passed")


def main():
    """Main execution function."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    db_dir = project_root / "db"
    db_path = db_dir / "pacers_analytics.db"
    
    logger.info("Starting Silver ETL build...")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Database path: {db_path}")
    
    try:
        # Load Bronze data
        logger.info("Loading Bronze data...")
        bronze_data = load_bronze_data(data_dir)
        
        # Build Silver tables
        logger.info("Building Silver tables...")
        silver_tables = build_silver_tables(bronze_data)
        
        # Validate data
        logger.info("Validating data...")
        validate_silver_data(silver_tables)
        
        # Save to parquet files
        logger.info("Saving to parquet files...")
        save_silver_tables(silver_tables, data_dir)
        
        # Load to SQLite
        logger.info("Loading to SQLite...")
        load_to_sqlite(silver_tables, db_path)
        
        logger.info("✅ Silver ETL build completed successfully!")
        
        # Print summary
        total_rows = sum(len(df) for df in silver_tables.values() if not df.empty)
        non_empty_tables = sum(1 for df in silver_tables.values() if not df.empty)
        
        logger.info(f"Summary:")
        logger.info(f"  Tables created: {non_empty_tables}/{len(silver_tables)}")
        logger.info(f"  Total rows: {total_rows:,}")
        logger.info(f"  Database: {db_path}")
        
    except Exception as e:
        logger.error(f"❌ Silver ETL build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()