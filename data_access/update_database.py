import sqlite3
import os

db_path = 'database/traffic_data.db'

# Check if database exists
if not os.path.exists(db_path):
    os.makedirs('database', exist_ok=True)
    print("Created database directory")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Updating database schema...")

# Add columns if they don't exist
try:
    cursor.execute("ALTER TABLE routes ADD COLUMN start_location TEXT")
    print("✓ Added start_location column")
except sqlite3.OperationalError as e:
    print(f"start_location: {e}")

try:
    cursor.execute("ALTER TABLE routes ADD COLUMN end_location TEXT")
    print("✓ Added end_location column")
except sqlite3.OperationalError as e:
    print(f"end_location: {e}")

# Create index
try:
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_route_locations 
        ON routes(start_location, end_location)
    """)
    print("✓ Created index")
except sqlite3.OperationalError as e:
    print(f"Index: {e}")

conn.commit()
conn.close()

print("\n✅ Database schema updated!")
print("Now run: python3 generate_colombo_data.py")