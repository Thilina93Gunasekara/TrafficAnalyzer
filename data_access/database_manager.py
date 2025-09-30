# data_access/database_manager.py
# Database operations layer - Repository pattern implementation

import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from .models import *
from config.settings import DatabaseConfig
from utilities.logger import get_logger


class DatabaseManager:
    """
    Database access layer implementing Repository pattern
    Handles all database operations for the traffic analysis system
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.db_path = DatabaseConfig.FULL_DB_PATH
        self._ensure_database_directory()
        self._initialize_database()

    def _ensure_database_directory(self):
        """Create database directory if it doesn't exist"""
        os.makedirs(DatabaseConfig.DB_PATH, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        connection = None
        try:
            connection = sqlite3.connect(
                self.db_path,
                timeout=DatabaseConfig.CONNECTION_TIMEOUT
            )
            connection.row_factory = sqlite3.Row  # Enable column access by name
            yield connection
        except sqlite3.Error as e:
            if connection:
                connection.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if connection:
                connection.close()

    def _initialize_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create routes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS routes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    start_latitude REAL,
                    start_longitude REAL,
                    end_latitude REAL,
                    end_longitude REAL,
                    distance_km REAL,
                    typical_speed_kmh REAL,
                    route_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create traffic_records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traffic_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    route_name TEXT NOT NULL,
                    travel_time_minutes INTEGER NOT NULL,
                    distance_km REAL,
                    day_type TEXT NOT NULL,
                    weather_condition TEXT,
                    season_type TEXT,
                    hour INTEGER,
                    day_of_week INTEGER,
                    is_holiday BOOLEAN DEFAULT FALSE,
                    traffic_density TEXT,
                    average_speed_kmh REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (route_name) REFERENCES routes (name)
                )
            ''')

            # Create indexes for better performance
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_traffic_route_time ON traffic_records(route_name, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_traffic_hour_day ON traffic_records(hour, day_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_traffic_weather ON traffic_records(weather_condition)')

            conn.commit()
            self.logger.info("Database initialized successfully")

        # Insert default routes
        self._insert_default_routes()

    def _insert_default_routes(self):
        """Insert default route configurations"""
        default_routes = [
            Route(name="High Level Road", start_latitude=6.8431, start_longitude=79.9186,
                  end_latitude=6.9271, end_longitude=79.8612, distance_km=12.5, typical_speed_kmh=35),
            Route(name="Low Level Road", start_latitude=6.8431, start_longitude=79.9186,
                  end_latitude=6.9271, end_longitude=79.8612, distance_km=14.2, typical_speed_kmh=30),
            Route(name="Baseline Road", start_latitude=6.8431, start_longitude=79.9186,
                  end_latitude=6.9271, end_longitude=79.8612, distance_km=13.8, typical_speed_kmh=32),
            Route(name="Galle Road", start_latitude=6.8431, start_longitude=79.9186,
                  end_latitude=6.9271, end_longitude=79.8612, distance_km=15.1, typical_speed_kmh=28),
            Route(name="Marine Drive", start_latitude=6.8431, start_longitude=79.9186,
                  end_latitude=6.9271, end_longitude=79.8612, distance_km=16.3, typical_speed_kmh=25),
            Route(name="Other Roads", start_latitude=6.8431, start_longitude=79.9186,
                  end_latitude=6.9271, end_longitude=79.8612, distance_km=11.8, typical_speed_kmh=20)
        ]

        for route in default_routes:
            self.create_route(route)

    # Route operations
    def create_route(self, route: Route) -> int:
        """Create a new route"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO routes 
                    (name, start_latitude, start_longitude, end_latitude, end_longitude, 
                     distance_km, typical_speed_kmh, route_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (route.name, route.start_latitude, route.start_longitude,
                      route.end_latitude, route.end_longitude, route.distance_km,
                      route.typical_speed_kmh, route.route_type))

                conn.commit()
                route_id = cursor.lastrowid
                self.logger.info(f"Route created: {route.name}")
                return route_id
        except sqlite3.Error as e:
            self.logger.error(f"Error creating route: {e}")
            raise

    def get_route(self, route_name: str) -> Optional[Route]:
        """Get route by name"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM routes WHERE name = ?', (route_name,))
                row = cursor.fetchone()

                if row:
                    return Route(
                        id=row['id'],
                        name=row['name'],
                        start_latitude=row['start_latitude'],
                        start_longitude=row['start_longitude'],
                        end_latitude=row['end_latitude'],
                        end_longitude=row['end_longitude'],
                        distance_km=row['distance_km'],
                        typical_speed_kmh=row['typical_speed_kmh'],
                        route_type=row['route_type']
                    )
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting route: {e}")
            raise

    def get_all_routes(self) -> List[Route]:
        """Get all routes"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM routes ORDER BY name')
                rows = cursor.fetchall()

                routes = []
                for row in rows:
                    routes.append(Route(
                        id=row['id'],
                        name=row['name'],
                        start_latitude=row['start_latitude'],
                        start_longitude=row['start_longitude'],
                        end_latitude=row['end_latitude'],
                        end_longitude=row['end_longitude'],
                        distance_km=row['distance_km'],
                        typical_speed_kmh=row['typical_speed_kmh'],
                        route_type=row['route_type']
                    ))
                return routes
        except sqlite3.Error as e:
            self.logger.error(f"Error getting routes: {e}")
            raise

    # Traffic record operations
    def create_traffic_record(self, record: TrafficRecord) -> int:
        """Create a new traffic record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO traffic_records 
                    (timestamp, route_name, travel_time_minutes, distance_km, day_type, 
                     weather_condition, season_type, hour, day_of_week, is_holiday, 
                     traffic_density, average_speed_kmh)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (record.timestamp, record.route_name, record.travel_time_minutes,
                      record.distance_km, record.day_type.value, record.weather_condition.value,
                      record.season_type.value, record.hour, record.day_of_week,
                      record.is_holiday, record.traffic_density.value, record.average_speed_kmh))

                conn.commit()
                record_id = cursor.lastrowid
                self.logger.debug(f"Traffic record created for {record.route_name}")
                return record_id
        except sqlite3.Error as e:
            self.logger.error(f"Error creating traffic record: {e}")
            raise

    def get_traffic_records(self, route_name: Optional[str] = None,
                            days_back: int = 30, limit: int = 1000) -> List[TrafficRecord]:
        """Get traffic records with optional filtering"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                query = '''
                    SELECT * FROM traffic_records 
                    WHERE timestamp >= datetime('now', '-{} days')
                '''.format(days_back)

                params = []
                if route_name:
                    query += ' AND route_name = ?'
                    params.append(route_name)

                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                records = []
                for row in rows:
                    records.append(TrafficRecord(
                        id=row['id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        route_name=row['route_name'],
                        travel_time_minutes=row['travel_time_minutes'],
                        distance_km=row['distance_km'],
                        day_type=DayType(row['day_type']),
                        weather_condition=WeatherCondition(row['weather_condition']),
                        season_type=SeasonType(row['season_type']),
                        hour=row['hour'],
                        day_of_week=row['day_of_week'],
                        is_holiday=bool(row['is_holiday']),
                        traffic_density=TrafficDensity(row['traffic_density']),
                        average_speed_kmh=row['average_speed_kmh']
                    ))
                return records
        except sqlite3.Error as e:
            self.logger.error(f"Error getting traffic records: {e}")
            raise

    def get_traffic_records_dataframe(self, route_name: Optional[str] = None,
                                      days_back: int = 30) -> pd.DataFrame:
        """Get traffic records as pandas DataFrame for analysis"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM traffic_records 
                    WHERE timestamp >= datetime('now', '-{} days')
                '''.format(days_back)

                params = {}
                if route_name:
                    query += ' AND route_name = :route_name'
                    params['route_name'] = route_name

                query += ' ORDER BY timestamp DESC'

                df = pd.read_sql_query(query, conn, params=params)

                # Convert timestamp to datetime
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])

                return df
        except sqlite3.Error as e:
            self.logger.error(f"Error getting traffic records DataFrame: {e}")
            raise

    # Analytics queries
    def get_route_analytics(self, route_name: str, days_back: int = 30) -> Optional[AnalyticsData]:
        """Get analytics data for a specific route"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get basic statistics
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_records,
                        AVG(travel_time_minutes) as avg_time,
                        MIN(travel_time_minutes) as min_time,
                        MAX(travel_time_minutes) as max_time,
                        AVG(CASE WHEN hour BETWEEN 7 AND 9 OR hour BETWEEN 17 AND 19 
                            THEN travel_time_minutes END) as peak_avg,
                        AVG(CASE WHEN hour NOT BETWEEN 7 AND 9 AND hour NOT BETWEEN 17 AND 19 
                            THEN travel_time_minutes END) as off_peak_avg,
                        AVG(CASE WHEN day_type = 'Weekend Day' 
                            THEN travel_time_minutes END) as weekend_avg,
                        AVG(CASE WHEN weather_condition IN ('Rainy', 'Heavy Rain') 
                            THEN travel_time_minutes END) as rainy_avg
                    FROM traffic_records 
                    WHERE route_name = ? 
                    AND timestamp >= datetime('now', '-{} days')
                '''.format(days_back), (route_name,))

                row = cursor.fetchone()

                if row and row['total_records'] > 0:
                    return AnalyticsData(
                        route_name=route_name,
                        average_travel_time=row['avg_time'] or 0.0,
                        min_travel_time=row['min_time'] or 0,
                        max_travel_time=row['max_time'] or 0,
                        peak_hour_average=row['peak_avg'] or 0.0,
                        off_peak_average=row['off_peak_avg'] or 0.0,
                        weekend_average=row['weekend_avg'] or 0.0,
                        rainy_day_average=row['rainy_avg'] or 0.0,
                        total_records=row['total_records'],
                        last_updated=datetime.now()
                    )
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting route analytics: {e}")
            raise

    def get_peak_hours_analysis(self, route_name: Optional[str] = None) -> Dict[int, float]:
        """Get average travel times by hour"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                query = '''
                    SELECT hour, AVG(travel_time_minutes) as avg_time
                    FROM traffic_records
                    WHERE timestamp >= datetime('now', '-30 days')
                '''

                params = []
                if route_name:
                    query = query.replace('WHERE', 'WHERE route_name = ? AND')
                    params.append(route_name)

                query += ' GROUP BY hour ORDER BY hour'

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return {row['hour']: row['avg_time'] for row in rows}
        except sqlite3.Error as e:
            self.logger.error(f"Error getting peak hours analysis: {e}")
            raise

    # Data maintenance operations
    def cleanup_old_records(self, days_to_keep: int = 90):
        """Remove old traffic records to maintain database size"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    DELETE FROM traffic_records 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(days_to_keep))

                deleted_count = cursor.rowcount
                conn.commit()

                self.logger.info(f"Cleaned up {deleted_count} old records")
                return deleted_count
        except sqlite3.Error as e:
            self.logger.error(f"Error cleaning up old records: {e}")
            raise

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get record counts
                cursor.execute('SELECT COUNT(*) as count FROM routes')
                routes_count = cursor.fetchone()['count']

                cursor.execute('SELECT COUNT(*) as count FROM traffic_records')
                records_count = cursor.fetchone()['count']

                # Get date range of records
                cursor.execute('SELECT MIN(timestamp) as min_date, MAX(timestamp) as max_date FROM traffic_records')
                date_range = cursor.fetchone()

                # Get database file size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

                return {
                    'routes_count': routes_count,
                    'records_count': records_count,
                    'earliest_record': date_range['min_date'],
                    'latest_record': date_range['max_date'],
                    'database_size_mb': db_size / (1024 * 1024),
                    'database_path': self.db_path
                }
        except sqlite3.Error as e:
            self.logger.error(f"Error getting database stats: {e}")
            raise


class TrafficRecordRepository:
    """
    Specialized repository for traffic record operations
    Implements specific business logic for traffic data
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = get_logger(__name__)

    def get_similar_conditions_records(self, request: PredictionRequest,
                                       days_back: int = 90) -> List[TrafficRecord]:
        """Get records with similar conditions for prediction"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Query for exact matches first
                cursor.execute('''
                    SELECT * FROM traffic_records 
                    WHERE route_name = ? 
                    AND day_type = ? 
                    AND hour = ? 
                    AND weather_condition = ?
                    AND season_type = ?
                    AND timestamp >= datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                    LIMIT 50
                '''.format(days_back), (
                    request.route_name,
                    request.day_type.value,
                    request.hour,
                    request.weather_condition.value,
                    request.season_type.value
                ))

                exact_matches = cursor.fetchall()

                if len(exact_matches) >= 5:  # Enough exact matches
                    records = []
                    for row in exact_matches:
                        records.append(TrafficRecord(
                            id=row['id'],
                            timestamp=datetime.fromisoformat(row['timestamp']),
                            route_name=row['route_name'],
                            travel_time_minutes=row['travel_time_minutes'],
                            distance_km=row['distance_km'],
                            day_type=DayType(row['day_type']),
                            weather_condition=WeatherCondition(row['weather_condition']),
                            season_type=SeasonType(row['season_type']),
                            hour=row['hour'],
                            day_of_week=row['day_of_week'],
                            is_holiday=bool(row['is_holiday']),
                            traffic_density=TrafficDensity(row['traffic_density']),
                            average_speed_kmh=row['average_speed_kmh']
                        ))
                    return records

                # If not enough exact matches, get broader matches
                cursor.execute('''
                    SELECT * FROM traffic_records 
                    WHERE route_name = ? 
                    AND day_type = ? 
                    AND ABS(hour - ?) <= 1
                    AND timestamp >= datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                    LIMIT 100
                '''.format(days_back), (
                    request.route_name,
                    request.day_type.value,
                    request.hour
                ))

                broader_matches = cursor.fetchall()
                records = []
                for row in broader_matches:
                    records.append(TrafficRecord(
                        id=row['id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        route_name=row['route_name'],
                        travel_time_minutes=row['travel_time_minutes'],
                        distance_km=row['distance_km'],
                        day_type=DayType(row['day_type']),
                        weather_condition=WeatherCondition(row['weather_condition']),
                        season_type=SeasonType(row['season_type']),
                        hour=row['hour'],
                        day_of_week=row['day_of_week'],
                        is_holiday=bool(row['is_holiday']),
                        traffic_density=TrafficDensity(row['traffic_density']),
                        average_speed_kmh=row['average_speed_kmh']
                    ))
                return records

        except sqlite3.Error as e:
            self.logger.error(f"Error getting similar conditions records: {e}")
            raise

    def bulk_insert_records(self, records: List[TrafficRecord]):
        """Bulk insert multiple traffic records efficiently"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                record_data = []
                for record in records:
                    record_data.append((
                        record.timestamp, record.route_name, record.travel_time_minutes,
                        record.distance_km, record.day_type.value, record.weather_condition.value,
                        record.season_type.value, record.hour, record.day_of_week,
                        record.is_holiday, record.traffic_density.value, record.average_speed_kmh
                    ))

                cursor.executemany('''
                    INSERT INTO traffic_records 
                    (timestamp, route_name, travel_time_minutes, distance_km, day_type, 
                     weather_condition, season_type, hour, day_of_week, is_holiday, 
                     traffic_density, average_speed_kmh)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', record_data)

                conn.commit()
                self.logger.info(f"Bulk inserted {len(records)} traffic records")

        except sqlite3.Error as e:
            self.logger.error(f"Error bulk inserting records: {e}")
            raise

    def get_latest_record_by_route(self, route_name: str) -> Optional[TrafficRecord]:
        """Get the most recent record for a specific route"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM traffic_records 
                    WHERE route_name = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (route_name,))

                row = cursor.fetchone()
                if row:
                    return TrafficRecord(
                        id=row['id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        route_name=row['route_name'],
                        travel_time_minutes=row['travel_time_minutes'],
                        distance_km=row['distance_km'],
                        day_type=DayType(row['day_type']),
                        weather_condition=WeatherCondition(row['weather_condition']),
                        season_type=SeasonType(row['season_type']),
                        hour=row['hour'],
                        day_of_week=row['day_of_week'],
                        is_holiday=bool(row['is_holiday']),
                        traffic_density=TrafficDensity(row['traffic_density']),
                        average_speed_kmh=row['average_speed_kmh']
                    )
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting latest record: {e}")
            raise