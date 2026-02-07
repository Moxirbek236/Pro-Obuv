#!/usr/bin/env python3
"""
SQLite Reference Cleanup Script

This script scans the codebase for remaining SQLite references and provides
migration guidance. It can also help migrate scripts to use PostgreSQL.

Usage:
    python scripts/cleanup_sqlite_references.py [--auto-fix]
"""

import os
import sys
import re
from pathlib import Path

# Root directory
ROOT = Path(__file__).parent.parent

# Files and directories to scan
SCAN_DIRS = ['scripts', 'tools', 'tests']

# Files to skip (backup files, etc.)
SKIP_PATTERNS = ['.bak', '.backup', '__pycache__', '.pyc', '.json', '.html', '.out', '.md']

# SQLite-specific patterns to find
SQLITE_PATTERNS = [
    (r'import sqlite3', 'Import statement'),
    (r'sqlite3\.connect', 'Connection creation'),
    (r'sqlite_master', 'SQLite system table'),
    (r'\.sqlite3?', 'SQLite file extension'),
    (r'AUTOINCREMENT', 'SQLite AUTOINCREMENT'),
    (r"datetime\('now'\)", 'SQLite datetime function'),
    (r'PRAGMA\s+', 'PRAGMA statement'),
    (r"row\.row_factory\s*=\s*sqlite3\.Row", 'SQLite Row factory'),
]

# Replacement mappings
SQLITE_TO_POSTGRES = {
    'import sqlite3': '''import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
load_dotenv()''',
    
    "sqlite3.connect('database.sqlite3')": '''psycopg2.connect(os.environ.get("DATABASE_URL"))''',
    
    "sqlite3.connect(DB_PATH)": '''psycopg2.connect(os.environ.get("DATABASE_URL"))''',
    
    "conn.row_factory = sqlite3.Row": '''# PostgreSQL with RealDictCursor already returns dict-like rows''',
    
    "sqlite_master": "information_schema.tables",
    
    "SELECT name FROM sqlite_master WHERE type='table'": """SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'""",
    
    "SELECT name FROM sqlite_master WHERE type='table' AND name=?": """SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s""",
    
    "datetime('now')": "NOW()",
    
    "PRAGMA": "-- PRAGMA (not supported in PostgreSQL, use pg_catalog instead)",
    
    "?": "%s",  # Parameter placeholder
}


def should_skip_file(filepath):
    """Check if file should be skipped."""
    filepath_str = str(filepath)
    return any(pattern in filepath_str for pattern in SKIP_PATTERNS)


def find_sqlite_references(filepath):
    """Find SQLite references in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception:
        return []
    
    findings = []
    for line_no, line in enumerate(lines, 1):
        for pattern, description in SQLITE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append({
                    'line_no': line_no,
                    'line': line.strip()[:80],
                    'pattern': pattern,
                    'description': description
                })
    
    return findings


def scan_directory(directory):
    """Scan a directory for SQLite references."""
    dir_path = ROOT / directory
    if not dir_path.exists():
        return {}
    
    results = {}
    for filepath in dir_path.rglob('*.py'):
        if should_skip_file(filepath):
            continue
        
        findings = find_sqlite_references(filepath)
        if findings:
            rel_path = str(filepath.relative_to(ROOT))
            results[rel_path] = findings
    
    return results


def generate_report():
    """Generate a report of all SQLite references."""
    print("=" * 70)
    print("🔍 SQLite Reference Scanner")
    print("=" * 70)
    
    all_results = {}
    total_files = 0
    total_references = 0
    
    for directory in SCAN_DIRS:
        print(f"\n📂 Scanning {directory}/...")
        results = scan_directory(directory)
        all_results.update(results)
        
        for filepath, findings in results.items():
            total_files += 1
            total_references += len(findings)
            print(f"\n  📄 {filepath}")
            for f in findings[:5]:  # Show first 5
                print(f"     Line {f['line_no']}: {f['description']}")
            if len(findings) > 5:
                print(f"     ... and {len(findings) - 5} more")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary")
    print("=" * 70)
    print(f"Files with SQLite references: {total_files}")
    print(f"Total SQLite references: {total_references}")
    
    if total_references > 0:
        print("\n⚠️ These files need to be updated to use PostgreSQL.")
        print("   Most are utility/development scripts and are NOT used in production.")
        print("\n📝 Migration Guide:")
        print("   1. Replace 'import sqlite3' with 'import psycopg2'")
        print("   2. Replace '?' placeholders with '%s'")
        print("   3. Replace 'sqlite_master' with 'information_schema.tables'")
        print("   4. Use environment variable DATABASE_URL for connection")
    else:
        print("\n✅ No SQLite references found!")
    
    return all_results


def migrate_file(filepath):
    """Attempt to migrate a file from SQLite to PostgreSQL."""
    print(f"\n🔄 Migrating {filepath}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Apply replacements
        for old, new in SQLITE_TO_POSTGRES.items():
            content = content.replace(old, new)
        
        if content != original:
            # Backup original
            backup_path = filepath + '.sqlite_backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original)
            
            # Write migrated content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"   ✅ Migrated (backup at {backup_path})")
            return True
        else:
            print(f"   ℹ️ No changes needed")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def create_postgres_template():
    """Create a PostgreSQL script template."""
    template = '''#!/usr/bin/env python3
"""
PostgreSQL Utility Script Template

This script template shows how to connect to PostgreSQL and execute queries.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use the centralized database utilities
from database.pg_utils import (
    get_connection,
    execute_query,
    get_tables,
    get_table_info,
    table_exists,
    get_row_count,
)


def main():
    """Main function demonstrating PostgreSQL usage."""
    
    # Example 1: List all tables
    print("Tables in database:")
    for table in get_tables():
        count = get_row_count(table)
        print(f"  - {table}: {count} rows")
    
    # Example 2: Check if table exists
    if table_exists('users'):
        print("\\nUsers table exists!")
    
    # Example 3: Execute a query
    users = execute_query(
        "SELECT id, email, first_name FROM users LIMIT 5",
        fetch_all=True
    )
    
    if users:
        print("\\nFirst 5 users:")
        for user in users:
            print(f"  {user['id']}: {user['email']} ({user.get('first_name', 'N/A')})")
    
    # Example 4: Get table info
    print("\\nUsers table columns:")
    for col in get_table_info('users'):
        print(f"  - {col['column_name']}: {col['data_type']}")


if __name__ == "__main__":
    main()
'''
    
    template_path = ROOT / 'scripts' / 'template_postgres_script.py'
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"✅ Template created: {template_path}")
    return template_path


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='SQLite Reference Cleanup')
    parser.add_argument('--auto-fix', action='store_true', help='Attempt automatic migration')
    parser.add_argument('--create-template', action='store_true', help='Create PostgreSQL script template')
    args = parser.parse_args()
    
    if args.create_template:
        create_postgres_template()
        return 0
    
    results = generate_report()
    
    if args.auto_fix and results:
        print("\n" + "=" * 70)
        print("🔄 Attempting Automatic Migration")
        print("=" * 70)
        
        migrated = 0
        for filepath in results.keys():
            full_path = ROOT / filepath
            if migrate_file(str(full_path)):
                migrated += 1
        
        print(f"\n✅ Migrated {migrated} files")
    
    return 0 if not results else 1


if __name__ == "__main__":
    sys.exit(main())
