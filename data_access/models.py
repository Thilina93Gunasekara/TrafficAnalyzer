# data_access/models.py
# Data models for the Traffic Analysis System

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class DayType(Enum):
    """Enumeration for day types"""
    WEEKDAY = "Week Day"
    WEEKEND = "Weekend Day"
    RAINY_DAY = "Raine Day"


class WeatherCondition(Enum):
    """Enumeration for weather conditions"""
    CLEAR = "Clear"
    CLOUDY = "Cloudy"
    RAINY = "Rainy"
    HEAVY_RAIN = "Heavy Rain"


class TrafficDensity(Enum):
    """Enumeration for traffic density levels"""
    LIGHT = "Light"
    MODERATE = "Moderate"
    HEAVY = "Heavy"
    VERY_HEAVY = "Very Heavy"


class SeasonType(Enum):
    """Enumeration for seasonal variations"""
    REGULAR = "Regular Season"
    SCHOOL_HOLIDAY = "School holidays"
    PUBLIC_HOLIDAY = "Public Holiday"


@dataclass
class Route:
    """Route data model"""
    id: Optional[int] = None
    name: str = ""
    start_latitude: float = 0.0
    start_longitude: float = 0.0
    end_latitude: float = 0.0
    end_longitude: float = 0.0
    distance_km: float = 0.0
    typical_speed_kmh: float = 0.0
    route_type: str = "main"

    def __str__(self):
        return f"Route: {self.name} ({self.distance_km:.1f}km)"


@dataclass
class TrafficRecord:
    """Traffic data record model"""
    id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    route_name: str = ""
    travel_time_minutes: int = 0
    distance_km: float = 0.0
    day_type: DayType = DayType.WEEKDAY
    weather_condition: WeatherCondition = WeatherCondition.CLEAR
    season_type: SeasonType = SeasonType.REGULAR
    hour: int = 0
    day_of_week: int = 0
    is_holiday: bool = False
    traffic_density: TrafficDensity = TrafficDensity.MODERATE
    average_speed_kmh: float = 0.0

    def __post_init__(self):
        """Post-initialization calculations"""
        if self.travel_time_minutes > 0 and self.distance_km > 0:
            self.average_speed_kmh = (self.distance_km / (self.travel_time_minutes / 60))

        if isinstance(self.timestamp, datetime):
            self.hour = self.timestamp.hour
            self.day_of_week = self.timestamp.weekday()

    def __str__(self):
        return f"Traffic Record: {self.route_name} at {self.timestamp.strftime('%H:%M')} - {self.travel_time_minutes} min"


@dataclass
class PredictionRequest:
    """Model for traffic prediction requests"""
    route_name: str
    day_type: DayType
    hour: int
    weather_condition: WeatherCondition
    season_type: SeasonType = SeasonType.REGULAR

    def __str__(self):
        return f"Prediction for {self.route_name} on {self.day_type.value} at {self.hour}:00"


@dataclass
class PredictionResult:
    """Model for traffic prediction results"""
    route_name: str
    predicted_time_minutes: int
    confidence_level: float
    factors_considered: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return f"{self.route_name}: {self.predicted_time_minutes} min (confidence: {self.confidence_level:.1%})"


@dataclass
class RouteComparison:
    """Model for comparing multiple routes"""
    request_params: PredictionRequest
    predictions: List[PredictionResult] = field(default_factory=list)
    best_route: str = ""
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_sorted_routes(self) -> List[PredictionResult]:
        """Get routes sorted by predicted travel time"""
        return sorted(self.predictions, key=lambda x: x.predicted_time_minutes)

    def get_time_difference(self, route1: str, route2: str) -> int:
        """Get time difference between two routes"""
        route1_time = next((p.predicted_time_minutes for p in self.predictions if p.route_name == route1), 0)
        route2_time = next((p.predicted_time_minutes for p in self.predictions if p.route_name == route2), 0)
        return abs(route1_time - route2_time)


@dataclass
class WeatherData:
    """Weather information model"""
    condition: WeatherCondition
    temperature_celsius: float
    humidity_percent: int
    wind_speed_kmh: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return f"Weather: {self.condition.value}, {self.temperature_celsius}°C, {self.humidity_percent}% humidity"


@dataclass
class RealTimeTrafficData:
    """Real-time traffic data from APIs"""
    route_name: str
    current_travel_time_minutes: int
    typical_travel_time_minutes: int
    delay_minutes: int = 0
    traffic_condition: TrafficDensity = TrafficDensity.MODERATE
    distance_km: float = 0.0
    average_speed_kmh: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Calculate derived values"""
        self.delay_minutes = max(0, self.current_travel_time_minutes - self.typical_travel_time_minutes)
        if self.distance_km > 0 and self.current_travel_time_minutes > 0:
            self.average_speed_kmh = (self.distance_km / (self.current_travel_time_minutes / 60))

    def get_delay_percentage(self) -> float:
        """Get delay as percentage of typical time"""
        if self.typical_travel_time_minutes > 0:
            return (self.delay_minutes / self.typical_travel_time_minutes) * 100
        return 0.0

    def __str__(self):
        return f"{self.route_name}: {self.current_travel_time_minutes} min ({self.delay_minutes} min delay)"


@dataclass
class AnalyticsData:
    """Analytics and statistics model"""
    route_name: str
    average_travel_time: float = 0.0
    min_travel_time: int = 0
    max_travel_time: int = 0
    peak_hour_average: float = 0.0
    off_peak_average: float = 0.0
    weekend_average: float = 0.0
    rainy_day_average: float = 0.0
    total_records: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

    def get_variability(self) -> float:
        """Calculate travel time variability"""
        if self.average_travel_time > 0:
            return ((self.max_travel_time - self.min_travel_time) / self.average_travel_time) * 100
        return 0.0

    def __str__(self):
        return f"{self.route_name} Analytics: Avg {self.average_travel_time:.1f} min, Range {self.min_travel_time}-{self.max_travel_time} min"


# Utility functions for models
def create_traffic_record_from_dict(data: dict) -> TrafficRecord:
    """Create TrafficRecord from dictionary"""
    return TrafficRecord(
        route_name=data.get('route_name', ''),
        travel_time_minutes=data.get('travel_time', 0),
        distance_km=data.get('distance', 0.0),
        day_type=DayType(data.get('day_type', DayType.WEEKDAY.value)),
        weather_condition=WeatherCondition(data.get('weather', WeatherCondition.CLEAR.value)),
        season_type=SeasonType(data.get('season', SeasonType.REGULAR.value)),
        traffic_density=TrafficDensity(data.get('traffic_density', TrafficDensity.MODERATE.value))
    )


def create_route_from_dict(data: dict) -> Route:
    """Create Route from dictionary"""
    return Route(
        name=data.get('name', ''),
        start_latitude=data.get('start_lat', 0.0),
        start_longitude=data.get('start_lng', 0.0),
        end_latitude=data.get('end_lat', 0.0),
        end_longitude=data.get('end_lng', 0.0),
        distance_km=data.get('distance', 0.0),
        typical_speed_kmh=data.get('speed', 0.0),
        route_type=data.get('type', 'main')
    )


# Export all models
__all__ = [
    'DayType',
    'WeatherCondition',
    'TrafficDensity',
    'SeasonType',
    'Route',
    'TrafficRecord',
    'PredictionRequest',
    'PredictionResult',
    'RouteComparison',
    'WeatherData',
    'RealTimeTrafficData',
    'AnalyticsData',
    'create_traffic_record_from_dict',
    'create_route_from_dict'
]