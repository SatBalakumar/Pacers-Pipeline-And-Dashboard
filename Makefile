# Pacers Analytics ETL Pipeline Makefile
# =====================================

# Project paths
PROJECT_ROOT := $(shell pwd)
DATA_DIR := $(PROJECT_ROOT)/data
DB_DIR := $(PROJECT_ROOT)/db
SCRIPTS_DIR := $(PROJECT_ROOT)/scripts
TESTS_DIR := $(PROJECT_ROOT)/tests
DB_FILE := $(DB_DIR)/pacers_analytics.db

# Python executable (use conda environment)
PYTHON := conda run -n pacers_de python

# Default target
.DEFAULT_GOAL := help

# Help target
help:
	@echo "Pacers Analytics ETL Pipeline"
	@echo "============================="
	@echo ""
	@echo "Available targets:"
	@echo "  setup        - Create necessary directories"
	@echo "  test         - Run validation tests"
	@echo "  build-silver - Build Silver tables from Bronze data"
	@echo "  build-gold   - Build Gold tables from Silver data"
	@echo "  build-all    - Build complete pipeline (Silver + Gold)"
	@echo "  validate     - Validate data integrity"
	@echo "  clean        - Clean generated files"
	@echo ""
	@echo "Dashboard targets:"
	@echo "  dashboard    - Launch Streamlit dashboard"
	@echo "  dash-setup   - Setup dashboard dependencies"
	@echo "  info         - Show database information"
	@echo "  check-data   - Check if Bronze data exists"
	@echo "  sizes        - Show file sizes"
	@echo "  backup       - Backup database"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Pacers-specific queries:"
	@echo "  pacers-games   - Show recent Pacers games"
	@echo "  pacers-players - Show Pacers roster"
	@echo "  pacers-stats   - Show Pacers season averages"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup"
	@echo "  make build-all"

# Setup directories and environment
setup:
	@echo "🏀 Setting up Pacers Analytics ETL environment..."
	@mkdir -p $(DATA_DIR)/raw
	@mkdir -p $(DATA_DIR)/silver
	@mkdir -p $(DATA_DIR)/gold
	@mkdir -p $(DB_DIR)
	@mkdir -p logs
	@echo "✅ Directories created"
	@echo "🏀 Ready to process Pacers data!"

# Run validation tests
test:
	@echo "Running ETL validation tests..."
	@cd $(PROJECT_ROOT) && $(PYTHON) $(TESTS_DIR)/test_validations.py
	@echo "✅ Validation tests completed"

# Build Silver tables from Bronze data
build-silver: setup
	@echo "🏀 Building Silver tables from Bronze data..."
	@cd $(PROJECT_ROOT) && $(PYTHON) $(SCRIPTS_DIR)/build_silver.py
	@echo "✅ Silver tables built successfully"

# Build Gold tables from Silver data  
build-gold: 
	@echo "🏆 Building Gold tables from Silver data..."
	@cd $(PROJECT_ROOT) && $(PYTHON) $(SCRIPTS_DIR)/build_gold.py
	@echo "✅ Gold tables built successfully"

# Build complete pipeline
build-all: build-silver build-gold
	@echo "🏀 Complete ETL pipeline built successfully!"
	@echo "Database: $(DB_FILE)"
	@make info

# Validate data integrity
validate:
	@echo "Validating data integrity..."
	@cd $(PROJECT_ROOT) && $(PYTHON) -c "\
from src.etl.sqlite_sink import SQLiteSink, validate_database_integrity; \
sink = SQLiteSink('$(DB_FILE)'); \
result = validate_database_integrity(sink); \
print('Integrity Check:', result['integrity_check']); \
print('Foreign Key Check:', result['foreign_key_check']); \
print('Errors:', result['errors'] if result['errors'] else 'None')"
	@echo "✅ Data validation completed"

# Show database information
info:
	@echo "Database Information"
	@echo "==================="
	@$(PYTHON) $(SCRIPTS_DIR)/show_database_info.py

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -rf $(DATA_DIR)/silver/*.parquet
	@rm -rf $(DATA_DIR)/gold/*.parquet
	@rm -f $(DB_FILE)
	@rm -rf logs/*.log
	@rm -rf __pycache__
	@find $(PROJECT_ROOT) -name "*.pyc" -delete
	@find $(PROJECT_ROOT) -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned generated files"

# Check if Bronze data exists
check-data:
	@echo "Checking for Bronze data..."
	@if [ -f "$(DATA_DIR)/raw/schedule/2024_NBA_Schedule.parquet" ]; then \
		echo "✅ Schedule data found"; \
	else \
		echo "❌ Schedule data missing"; \
	fi
	@if [ -f "$(DATA_DIR)/raw/players/2024_NBA_Players.parquet" ]; then \
		echo "✅ Players data found"; \
	else \
		echo "❌ Players data missing"; \
	fi
	@if [ -d "$(DATA_DIR)/raw/Boxscores" ] && [ -n "$$(ls -A $(DATA_DIR)/raw/Boxscores 2>/dev/null)" ]; then \
		BOXSCORE_COUNT=$$(ls $(DATA_DIR)/raw/Boxscores/*.parquet 2>/dev/null | wc -l); \
		echo "✅ Boxscore data found ($$BOXSCORE_COUNT files)"; \
	else \
		echo "❌ Boxscore data missing"; \
	fi

# Pacers-specific targets
pacers-games:
	@echo "Querying Pacers games..."
	@cd $(PROJECT_ROOT) && $(PYTHON) -c "\
from src.etl.sqlite_sink import SQLiteSink; \
sink = SQLiteSink('$(DB_FILE)'); \
result = sink.execute_query('SELECT * FROM gold_pacers_games ORDER BY game_datetime_est DESC LIMIT 10'); \
print(result.to_string(index=False))"

pacers-players:
	@echo "Querying Pacers players..."
	@cd $(PROJECT_ROOT) && $(PYTHON) -c "\
from src.etl.sqlite_sink import SQLiteSink; \
sink = SQLiteSink('$(DB_FILE)'); \
result = sink.execute_query('SELECT * FROM gold_pacers_players ORDER BY last_name'); \
print(result[['first_name', 'last_name', 'position_code', 'height_inches', 'jersey_number']].to_string(index=False))"

pacers-stats:
	@echo "Querying Pacers season averages..."
	@cd $(PROJECT_ROOT) && $(PYTHON) -c "\
from src.etl.sqlite_sink import SQLiteSink; \
sink = SQLiteSink('$(DB_FILE)'); \
result = sink.execute_query('SELECT * FROM gold_pacers_season_averages ORDER BY ppg DESC LIMIT 10'); \
print(result[['full_name', 'gp', 'mpg', 'ppg', 'rpg', 'apg']].to_string(index=False))"

# Show file sizes
sizes:
	@echo "File Sizes"
	@echo "=========="
	@if [ -d "$(DATA_DIR)/raw" ]; then \
		echo "Bronze data:"; \
		du -sh $(DATA_DIR)/raw/* 2>/dev/null || echo "  No Bronze data"; \
	fi
	@if [ -d "$(DATA_DIR)/silver" ]; then \
		echo "Silver data:"; \
		du -sh $(DATA_DIR)/silver/* 2>/dev/null || echo "  No Silver data"; \
	fi
	@if [ -d "$(DATA_DIR)/gold" ]; then \
		echo "Gold data:"; \
		du -sh $(DATA_DIR)/gold/* 2>/dev/null || echo "  No Gold data"; \
	fi
	@if [ -f "$(DB_FILE)" ]; then \
		echo "Database:"; \
		du -sh $(DB_FILE); \
	fi

# Backup database
backup:
	@if [ -f "$(DB_FILE)" ]; then \
		BACKUP_FILE="$(DB_DIR)/backup_$$(date +%Y%m%d_%H%M%S).db"; \
		cp "$(DB_FILE)" "$$BACKUP_FILE"; \
		echo "Database backed up to $$BACKUP_FILE"; \
	else \
		echo "No database found to backup"; \
	fi

# Development targets
dev-build: clean test build-all validate
	@echo "Development build completed with full validation!"

# Production targets  
prod-build: setup build-all validate
	@echo "Production build completed!"

# Quick rebuild (skip tests)
quick-build: build-all
	@echo "Quick build completed!"

# Debug target
debug:
	@echo "Debug Information"
	@echo "================="
	@echo "Project Root: $(PROJECT_ROOT)"
	@echo "Python: $(PYTHON)"
	@echo "Python Version: $$($(PYTHON) --version)"
	@echo "Conda Environment: $(CONDA_DEFAULT_ENV)"
	@make check-data
	@make sizes

# Declare phony targets
.PHONY: help setup clean test build-silver build-gold build-all validate info check-data pacers-games pacers-players pacers-stats sizes backup dev-build prod-build quick-build debug dashboard dash-setup

# Dashboard targets
dashboard:
	@echo "🏀 Launching Pacers Analytics Dashboard..."
	@if [ ! -f "$(DB_FILE)" ]; then \
		echo "❌ Database not found. Running build-all first..."; \
		$(MAKE) build-all; \
	fi
	@echo "🔄 Starting dashboard with conda environment activation..."
	@cd dashboard && bash run_dashboard.sh

dash-setup:
	@echo "Setting up dashboard dependencies in conda environment..."
	@eval "$$(conda shell.bash hook)" && conda activate pacers_de && pip install streamlit plotly
	@echo "Dashboard setup complete!"