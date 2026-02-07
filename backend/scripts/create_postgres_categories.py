
import psycopg2
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def create_categories_table():
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("❌ DATABASE_URL not set")
        return False
        
    try:
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()

        print("Creating categories table...")
        # Create table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                display_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                image_url TEXT,
                slug VARCHAR(255),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Check if empty
        cur.execute("SELECT COUNT(*) FROM categories")
        count = cur.fetchone()[0]

        if count == 0:
            print("Seeding initial categories...")
            # Using data relevant to "Safety" / "Pro-Obuv" (Shoes/Safety gear)
            categories = [
                ('Maxsus poyabzallar', 'Harbiy va maxsus xizmatlar uchun poyabzallar', 1, True, 'safety_shoes.jpg'),
                ('Ishchi poyabzallar', 'Qurilish va ishlab chiqarish uchun', 2, True, 'work_shoes.jpg'),
                ('Etiklar', 'Qishki va rezina etiklar', 3, True, 'boots.jpg'),
                ('Sandallar', 'Yozgi maxsus sandallar', 4, True, 'sandals.jpg'),
                ('Aksessuarlar', 'Poyabzal parvarishi va qo\'shimchalar', 5, True, 'accessories.jpg')
            ]
            
            for cat in categories:
                # Generate slug from name
                slug = cat[0].lower().replace(' ', '-').replace("'", "")
                
                cur.execute("""
                    INSERT INTO categories (name, description, display_order, is_active, image_url, slug)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (*cat, slug))
            
            print(f"Added {len(categories)} categories.")
        else:
            print(f"Categories table already has {count} items.")

        conn.commit()
        conn.close()
        print("✅ Categories table created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating categories table: {e}")
        return False

if __name__ == "__main__":
    create_categories_table()
