# config/settings.py
# Configuration settings for the Traffic Analysis System

import os
from datetime import timedelta


class DatabaseConfig:
    """Database configuration settings"""
    DB_NAME = 'traffic_data.db'
    DB_PATH = 'database/'
    FULL_DB_PATH = os.path.join(DB_PATH, DB_NAME)
    CONNECTION_TIMEOUT = 30


class APIConfig:
    """External API configuration"""
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', 'your_api_key_here')
    OPENWEATHER_API_KEY = '67e270ed8a0a234d0b7d731da4af4183'

    # API URLs
    GOOGLE_DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
    OPENWEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"

    # Request settings
    REQUEST_TIMEOUT = 10
    MAX_RETRIES = 3


class TrafficConfig:
    """Traffic analysis configuration"""
    DEFAULT_ROUTES = [
        'High Level Road',
        'Low Level Road',
        'Baseline Road',
        'Galle Road',
        'Marine Drive',
        'Other Roads'
    ]

    # Coordinates (Maharagama to Town Hall)
    ORIGIN_COORDS = {'lat': 6.8431, 'lng': 79.9186}
    DESTINATION_COORDS = {'lat': 6.9271, 'lng': 79.8612}

    # Time settings
    RUSH_HOUR_MORNING = (7, 9)
    RUSH_HOUR_EVENING = (17, 19)
    PEAK_TRAFFIC_MULTIPLIER = 1.6
    OFF_PEAK_MULTIPLIER = 0.9

    # Weather impact factors
    WEATHER_MULTIPLIERS = {
        'Clear': 1.0,
        'Cloudy': 1.1,
        'Rainy': 1.3,
        'Heavy Rain': 1.5
    }


class DataCollectionConfig:
    """Data collection settings"""
    COLLECTION_INTERVAL = timedelta(minutes=15)  # Collect data every 15 minutes
    HISTORICAL_DATA_RETENTION = timedelta(days=90)  # Keep 90 days of data
    BATCH_SIZE = 50  # Process data in batches


class LoggingConfig:
    """Logging configuration"""
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'logs/traffic_analyzer.log'
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5


class WebConfig:
    """Web application configuration"""
    HOST = '127.0.0.1'
    PORT = 5000
    DEBUG = True
    SECRET_KEY = 'traffic_analyzer_secret_key_change_in_production'


# Application-wide settings
class AppConfig:
    """Main application configuration"""
    APP_NAME = "Maharagama-TownHall Traffic Analyzer"
    VERSION = "1.0.0"
    AUTHOR = "Traffic Analysis Team"

    # Feature flags
    ENABLE_WEB_INTERFACE = True
    ENABLE_API_INTEGRATION = True
    ENABLE_REAL_TIME_DATA = True
    ENABLE_PREDICTIONS = True