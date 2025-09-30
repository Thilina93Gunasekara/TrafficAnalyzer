# quick_stats.py
import sqlite3

conn = sqlite3.connect('database/traffic_data.db')
cursor = conn.cursor()

print("\n🚗 QUICK DATABASE STATS\n")

cursor.execute("SELECT COUNT(*) FROM routes")
print(f"Routes: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM traffic_records")
print(f"Traffic Records: {cursor.fetchone()[0]:,}")

cursor.execute("SELECT route_name, AVG(travel_time_minutes) FROM traffic_records GROUP BY route_name")
print("\nAverage Times:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]:.1f} min")

conn.close()