"""
Tests for ETL schemas and data validation.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.etl.schemas import (
    get_silver_schema,
    validate_schema_compliance,
    SILVER_TABLES_DDL
)
from src.etl.utils import (
    to_nullable_int,
    ensure_pk_unique,
    ensure_fk,
    parse_height_to_inches,
    parse_jersey_number,
    iso8601_to_minutes
)


class TestSchemas:
    """Test schema definitions and validation."""
    
    def test_get_silver_schema_exists(self):
        """Test that all expected schemas exist."""
        expected_tables = [
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
        
        for table in expected_tables:
            schema = get_silver_schema(table)
            assert schema is not None, f"Schema not found for {table}"
            assert isinstance(schema, dict), f"Schema for {table} should be a dict"
    
    def test_schema_has_required_columns(self):
        """Test that schemas have expected column types."""
        # Test venues schema
        venues_schema = get_silver_schema('venues_silver')
        assert 'venue_id' in venues_schema
        assert venues_schema['venue_id'] == 'Int32'
        
        # Test players schema
        players_schema = get_silver_schema('players_silver')
        assert 'player_id' in players_schema
        assert 'first_name' in players_schema
        assert 'height_inches' in players_schema
        assert players_schema['player_id'] == 'Int64'
        assert players_schema['height_inches'] == 'Int8'
    
    def test_ddl_statements(self):
        """Test that DDL statements are valid."""
        assert len(SILVER_TABLES_DDL) > 0, "No DDL statements found"
        
        for table_name, ddl in SILVER_TABLES_DDL.items():
            assert ddl.strip().startswith('CREATE TABLE'), f"Invalid DDL for {table_name}"
            assert table_name in ddl, f"Table name not in DDL for {table_name}"


class TestSchemaValidation:
    """Test schema validation functions."""
    
    def test_validate_schema_compliance_valid(self):
        """Test validation with compliant DataFrame."""
        venues_schema = get_silver_schema('venues_silver')
        
        # Create valid DataFrame
        df = pd.DataFrame({
            'venue_id': [1, 2, 3],
            'venue_name': ['Arena 1', 'Arena 2', 'Arena 3'],
            'venue_city': ['City 1', 'City 2', 'City 3'],
            'venue_state': ['ST1', 'ST2', 'ST3'],
            'venue_capacity': [20000, 21000, 22000]
        })
        
        # Convert to proper dtypes
        for col, dtype in venues_schema.items():
            if col in df.columns:
                if dtype.startswith('Int'):
                    df[col] = to_nullable_int(df[col], dtype)
                elif dtype == 'string':
                    df[col] = df[col].astype('string')
        
        # Should not raise exception
        validate_schema_compliance(df, 'venues_silver')
    
    def test_validate_schema_compliance_missing_column(self):
        """Test validation with missing required column."""
        df = pd.DataFrame({
            'venue_id': [1, 2, 3],
            'venue_name': ['Arena 1', 'Arena 2', 'Arena 3']
            # Missing venue_city, venue_state, venue_capacity
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_schema_compliance(df, 'venues_silver')
    
    def test_validate_schema_compliance_wrong_dtype(self):
        """Test validation with wrong data type."""
        df = pd.DataFrame({
            'venue_id': ['1', '2', '3'],  # Should be Int32
            'venue_name': ['Arena 1', 'Arena 2', 'Arena 3'],
            'venue_city': ['City 1', 'City 2', 'City 3'],
            'venue_state': ['ST1', 'ST2', 'ST3'],
            'venue_capacity': [20000, 21000, 22000]
        })
        
        with pytest.raises(ValueError, match="Column venue_id has wrong dtype"):
            validate_schema_compliance(df, 'venues_silver')


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_to_nullable_int(self):
        """Test nullable integer conversion."""
        # Test regular conversion
        series = pd.Series([1, 2, 3, None])
        result = to_nullable_int(series, 'Int32')
        assert result.dtype == 'Int32'
        assert pd.isna(result.iloc[3])
        
        # Test with float values
        series = pd.Series([1.0, 2.0, 3.0, np.nan])
        result = to_nullable_int(series, 'Int64')
        assert result.dtype == 'Int64'
        assert result.iloc[0] == 1
    
    def test_ensure_pk_unique_valid(self):
        """Test PK uniqueness validation with valid data."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C']
        })
        
        # Should not raise exception
        ensure_pk_unique(df, 'id')
    
    def test_ensure_pk_unique_invalid(self):
        """Test PK uniqueness validation with duplicates."""
        df = pd.DataFrame({
            'id': [1, 2, 2],  # Duplicate
            'name': ['A', 'B', 'C']
        })
        
        with pytest.raises(ValueError, match="Primary key 'id' has duplicate values"):
            ensure_pk_unique(df, 'id')
    
    def test_ensure_fk_valid(self):
        """Test FK validation with valid references."""
        child_df = pd.DataFrame({
            'id': [1, 2, 3],
            'parent_id': [10, 20, 30]
        })
        
        parent_df = pd.DataFrame({
            'id': [10, 20, 30, 40],
            'name': ['A', 'B', 'C', 'D']
        })
        
        # Should not raise exception
        ensure_fk(child_df, 'parent_id', parent_df, 'id')
    
    def test_ensure_fk_invalid(self):
        """Test FK validation with missing references."""
        child_df = pd.DataFrame({
            'id': [1, 2, 3],
            'parent_id': [10, 20, 99]  # 99 doesn't exist in parent
        })
        
        parent_df = pd.DataFrame({
            'id': [10, 20, 30],
            'name': ['A', 'B', 'C']
        })
        
        with pytest.raises(ValueError, match="Foreign key violation"):
            ensure_fk(child_df, 'parent_id', parent_df, 'id')
    
    def test_parse_height_to_inches(self):
        """Test height parsing function."""
        assert parse_height_to_inches("6-3") == 75
        assert parse_height_to_inches("6'3\"") == 75
        assert parse_height_to_inches("6' 3\"") == 75
        assert parse_height_to_inches("6ft 3in") == 75
        assert parse_height_to_inches("5-11") == 71
        assert pd.isna(parse_height_to_inches("Invalid"))
        assert pd.isna(parse_height_to_inches(None))
    
    def test_parse_jersey_number(self):
        """Test jersey number parsing function."""
        assert parse_jersey_number("23") == 23
        assert parse_jersey_number("#23") == 23
        assert parse_jersey_number("No. 23") == 23
        assert parse_jersey_number("Jersey #45") == 45
        assert pd.isna(parse_jersey_number("Invalid"))
        assert pd.isna(parse_jersey_number(None))
    
    def test_iso8601_to_minutes(self):
        """Test ISO 8601 duration parsing."""
        assert iso8601_to_minutes("PT48M") == 48
        assert iso8601_to_minutes("PT1H36M") == 96
        assert iso8601_to_minutes("PT2H15M30S") == 135.5
        assert iso8601_to_minutes("PT30M45S") == 30.75
        assert pd.isna(iso8601_to_minutes("Invalid"))
        assert pd.isna(iso8601_to_minutes(None))


class TestDataTypes:
    """Test pandas nullable dtypes."""
    
    def test_nullable_int_types(self):
        """Test nullable integer types work correctly."""
        for int_type in ['Int8', 'Int16', 'Int32', 'Int64']:
            series = pd.Series([1, 2, None], dtype=int_type)
            assert series.dtype == int_type
            assert pd.isna(series.iloc[2])
            assert series.iloc[0] == 1
    
    def test_nullable_boolean(self):
        """Test nullable boolean type."""
        series = pd.Series([True, False, None], dtype='boolean')
        assert series.dtype == 'boolean'
        assert pd.isna(series.iloc[2])
        assert series.iloc[0] is True
    
    def test_string_dtype(self):
        """Test string dtype."""
        series = pd.Series(['A', 'B', None], dtype='string')
        assert series.dtype == 'string'
        assert pd.isna(series.iloc[2])
        assert series.iloc[0] == 'A'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])