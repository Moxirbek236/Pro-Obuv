#!/usr/bin/env python3
"""
Script to add missing card_name column to payment_cards table
"""

import sqlite3
import sys
import os

def add_card_name_column():
    """Add the missing card_name and bank_name columns to the payment_cards table."""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), 'database.sqlite3')
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Check current columns
        cur.execute("PRAGMA table_info(payment_cards)")
        columns = [row[1] for row in cur.fetchall()]
        
        print(f"🔍 Current columns in payment_cards: {columns}")
        
        changes_made = False
        
        # Add card_name column if missing
        if 'card_name' not in columns:
            print("🔧 Adding card_name column to payment_cards table...")
            cur.execute("ALTER TABLE payment_cards ADD COLUMN card_name TEXT NOT NULL DEFAULT 'Default Card'")
            changes_made = True
        else:
            print("✅ card_name column already exists")
            
        # Add bank_name column if missing
        if 'bank_name' not in columns:
            print("🔧 Adding bank_name column to payment_cards table...")
            cur.execute("ALTER TABLE payment_cards ADD COLUMN bank_name TEXT")
            changes_made = True
        else:
            print("✅ bank_name column already exists")
            
        # Add created_by column if missing
        if 'created_by' not in columns:
            print("🔧 Adding created_by column to payment_cards table...")
            cur.execute("ALTER TABLE payment_cards ADD COLUMN created_by INTEGER NOT NULL DEFAULT 1")
            changes_made = True
        else:
            print("✅ created_by column already exists")
        
        if changes_made:
            # Update existing records with meaningful names
            print("📝 Updating existing records with card names and bank names...")
            cur.execute("""
                UPDATE payment_cards 
                SET card_name = CASE 
                    WHEN card_type = 'uzcard' THEN 'UzCard - ' || substr(card_number, -4)
                    WHEN card_type = 'humo' THEN 'Humo - ' || substr(card_number, -4) 
                    WHEN card_type = 'visa' THEN 'Visa - ' || substr(card_number, -4)
                    WHEN card_type = 'mastercard' THEN 'MasterCard - ' || substr(card_number, -4)
                    ELSE 'Card - ' || substr(card_number, -4)
                END,
                bank_name = CASE 
                    WHEN card_type = 'uzcard' THEN 'Milliy bank'
                    WHEN card_type = 'humo' THEN 'Xalq banki'
                    WHEN card_type = 'visa' THEN 'Toshkent shahar banki'
                    WHEN card_type = 'mastercard' THEN 'Ipoteka banki'
                    ELSE 'Default Bank'
                END
                WHERE card_name = 'Default Card' OR bank_name IS NULL
            """)
            
            # Commit changes
            conn.commit()
            print("💾 Changes committed to database")
        
        # Verify the columns were added
        cur.execute("PRAGMA table_info(payment_cards)")
        new_columns = [row[1] for row in cur.fetchall()]
        
        missing_cols = []
        for required_col in ['card_name', 'bank_name', 'created_by']:
            if required_col not in new_columns:
                missing_cols.append(required_col)
                
        if not missing_cols:
            print("✅ Successfully ensured all required columns exist in payment_cards table")
            
            # Show updated records
            cur.execute("SELECT id, card_name, card_number, card_type, bank_name FROM payment_cards")
            records = cur.fetchall()
            if records:
                print("\n📋 Updated payment cards:")
                for record in records:
                    print(f"  - ID: {record[0]}, Name: {record[1]}, Number: {record[2]}, Type: {record[3]}, Bank: {record[4]}")
            else:
                print("📋 No payment card records found")
                
            return True
        else:
            print(f"❌ Failed to add columns: {missing_cols}")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Starting payment_cards table migration...")
    success = add_card_name_column()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("✅ The app should now work without the column errors.")
        sys.exit(0)
    else:
        print("\n💥 Migration failed!")
        print("❌ Please check the error messages above.")
        sys.exit(1)
