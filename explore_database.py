# explore_database.py
# Interactive database explorer

import sqlite3


def explore_database():
    """Interactive database explorer"""

    conn = sqlite3.connect('database/traffic_data.db')
    cursor = conn.cursor()

    while True:
        print("\n" + "=" * 60)
        print("🗄️  DATABASE EXPLORER")
        print("=" * 60)
        print("\n1. View all routes")
        print("2. View traffic records for a specific route")
        print("3. View traffic at specific hour")
        print("4. View statistics")
        print("5. Search by date")
        print("6. Custom SQL query")
        print("7. Exit")

        choice = input("\n➤ Enter choice (1-7): ").strip()

        if choice == '1':
            view_all_routes(cursor)
        elif choice == '2':
            view_route_records(cursor)
        elif choice == '3':
            view_by_hour(cursor)
        elif choice == '4':
            view_statistics(cursor)
        elif choice == '5':
            view_by_date(cursor)
        elif choice == '6':
            custom_query(cursor)
        elif choice == '7':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

    conn.close()


def view_all_routes(cursor):
    """View all routes"""
    cursor.execute("SELECT name, distance_km, typical_speed_kmh FROM routes")
    routes = cursor.fetchall()

    print("\n📍 ALL ROUTES:")
    print("-" * 60)
    for i, route in enumerate(routes, 1):
        print(f"{i}. {route[0]:<20} {route[1]:.1f} km, {route[2]:.0f} km/h")


def view_route_records(cursor):
    """View records for specific route"""
    cursor.execute("SELECT DISTINCT route_name FROM traffic_records ORDER BY route_name")
    routes = [r[0] for r in cursor.fetchall()]

    print("\n📍 Available Routes:")
    for i, route in enumerate(routes, 1):
        print(f"{i}. {route}")

    choice = input("\n➤ Enter route number: ").strip()

    try:
        route_name = routes[int(choice) - 1]
        cursor.execute("""
            SELECT timestamp, travel_time_minutes, day_type, weather_condition
            FROM traffic_records
            WHERE route_name = ?
            ORDER BY timestamp DESC
            LIMIT 20
        """, (route_name,))

        records = cursor.fetchall()

        print(f"\n🚗 Recent records for {route_name}:")
        print("-" * 60)
        for record in records:
            print(f"{record[0]} | {record[1]} min | {record[2]} | {record[3]}")

        print(f"\n✅ Showing {len(records)} most recent records")

    except (ValueError, IndexError):
        print("❌ Invalid choice")


def view_by_hour(cursor):
    """View traffic at specific hour"""
    hour = input("\n➤ Enter hour (0-23): ").strip()

    try:
        hour = int(hour)
        if 0 <= hour <= 23:
            cursor.execute("""
                SELECT route_name, AVG(travel_time_minutes) as avg_time, COUNT(*) as count
                FROM traffic_records
                WHERE hour = ?
                GROUP BY route_name
                ORDER BY avg_time
            """, (hour,))

            results = cursor.fetchall()

            print(f"\n⏰ Traffic at {hour:02d}:00:")
            print("-" * 60)
            for result in results:
                print(f"{result[0]:<20} {result[1]:.1f} min (from {result[2]} records)")
        else:
            print("❌ Hour must be between 0-23")
    except ValueError:
        print("❌ Invalid hour")


def view_statistics(cursor):
    """View database statistics"""
    print("\n📊 DATABASE STATISTICS:")
    print("-" * 60)

    # Total records
    cursor.execute("SELECT COUNT(*) FROM traffic_records")
    total = cursor.fetchone()[0]
    print(f"Total Records: {total:,}")

    # Average by route
    cursor.execute("""
        SELECT route_name, 
               AVG(travel_time_minutes) as avg,
               MIN(travel_time_minutes) as min,
               MAX(travel_time_minutes) as max
        FROM traffic_records
        GROUP BY route_name
    """)

    print("\nRoute Statistics:")
    for row in cursor.fetchall():
        print(f"  {row[0]:<20} Avg: {row[1]:.1f}, Range: {row[2]}-{row[3]} min")


def view_by_date(cursor):
    """View records by date"""
    date = input("\n➤ Enter date (YYYY-MM-DD) or press Enter for today: ").strip()

    if not date:
        from datetime import datetime
        date = datetime.now().strftime('%Y-%m-%d')

    cursor.execute("""
        SELECT route_name, travel_time_minutes, hour
        FROM traffic_records
        WHERE DATE(timestamp) = ?
        ORDER BY hour
    """, (date,))

    results = cursor.fetchall()

    if results:
        print(f"\n📅 Records for {date}:")
        print("-" * 60)
        for result in results:
            print(f"{result[2]:02d}:00 | {result[0]:<20} | {result[1]} min")
        print(f"\n✅ Found {len(results)} records")
    else:
        print(f"❌ No records found for {date}")


def custom_query(cursor):
    """Run custom SQL query"""
    print("\n💡 Tables: routes, traffic_records")
    print("Example: SELECT * FROM routes")

    query = input("\n➤ Enter SQL query: ").strip()

    try:
        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            print("\n✅ Results:")
            print("-" * 60)
            for row in results:
                print(row)
            print(f"\n✅ Found {len(results)} rows")
        else:
            print("✅ Query executed (no results)")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    explore_database()