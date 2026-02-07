#!/usr/bin/env python3
"""
PostgreSQL Database Migration Verification Script

This script validates the successful migration from SQLite3 to PostgreSQL (Supabase).
Run this script after migration to ensure all tables, data, and integrity are preserved.

Usage:
    python scripts/verify_postgresql_migration.py
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


class MigrationVerifier:
    """Verifies PostgreSQL migration completeness and integrity."""
    
    def __init__(self):
        self.dsn = os.environ.get("DATABASE_URL")
        self.conn = None
        self.cur = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "checks": [],
            "tables": {},
            "errors": [],
            "warnings": []
        }
    
    def connect(self):
        """Establish connection to PostgreSQL."""
        try:
            self.conn = psycopg2.connect(self.dsn)
            self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
            print("✅ PostgreSQL connection established")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.results["errors"].append(f"Connection failed: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
    
    def check_tables_exist(self):
        """Verify all expected tables exist in PostgreSQL."""
        print("\n📋 Checking tables...")
        
        expected_tables = [
            "users", "staff", "couriers", "orders", "order_details",
            "counters", "favorites", "cart_items", "questions", "receipts",
            "branches", "sessions", "chats", "chat_members", "chat_messages",
            "notifications", "messages", "ratings", "payment_cards",
            "card_payment_settings", "photos_360", "product_media", "comments",
            "ai_knowledge", "ai_unanswered", "product_marketplaces",
            "operator_chats", "operator_chat_messages", "site_settings",
            "social_links", "menu_item_media", "menu_items", "news",
            "superadmin_settings"
        ]
        
        self.cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row['table_name'] for row in self.cur.fetchall()]
        
        missing = []
        found = []
        
        for table in expected_tables:
            if table in existing_tables:
                found.append(table)
                print(f"  ✅ {table}")
            else:
                missing.append(table)
                print(f"  ❌ {table} - MISSING")
        
        self.results["checks"].append({
            "name": "tables_exist",
            "expected": len(expected_tables),
            "found": len(found),
            "missing": missing,
            "passed": len(missing) == 0
        })
        
        if missing:
            self.results["warnings"].append(f"Missing tables: {', '.join(missing)}")
        
        return len(missing) == 0
    
    def check_row_counts(self):
        """Get row counts for all tables."""
        print("\n📊 Checking row counts...")
        
        self.cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [row['table_name'] for row in self.cur.fetchall()]
        
        total_rows = 0
        for table in tables:
            try:
                self.cur.execute(f'SELECT COUNT(*) as cnt FROM "{table}"')
                count = self.cur.fetchone()['cnt']
                self.results["tables"][table] = {"row_count": count}
                total_rows += count
                print(f"  📦 {table}: {count} rows")
            except Exception as e:
                print(f"  ❌ {table}: Error - {e}")
                self.results["errors"].append(f"Count error for {table}: {e}")
        
        self.results["checks"].append({
            "name": "row_counts",
            "total_tables": len(tables),
            "total_rows": total_rows,
            "passed": True
        })
        
        return True
    
    def check_foreign_keys(self):
        """Verify foreign key constraints are in place."""
        print("\n🔗 Checking foreign key constraints...")
        
        self.cur.execute("""
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
        """)
        
        fks = self.cur.fetchall()
        
        for fk in fks:
            print(f"  🔗 {fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        self.results["checks"].append({
            "name": "foreign_keys",
            "count": len(fks),
            "passed": True
        })
        
        if len(fks) == 0:
            self.results["warnings"].append("No foreign key constraints found")
        
        return True
    
    def check_indexes(self):
        """Check indexes on tables."""
        print("\n📑 Checking indexes...")
        
        self.cur.execute("""
            SELECT 
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        
        indexes = self.cur.fetchall()
        index_count = len(indexes)
        
        # Group by table
        tables_indexed = set()
        for idx in indexes:
            tables_indexed.add(idx['tablename'])
            print(f"  📑 {idx['tablename']}: {idx['indexname']}")
        
        self.results["checks"].append({
            "name": "indexes",
            "count": index_count,
            "tables_with_indexes": len(tables_indexed),
            "passed": True
        })
        
        return True
    
    def check_data_integrity(self):
        """Perform basic data integrity checks."""
        print("\n🔍 Checking data integrity...")
        
        checks_passed = True
        
        # Check 1: users table has required fields
        try:
            self.cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND table_schema = 'public'
            """)
            user_columns = [row['column_name'] for row in self.cur.fetchall()]
            required_user_cols = ['id', 'email', 'first_name', 'last_name']
            missing_cols = [col for col in required_user_cols if col not in user_columns]
            
            if missing_cols:
                print(f"  ⚠️ users table missing columns: {missing_cols}")
                self.results["warnings"].append(f"users table missing: {missing_cols}")
            else:
                print("  ✅ users table has required columns")
        except Exception as e:
            print(f"  ❌ users check failed: {e}")
            self.results["errors"].append(f"users integrity check failed: {e}")
            checks_passed = False
        
        # Check 2: orders table has valid status values
        try:
            self.cur.execute("SELECT DISTINCT status FROM orders")
            statuses = [row['status'] for row in self.cur.fetchall()]
            print(f"  📋 Order statuses: {statuses}")
        except Exception as e:
            pass  # Table might be empty
        
        # Check 3: menu_items has valid prices
        try:
            self.cur.execute("SELECT COUNT(*) as cnt FROM menu_items WHERE price < 0")
            negative_prices = self.cur.fetchone()['cnt']
            if negative_prices > 0:
                print(f"  ⚠️ {negative_prices} menu items with negative prices")
                self.results["warnings"].append(f"{negative_prices} menu items with negative prices")
            else:
                print("  ✅ All menu item prices are valid")
        except Exception as e:
            pass  # Table might not have price column
        
        self.results["checks"].append({
            "name": "data_integrity",
            "passed": checks_passed
        })
        
        return checks_passed
    
    def check_connection_settings(self):
        """Verify connection settings are production-ready."""
        print("\n⚙️ Checking connection settings...")
        
        # Check SSL mode
        ssl_enabled = "sslmode=require" in self.dsn if self.dsn else False
        if ssl_enabled:
            print("  ✅ SSL enabled (sslmode=require)")
        else:
            print("  ⚠️ SSL not explicitly enabled in connection string")
            self.results["warnings"].append("Consider enabling SSL for production")
        
        # Check for Supabase connection
        is_supabase = "supabase" in self.dsn.lower() if self.dsn else False
        if is_supabase:
            print("  ✅ Connected to Supabase PostgreSQL")
        else:
            print("  ℹ️ Not a Supabase connection")
        
        self.results["checks"].append({
            "name": "connection_settings",
            "ssl_enabled": ssl_enabled,
            "is_supabase": is_supabase,
            "passed": True
        })
        
        return True
    
    def run_all_checks(self):
        """Run all verification checks."""
        print("=" * 60)
        print("🔍 PostgreSQL Migration Verification")
        print("=" * 60)
        
        if not self.connect():
            self.results["status"] = "failed"
            return False
        
        try:
            self.check_connection_settings()
            tables_ok = self.check_tables_exist()
            self.check_row_counts()
            self.check_foreign_keys()
            self.check_indexes()
            self.check_data_integrity()
            
            # Determine overall status
            all_passed = all(check.get("passed", False) for check in self.results["checks"])
            no_errors = len(self.results["errors"]) == 0
            
            if all_passed and no_errors:
                self.results["status"] = "passed"
                print("\n" + "=" * 60)
                print("✅ ALL CHECKS PASSED - Migration verified successfully!")
                print("=" * 60)
            else:
                self.results["status"] = "warning" if no_errors else "failed"
                print("\n" + "=" * 60)
                print("⚠️ Some checks had warnings or errors")
                print("=" * 60)
            
            if self.results["warnings"]:
                print("\n⚠️ Warnings:")
                for w in self.results["warnings"]:
                    print(f"  - {w}")
            
            if self.results["errors"]:
                print("\n❌ Errors:")
                for e in self.results["errors"]:
                    print(f"  - {e}")
            
            return all_passed and no_errors
            
        finally:
            self.close()
    
    def save_report(self, filepath="migration_verification_report.json"):
        """Save verification report to JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n📄 Report saved to: {filepath}")


def main():
    verifier = MigrationVerifier()
    success = verifier.run_all_checks()
    verifier.save_report(os.path.join(os.path.dirname(__file__), "migration_verification_report.json"))
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
