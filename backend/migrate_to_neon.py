import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Source and Destination
SOURCE_URL = "postgresql://postgres:sjtmsimram10@db.hzkywrbbbykbdaapuyca.supabase.co:5432/postgres?sslmode=require"
DEST_URL = "postgresql://neondb_owner:npg_OquwgU9JZI8o@ep-flat-wind-aij3lx8p-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Tables to skip or handle specially
SKIP_TABLES = ['sessions', 'spatial_ref_sys']

def migrate():
    print("🚀 Starting Optimized Database Migration: Supabase -> Neon")
    
    try:
        src_conn = psycopg2.connect(SOURCE_URL)
        dest_conn = psycopg2.connect(DEST_URL)
        dest_conn.autocommit = True
        
        src_cur = src_conn.cursor(cursor_factory=RealDictCursor)
        dest_cur = dest_conn.cursor()
        
        # 1. Get all tables from public schema
        src_cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND table_name NOT IN %s
        """, (tuple(SKIP_TABLES),))
        tables = [row['table_name'] for row in src_cur.fetchall()]
        print(f"Found {len(tables)} tables to migrate.")
        
        for table in tables:
            print(f"\n📦 Migrating table: {table}...")
            
            # 1. Get column info
            src_cur.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, (table,))
            columns_info = src_cur.fetchall()
            
            cols = [c['column_name'] for c in columns_info]
            
            # 2. Create table in destination
            col_defs = []
            for c in columns_info:
                col_name = c['column_name']
                col_type = c['data_type']
                
                if col_type == 'character varying':
                    col_type = 'TEXT'
                elif col_type == 'timestamp with time zone':
                    col_type = 'TIMESTAMPTZ'
                elif col_type == 'timestamp without time zone':
                    col_type = 'TIMESTAMP'
                
                null_str = "NULL" if c['is_nullable'] == 'YES' else "NOT NULL"
                
                if col_name == 'id' and c['column_default'] and 'nextval' in c['column_default']:
                    col_defs.append(f'"{col_name}" SERIAL PRIMARY KEY')
                else:
                    col_defs.append(f'"{col_name}" {col_type} {null_str}')
            
            col_defs_str = ", ".join(col_defs)
            create_sql = f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs_str})'
            try:
                dest_cur.execute(create_sql)
            except Exception as e:
                print(f"  ⚠️ Table create error: {e}")

            # 3. Clear existing data
            print(f"  Emptying destination table '{table}'...")
            try:
                dest_cur.execute(f'TRUNCATE TABLE "{table}" CASCADE')
            except Exception as e:
                print(f"  ⚠️ Truncate failed: {e}")

            # 4. Copy data using execute_values (Bulk Insert)
            src_cur.execute(f'SELECT * FROM "{table}"')
            rows = src_cur.fetchall()
            
            if rows:
                print(f"  Bulk inserting {len(rows)} rows...")
                quoted_cols = [f'"{c}"' for c in cols]
                cols_str = ", ".join(quoted_cols)
                
                # prepare values list
                values = []
                for row in rows:
                    values.append(tuple(row[c] for c in cols))
                
                insert_sql = f'INSERT INTO "{table}" ({cols_str}) VALUES %s'
                execute_values(dest_cur, insert_sql, values)
                print(f"  ✅ {table} data migrated.")
            else:
                print(f"  ℹ️ {table} is empty, skipping data copy.")

            # 5. Reset Serial Sequences
            if 'id' in cols:
                try:
                    dest_cur.execute(f"SELECT pg_get_serial_sequence('\"{table}\"', 'id')")
                    seq_name = dest_cur.fetchone()[0]
                    if seq_name:
                        dest_cur.execute(f"SELECT setval('{seq_name}', COALESCE(MAX(id), 1), false) FROM \"{table}\"")
                        # Above line: false means the next nextval will return the max ID if we don't increment.
                        # Actually, better to just set it to max(id) and let next one be max(id)+1.
                        dest_cur.execute(f"SELECT setval('{seq_name}', (SELECT COALESCE(MAX(id), 0) + 1 FROM \"{table}\"), false)")
                        print(f"  🔄 Sequence '{seq_name}' reset.")
                except Exception as e:
                    pass

        print("\n🎉 Optimized Migration completed successfully!")
        
        src_conn.close()
        dest_conn.close()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate()
