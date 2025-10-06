"""
ETL utility functions for the Pacers Data Engineering project.

This module contains helper functions for data processing, file handling,
and common transformations used throughout the pipeline.
"""

import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def iso8601_to_minutes(s: Union[str, None]) -> Union[float, None]:
    """
    Parse ISO-8601 duration string to minutes as float.
    
    Args:
        s: Duration string like "PT33M19.00S" or None
        
    Returns:
        Minutes as float32 or None if input is None/invalid
        
    Examples:
        >>> iso8601_to_minutes("PT33M19.00S")
        33.316666666666666
        >>> iso8601_to_minutes("PT1H23M45.50S") 
        83.75833333333333
    """
    if s is None or pd.isna(s):
        return None
        
    # Pattern to match PT[H]H[M]M[S]S format
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?'
    match = re.match(pattern, str(s))
    
    if not match:
        return None
        
    hours, minutes, seconds = match.groups()
    
    total_minutes = 0.0
    if hours:
        total_minutes += float(hours) * 60
    if minutes:
        total_minutes += float(minutes)
    if seconds:
        total_minutes += float(seconds) / 60
        
    return total_minutes


def to_nullable_int(series: pd.Series, bits: int) -> pd.Series:
    """
    Convert series to pandas nullable integer dtype, handling empty strings and invalid values.
    
    Args:
        series: Input pandas Series
        bits: Integer bit size (8, 16, 32, 64)
        
    Returns:
        Series with Int{bits}Dtype
    """
    dtype_map = {8: 'Int8', 16: 'Int16', 32: 'Int32', 64: 'Int64'}
    if bits not in dtype_map:
        raise ValueError(f"Invalid bits: {bits}. Must be one of {list(dtype_map.keys())}")
    
    # Handle empty strings and invalid values
    series_clean = series.copy()
    
    # Replace empty strings with NaN
    if series_clean.dtype == 'object':
        series_clean = series_clean.replace('', pd.NA)
        
        # Try to convert to numeric, coercing errors to NaN
        series_clean = pd.to_numeric(series_clean, errors='coerce')
    
    return series_clean.astype(dtype_map[bits])


def coalesce(*series_or_vals) -> Union[pd.Series, any]:
    """
    Return first non-null value from series or scalar values.
    
    Args:
        *series_or_vals: Series or scalar values to coalesce
        
    Returns:
        First non-null value (Series if input contains Series, scalar otherwise)
    """
    if not series_or_vals:
        return None
        
    # Check if any input is a Series
    has_series = any(isinstance(x, pd.Series) for x in series_or_vals)
    
    if has_series:
        # Convert scalars to Series and align
        first_series = next(x for x in series_or_vals if isinstance(x, pd.Series))
        result = pd.Series(index=first_series.index, dtype='object')
        
        for val in series_or_vals:
            if isinstance(val, pd.Series):
                mask = result.isna() & val.notna()
                result.loc[mask] = val.loc[mask]
            else:
                mask = result.isna()
                result.loc[mask] = val
                
        return result
    else:
        # All scalars
        for val in series_or_vals:
            if val is not None and not pd.isna(val):
                return val
        return None


def parse_score(score_str: Union[str, None]) -> Tuple[Union[int, None], Union[int, None]]:
    """
    Parse score string like "111-105" into (home, away) tuple.
    
    Args:
        score_str: Score string in format "home-away"
        
    Returns:
        Tuple of (home_score, away_score) as integers or (None, None)
    """
    if score_str is None or pd.isna(score_str):
        return None, None
        
    try:
        parts = str(score_str).split('-')
        if len(parts) == 2:
            home_score = int(parts[0].strip())
            away_score = int(parts[1].strip())
            return home_score, away_score
    except (ValueError, AttributeError):
        pass
        
    return None, None


def parse_margin(margin_str: Union[str, None]) -> Union[int, None]:
    """
    Parse margin string like "+5" or "-12" into integer.
    
    Args:
        margin_str: Margin string with + or - prefix
        
    Returns:
        Margin as integer or None if invalid
    """
    if margin_str is None or pd.isna(margin_str):
        return None
        
    try:
        margin_clean = str(margin_str).strip().replace('+', '')
        return int(margin_clean)
    except (ValueError, AttributeError):
        return None


def ensure_pk_unique(df: pd.DataFrame, cols: List[str], table: str) -> None:
    """
    Ensure primary key uniqueness. Raise error if duplicates found.
    
    Args:
        df: DataFrame to check
        cols: List of column names forming the primary key
        table: Table name for error message
        
    Raises:
        ValueError: If duplicate primary keys found
    """
    if df.empty:
        return
        
    # Check for duplicates
    duplicates = df.duplicated(subset=cols, keep=False)
    if duplicates.any():
        dup_rows = df[duplicates][cols].drop_duplicates()
        raise ValueError(
            f"Primary key violation in {table}. "
            f"Duplicate {cols}: {dup_rows.to_dict('records')}"
        )


def ensure_fk(
    df_child: pd.DataFrame, 
    col_child: str, 
    df_parent: pd.DataFrame, 
    col_parent: str,
    child_name: str, 
    parent_name: str
) -> None:
    """
    Ensure foreign key referential integrity. Raise error if orphaned records found.
    
    Args:
        df_child: Child DataFrame containing foreign key
        col_child: Foreign key column name in child
        df_parent: Parent DataFrame containing primary key
        col_parent: Primary key column name in parent
        child_name: Child table name for error message
        parent_name: Parent table name for error message
        
    Raises:
        ValueError: If foreign key violations found
    """
    if df_child.empty or df_parent.empty:
        return
        
    # Filter out null foreign keys (allowed)
    child_fks = df_child[df_child[col_child].notna()][col_child]
    parent_pks = df_parent[col_parent]
    
    # Find orphaned foreign keys
    orphaned = child_fks[~child_fks.isin(parent_pks)]
    
    if not orphaned.empty:
        orphaned_values = orphaned.unique()[:10]  # Limit output
        raise ValueError(
            f"Foreign key violation: {child_name}.{col_child} -> {parent_name}.{col_parent}. "
            f"Orphaned values: {orphaned_values.tolist()}"
        )


def parse_height_to_inches(height_str: Union[str, None]) -> Union[int, None]:
    """
    Parse height string like "6-7" to inches.
    
    Args:
        height_str: Height in format "feet-inches"
        
    Returns:
        Total inches as integer or None if invalid
    """
    if height_str is None or pd.isna(height_str):
        return None
        
    try:
        parts = str(height_str).split('-')
        if len(parts) == 2:
            feet = int(parts[0])
            inches = int(parts[1])
            total_inches = feet * 12 + inches
            return total_inches if total_inches > 0 else None
    except (ValueError, AttributeError):
        pass
        
    return None


def parse_jersey_number(jersey_str: Union[str, None]) -> Union[int, None]:
    """
    Parse jersey number, handling "00" as 0.
    
    Args:
        jersey_str: Jersey number as string
        
    Returns:
        Jersey number as integer (0-99) or None if invalid
    """
    if jersey_str is None or pd.isna(jersey_str):
        return None
        
    try:
        jersey_clean = str(jersey_str).strip()
        if jersey_clean == "00":
            return 0
        
        jersey_num = int(jersey_clean)
        return jersey_num if 0 <= jersey_num <= 99 else None
    except (ValueError, AttributeError):
        return None


def snakecase_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert DataFrame column names to snake_case.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with snake_case column names
    """
    df_copy = df.copy()
    df_copy.columns = [
        re.sub(r'(?<!^)(?=[A-Z])', '_', col).lower().replace(' ', '_')
        for col in df_copy.columns
    ]
    return df_copy


def read_parquet_dir(
    directory: Union[str, Path], 
    pattern: str = "*.parquet"
) -> pd.DataFrame:
    """
    Read all parquet files from a directory matching a pattern.
    
    Args:
        directory: Path to directory containing parquet files
        pattern: File pattern to match (default: "*.parquet")
        
    Returns:
        Combined DataFrame from all matching files
    """
    directory = Path(directory)
    files = list(directory.glob(pattern))
    
    if not files:
        logger.warning(f"No files found matching pattern '{pattern}' in {directory}")
        return pd.DataFrame()
    
    logger.info(f"Reading {len(files)} files from {directory}")
    
    dataframes = []
    for file in tqdm(files, desc="Reading parquet files"):
        try:
            df = pd.read_parquet(file)
            # Add source file information
            df['source_file'] = file.name
            dataframes.append(df)
        except Exception as e:
            logger.error(f"Error reading {file}: {e}")
            
    if dataframes:
        return pd.concat(dataframes, ignore_index=True)
    else:
        return pd.DataFrame()


def standardize_team_names(df: pd.DataFrame, team_col: str = 'TEAM_ABBREVIATION') -> pd.DataFrame:
    """
    Standardize team abbreviations and names.
    
    Args:
        df: Input DataFrame
        team_col: Column containing team abbreviations
        
    Returns:
        DataFrame with standardized team names
    """
    team_mapping = {
        'IND': 'Indiana Pacers',
        'LAL': 'Los Angeles Lakers',
        'BOS': 'Boston Celtics',
        'GSW': 'Golden State Warriors',
        'MIA': 'Miami Heat',
        'CHI': 'Chicago Bulls',
        'NYK': 'New York Knicks',
        'BRK': 'Brooklyn Nets',
        'PHI': 'Philadelphia 76ers',
        'TOR': 'Toronto Raptors',
        'MIL': 'Milwaukee Bucks',
        'CLE': 'Cleveland Cavaliers',
        'ATL': 'Atlanta Hawks',
        'ORL': 'Orlando Magic',
        'WAS': 'Washington Wizards',
        'CHA': 'Charlotte Hornets',
        'DET': 'Detroit Pistons',
        'DEN': 'Denver Nuggets',
        'MIN': 'Minnesota Timberwolves',
        'OKC': 'Oklahoma City Thunder',
        'POR': 'Portland Trail Blazers',
        'UTA': 'Utah Jazz',
        'SAC': 'Sacramento Kings',
        'LAC': 'Los Angeles Clippers',
        'PHX': 'Phoenix Suns',
        'NOP': 'New Orleans Pelicans',
        'DAL': 'Dallas Mavericks',
        'MEM': 'Memphis Grizzlies',
        'HOU': 'Houston Rockets',
        'SAS': 'San Antonio Spurs'
    }
    
    df_copy = df.copy()
    if team_col in df_copy.columns:
        df_copy['team_full_name'] = df_copy[team_col].map(team_mapping)
    
    return df_copy


def clean_numeric_columns(df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
    """
    Clean and convert numeric columns, handling missing values.
    
    Args:
        df: Input DataFrame
        numeric_cols: List of column names to convert to numeric
        
    Returns:
        DataFrame with cleaned numeric columns
    """
    df_copy = df.copy()
    
    for col in numeric_cols:
        if col in df_copy.columns:
            # Convert to numeric, coercing errors to NaN
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
            
            # Fill NaN with 0 for stats columns (common in basketball data)
            if any(stat in col.lower() for stat in ['pts', 'reb', 'ast', 'stl', 'blk', 'min']):
                df_copy[col] = df_copy[col].fillna(0)
    
    return df_copy


def filter_pacers_data(df: pd.DataFrame, team_col: str = 'TEAM_ABBREVIATION') -> pd.DataFrame:
    """
    Filter DataFrame to include only Indiana Pacers data.
    
    Args:
        df: Input DataFrame
        team_col: Column containing team abbreviations
        
    Returns:
        DataFrame filtered for Pacers data only
    """
    if team_col in df.columns:
        return df[df[team_col] == 'IND'].copy()
    else:
        logger.warning(f"Column '{team_col}' not found. Returning original DataFrame.")
        return df


def calculate_advanced_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate advanced basketball statistics.
    
    Args:
        df: DataFrame with basic basketball stats
        
    Returns:
        DataFrame with additional advanced statistics
    """
    df_copy = df.copy()
    
    # Field Goal Percentage
    if 'FGM' in df_copy.columns and 'FGA' in df_copy.columns:
        df_copy['FG_PCT'] = np.where(
            df_copy['FGA'] > 0, 
            df_copy['FGM'] / df_copy['FGA'], 
            0
        )
    
    # Three Point Percentage
    if 'FG3M' in df_copy.columns and 'FG3A' in df_copy.columns:
        df_copy['FG3_PCT'] = np.where(
            df_copy['FG3A'] > 0, 
            df_copy['FG3M'] / df_copy['FG3A'], 
            0
        )
    
    # Free Throw Percentage
    if 'FTM' in df_copy.columns and 'FTA' in df_copy.columns:
        df_copy['FT_PCT'] = np.where(
            df_copy['FTA'] > 0, 
            df_copy['FTM'] / df_copy['FTA'], 
            0
        )
    
    # True Shooting Percentage
    if all(col in df_copy.columns for col in ['PTS', 'FGA', 'FTA']):
        df_copy['TS_PCT'] = np.where(
            (2 * (df_copy['FGA'] + 0.44 * df_copy['FTA'])) > 0,
            df_copy['PTS'] / (2 * (df_copy['FGA'] + 0.44 * df_copy['FTA'])),
            0
        )
    
    # Effective Field Goal Percentage
    if all(col in df_copy.columns for col in ['FGM', 'FG3M', 'FGA']):
        df_copy['EFG_PCT'] = np.where(
            df_copy['FGA'] > 0,
            (df_copy['FGM'] + 0.5 * df_copy['FG3M']) / df_copy['FGA'],
            0
        )
    
    return df_copy


def validate_data_quality(df: pd.DataFrame, required_cols: List[str]) -> Dict[str, any]:
    """
    Validate data quality and return summary statistics.
    
    Args:
        df: DataFrame to validate
        required_cols: List of required column names
        
    Returns:
        Dictionary with data quality metrics
    """
    validation_results = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'missing_required_columns': [],
        'null_percentages': {},
        'duplicate_rows': 0,
        'data_types': {}
    }
    
    # Check for missing required columns
    for col in required_cols:
        if col not in df.columns:
            validation_results['missing_required_columns'].append(col)
    
    # Calculate null percentages
    for col in df.columns:
        null_pct = (df[col].isnull().sum() / len(df)) * 100
        validation_results['null_percentages'][col] = round(null_pct, 2)
    
    # Check for duplicate rows
    validation_results['duplicate_rows'] = int(df.duplicated().sum())
    
    # Data types - convert to string to avoid numpy array issues
    validation_results['data_types'] = {col: str(dtype) for col, dtype in df.dtypes.to_dict().items()}
    
    return validation_results