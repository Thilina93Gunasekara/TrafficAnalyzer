# generate_colombo_data.py
# Generate realistic sample traffic data for Colombo routes

import sqlite3
import random
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Tuple
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from data_access.models import DayType, WeatherCondition, SeasonType, TrafficDensity


@dataclass
class ColomboRoute:
    """Route definition for Colombo area"""
    name: str
    from_location: str
    to_location: str
    distance_km: float
    base_speed_kmh: float
    route_type: str
    flood_prone: bool = False


class ColomboDataGenerator:
    """Generate realistic traffic data for Colombo routes"""

    def __init__(self, db_path='database/traffic_data.db'):
        self.db_path = db_path
        self.routes = self._define_colombo_routes()
        self.holidays = self._get_sri_lankan_holidays()

    def _define_colombo_routes(self) -> List[ColomboRoute]:
        """Define all major routes in Colombo area"""
        return [
            # Maharagama to Town Hall (existing)
            ColomboRoute("High Level Road", "Maharagama", "Town Hall, Colombo", 12.5, 35, "main"),
            ColomboRoute("Low Level Road", "Maharagama", "Town Hall, Colombo", 14.2, 30, "main", True),
            ColomboRoute("Baseline Road", "Maharagama", "Town Hall, Colombo", 13.8, 32, "main"),
            ColomboRoute("Galle Road", "Maharagama", "Town Hall, Colombo", 15.1, 28, "main"),
            ColomboRoute("Marine Drive", "Maharagama", "Town Hall, Colombo", 16.3, 25, "scenic", True),
            ColomboRoute("Other Roads", "Maharagama", "Town Hall, Colombo", 11.8, 20, "minor"),

            # Nugegoda to Fort
            ColomboRoute("High Level Road", "Nugegoda", "Colombo Fort", 11.2, 38, "main"),
            ColomboRoute("Galle Road", "Nugegoda", "Colombo Fort", 10.8, 32, "main"),
            ColomboRoute("Duplication Road", "Nugegoda", "Colombo Fort", 12.1, 35, "main"),

            # Dehiwala to Pettah
            ColomboRoute("Galle Road", "Dehiwala", "Pettah", 9.5, 30, "main"),
            ColomboRoute("Old Galle Road", "Dehiwala", "Pettah", 10.2, 25, "minor"),

            # Mount Lavinia to Colombo
            ColomboRoute("Galle Road", "Mount Lavinia", "Colombo Fort", 12.4, 32, "main"),
            ColomboRoute("Marine Drive", "Mount Lavinia", "Colombo Fort", 13.8, 28, "scenic", True),

            # Moratuwa to Colombo
            ColomboRoute("Galle Road", "Moratuwa", "Colombo Fort", 18.5, 35, "main"),
            ColomboRoute("New Galle Road", "Moratuwa", "Colombo Fort", 17.2, 40, "highway"),

            # Battaramulla to Fort
            ColomboRoute("Baseline Road", "Battaramulla", "Colombo Fort", 10.5, 35, "main"),
            ColomboRoute("Parliament Road", "Battaramulla", "Colombo Fort", 11.8, 30, "main"),

            # Rajagiriya to Colombo
            ColomboRoute("Kotte Road", "Rajagiriya", "Colombo Fort", 8.9, 38, "main"),
            ColomboRoute("Nawala Road", "Rajagiriya", "Colombo Fort", 9.5, 35, "main"),

            # Malabe to Colombo
            ColomboRoute("Kaduwela Road", "Malabe", "Colombo Fort", 15.6, 40, "main"),
            ColomboRoute("Athurugiriya Road", "Malabe", "Colombo Fort", 16.8, 38, "main"),

            # Negombo to Colombo
            ColomboRoute("Negombo Road", "Negombo", "Colombo Fort", 38.5, 50, "highway"),
            ColomboRoute("Old Negombo Road", "Negombo", "Colombo Fort", 42.1, 40, "main"),

            # Gampaha to Colombo
            ColomboRoute("Kandy Road", "Gampaha", "Colombo Fort", 28.3, 45, "main"),
            ColomboRoute("Old Kandy Road", "Gampaha", "Colombo Fort", 30.5, 38, "main"),

            # Kadawatha to Colombo
            ColomboRoute("Kandy Road", "Kadawatha", "Colombo Fort", 18.9, 42, "main"),
            ColomboRoute("Ragama Road", "Kadawatha", "Colombo Fort", 20.3, 38, "main"),

            # Wattala to Colombo
            ColomboRoute("Negombo Road", "Wattala", "Colombo Fort", 16.7, 40, "main"),

            # Kelaniya to Colombo
            ColomboRoute("Kandy Road", "Kelaniya", "Colombo Fort", 12.4, 38, "main"),
            ColomboRoute("Baseline Road", "Kelaniya", "Colombo Fort", 13.2, 35, "main"),

            # Kalutara to Colombo
            ColomboRoute("Galle Road", "Kalutara", "Colombo Fort", 42.8, 50, "main"),
            ColomboRoute("Southern Expressway", "Kalutara", "Colombo Fort", 45.2, 80, "highway"),

            # Panadura to Colombo
            ColomboRoute("Galle Road", "Panadura", "Colombo Fort", 28.4, 45, "main"),

            # Borella to Fort
            ColomboRoute("Maradana Road", "Borella", "Colombo Fort", 4.2, 30, "main"),
            ColomboRoute("Baseline Road", "Borella", "Colombo Fort", 4.8, 28, "main"),

            # Pettah to Galle Face
            ColomboRoute("Main Street", "Pettah", "Galle Face", 2.5, 20, "main"),
            ColomboRoute("York Street", "Pettah", "Galle Face", 2.8, 18, "minor"),
        ]

    def _get_sri_lankan_holidays(self) -> set:
        """Get Sri Lankan public holidays"""
        return {
            (1, 1), (1, 14), (2, 4), (2, 23), (3, 29), (4, 12),
            (5, 1), (5, 23), (5, 24), (6, 18), (8, 19), (10, 31), (12, 25)
        }

    def generate_traffic_data(self, days_back: int = 90, records_per_route_per_day: int = 16):
        """Generate comprehensive traffic data"""
        print(f"Generating traffic data for {len(self.routes)} routes...")
        print(f"Period: Last {days_back} days")
        print(f"Records per route per day: {records_per_route_per_day}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create routes table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_location TEXT,
                end_location TEXT,
                start_latitude REAL,
                start_longitude REAL,
                end_latitude REAL,
                end_longitude REAL,
                distance_km REAL,
                typical_speed_kmh REAL,
                route_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, start_location, end_location)
            )
        ''')

        # Insert routes
        for route in self.routes:
            cursor.execute('''
                INSERT OR IGNORE INTO routes 
                (name, start_location, end_location, distance_km, typical_speed_kmh, route_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (route.name, route.from_location, route.to_location,
                  route.distance_km, route.base_speed_kmh, route.route_type))

        conn.commit()

        # Generate traffic records
        start_date = datetime.now() - timedelta(days=days_back)
        total_records = 0

        for route in self.routes:
            route_records = 0

            for day in range(days_back):
                current_date = start_date + timedelta(days=day)

                # Determine day characteristics
                is_weekend = current_date.weekday() >= 5
                is_holiday = (current_date.month, current_date.day) in self.holidays

                # Generate records at different hours
                hours = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]

                for hour in random.sample(hours, min(records_per_route_per_day, len(hours))):
                    record_time = current_date.replace(
                        hour=hour,
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
                    )

                    # Generate realistic traffic data
                    traffic_data = self._generate_realistic_traffic(
                        route, record_time, is_weekend, is_holiday
                    )

                    cursor.execute('''
                        INSERT INTO traffic_records 
                        (timestamp, route_name, travel_time_minutes, distance_km, 
                         day_type, weather_condition, season_type, hour, day_of_week, 
                         is_holiday, traffic_density, average_speed_kmh)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record_time,
                        f"{route.from_location} to {route.to_location} via {route.name}",
                        traffic_data['travel_time'],
                        route.distance_km,
                        traffic_data['day_type'],
                        traffic_data['weather'],
                        traffic_data['season'],
                        hour,
                        current_date.weekday(),
                        is_holiday,
                        traffic_data['traffic_density'],
                        traffic_data['avg_speed']
                    ))

                    route_records += 1
                    total_records += 1

            print(f"  ✓ {route.from_location} to {route.to_location} via {route.name}: {route_records} records")

        conn.commit()
        conn.close()

        print(f"\n✅ Successfully generated {total_records} traffic records!")
        print(f"Database: {self.db_path}")

    def _generate_realistic_traffic(self, route: ColomboRoute, timestamp: datetime,
                                    is_weekend: bool, is_holiday: bool) -> dict:
        """Generate realistic traffic conditions"""
        hour = timestamp.hour
        month = timestamp.month

        # Base travel time
        base_time = (route.distance_km / route.base_speed_kmh) * 60

        # Time-based multiplier
        if 7 <= hour <= 9:  # Morning rush
            time_multiplier = random.uniform(1.6, 2.2)
            traffic_density = random.choice(['Heavy', 'Very Heavy'])
        elif 17 <= hour <= 19:  # Evening rush
            time_multiplier = random.uniform(1.7, 2.3)
            traffic_density = random.choice(['Heavy', 'Very Heavy'])
        elif 10 <= hour <= 16:  # Daytime
            time_multiplier = random.uniform(1.1, 1.4)
            traffic_density = random.choice(['Moderate', 'Heavy'])
        else:  # Off-peak
            time_multiplier = random.uniform(0.85, 1.1)
            traffic_density = random.choice(['Light', 'Moderate'])

        # Weekend adjustment
        if is_weekend:
            time_multiplier *= 0.75
            if traffic_density == 'Very Heavy':
                traffic_density = 'Heavy'

        # Holiday adjustment
        if is_holiday:
            time_multiplier *= 0.65
            traffic_density = 'Light'

        # Weather simulation (Sri Lankan patterns)
        if month in [5, 6, 7, 8, 9, 10, 11, 12]:  # Monsoon months
            weather_options = ['Clear', 'Cloudy', 'Rainy', 'Heavy Rain']
            weather_probs = [0.3, 0.3, 0.3, 0.1]
        else:
            weather_options = ['Clear', 'Cloudy', 'Rainy', 'Heavy Rain']
            weather_probs = [0.5, 0.3, 0.15, 0.05]

        weather = random.choices(weather_options, weights=weather_probs)[0]

        # Weather impact
        if weather == 'Heavy Rain':
            time_multiplier *= random.uniform(1.3, 1.6)
            if route.flood_prone:
                time_multiplier *= 1.2
        elif weather == 'Rainy':
            time_multiplier *= random.uniform(1.15, 1.3)

        # Route type adjustment
        if route.route_type == 'highway':
            time_multiplier *= 0.85  # Highways are more efficient
        elif route.route_type == 'minor':
            time_multiplier *= 1.15  # Minor roads slower

        # Calculate final values
        travel_time = int(base_time * time_multiplier)
        avg_speed = route.distance_km / (travel_time / 60) if travel_time > 0 else 0

        # Determine day type
        if weather in ['Heavy Rain', 'Rainy']:
            day_type = 'Raine Day'
        elif is_weekend:
            day_type = 'Weekend Day'
        else:
            day_type = 'Week Day'

        # Determine season
        if is_holiday:
            season = 'Public Holiday'
        elif month in [4, 8, 12]:  # School holiday months
            season = 'School holidays'
        else:
            season = 'Regular Season'

        return {
            'travel_time': travel_time,
            'avg_speed': round(avg_speed, 2),
            'day_type': day_type,
            'weather': weather,
            'season': season,
            'traffic_density': traffic_density
        }


def main():
    """Run data generation"""
    generator = ColomboDataGenerator()
    generator.generate_traffic_data(days_back=90, records_per_route_per_day=16)


if __name__ == "__main__":
    main()