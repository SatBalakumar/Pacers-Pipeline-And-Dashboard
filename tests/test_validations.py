"""
Tests for ETL validations and transformations.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path for imports  
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.etl.bronze_to_silver import (
    make_venues_silver,
    make_teams_silver,
    make_players_silver
)
from src.etl.seed_codes import (
    build_gametypes_silver,
    build_positions_silver,
    build_countries_silver
)
from src.etl.silver_to_gold import (
    make_gold_games,
    make_gold_player_info
)


class TestBronzeToSilver:
    """Test Bronze to Silver transformations."""
    
    def test_make_venues_silver(self):
        """Test venues transformation."""
        # Create sample schedule data
        schedule_data = pd.DataFrame({
            'venue_name': ['Arena A', 'Arena B', 'Arena A'],
            'venue_city': ['City 1', 'City 2', 'City 1'],
            'venue_state': ['ST1', 'ST2', 'ST1'],
            'venue_capacity': [20000, 21000, 20000]
        })
        
        result = make_venues_silver(schedule_data)
        
        # Should deduplicate venues
        assert len(result) == 2
        assert 'venue_id' in result.columns
        assert result['venue_id'].dtype == 'Int32'
        assert 'Arena A' in result['venue_name'].values
        assert 'Arena B' in result['venue_name'].values
    
    def test_make_teams_silver(self):
        """Test teams transformation."""
        # Create sample data with teams
        data = pd.DataFrame({
            'team_name': ['Lakers', 'Warriors', 'Lakers'],
            'team_city': ['Los Angeles', 'Golden State', 'Los Angeles'],
            'team_abbreviation': ['LAL', 'GSW', 'LAL'],
            'conference': ['West', 'West', 'West']
        })
        
        result = make_teams_silver(data)
        
        # Should deduplicate teams
        assert len(result) == 2
        assert 'team_id' in result.columns
        assert result['team_id'].dtype == 'Int32'
        assert 'Lakers' in result['team_name'].values
        assert 'Warriors' in result['team_name'].values
    
    def test_make_players_silver_basic(self):
        """Test basic players transformation."""
        # Create sample players data
        players_data = pd.DataFrame({
            'PERSON_ID': [123, 456],
            'FIRST_NAME': ['John', 'Jane'],
            'LAST_NAME': ['Doe', 'Smith'],
            'TEAM_ID': [1, 2],
            'POSITION': ['PG', 'SG'],
            'HEIGHT': ['6-3', '5-11'],
            'WEIGHT': [180, 165],
            'JERSEY': ['23', '45'],
            'BIRTHDATE': ['1990-01-15', '1992-03-20'],
            'COUNTRY': ['USA', 'Canada']
        })
        
        # Create lookup tables
        teams_silver = pd.DataFrame({
            'team_id': [1, 2],
            'team_name': ['Team A', 'Team B']
        })
        
        positions_silver = build_positions_silver()
        countries_silver = build_countries_silver()
        draftpicks_silver = pd.DataFrame({
            'draftpick_id': [1],
            'player_id': [999]  # No matches
        })
        
        result = make_players_silver(
            players_data,
            teams_silver,
            positions_silver,
            countries_silver,
            draftpicks_silver
        )
        
        assert len(result) == 2
        assert 'player_id' in result.columns
        assert result['player_id'].dtype == 'Int64'
        assert result['height_inches'].iloc[0] == 75  # 6-3
        assert result['height_inches'].iloc[1] == 71  # 5-11
        assert result['jersey_number'].iloc[0] == 23
        assert result['jersey_number'].iloc[1] == 45


class TestSeedCodes:
    """Test seed/lookup table builders."""
    
    def test_build_gametypes_silver(self):
        """Test game types seed data."""
        result = build_gametypes_silver()
        
        assert len(result) >= 4  # Preseason, Regular, Playoffs, etc.
        assert 'game_type_id' in result.columns
        assert 'game_type_name' in result.columns
        assert result['game_type_id'].dtype == 'Int8'
        
        # Check specific game types exist
        game_types = result['game_type_name'].tolist()
        assert 'Regular Season' in game_types
        assert 'Preseason' in game_types
        assert 'Playoffs' in game_types
    
    def test_build_positions_silver(self):
        """Test positions seed data."""
        result = build_positions_silver()
        
        assert len(result) >= 5  # PG, SG, SF, PF, C
        assert 'position_id' in result.columns
        assert 'position_code' in result.columns
        assert 'position_name' in result.columns
        assert result['position_id'].dtype == 'Int8'
        
        # Check specific positions exist
        position_codes = result['position_code'].tolist()
        assert 'PG' in position_codes
        assert 'SG' in position_codes
        assert 'SF' in position_codes
        assert 'PF' in position_codes
        assert 'C' in position_codes
    
    def test_build_countries_silver(self):
        """Test countries seed data."""
        result = build_countries_silver()
        
        assert len(result) >= 10  # Many countries
        assert 'country_id' in result.columns
        assert 'country_code' in result.columns
        assert 'country_name' in result.columns
        assert result['country_id'].dtype == 'Int16'
        
        # Check specific countries exist
        country_codes = result['country_code'].tolist()
        assert 'USA' in country_codes
        assert 'CAN' in country_codes


class TestSilverToGold:
    """Test Silver to Gold transformations."""
    
    def test_make_gold_player_info(self):
        """Test gold player info transformation."""
        # Create sample Silver tables
        players_silver = pd.DataFrame({
            'player_id': [1, 2],
            'first_name': ['John', 'Jane'],
            'last_name': ['Doe', 'Smith'],
            'team_id': [10, 20],
            'position_id': [1, 2],
            'country_id': [1, 2],
            'draftpick_id': [100, 200]
        })
        
        teams_silver = pd.DataFrame({
            'team_id': [10, 20],
            'team_name': ['Lakers', 'Warriors'],
            'team_city': ['Los Angeles', 'Golden State'],
            'team_abbreviation': ['LAL', 'GSW']
        })
        
        positions_silver = pd.DataFrame({
            'position_id': [1, 2],
            'position_code': ['PG', 'SG'],
            'position_name': ['Point Guard', 'Shooting Guard']
        })
        
        countries_silver = pd.DataFrame({
            'country_id': [1, 2],
            'country_code': ['USA', 'CAN'],
            'country_name': ['United States', 'Canada']
        })
        
        draftpicks_silver = pd.DataFrame({
            'draftpick_id': [100, 200],
            'draft_year': [2020, 2021],
            'draft_round': [1, 2],
            'draft_number': [5, 15]
        })
        
        result = make_gold_player_info(
            players_silver,
            teams_silver,
            positions_silver,
            countries_silver,
            draftpicks_silver
        )
        
        assert len(result) == 2
        assert 'full_name' in result.columns
        assert result['full_name'].iloc[0] == 'John Doe'
        assert result['full_name'].iloc[1] == 'Jane Smith'
        assert 'team_name_team' in result.columns
        assert 'position_code' in result.columns
        assert 'country_name' in result.columns


class TestDataIntegrity:
    """Test data integrity and validation."""
    
    def test_primary_key_uniqueness(self):
        """Test that primary keys are unique."""
        from src.etl.utils import ensure_pk_unique
        
        # Valid case
        df_valid = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
        try:
            ensure_pk_unique(df_valid, 'id')
            success = True
        except ValueError:
            success = False
        assert success
        
        # Invalid case with duplicates
        df_invalid = pd.DataFrame({'id': [1, 2, 2], 'name': ['A', 'B', 'C']})
        try:
            ensure_pk_unique(df_invalid, 'id')
            success = True
        except ValueError:
            success = False
        assert not success
    
    def test_foreign_key_integrity(self):
        """Test foreign key relationships."""
        from src.etl.utils import ensure_fk
        
        # Valid case
        child_df = pd.DataFrame({'id': [1, 2], 'parent_id': [10, 20]})
        parent_df = pd.DataFrame({'id': [10, 20, 30], 'name': ['A', 'B', 'C']})
        
        try:
            ensure_fk(child_df, 'parent_id', parent_df, 'id')
            success = True
        except ValueError:
            success = False
        assert success
        
        # Invalid case with missing FK
        child_df_invalid = pd.DataFrame({'id': [1, 2], 'parent_id': [10, 99]})
        
        try:
            ensure_fk(child_df_invalid, 'parent_id', parent_df, 'id')
            success = True
        except ValueError:
            success = False
        assert not success


class TestNullableTypes:
    """Test nullable pandas dtypes."""
    
    def test_nullable_integers(self):
        """Test nullable integer conversion."""
        from src.etl.utils import to_nullable_int
        
        # Regular integers
        series = pd.Series([1, 2, 3])
        result = to_nullable_int(series, 'Int32')
        assert result.dtype == 'Int32'
        assert result.iloc[0] == 1
        
        # With nulls
        series_with_nulls = pd.Series([1, 2, None])
        result = to_nullable_int(series_with_nulls, 'Int32')
        assert result.dtype == 'Int32'
        assert pd.isna(result.iloc[2])
        
        # Float to int conversion
        float_series = pd.Series([1.0, 2.0, np.nan])
        result = to_nullable_int(float_series, 'Int64')
        assert result.dtype == 'Int64'
        assert result.iloc[0] == 1
        assert pd.isna(result.iloc[2])


def run_all_tests():
    """Run all tests manually (since pytest might not be available)."""
    test_classes = [
        TestBronzeToSilver,
        TestSeedCodes,
        TestSilverToGold,
        TestDataIntegrity,
        TestNullableTypes
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        instance = test_class()
        methods = [method for method in dir(instance) if method.startswith('test_')]
        
        for method_name in methods:
            total_tests += 1
            try:
                method = getattr(instance, method_name)
                method()
                print(f"✅ {test_class.__name__}.{method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"❌ {test_class.__name__}.{method_name}: {e}")
    
    print(f"\nTest Results: {passed_tests}/{total_tests} passed")
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)