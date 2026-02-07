#!/usr/bin/env python3
"""
PostgreSQL Database Utilities

This module provides PostgreSQL-specific database utilities for the application.
All SQLite functionality has been removed as the application now runs 100% on PostgreSQL.

Usage:
    from database.pg_utils import get_connection, execute_query, get_table_info
"""

import os
import sys
from contextlib import contextmanager
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import psycopg2
    from psycopg2 import pool as psycopg2_pool
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from dotenv import load_dotenv
load_dotenv()


class PostgresqlError(Exception):
    """Custom exception for PostgreSQL errors."""
    pass


class PgConnectionManager:
    """
    PostgreSQL Connection Manager with connection pooling.
    
    This class manages database connections using psycopg2's ThreadedConnectionPool.
    It provides thread-safe connection handling and automatic cleanup.
    """
    
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if PgConnectionManager._pool is None:
            self._init_pool()
    
    def _init_pool(self):
        """Initialize the connection pool."""
        if not PSYCOPG2_AVAILABLE:
            raise PostgresqlError("psycopg2 is not installed. Run: pip install psycopg2-binary")
        
        dsn = os.environ.get("DATABASE_URL")
        if not dsn:
            raise PostgresqlError("DATABASE_URL environment variable is not set")
        
        max_connections = int(os.environ.get("DB_POOL_MAX_CONNECTIONS", "20"))
        
        try:
            PgConnectionManager._pool = psycopg2_pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=max_connections,
                dsn=dsn,
                cursor_factory=RealDictCursor
            )
            print(f"PostgreSQL connection pool initialized (max: {max_connections})")
        except Exception as e:
            raise PostgresqlError(f"Failed to initialize connection pool: {e}")
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Usage:
            with conn_manager.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1")
        """
        conn = None
        try:
            conn = PgConnectionManager._pool.getconn()
            conn.autocommit = True
            
            # Pre-ping to check if connection is alive
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            except (psycopg2.OperationalError, psycopg2.InterfaceError):
                # Connection is stale, get a new one
                PgConnectionManager._pool.putconn(conn, close=True)
                conn = PgConnectionManager._pool.getconn()
                conn.autocommit = True
            
            yield conn
        finally:
            if conn:
                PgConnectionManager._pool.putconn(conn)
    
    def close_pool(self):
        """Close all connections in the pool."""
        if PgConnectionManager._pool:
            PgConnectionManager._pool.closeall()
            PgConnectionManager._pool = None


# Global connection manager instance
_conn_manager = None


def get_connection_manager():
    """Get the global connection manager instance."""
    global _conn_manager
    if _conn_manager is None:
        _conn_manager = PgConnectionManager()
    return _conn_manager


@contextmanager
def get_connection():
    """
    Get a database connection from the pool.
    
    Usage:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users")
            rows = cur.fetchall()
    """
    manager = get_connection_manager()
    with manager.get_connection() as conn:
        yield conn


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=True):
    """
    Execute a database query.
    
    Args:
        query: SQL query string (use %s for parameters)
        params: Tuple of parameters
        fetch_one: Return single row
        fetch_all: Return all rows
        commit: Commit the transaction (for INSERT/UPDATE/DELETE)
    
    Returns:
        - If fetch_one: Single row as dict or None
        - If fetch_all: List of rows as dicts
        - Otherwise: Number of affected rows
    
    Example:
        # SELECT
        user = execute_query("SELECT * FROM users WHERE id = %s", (1,), fetch_one=True)
        
        # INSERT
        execute_query("INSERT INTO users (name, email) VALUES (%s, %s)", ("John", "john@example.com"))
        
        # SELECT ALL
        users = execute_query("SELECT * FROM users ORDER BY id", fetch_all=True)
    """
    with get_connection() as conn:
        cur = conn.cursor()
        
        try:
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            
            if fetch_one:
                result = cur.fetchone()
                return dict(result) if result else None
            elif fetch_all:
                results = cur.fetchall()
                return [dict(row) for row in results]
            else:
                if commit:
                    conn.commit()
                return cur.rowcount
        except Exception as e:
            if commit:
                conn.rollback()
            raise PostgresqlError(f"Query execution failed: {e}")


def get_tables():
    """
    Get list of all tables in the public schema.
    
    Returns:
        List of table names
    """
    query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """
    rows = execute_query(query, fetch_all=True)
    return [row['table_name'] for row in rows]


def get_table_info(table_name):
    """
    Get information about a table's columns.
    
    Args:
        table_name: Name of the table
    
    Returns:
        List of column info dicts with keys: column_name, data_type, is_nullable, column_default
    """
    query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """
    return execute_query(query, (table_name,), fetch_all=True)


def get_primary_keys(table_name):
    """
    Get primary key columns for a table.
    
    Args:
        table_name: Name of the table
    
    Returns:
        List of primary key column names
    """
    query = """
        SELECT a.attname as column_name
        FROM   pg_index i
        JOIN   pg_attribute a ON a.attrelid = i.indrelid
                             AND a.attnum = ANY(i.indkey)
        WHERE  i.indrelid = %s::regclass
        AND    i.indisprimary
    """
    rows = execute_query(query, (table_name,), fetch_all=True)
    return [row['column_name'] for row in rows]


def get_foreign_keys(table_name=None):
    """
    Get foreign key constraints.
    
    Args:
        table_name: Optional, filter by table name
    
    Returns:
        List of foreign key info dicts
    """
    query = """
        SELECT 
            tc.table_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
    """
    
    if table_name:
        query += " AND tc.table_name = %s"
        return execute_query(query, (table_name,), fetch_all=True)
    
    return execute_query(query, fetch_all=True)


def get_indexes(table_name=None):
    """
    Get indexes for tables.
    
    Args:
        table_name: Optional, filter by table name
    
    Returns:
        List of index info dicts
    """
    query = """
        SELECT 
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
    """
    
    if table_name:
        query += " AND tablename = %s"
        return execute_query(query, (table_name,), fetch_all=True)
    
    return execute_query(query, fetch_all=True)


def table_exists(table_name):
    """
    Check if a table exists.
    
    Args:
        table_name: Name of the table
    
    Returns:
        True if table exists, False otherwise
    """
    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        ) as exists
    """
    result = execute_query(query, (table_name,), fetch_one=True)
    return result['exists'] if result else False


def column_exists(table_name, column_name):
    """
    Check if a column exists in a table.
    
    Args:
        table_name: Name of the table
        column_name: Name of the column
    
    Returns:
        True if column exists, False otherwise
    """
    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = %s 
            AND column_name = %s
        ) as exists
    """
    result = execute_query(query, (table_name, column_name), fetch_one=True)
    return result['exists'] if result else False


def get_row_count(table_name):
    """
    Get the number of rows in a table.
    
    Args:
        table_name: Name of the table
    
    Returns:
        Number of rows
    """
    # Use safe quoting for table name
    query = f'SELECT COUNT(*) as count FROM "{table_name}"'
    result = execute_query(query, fetch_one=True)
    return result['count'] if result else 0


def now_iso():
    """Get current timestamp in ISO format for database inserts."""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def now_timestamp():
    """Get current timestamp with timezone for PostgreSQL TIMESTAMPTZ columns."""
    return datetime.utcnow()


# Alias for backward compatibility
get_current_timestamp = now_timestamp


if __name__ == "__main__":
    # Test the utilities
    print("Testing PostgreSQL utilities...")
    
    try:
        tables = get_tables()
        print(f"\n✅ Found {len(tables)} tables:")
        for table in tables[:10]:
            count = get_row_count(table)
            print(f"  - {table}: {count} rows")
        
        if len(tables) > 10:
            print(f"  ... and {len(tables) - 10} more tables")
        
        print("\n✅ PostgreSQL utilities working correctly!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
