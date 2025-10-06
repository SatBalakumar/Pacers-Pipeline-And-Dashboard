#  Pacers Analytics Pipeline & Dashboard

A comprehensive Bronze→Silver→Gold ETL pipeline and interactive analytics dashboard for NBA Indiana Pacers data, built with Python, pandas, SQLite, and Streamlit.

##  Features

 **Complete ETL Pipeline** - Bronze→Silver→Gold medallion architecture  
 **Interactive Dashboard** - Streamlit analytics with Pacers themin## 📋 Data Requirements

### **Expected Data Structure:**
```
data/raw/
├── players/
│   └── 2024_NBA_Players.parquet      # Player information & demographics
├── schedule/
│   └── 2024_NBA_Schedule.parquet     # Game schedule & results
├── Boxscores/                         # Individual game statistics
│   ├── 2025_0042400101_NBA_Traditional_boxscores.parquet
│   ├── 2025_0042400102_NBA_Traditional_boxscores.parquet
│   └── *.parquet                     # Additional boxscore files
└── PBP/                              # Play-by-play data (optional)
    ├── 2024_0042400101_NBA_PBP.parquet
    └── *.parquet                     # Additional PBP files
```

### **📊 Exploratory Data Analysis**
The `notebooks/` folder contains comprehensive EDA for each data source:
- **`pacers_eda.ipynb`** - Pacers-specific analysis and insights
- **`schedule_deep_eda_cleaning.ipynb`** - Game schedule data exploration
- **`players_deep_eda_cleaning.ipynb`** - Player demographics analysis
- **`boxscore_deep_eda_cleaning.ipynb`** - Game statistics exploration
- **`PBP_deep_eda_cleaning.ipynb`** - Play-by-play data analysis

### **📚 Documentation**
The `docs/` folder contains technical documentation:
- **`ERD.md`** - Complete Entity Relationship Diagram
- **`data_quality_validation.md`** - Data quality standards
- **`database_schema.dbml`** - Database schema definition
- **`erdDiagram.png`** - Visual database diagram

**⚠️ Data Not Included:** Raw NBA data files are not included due to size and licensing considerations. You'll need to obtain NBA data separately and place it in the correct directory structure.Validation** - Schema compliance and integrity checks  
 **Comprehensive Logging** - Timestamped logs for all ETL operations  
 **Pacers-Focused Analytics** - Team-specific views and insights  
 **Make Automation** - Simple commands for entire workflow  

##  Architecture

This project implements a medallion data architecture:

- ** Bronze Layer**: Raw NBA data (parquet files)
- ** Silver Layer**: Cleaned, validated data with proper schemas  
- ** Gold Layer**: Business-ready analytical tables and Pacers-focused views
- ** Dashboard**: Interactive Streamlit application with official Pacers styling

## Quick Start

### **Prerequisites**
- Conda or Miniconda installed
- Git for cloning repository
- Raw NBA data files (not included)

### **1. Setup Environment**
```bash
# Clone repository
git clone https://github.com/SatBalakumar/Pacers-Pipeline-And-Dashboard.git
cd Pacers-Pipeline-And-Dashboard

# Create and activate conda environment
conda env create -f environment.yml
conda activate pacers_de

# Verify installation
python --version  # Should be 3.10.15
```

### **2. Complete Workflow (4 Commands)**
```bash
# Clean any existing files
make clean

# Setup project structure  
make setup

# Build complete ETL pipeline (Bronze→Silver→Gold)
make build-all

# Launch interactive dashboard
make dashboard
```

**Dashboard will open at:** `http://localhost:8501`

---

## Complete Workflow Guide

### **🧹 Step 1: Clean Environment**
Remove all generated files and start fresh:
```bash
make clean
```
*Removes Silver/Gold parquet files, SQLite database, logs, and Python cache*

### **🏗️ Step 2: Setup Project Structure**  
Create necessary directories:
```bash
make setup
```
*Creates `data/`, `db/`, `logs/` directories with proper structure*

### ** Step 3: Verify Your Data**
Check that you have required Bronze data:
```bash
make check-data
```
*Expected: Schedule, Players, and Boxscore data files in `data/raw/`*

### **⚡ Step 4: Build ETL Pipeline**

**Option A: Complete Build (Recommended)**
```bash
make build-all
```

**Option B: Step-by-Step**
```bash
make build-silver  # Bronze → Silver
make build-gold    # Silver → Gold
```

**Option C: Enhanced Logging Pipeline**
```bash
python scripts/run_etl_pipeline.py
```
*All console output saved to `logs/etl_pipeline_YYYYMMDD_HHMMSS.log`*

### ** Step 5: Validate Build**
Check data integrity:
```bash
make validate  # Data integrity checks
make info      # Database summary
make sizes     # File sizes
```

### ** Step 6: Test Pacers Data**
Quick validation of Pacers-specific data:
```bash
make pacers-games    # Recent games
make pacers-players  # Current roster  
make pacers-stats    # Season averages
```

### ** Step 7: Launch Dashboard**
```bash
make dashboard
```
*Automatically checks database, activates environment, launches Streamlit*

---

## Dashboard Features

### **Home Tab**
- Project overview and statistics
- Database summary with row counts
- Recent Pacers performance metrics

### **Game Summary Tab** 
- Detailed game analysis with team comparisons
- Play-by-play data with filtering
- Game result trends and insights

### **Boxscore Browser Tab**
- Player statistics with highlighting for stat leaders
- Team filtering and game selection
- Performance metrics visualization

### **Player Lookup Tab**
- Individual player analysis and biography
- Recent game performance (last 10 games)
- Season averages and career statistics
- Recent play-by-play actions

** Official Indiana Pacers Theme:**
- Blue (RGB 0,45,98), Yellow (RGB 253,187,48), Silver (RGB 190,192,194)
- Sticky navigation tabs
- Clean, professional typography

---

## Make Commands Reference

### **Core Pipeline**
```bash
make build-silver    # Build Silver tables from Bronze data
make build-gold      # Build Gold tables from Silver data  
make build-all       # Build complete pipeline
make validate        # Validate data integrity
make test           # Run ETL validation tests
```

### **Dashboard**
```bash
make dashboard      # Launch Streamlit dashboard
make dash-setup     # Install dashboard dependencies
```

### **Data Exploration**
```bash
make pacers-games   # Recent Pacers games with results
make pacers-players # Current Pacers roster
make pacers-stats   # Top Pacers season averages
make info          # Database summary and table counts
```

### **Utilities**
```bash
make clean         # Clean all generated files
make setup         # Create project directories
make backup        # Backup SQLite database
make check-data    # Verify Bronze data exists
make sizes         # Show file sizes
make debug         # Debug information
```

### **Development Workflows**
```bash
make dev-build     # Full build with tests and validation
make prod-build    # Production build with validation
make quick-build   # Quick rebuild (skip tests)
```

---

## 📁 Project Structure

```
├── 📂 data/
│   ├── 🥉 raw/                     # Bronze: Raw NBA data
│   │   ├── players/
│   │   │   └── 2024_NBA_Players.parquet
│   │   ├── schedule/
│   │   │   └── 2024_NBA_Schedule.parquet
│   │   ├── Boxscores/              # Game boxscore files
│   │   │   └── *.parquet
│   │   └── PBP/                    # Play-by-play files (optional)
│   │       └── *.parquet
│   ├── 🥈 silver/                  # Silver: Cleaned tables  
│   └── 🥇 gold/                    # Gold: Analytical tables
├── 📂 src/etl/
│   ├── schemas.py                  # Table schemas and DDL
│   ├── utils.py                    # ETL utilities
│   ├── bronze_to_silver.py         # Bronze→Silver transformations
│   ├── silver_to_gold.py           # Silver→Gold transformations
│   └── sqlite_sink.py              # Database operations
├── 📂 scripts/
│   ├── build_silver.py             # Silver ETL pipeline
│   ├── build_gold.py               # Gold ETL pipeline
│   ├── run_etl_pipeline.py         # Complete pipeline with logging
│   └── show_database_info.py       # Database information
├── 📂 dashboard/
│   ├── app.py                      # Streamlit dashboard
│   └── run_dashboard.sh            # Dashboard launcher
├── 📂 notebooks/                   # EDA and Analysis
│   ├── pacers_eda.ipynb            # Pacers-focused analysis
│   ├── schedule_deep_eda_cleaning.ipynb  # Schedule data exploration
│   ├── players_deep_eda_cleaning.ipynb   # Player data exploration
│   ├── boxscore_deep_eda_cleaning.ipynb  # Boxscore data exploration
│   └── PBP_deep_eda_cleaning.ipynb       # Play-by-play exploration
├── 📂 docs/                        # Documentation
│   ├── ERD.md                      # Entity Relationship Diagram
│   ├── data_quality_validation.md  # Data quality documentation
│   ├── database_schema.dbml        # Database schema definition
│   └── erdDiagram.png              # Visual ERD diagram
├── 📂 tests/
│   ├── test_schemas.py             # Schema validation
│   └── test_validations.py         # ETL validation
├── 📂 logs/                        # ETL operation logs
├── 📂 db/
│   └── pacers_analytics.db         # SQLite database
├── environment.yml                 # Conda environment definition
└── Makefile                        # Build automation
```

---

## Data Schema

### ** Silver Tables (12 tables)**
- `venues_silver` - NBA arenas and venues
- `teams_silver` - NBA teams information  
- `players_silver` - Player profiles with positions
- `games_silver` - Game schedule and results
- `playerboxscore_silver` - Individual player statistics
- `gameteamtotals_silver` - Team-level game statistics
- Lookup tables: `gametypes_silver`, `positions_silver`, `countries_silver`

### ** Gold Tables (5 core tables)**
- `gold_games` - Team-centric game view with opponent data
- `gold_game_summary` - Game-centric summary view
- `gold_player_info` - Enhanced player profiles with joins
- `gold_player_boxscore` - Enriched player statistics
- `gold_player_averages` - Season aggregations

### ** Gold Views (Pacers-Focused)**
- `gold_pacers_games` - Pacers games only
- `gold_pacers_players` - Current Pacers roster
- `gold_pacers_season_averages` - Pacers player statistics
- `gold_game_summary_with_status` - Games with status info
- `gold_team_standings` - League standings
- `gold_regular_season_games`, `gold_playoff_games` - Game type filters

---

## Logging System

All ETL operations are logged with timestamps:

### **Log Files Created:**
```
logs/
├── build_silver_20251006_143022.log      # Silver layer build
├── build_gold_20251006_143045.log        # Gold layer build
├── etl_pipeline_20251006_143022.log      # Complete pipeline
└── database_info_20251006_143100.log     # Database queries
```

### **View Logs:**
```bash
ls -la logs/                    # List all log files
tail -f logs/etl_pipeline_*.log # Follow latest pipeline log
```

**Dual Output:** All logs saved to files AND displayed in console

---

## Troubleshooting

### **Database not found?**
```bash
make build-all
```

### **Environment issues?**
```bash
make debug
```

### **Need fresh start?**
```bash
make clean && make setup && make build-all
```

### **Dashboard won't start?**
```bash
make dash-setup  # Install dependencies
make dashboard   # Try again
```

---

## Example Analytics Queries

```sql
-- Top Pacers scorers this season
SELECT full_name, gp, ppg, rpg, apg 
FROM gold_pacers_season_averages 
ORDER BY ppg DESC LIMIT 10;

-- Recent Pacers games with results  
SELECT game_datetime_est, team_abbreviation_opp, pts,
       CASE WHEN pts > opp_pts THEN 'W' ELSE 'L' END as result
FROM gold_pacers_games 
ORDER BY game_datetime_est DESC LIMIT 10;

-- Team standings
SELECT team_abbreviation_team, wins, losses,
       ROUND(wins * 100.0 / (wins + losses), 1) as win_pct
FROM gold_team_standings 
ORDER BY win_pct DESC;
```

---

## Technical Details

### **Data Types**
- Nullable Pandas dtypes: `Int64`, `boolean`, `string`, `float64`
- Proper NULL handling distinguishing 0 from NULL
- Type safety with automated validation

### **Performance Features**
- Efficient parquet storage for Bronze/Silver layers
- SQLite indexing on primary/foreign keys
- Memory-efficient pandas transformations
- Incremental processing support

### **Dependencies**
- Python 3.10+
- pandas (with nullable dtypes)
- pyarrow (parquet support)
- sqlite3 (database operations)
- streamlit (dashboard)
- plotly (visualizations)

---

## 📋 Data Requirements

### **Expected Data Structure:**
```
data/raw/
├── players/
│   └── 2024_NBA_Players.parquet      # Player information & demographics
├── schedule/
│   └── 2024_NBA_Schedule.parquet     # Game schedule & results
├── Boxscores/                         # Individual game statistics
│   ├── 2025_0042400101_NBA_Traditional_boxscores.parquet
│   ├── 2025_0042400102_NBA_Traditional_boxscores.parquet
│   └── *.parquet                     # Additional boxscore files
└── PBP/                              # Play-by-play data (optional)
    ├── 2024_0042400101_NBA_PBP.parquet
    └── *.parquet                     # Additional PBP files
```

### **📊 Exploratory Data Analysis**
The `notebooks/` folder contains comprehensive EDA for each data source:
- **`pacers_eda.ipynb`** - Pacers-specific analysis and insights
- **`schedule_deep_eda_cleaning.ipynb`** - Game schedule data exploration
- **`players_deep_eda_cleaning.ipynb`** - Player demographics analysis
- **`boxscore_deep_eda_cleaning.ipynb`** - Game statistics exploration
- **`PBP_deep_eda_cleaning.ipynb`** - Play-by-play data analysis

### **📚 Documentation**
The `docs/` folder contains technical documentation:
- **`ERD.md`** - Complete Entity Relationship Diagram
- **`data_quality_validation.md`** - Data quality standards
- **`database_schema.dbml`** - Database schema definition
- **`erdDiagram.png`** - Visual database diagram

**⚠️ Data Not Included:** Raw NBA data files are not included due to size and licensing considerations. You'll need to obtain NBA data separately and place it in the correct directory structure.

---

## Contributing

1. Follow PEP-8 style guidelines
2. Add docstrings to all functions  
3. Never commit data files or databases
4. Test changes with `make test`
5. Update documentation for new features

---

Built with for Indiana Pacers analytics