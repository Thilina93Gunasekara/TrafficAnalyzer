"""
Data Access Layer
Contains database operations, models, and data repositories
"""

from .models import (
    Route, TrafficRecord, PredictionRequest, PredictionResult,
    RouteComparison, WeatherData, RealTimeTrafficData, AnalyticsData,
    DayType, WeatherCondition, TrafficDensity, SeasonType
)
from .database_manager import DatabaseManager, TrafficRecordRepository

__all__ = [
    'Route', 'TrafficRecord', 'PredictionRequest', 'PredictionResult',
    'RouteComparison', 'WeatherData', 'RealTimeTrafficData', 'AnalyticsData',
    'DayType', 'WeatherCondition', 'TrafficDensity', 'SeasonType',
    'DatabaseManager', 'TrafficRecordRepository'
]