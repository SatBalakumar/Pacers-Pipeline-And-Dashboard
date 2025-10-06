# Data Quality and Validation Framework
## Pacers Analytics Pipeline

**Document Version**: 1.0  
**Last Updated**: October 6, 2025  
**Pipeline Architecture**: Bronze → Silver → Gold  

---

## Executive Summary

The Pacers Analytics data pipeline implements a comprehensive data quality and validation framework that ensures data integrity, consistency, and reliability throughout the Bronze-Silver-Gold architecture. This document outlines how the pipeline handles duplicate detection, referential integrity, missing/malformed data, and consistency checks.

---

## 1. Data Quality Architecture Overview

### 1.1 Multi-Layer Validation Approach
- **Bronze Layer**: Raw data ingestion with minimal validation
- **Silver Layer**: Comprehensive data cleaning, normalization, and validation
- **Gold Layer**: Business logic validation and analytical consistency checks

### 1.2 Validation Philosophy
```
Input Data → Validate → Transform → Validate → Output
     ↓           ↓          ↓          ↓         ↓
   Bronze    Type Check  Clean &   Schema    Gold
   Layer                 Normalize  Validate  Layer
```

---

## 2. Duplicate Detection and Management

### 2.1 Primary Key Uniqueness Enforcement

#### Implementation: `ensure_pk_unique()` Function
```python
# Location: src/etl/utils.py:171-194
def ensure_pk_unique(df: pd.DataFrame, cols: List[str], table: str) -> None
```

**Functionality**:
- Detects duplicate primary keys using `pandas.duplicated()`
- Raises `ValueError` with specific duplicate values if violations found
- Applied to all Silver tables during transformation

**Tables with PK Validation**:
- `venues_silver`: `venue_id`
- `teams_silver`: `team_id` 
- `players_silver`: `player_id`
- `games_silver`: `game_id`
- `gameteamtotals_silver`: `(game_id, team_id)`
- `playerboxscore_silver`: `(game_id, player_id)`
- `draftpicks_silver`: `draftpick_id`

#### Hash-Based Deterministic ID Generation
```python
# Example from venues_silver transformation
venue_df['venue_key'] = venue_df.apply(
    lambda row: '_'.join(str(row[col]) for col in available_cols), axis=1
)
venue_df['venue_id'] = venue_df['venue_key'].apply(
    lambda x: int(hashlib.md5(x.encode()).hexdigest()[:8], 16) % 1000000
)
```

**Benefits**:
- Prevents accidental duplicates from source data variations
- Ensures reproducible IDs across pipeline runs
- Handles venue/team/player identification consistently

### 2.2 Row-Level Duplicate Detection

#### Implementation: `validate_data_quality()` Function
```python
# Location: src/etl/utils.py:492-528
validation_results['duplicate_rows'] = int(df.duplicated().sum())
```

**Process**:
- Counts complete row duplicates using `df.duplicated()`
- Reports duplicate count in validation metrics
- Applied during Silver table validation

---

## 3. Referential Integrity Management

### 3.1 Foreign Key Validation

#### Implementation: `ensure_fk()` Function
```python
# Location: src/etl/utils.py:196-232
def ensure_fk(df_child, col_child, df_parent, col_parent, child_name, parent_name)
```

**Validation Logic**:
1. **Null Handling**: Allows null foreign keys (optional relationships)
2. **Orphan Detection**: Identifies child records without matching parent
3. **Error Reporting**: Lists specific orphaned values (limited to first 10)
4. **Exception Handling**: Raises `ValueError` with detailed violation information

**Key Relationships Validated**:
```
players_silver.team_id → teams_silver.team_id
players_silver.position_id → positions_silver.position_id  
players_silver.country_id → countries_silver.country_id
games_silver.home_team_id → teams_silver.team_id
games_silver.away_team_id → teams_silver.team_id
games_silver.venue_id → venues_silver.venue_id
playerboxscore_silver.game_id → games_silver.game_id
playerboxscore_silver.player_id → players_silver.player_id
```

### 3.2 Database-Level Integrity Checks

#### Implementation: `validate_database_integrity()` Function
```python
# Location: src/etl/sqlite_sink.py:304-338
def validate_database_integrity(sink: SQLiteSink) -> Dict
```

**Database Validation Steps**:
1. **PRAGMA integrity_check**: Validates SQLite database structure
2. **PRAGMA foreign_key_check**: Identifies foreign key constraint violations
3. **Constraint Reporting**: Returns detailed violation records

### 3.3 Gold Layer Cross-Validation

#### Implementation: `validate_gold_data()` Function
```python
# Location: src/etl/silver_to_gold.py:484-515
def validate_gold_data(gold_games, gold_player_boxscore, games_silver, teams_silver)
```

**Cross-Layer Validation**:
- Validates Gold table foreign keys against Silver tables
- Ensures analytical transformations maintain referential integrity
- Prevents orphaned records in analytical layers

---

## 4. Missing and Malformed Data Handling

### 4.1 Null Value Management

#### Type-Safe Nullable Integer Conversion
```python
# Location: src/etl/utils.py:52-72
def to_nullable_int(series: pd.Series, bits: int) -> pd.Series
```

**Process**:
1. **Empty String Handling**: Converts empty strings to `pd.NA`
2. **Type Coercion**: Uses `pd.to_numeric(errors='coerce')` for safe conversion
3. **Nullable Types**: Returns `Int8`, `Int16`, `Int32`, or `Int64` nullable types
4. **Error Prevention**: Prevents downstream type errors from invalid data

#### Coalescing for Missing Values
```python
# Location: src/etl/utils.py:75-106
def coalesce(*series_or_vals) -> Union[pd.Series, any]
```

**Functionality**:
- Returns first non-null value from multiple sources
- Handles both scalar and Series inputs
- Prevents null propagation in calculations

### 4.2 Data Validation and Quality Metrics

#### Implementation: `validate_data_quality()` Function
```python
# Location: src/etl/utils.py:492-528
def validate_data_quality(df: pd.DataFrame, required_cols: List[str]) -> Dict
```

**Validation Metrics Collected**:
- **Total Rows/Columns**: Basic dimensional validation
- **Missing Required Columns**: Schema compliance checking
- **Null Percentages**: Column-level completeness metrics
- **Duplicate Rows**: Complete row duplication detection
- **Data Types**: Schema conformance validation

**Output Example**:
```json
{
    "total_rows": 1453,
    "total_columns": 23,
    "missing_required_columns": [],
    "null_percentages": {
        "player_id": 0.0,
        "first_name": 2.1,
        "height_inches": 0.8
    },
    "duplicate_rows": 0,
    "data_types": {"player_id": "Int32", "first_name": "object"}
}
```

### 4.3 Malformed Data Transformation

#### Height Parsing with Error Handling
```python
# Location: src/etl/utils.py:244-270
def parse_height_to_inches(height_str: Union[str, None]) -> Union[int, None]
```

**Robust Parsing Logic**:
- Handles various height formats (`"6-2"`, `"74"`, etc.)
- Provides sensible defaults (72 inches = 6 feet)
- Graceful error handling with try/catch blocks

#### ISO-8601 Duration Parsing
```python
# Location: src/etl/utils.py:18-51
def iso8601_to_minutes(s: Union[str, None]) -> Union[float, None]
```

**Features**:
- Regex-based parsing for `PT33M19.00S` format
- Handles hours, minutes, and seconds components
- Returns None for invalid formats (no error thrown)

---

## 5. Consistency Checks and Business Logic Validation

### 5.1 Schema Enforcement

#### Silver Table Schema Application
```python
# Applied in all make_*_silver() functions
schema = get_silver_schema('table_name')
for col, dtype in schema.items():
    if col in df.columns:
        if dtype.startswith('Int'):
            bits = int(dtype[3:])
            df[col] = to_nullable_int(df[col], bits)
        else:
            df[col] = df[col].astype(dtype)
```

**Benefits**:
- Ensures consistent data types across pipeline runs
- Prevents downstream calculation errors
- Enables reliable analytical operations

### 5.2 Calculated Field Validation

#### Shooting Percentage Calculations (Gold Layer)
```python
# Location: src/etl/silver_to_gold.py:276-283
result['fg_pct'] = result['fgm'] / result['fga'].replace(0, 1)
result['fg3_pct'] = result['fg3m'] / result['fg3a'].replace(0, 1) 
result['ft_pct'] = result['ftm'] / result['fta'].replace(0, 1)

# Handle division by zero and infinity
result['fg_pct'] = result['fg_pct'].replace([float('inf'), -float('inf')], 0)
```

**Consistency Features**:
- Prevents division by zero errors
- Handles infinity values gracefully
- Ensures percentage fields are always valid numbers

### 5.3 Game Context Validation

#### Home/Away Team Logic Validation
```python
# Location: src/etl/silver_to_gold.py:251-258
result['is_home'] = result['team_id'] == result['home_team_id']
result['opp_team_id'] = result.apply(
    lambda row: row['away_team_id'] if row['is_home'] else row['home_team_id'],
    axis=1
)
```

**Business Logic Checks**:
- Validates team assignment logic
- Ensures opponent identification is consistent
- Maintains home/away context throughout transformations

---

## 6. Error Handling and Logging Framework

### 6.1 Structured Error Handling

#### Exception Patterns Used Throughout Pipeline
```python
try:
    # Data transformation operations
    result = transform_data(df)
    ensure_pk_unique(result, ['id'], 'table_name')
    
except ValueError as e:
    logger.error(f"Data validation failed: {e}")
    raise
    
except Exception as e:
    logger.error(f"Unexpected error in transformation: {e}")
    raise
```

### 6.2 Logging Strategy

#### Implementation: Comprehensive Logging
```python
# Location: src/etl/sqlite_sink.py:12-18
import logging
logger = logging.getLogger(__name__)
```

**Logging Levels Used**:
- **INFO**: Successful operations, table creation, data insertion
- **WARNING**: Non-critical issues (empty DataFrames, skipped operations)
- **ERROR**: Validation failures, constraint violations, system errors

**Example Log Messages**:
- `"Created table: players_silver"`
- `"Inserted 1453 rows into players_silver"`
- `"Skipping empty DataFrame for table: venues_silver"`
- `"Failed to create table players_silver: UNIQUE constraint failed"`

---

## 7. Data Quality Metrics and Monitoring

### 7.1 Automated Quality Checks

#### Silver Layer Validation Summary
For each Silver table, the pipeline automatically validates:
- ✅ Primary key uniqueness
- ✅ Foreign key referential integrity  
- ✅ Schema conformance
- ✅ Required column presence
- ✅ Data type consistency
- ✅ Null value percentages

#### Gold Layer Validation Summary  
For Gold analytical tables:
- ✅ Cross-layer foreign key validation
- ✅ Calculation result consistency
- ✅ Business logic validation
- ✅ Analytical metric accuracy

### 7.2 Pipeline Quality Metrics

#### Key Performance Indicators
- **Data Completeness**: % of expected records successfully processed
- **Data Accuracy**: % of records passing validation checks
- **Referential Integrity**: % of foreign key relationships maintained
- **Schema Compliance**: % of fields matching expected types
- **Duplicate Rate**: % of duplicate records detected and handled

#### Validation Success Criteria
```
✅ All primary keys unique across all tables
✅ All foreign key relationships maintained
✅ Zero orphaned records in analytical layers
✅ All calculated fields within expected ranges
✅ All schema requirements met
✅ Error rate < 1% of total records processed
```

---

## 8. Recovery and Remediation Procedures

### 8.1 Data Quality Failures

#### Primary Key Violations
**Detection**: `ensure_pk_unique()` raises ValueError with duplicate details
**Resolution**:
1. Investigate source data for unexpected duplicates
2. Review ID generation logic for deterministic conflicts
3. Implement additional deduplication rules if needed
4. Re-run pipeline after source correction

#### Foreign Key Violations  
**Detection**: `ensure_fk()` raises ValueError with orphaned record details
**Resolution**:
1. Check for missing parent records in lookup tables
2. Verify join logic in transformation functions
3. Add missing lookup entries if appropriate
4. Implement default/fallback values for optional relationships

### 8.2 Data Completeness Issues

#### Missing Required Columns
**Detection**: `validate_data_quality()` reports missing columns
**Resolution**:
1. Check source file schema changes
2. Update schema mappings in transformation functions
3. Implement column aliasing if source renamed fields
4. Add default value handling for newly required fields

#### High Null Percentages
**Detection**: Quality metrics report >20% null values
**Investigation**:
1. Analyze source data quality trends
2. Check for upstream data collection issues
3. Implement additional data cleaning rules
4. Update business logic to handle increased nulls

---

## 9. Future Enhancements

### 9.1 Advanced Data Quality Features

#### Statistical Outlier Detection
- Implement z-score analysis for numerical fields
- Flag statistical anomalies in player performance data
- Add seasonal trending analysis for data quality monitoring

#### Real-time Data Quality Monitoring
- Stream processing validation for live game data
- Real-time alerting for data quality degradation
- Dashboard integration for quality metrics visualization

#### Machine Learning-Based Validation
- Anomaly detection models for unusual data patterns
- Predictive data quality scoring
- Automated data correction suggestions

### 9.2 Enhanced Consistency Checks

#### Cross-Game Validation
- Player performance consistency across games
- Team total vs. individual player stat reconciliation
- Season-to-season player development validation

#### Business Rule Validation
- Salary cap compliance checking (when salary data available)
- Roster size and composition validation
- Game scheduling and timing consistency checks

---

## 10. Conclusion

The Pacers Analytics pipeline implements a robust, multi-layered data quality and validation framework that ensures high data integrity throughout the Bronze-Silver-Gold architecture. Through comprehensive duplicate detection, referential integrity enforcement, missing data handling, and consistency checks, the pipeline delivers reliable, high-quality data for analytical and dashboard applications.

**Key Strengths**:
- ✅ Proactive validation at each transformation layer
- ✅ Comprehensive error handling and logging
- ✅ Automated quality metric collection
- ✅ Strong referential integrity enforcement
- ✅ Robust handling of malformed source data

**Quality Assurance Commitment**:
The pipeline prioritizes data reliability over speed, implementing thorough validation checks that ensure downstream analytics and dashboard applications can depend on consistent, accurate data for business decision-making.

---

**Document Maintained By**: Data Engineering Team  
**Review Cycle**: Monthly or after major pipeline changes  
**Related Documentation**: 
- Database Schema (database_schema.dbml)
- ETL Pipeline Documentation (README.md)
- Dashboard Integration Guide