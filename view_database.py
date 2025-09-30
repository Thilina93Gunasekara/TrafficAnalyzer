# view_database.py
# Simple database viewer for PyCharm Community Edition

import sqlite3
import os
from datetime import datetime


def view_database():
    """View database contents in a simple format"""

    db_path = 'database/traffic_data.db'

    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("🗄️  TRAFFIC ANALYSIS DATABASE VIEWER")
    print("=" * 80)

    # Database info
    print(f"\n📁 Database: {db_path}")
    print(f"📅 Viewed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. ROUTES TABLE
    print("\n" + "-" * 80)
    print("📍 ROUTES TABLE")
    print("-" * 80)

    cursor.execute("SELECT * FROM routes ORDER BY name")
    routes = cursor.fetchall()

    print(f"\n{'ID':<5} {'Route Name':<20} {'Distance (km)':<15} {'Speed (km/h)':<15} {'Type':<10}")
    print("-" * 80)

    for route in routes:
        print(f"{route[0]:<5} {route[1]:<20} {route[6]:<15.1f} {route[7]:<15.1f} {route[8]:<10}")

    print(f"\n✅ Total Routes: {len(routes)}")

    # 2. TRAFFIC RECORDS SUMMARY
    print("\n" + "-" * 80)
    print("🚗 TRAFFIC RECORDS SUMMARY")
    print("-" * 80)

    cursor.execute("SELECT COUNT(*) FROM traffic_records")
    total_records = cursor.fetchone()[0]
    print(f"\n📊 Total Records: {total_records:,}")

    if total_records > 0:
        # Latest record
        cursor.execute("""
            SELECT route_name, travel_time_minutes, timestamp 
            FROM traffic_records 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        latest = cursor.fetchone()
        print(f"🕐 Latest Record: {latest[2]} - {latest[0]} ({latest[1]} min)")

        # Oldest record
        cursor.execute("""
            SELECT route_name, travel_time_minutes, timestamp 
            FROM traffic_records 
            ORDER BY timestamp ASC 
            LIMIT 1
        """)
        oldest = cursor.fetchone()
        print(f"🕐 Oldest Record: {oldest[2]} - {oldest[0]} ({oldest[1]} min)")

    # 3. STATISTICS BY ROUTE
    print("\n" + "-" * 80)
    print("📈 STATISTICS BY ROUTE")
    print("-" * 80)

    cursor.execute("""
        SELECT 
            route_name,
            COUNT(*) as count,
            AVG(travel_time_minutes) as avg_time,
            MIN(travel_time_minutes) as min_time,
            MAX(travel_time_minutes) as max_time
        FROM traffic_records
        GROUP BY route_name
        ORDER BY avg_time
    """)

    print(f"\n{'Route Name':<20} {'Records':<10} {'Avg Time':<12} {'Min':<8} {'Max':<8}")
    print("-" * 80)

    stats = cursor.fetchall()
    for stat in stats:
        print(f"{stat[0]:<20} {stat[1]:<10} {stat[2]:<12.1f} {stat[3]:<8} {stat[4]:<8}")

    # 4. PEAK HOURS ANALYSIS
    print("\n" + "-" * 80)
    print("⏰ TRAFFIC BY HOUR")
    print("-" * 80)

    cursor.execute("""
        SELECT 
            hour,
            AVG(travel_time_minutes) as avg_time,
            COUNT(*) as count
        FROM traffic_records
        GROUP BY hour
        ORDER BY hour
    """)

    print(f"\n{'Hour':<10} {'Avg Time (min)':<20} {'Records':<10} {'Traffic Level':<15}")
    print("-" * 80)

    hours_data = cursor.fetchall()
    for hour_data in hours_data:
        hour = hour_data[0]
        avg_time = hour_data[1]
        count = hour_data[2]

        # Determine traffic level
        if avg_time > 40:
            level = "🔴 Heavy"
        elif avg_time > 30:
            level = "🟡 Moderate"
        else:
            level = "🟢 Light"

        print(f"{hour:02d}:00     {avg_time:<20.1f} {count:<10} {level:<15}")

    # 5. WEATHER IMPACT
    print("\n" + "-" * 80)
    print("🌦️  WEATHER IMPACT")
    print("-" * 80)

    cursor.execute("""
        SELECT 
            weather_condition,
            AVG(travel_time_minutes) as avg_time,
            COUNT(*) as count
        FROM traffic_records
        GROUP BY weather_condition
        ORDER BY avg_time DESC
    """)

    print(f"\n{'Weather':<20} {'Avg Time (min)':<20} {'Records':<10}")
    print("-" * 80)

    weather_data = cursor.fetchall()
    for weather in weather_data:
        print(f"{weather[0]:<20} {weather[1]:<20.1f} {weather[2]:<10}")

    # 6. SAMPLE RECORDS
    print("\n" + "-" * 80)
    print("📋 RECENT TRAFFIC RECORDS (Last 10)")
    print("-" * 80)

    cursor.execute("""
        SELECT 
            timestamp, 
            route_name, 
            travel_time_minutes, 
            day_type, 
            weather_condition,
            traffic_density
        FROM traffic_records
        ORDER BY timestamp DESC
        LIMIT 10
    """)

    print(f"\n{'Time':<20} {'Route':<18} {'Duration':<10} {'Day':<12} {'Weather':<12} {'Density':<12}")
    print("-" * 80)

    recent = cursor.fetchall()
    for record in recent:
        print(f"{record[0]:<20} {record[1]:<18} {record[2]:<10} {record[3]:<12} {record[4]:<12} {record[5]:<12}")

    conn.close()

    print("\n" + "=" * 80)
    print("✅ Database view complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    view_database()