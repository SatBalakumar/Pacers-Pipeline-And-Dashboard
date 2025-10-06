# Pacers Analytics Dashboard 🏀

A comprehensive Bronze→Silver→Gold ETL pipeline for NBA Indiana Pacers analytics, built with Python, pandas, and SQLite.

## Architecture

This project implements a medallion data architecture:

- **Bronze Layer**: Raw NBA data (parquet files)
- **Silver Layer**: Cleaned, validated data with proper schemas
- **Gold Layer**: Business-ready analytical tables and aggregations

## Quick Start

### Environment Setup
```bash
# Create conda environment from file
conda env create -f environment.yml

# Activate environment
conda activate pacers_de

# Verify installation
python --version  # Should be 3.10.15
```

### Run Pipeline
```bash
# Build complete ETL pipeline
make build-all

# Query Pacers data
make pacers-stats
make pacers-games
make pacers-players
```

## Features

✅ **Bronze → Silver → Gold ETL Pipeline**
- Automated data transformation and validation
- Comprehensive schema definitions with nullable pandas dtypes
- Primary key and foreign key integrity constraints
- ISO-8601 duration parsing and data normalization

✅ **Data Validation Framework**
- Schema compliance validation
- Primary key uniqueness checks
- Foreign key referential integrity
- Comprehensive error handling and logging

✅ **SQLite Integration**
- Automatic table creation with proper DDL
- Gold analytical views (Pacers-focused)
- Database integrity validation
- Backup and maintenance utilities

✅ **Pacers-Specific Analytics**
- Player season averages and performance metrics
- Game results with opponent analysis
- Position-based statistical breakdowns
- Draft pick and country origin analysis

## Project Structure

```
├── data/
│   ├── raw/                    # Bronze layer (NBA source data)
│   │   ├── players/
│   │   │   └── 2024_NBA_Players.parquet
│   │   ├── schedule/
│   │   │   └── 2024_NBA_Schedule.parquet
│   │   └── Boxscores/*.parquet
│   ├── silver/                 # Cleaned, validated tables
│   └── gold/                   # Analytical tables
├── src/etl/
│   ├── schemas.py              # Table schemas and DDL
│   ├── utils.py                # ETL utilities and validation
│   ├── seed_codes.py           # Lookup table builders
│   ├── bronze_to_silver.py     # Bronze→Silver transformations
│   ├── silver_to_gold.py       # Silver→Gold transformations
│   └── sqlite_sink.py          # Database operations
├── scripts/
│   ├── build_silver.py         # Silver ETL pipeline
│   └── build_gold.py           # Gold ETL pipeline
├── tests/
│   ├── test_schemas.py         # Schema validation tests
│   └── test_validations.py     # ETL transformation tests
├── db/
│   └── pacers_analytics.db     # SQLite database
└── Makefile                    # Build automation
```

## Data Schema

### Silver Tables (12 tables)
- `venues_silver` - NBA arenas and venues
- `teams_silver` - NBA teams information
- `players_silver` - Player profiles with positions, draft info
- `games_silver` - Game schedule and results
- `playerboxscore_silver` - Individual player game statistics
- `gameteamtotals_silver` - Team-level game statistics
- Lookup tables: `gametypes_silver`, `positions_silver`, `countries_silver`, etc.

### Gold Tables (5+ tables)
- `gold_games` - Team-centric game view with opponent data
- `gold_player_info` - Enhanced player profiles with joins
- `gold_player_boxscore` - Enriched player statistics
- `gold_player_averages` - Season aggregations and averages
- `gold_game_summary` - Game-centric summary view

### Gold Views (10+ views)
- `gold_pacers_games` - Pacers games only
- `gold_pacers_players` - Current Pacers roster
- `gold_pacers_season_averages` - Pacers player statistics
- `gold_regular_season_games`, `gold_playoff_games` - Game type filters
- `gold_team_standings` - League standings calculation

## Make Commands

### Core Pipeline
- `make build-silver` - Build Silver tables from Bronze data
- `make build-gold` - Build Gold tables from Silver data  
- `make build-all` - Build complete pipeline
- `make validate` - Validate data integrity
- `make test` - Run ETL validation tests

### Data Exploration
- `make pacers-games` - Recent Pacers games
- `make pacers-players` - Current Pacers roster
- `make pacers-stats` - Top Pacers season averages
- `make info` - Database summary and statistics

### Utilities
- `make clean` - Clean generated files
- `make backup` - Backup database
- `make check-data` - Verify Bronze data exists
- `make debug` - Show debug information

## Technical Implementation

### Data Types
- **Nullable Pandas dtypes**: `Int8/16/32/64`, `boolean`, `string`, `float32/64`
- **Proper NULL handling**: Distinguishes between 0 and NULL values
- **Type safety**: Automated conversion with validation

### Validation Framework
```python
# Primary key uniqueness
ensure_pk_unique(df, 'player_id')

# Foreign key integrity  
ensure_fk(child_df, 'team_id', teams_df, 'team_id')

# Schema compliance
validate_schema_compliance(df, 'players_silver')
```

### Performance Features
- **Efficient parquet storage** for Bronze and Silver layers
- **SQLite indexing** on primary and foreign keys
- **Incremental processing** support for large datasets
- **Memory-efficient transformations** with pandas

## Installation & Setup

### Prerequisites
- **Conda or Miniconda** installed on your system
- **Git** for cloning the repository

### Step-by-Step Setup
```bash
# 1. Clone the repository
git clone https://github.com/SatBalakumar/Pacers-Pipeline-And-Dashboard.git
cd Pacers-Pipeline-And-Dashboard

# 2. Create conda environment
conda env create -f environment.yml

# 3. Activate environment  
conda activate pacers_de

# 4. Verify setup
python --version  # Should output: Python 3.10.15
make info         # Should show database structure

# 5. Run the pipeline (if you have data)
make build-all
```

### Alternative Setup (pip users)
```bash
# Create virtual environment
python -m venv pacers_env
source pacers_env/bin/activate  # On Windows: pacers_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify setup
python --version  # Should be Python 3.10+
```

**Note**: The conda environment (`environment.yml`) is recommended as it includes all exact package versions used in development.

## Dependencies

- **Python 3.10+**
- **pandas** (with nullable dtypes) 
- **pyarrow** (parquet support)
- **sqlite3** (database operations)
- **pathlib** (file operations)
- **Streamlit** (for dashboard - optional)

## Example Queries

```sql
-- Top Pacers scorers this season
SELECT full_name, gp, ppg, rpg, apg 
FROM gold_pacers_season_averages 
ORDER BY ppg DESC LIMIT 10;

-- Recent Pacers games with results
SELECT game_datetime_est, team_abbreviation_opp, pts, 
       CASE WHEN pts > (opponent points) THEN 'W' ELSE 'L' END as result
FROM gold_pacers_games 
ORDER BY game_datetime_est DESC LIMIT 10;

-- Team standings (wins/losses)
SELECT team_abbreviation_team, wins, losses, 
       ROUND(wins * 100.0 / (wins + losses), 1) as win_pct
FROM gold_team_standings 
WHERE season = '2024-25'
ORDER BY win_pct DESC;
```

## Development

```bash
# Run tests with validation
make dev-build

# Quick rebuild without tests  
make quick-build

# Production build with full validation
make prod-build
```

## Data Sources

This pipeline processes NBA data including:
- **Player Information**: Demographics, physical stats, draft history
- **Game Schedule**: Dates, venues, matchups, results
- **Box Scores**: Individual and team game statistics
- **Play-by-Play**: Detailed game events (optional)

### Expected Data Structure
```
data/raw/
├── players/
│   └── 2024_NBA_Players.parquet
├── schedule/
│   └── 2024_NBA_Schedule.parquet
├── Boxscores/
│   └── *.parquet files
└── PBP/
    └── *.parquet files (optional)
```

**⚠️ Data Not Included**: Raw data files are not included in this repository due to size and licensing considerations. You'll need to obtain NBA data separately and place it in the appropriate folders before running the pipeline.

Built for the Indiana Pacers analytics team with a focus on player development and game analysis.

### Run ETL Pipeline
```bash
make etl
```

### Available Make Commands
```bash
make setup          # Set up environment and dependencies
make etl             # Run full ETL pipeline
make clean           # Clean temporary files
make test            # Run tests
make docs            # Generate documentation
```

## Data Sources

- **Players**: `data/raw/players/2024_NBA_Players.parquet`
- **Schedule**: `data/raw/schedule/2024_NBA_Schedule.parquet`  
- **Boxscores**: Individual game boxscore files in `data/raw/Boxscores/`
- **Play-by-Play**: Detailed game event data in `data/raw/PBP/`

## Architecture

The pipeline follows a standard ETL pattern:
1. **Extract**: Read parquet files from `data/raw/`
2. **Transform**: Clean, validate, and process data
3. **Load**: Store results in SQLite database and processed files

## Analytics Focus

Primary analysis areas:
- Team performance metrics
- Player statistics and trends
- Game-by-game analysis
- Advanced basketball analytics

## Contributing

1. Follow PEP-8 style guidelines
2. Add docstrings to all functions
3. Keep imports organized
4. Never commit data files or databases
5. Ensure .gitkeep files maintain folder structure