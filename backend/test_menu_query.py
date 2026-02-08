import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
dsn = os.environ.get("DATABASE_URL")

try:
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    query = """SELECT m.id, m.name, m.price, m.category, m.description, m.image_url, m.available, m.stock_quantity, m.orders_count, m.rating, m.discount_percentage, m.sizes, m.colors, m.created_at,
                   m.weight, m.material, m.purpose, m.season, m.brand, m.features, m.shoe_type, m.sole_type, m.height, m.clothing_type, m.thickness, m.standard,
                   COALESCE(AVG(r.rating), 0) as avg_rating, COUNT(r.rating) as rating_count
                   FROM menu_items m
                   LEFT JOIN ratings r ON m.id = r.menu_item_id
                   WHERE m.available = TRUE
                   GROUP BY m.id
                   ORDER BY 
                       CASE 
                           WHEN m.category = 'Safety Boots' THEN 1
                           WHEN m.category = 'Protective Suits' THEN 2
                           WHEN m.category = 'Head Protection' THEN 3
                           WHEN m.category = 'Hand Protection' THEN 4
                           WHEN m.category = 'Eye Protection' THEN 5
                           WHEN m.category = 'Respiratory Protection' THEN 6
                           ELSE 7
                       END,
                       m.is_new DESC,
                       m.orders_count DESC, 
                       avg_rating DESC,
                       m.name ASC LIMIT 5"""
    cur.execute(query)
    rows = cur.fetchall()
    print(f"Query successful, fetched {len(rows)} rows")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
