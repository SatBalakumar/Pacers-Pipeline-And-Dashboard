"""
SQLite database sink for ETL pipeline.

Handles all SQLite database operations including table creation, data insertion,
and view management.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import logging

from .schemas import sqlite_ddl
from .silver_to_gold import create_gold_views_sql


logger = logging.getLogger(__name__)


class SQLiteSink:
    """SQLite database sink for the ETL pipeline."""
    
    def __init__(self, db_path: str):
        """
        Initialize SQLite sink.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def create_tables(self) -> None:
        """Create all Silver tables in SQLite database."""
        with self._get_connection() as conn:
            for table_name, ddl in sqlite_ddl.items():
                try:
                    conn.execute(ddl)
                    logger.info(f"Created table: {table_name}")
                except sqlite3.Error as e:
                    logger.error(f"Failed to create table {table_name}: {e}")
                    raise
            
            conn.commit()
            logger.info("All Silver tables created successfully")
    
    def insert_dataframe(
        self, 
        df: pd.DataFrame, 
        table_name: str,
        if_exists: str = 'replace'
    ) -> None:
        """
        Insert DataFrame into SQLite table.
        
        Args:
            df: DataFrame to insert
            table_name: Name of the table
            if_exists: How to handle existing data ('replace', 'append', 'fail')
        """
        if df.empty:
            logger.warning(f"Skipping empty DataFrame for table: {table_name}")
            return
        
        # Convert pandas nullable dtypes to SQLite-compatible types
        df_clean = self._prepare_dataframe_for_sqlite(df)
        
        with self._get_connection() as conn:
            try:
                # Temporarily disable foreign key constraints during insertion
                conn.execute("PRAGMA foreign_keys = OFF")
                
                # For large tables, insert in batches to avoid "too many SQL variables" error
                if len(df_clean) > 5000:
                    # Insert in chunks for large datasets
                    batch_size = 1000
                    for i in range(0, len(df_clean), batch_size):
                        batch = df_clean.iloc[i:i+batch_size]
                        batch.to_sql(
                            table_name,
                            conn,
                            if_exists='append' if i > 0 else if_exists,
                            index=False,
                            method='multi'
                        )
                else:
                    # Small tables can be inserted at once
                    df_clean.to_sql(
                        table_name,
                        conn,
                        if_exists=if_exists,
                        index=False,
                        method='multi'
                    )
                
                # Re-enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON")
                conn.commit()
                
                logger.info(f"Inserted {len(df_clean)} rows into {table_name}")
            except Exception as e:
                logger.error(f"Failed to insert data into {table_name}: {e}")
                raise
    
    def _prepare_dataframe_for_sqlite(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare DataFrame for SQLite insertion by handling nullable dtypes.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with SQLite-compatible types
        """
        df_clean = df.copy()
        
        # Convert nullable integer types to regular int64 with NaN for nulls
        for col in df_clean.columns:
            dtype = df_clean[col].dtype
            
            if dtype.name.startswith(('Int', 'boolean')):
                # Convert nullable types to regular types
                if dtype.name == 'boolean':
                    df_clean[col] = df_clean[col].astype('object')
                else:
                    df_clean[col] = df_clean[col].astype('float64')
            
            elif dtype.name == 'string':
                # Convert string dtype to object
                df_clean[col] = df_clean[col].astype('object')
        
        return df_clean
    
    def create_views(self) -> None:
        """Create all Gold views in SQLite database."""
        views = create_gold_views_sql()
        
        with self._get_connection() as conn:
            for view_name, sql in views.items():
                try:
                    conn.execute(sql)
                    logger.info(f"Created view: {view_name}")
                except sqlite3.Error as e:
                    logger.error(f"Failed to create view {view_name}: {e}")
                    raise
            
            conn.commit()
            logger.info("All Gold views created successfully")
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Query results as DataFrame
        """
        with self._get_connection() as conn:
            try:
                return pd.read_sql_query(query, conn)
            except Exception as e:
                logger.error(f"Failed to execute query: {e}")
                raise
    
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """
        Get table schema information.
        
        Args:
            table_name: Name of the table
            
        Returns:
            DataFrame with table schema info
        """
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)
    
    def get_table_count(self, table_name: str) -> int:
        """
        Get row count for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Number of rows in the table
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result['count'].iloc[0] if not result.empty else 0
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the database.
        
        Returns:
            List of table names
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        result = self.execute_query(query)
        return result['name'].tolist() if not result.empty else []
    
    def list_views(self) -> List[str]:
        """
        List all views in the database.
        
        Returns:
            List of view names
        """
        query = "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
        result = self.execute_query(query)
        return result['name'].tolist() if not result.empty else []
    
    def vacuum(self) -> None:
        """Vacuum the database to reclaim space."""
        with self._get_connection() as conn:
            conn.execute("VACUUM")
            logger.info("Database vacuumed successfully")
    
    def analyze(self) -> None:
        """Analyze the database to update statistics."""
        with self._get_connection() as conn:
            conn.execute("ANALYZE")
            logger.info("Database analyzed successfully")
    
    def get_database_size(self) -> int:
        """
        Get database file size in bytes.
        
        Returns:
            Database file size in bytes
        """
        if self.db_path.exists():
            return self.db_path.stat().st_size
        return 0
    
    def backup_database(self, backup_path: str) -> None:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path for the backup file
        """
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._get_connection() as source:
            with sqlite3.connect(backup_path) as backup:
                source.backup(backup)
        
        logger.info(f"Database backed up to: {backup_path}")
    
    def close(self) -> None:
        """Close database connection (placeholder for consistency)."""
        # SQLite connections are closed automatically with context managers
        pass


def create_database_summary(sink: SQLiteSink) -> Dict:
    """
    Create a summary of the database contents.
    
    Args:
        sink: SQLite sink instance
        
    Returns:
        Dictionary with database summary
    """
    summary = {
        'database_path': str(sink.db_path),
        'database_size_mb': round(sink.get_database_size() / (1024 * 1024), 2),
        'tables': {},
        'views': sink.list_views(),
        'total_tables': 0,
        'total_views': 0,
        'total_rows': 0
    }
    
    tables = sink.list_tables()
    for table in tables:
        try:
            count = sink.get_table_count(table)
            summary['tables'][table] = count
            summary['total_rows'] += count
        except Exception as e:
            logger.warning(f"Could not get count for table {table}: {e}")
            summary['tables'][table] = -1
    
    summary['total_tables'] = len(tables)
    summary['total_views'] = len(summary['views'])
    
    return summary


def validate_database_integrity(sink: SQLiteSink) -> Dict:
    """
    Validate database integrity and foreign key constraints.
    
    Args:
        sink: SQLite sink instance
        
    Returns:
        Dictionary with validation results
    """
    results = {
        'integrity_check': None,
        'foreign_key_check': None,
        'errors': []
    }
    
    try:
        # Check database integrity
        integrity_result = sink.execute_query("PRAGMA integrity_check")
        results['integrity_check'] = integrity_result['integrity_check'].tolist()
        
        # Check foreign key constraints
        fk_result = sink.execute_query("PRAGMA foreign_key_check")
        if not fk_result.empty:
            results['foreign_key_check'] = fk_result.to_dict('records')
            results['errors'].append("Foreign key constraint violations found")
        else:
            results['foreign_key_check'] = "OK"
        
    except Exception as e:
        results['errors'].append(f"Validation failed: {e}")
    
    return results