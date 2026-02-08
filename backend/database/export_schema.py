#!/usr/bin/env python3
"""
PostgreSQL Schema Export Script

This script exports the current PostgreSQL database schema for documentation
and backup purposes. Run this to generate DDL statements for all tables.

Usage:
    python database/export_schema.py
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ psycopg2 not installed")
    sys.exit(1)


def get_tables_schema():
    """Export schema for all tables."""
    dsn = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(dsn)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    schema_output = []
    schema_output.append(f"-- PostgreSQL Schema Export")
    schema_output.append(f"-- Generated: {datetime.now().isoformat()}")
    schema_output.append(f"-- Database: Supabase PostgreSQL")
    schema_output.append("")
    
    # Get all tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = [row['table_name'] for row in cur.fetchall()]
    
    for table in tables:
        schema_output.append(f"\n-- ═══════════════════════════════════════════════════════")
        schema_output.append(f"-- Table: {table}")
        schema_output.append(f"-- ═══════════════════════════════════════════════════════")
        
        # Get columns
        cur.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table,))
        
        columns = cur.fetchall()
        
        col_defs = []
        for col in columns:
            col_type = col['data_type'].upper()
            if col['character_maximum_length']:
                col_type = f"VARCHAR({col['character_maximum_length']})"
            
            nullable = "" if col['is_nullable'] == 'YES' else " NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            
            col_defs.append(f"    {col['column_name']} {col_type}{nullable}{default}")
        
        # Get primary keys
        cur.execute("""
            SELECT a.attname
            FROM   pg_index i
            JOIN   pg_attribute a ON a.attrelid = i.indrelid
                                 AND a.attnum = ANY(i.indkey)
            WHERE  i.indrelid = %s::regclass
            AND    i.indisprimary
        """, (table,))
        
        pks = [row['attname'] for row in cur.fetchall()]
        if pks:
            col_defs.append(f"    PRIMARY KEY ({', '.join(pks)})")
        
        create_stmt = f"CREATE TABLE IF NOT EXISTS {table} (\n"
        create_stmt += ",\n".join(col_defs)
        create_stmt += "\n);"
        
        schema_output.append(create_stmt)
    
    conn.close()
    return "\n".join(schema_output)


def main():
    print("Exporting PostgreSQL schema...")
    
    try:
        schema = get_tables_schema()
        
        # Save to file
        output_path = os.path.join(os.path.dirname(__file__), "schema_export.sql")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(schema)
        
        print(f"✅ Schema exported to: {output_path}")
        print(f"\nPreview (first 100 lines):")
        print("-" * 60)
        for line in schema.split("\n")[:100]:
            print(line)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
