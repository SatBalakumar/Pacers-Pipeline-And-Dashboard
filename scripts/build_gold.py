#!/usr/bin/env python3
"""
Build Gold tables from Silver data.

This script processes Silver tables and creates Gold analytical tables
with joins, aggregations, and business logic.
"""

import pandas as pd
import sys
from pathlib import Path
import logging
from typing import Dict

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.etl.silver_to_gold import (
    make_gold_games,
    make_gold_game_summary,
    make_gold_player_info,
    make_gold_player_boxscore,
    make_gold_player_averages,
    validate_gold_data
)
from src.etl.sqlite_sink import SQLiteSink, create_database_summary


# Configure logging
from datetime import datetime

# Create logs directory if it doesn't exist
project_root = Path(__file__).parent.parent
logs_dir = project_root / "logs"
logs_dir.mkdir(exist_ok=True)

# Generate timestamped log filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = logs_dir / f"build_gold_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also output to console
    ]
)
logger = logging.getLogger(__name__)


def load_silver_tables(data_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Load Silver tables from parquet files.
    
    Args:
        data_dir: Path to data directory
        
    Returns:
        Dictionary of Silver DataFrames
    """
    silver_tables = {}
    silver_dir = data_dir / "silver"
    
    if not silver_dir.exists():
        raise FileNotFoundError(f"Silver directory not found: {silver_dir}")
    
    # List of expected Silver tables
    table_names = [
        'venues_silver',
        'teams_silver',
        'gametypes_silver', 
        'positions_silver',
        'countries_silver',
        'games_silver',
        'players_silver',
        'draftpicks_silver',
        'playerboxscore_silver',
        'gameteamtotals_silver',
        'substitutions_silver',
        'officials_silver'
    ]
    
    for table_name in table_names:
        file_path = silver_dir / f"{table_name}.parquet"
        if file_path.exists():
            try:
                silver_tables[table_name] = pd.read_parquet(file_path)
                logger.info(f"Loaded {table_name}: {len(silver_tables[table_name])} rows")
            except Exception as e:
                logger.error(f"Failed to load {table_name}: {e}")
                silver_tables[table_name] = pd.DataFrame()
        else:
            logger.warning(f"Silver table not found: {file_path}")
            silver_tables[table_name] = pd.DataFrame()
    
    return silver_tables


def build_gold_tables(silver_tables: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Build all Gold tables from Silver data.
    
    Args:
        silver_tables: Dictionary of Silver DataFrames
        
    Returns:
        Dictionary of Gold DataFrames
    """
    gold_tables = {}
    
    logger.info("Building Gold tables...")
    
    # Gold games (team-centric view)
    logger.info("Building gold_games...")
    gold_tables['gold_games'] = make_gold_games(
        silver_tables['games_silver'],
        silver_tables['gameteamtotals_silver'],
        silver_tables['teams_silver']
    )
    logger.info(f"Built gold_games: {len(gold_tables['gold_games'])} rows")
    
    # Gold game summary (game-centric view)
    logger.info("Building gold_game_summary...")
    gold_tables['gold_game_summary'] = make_gold_game_summary(
        silver_tables['games_silver'],
        silver_tables['teams_silver']
    )
    logger.info(f"Built gold_game_summary: {len(gold_tables['gold_game_summary'])} rows")
    
    # Gold player info (enriched player data)
    logger.info("Building gold_player_info...")
    gold_tables['gold_player_info'] = make_gold_player_info(
        silver_tables['players_silver'],
        silver_tables['teams_silver'],
        silver_tables['positions_silver'],
        silver_tables['countries_silver'],
        silver_tables['draftpicks_silver']
    )
    logger.info(f"Built gold_player_info: {len(gold_tables['gold_player_info'])} rows")
    
    # Gold player boxscore (enriched boxscore data)
    logger.info("Building gold_player_boxscore...")
    gold_tables['gold_player_boxscore'] = make_gold_player_boxscore(
        silver_tables['playerboxscore_silver'],
        silver_tables['games_silver'],
        silver_tables['teams_silver'],
        silver_tables['positions_silver']
    )
    logger.info(f"Built gold_player_boxscore: {len(gold_tables['gold_player_boxscore'])} rows")
    
    # Gold player averages (season aggregations)
    logger.info("Building gold_player_averages...")
    gold_tables['gold_player_averages'] = make_gold_player_averages(
        gold_tables['gold_player_boxscore']
    )
    logger.info(f"Built gold_player_averages: {len(gold_tables['gold_player_averages'])} rows")
    
    logger.info("Gold tables built successfully")
    return gold_tables


def save_gold_tables(gold_tables: Dict[str, pd.DataFrame], data_dir: Path) -> None:
    """
    Save Gold tables to parquet files.
    
    Args:
        gold_tables: Dictionary of Gold DataFrames
        data_dir: Path to data directory
    """
    gold_dir = data_dir / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)
    
    for table_name, df in gold_tables.items():
        if not df.empty:
            output_path = gold_dir / f"{table_name}.parquet"
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved {table_name}: {len(df)} rows to {output_path}")
        else:
            logger.warning(f"Skipping empty table: {table_name}")


def load_to_sqlite(gold_tables: Dict[str, pd.DataFrame], db_path: Path) -> None:
    """
    Load Gold tables into SQLite database and create views.
    
    Args:
        gold_tables: Dictionary of Gold DataFrames
        db_path: Path to SQLite database
    """
    sink = SQLiteSink(str(db_path))
    
    logger.info("Loading Gold data into SQLite...")
    for table_name, df in gold_tables.items():
        if not df.empty:
            sink.insert_dataframe(df, table_name, if_exists='replace')
        else:
            logger.warning(f"Skipping empty table for SQLite: {table_name}")
    
    logger.info("Creating Gold views...")
    sink.create_views()
    
    # Get database summary
    summary = create_database_summary(sink)
    
    logger.info("Updated SQLite Database Summary:")
    logger.info(f"  Database size: {summary['database_size_mb']} MB")
    logger.info(f"  Total tables: {summary['total_tables']}")
    logger.info(f"  Total views: {summary['total_views']}")
    logger.info(f"  Total rows: {summary['total_rows']}")
    
    # Show Gold table counts
    gold_table_names = [name for name in summary['tables'].keys() if name.startswith('gold_')]
    if gold_table_names:
        logger.info("Gold tables:")
        for table in gold_table_names:
            logger.info(f"    {table}: {summary['tables'][table]} rows")
    
    # Show views
    if summary['views']:
        logger.info("Views created:")
        for view in summary['views']:
            logger.info(f"    {view}")


def validate_gold_data_wrapper(
    gold_tables: Dict[str, pd.DataFrame],
    silver_tables: Dict[str, pd.DataFrame]
) -> None:
    """
    Validate Gold data integrity.
    
    Args:
        gold_tables: Dictionary of Gold DataFrames
        silver_tables: Dictionary of Silver DataFrames for FK validation
    """
    logger.info("Validating Gold data...")
    
    try:
        validate_gold_data(
            gold_tables.get('gold_games', pd.DataFrame()),
            gold_tables.get('gold_player_boxscore', pd.DataFrame()),
            silver_tables.get('games_silver', pd.DataFrame()),
            silver_tables.get('teams_silver', pd.DataFrame())
        )
        logger.info("✅ Gold data validation passed")
    except ValueError as e:
        logger.error(f"❌ Gold data validation failed: {e}")
        raise


def create_pacers_analysis(gold_tables: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Note: Pacers-specific analysis is now handled via SQL views.
    This function is kept for compatibility but returns empty dict.
    Use SQL views: gold_pacers_games, gold_pacers_players, etc.
    """
    logger.info("Pacers analysis now handled via SQL views - skipping physical table creation")
    return {}


def main():
    """Main execution function."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    db_dir = project_root / "db"
    db_path = db_dir / "pacers_analytics.db"
    
    logger.info("Starting Gold ETL build...")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Database path: {db_path}")
    
    try:
        # Load Silver data
        logger.info("Loading Silver data...")
        silver_tables = load_silver_tables(data_dir)
        
        # Build Gold tables
        logger.info("Building Gold tables...")
        gold_tables = build_gold_tables(silver_tables)
        
        # Validate data
        logger.info("Validating data...")
        validate_gold_data_wrapper(gold_tables, silver_tables)
        
        # Create Pacers analysis
        logger.info("Creating Pacers analysis...")
        analysis_tables = create_pacers_analysis(gold_tables)
        
        # Combine all Gold tables
        all_gold_tables = {**gold_tables, **analysis_tables}
        
        # Save to parquet files
        logger.info("Saving to parquet files...")
        save_gold_tables(all_gold_tables, data_dir)
        
        # Load to SQLite
        logger.info("Loading to SQLite...")
        load_to_sqlite(all_gold_tables, db_path)
        
        logger.info("✅ Gold ETL build completed successfully!")
        
        # Print summary
        total_rows = sum(len(df) for df in all_gold_tables.values() if not df.empty)
        non_empty_tables = sum(1 for df in all_gold_tables.values() if not df.empty)
        
        logger.info(f"Summary:")
        logger.info(f"  Gold tables created: {non_empty_tables}/{len(all_gold_tables)}")
        logger.info(f"  Total rows: {total_rows:,}")
        logger.info(f"  Database: {db_path}")
        
        # Show specific Pacers data counts via SQL views
        logger.info("Pacers-specific data (available via SQL views):")
        logger.info("  Use SQL views: gold_pacers_games, gold_pacers_players,")
        logger.info("                 gold_pacers_player_stats, gold_pacers_season_averages")
        
    except Exception as e:
        logger.error(f"❌ Gold ETL build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()