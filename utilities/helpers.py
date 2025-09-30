# utilities/helpers.py
# Common utility functions used across the application

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import re
import json
import hashlib


def format_time_minutes(minutes: int) -> str:
    """Format minutes into a readable time string"""
    if minutes < 60:
        return f"{minutes} minutes"
    else:
        hours = minutes // 60
        remaining_mins = minutes % 60
        if remaining_mins == 0:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours > 1 else ''} {remaining_mins} minutes"


def format_distance_km(distance: float) -> str:
    """Format distance in kilometers"""
    if distance < 1:
        return f"{int(distance * 1000)} meters"
    else:
        return f"{distance:.1f} km"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100


def validate_hour(hour: int) -> bool:
    """Validate if hour is in valid range"""
    return 0 <= hour <= 23


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude"""
    return -90 <= lat <= 90 and -180 <= lon <= 180


def parse_time_string(time_str: str) -> Optional[datetime]:
    """Parse various time string formats"""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%H:%M:%S",
        "%H:%M"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue

    return None


def calculate_travel_time_from_speed(distance_km: float, speed_kmh: float) -> int:
    """Calculate travel time in minutes from distance and speed"""
    if speed_kmh <= 0:
        return 0
    return int((distance_km / speed_kmh) * 60)


def sanitize_route_name(route_name: str) -> str:
    """Sanitize route name for use in filenames"""
    return re.sub(r'[^\w\s-]', '', route_name).strip().replace(' ', '_')


def generate_cache_key(*args) -> str:
    """Generate a cache key from arguments"""
    key_string = '_'.join(str(arg) for arg in args)
    return hashlib.md5(key_string.encode()).hexdigest()


def format_timestamp(dt: datetime, format_type: str = 'full') -> str:
    """Format datetime in various formats"""
    formats = {
        'full': "%Y-%m-%d %H:%M:%S",
        'date': "%Y-%m-%d",
        'time': "%H:%M",
        'short': "%m/%d %H:%M",
        'display': "%B %d, %Y at %I:%M %p"
    }
    return dt.strftime(formats.get(format_type, formats['full']))


def is_rush_hour(hour: int) -> bool:
    """Check if given hour is rush hour"""
    return (7 <= hour <= 9) or (17 <= hour <= 19)


def calculate_eta(current_time: datetime, travel_minutes: int) -> datetime:
    """Calculate estimated time of arrival"""
    return current_time + timedelta(minutes=travel_minutes)


def get_day_type_from_datetime(dt: datetime) -> str:
    """Get day type (Weekday/Weekend) from datetime"""
    return "Weekend Day" if dt.weekday() >= 5 else "Week Day"


def convert_to_json(obj: Any) -> str:
    """Convert object to JSON string with custom handling"""

    def default_handler(o):
        if isinstance(o, datetime):
            return o.isoformat()
        if hasattr(o, '__dict__'):
            return o.__dict__
        return str(o)

    return json.dumps(obj, default=default_handler, indent=2)


def parse_json_safe(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def calculate_average(values: List[float]) -> float:
    """Calculate average of a list of values"""
    if not values:
        return 0.0
    return sum(values) / len(values)


def calculate_median(values: List[float]) -> float:
    """Calculate median of a list of values"""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    mid = n // 2

    if n % 2 == 0:
        return (sorted_values[mid - 1] + sorted_values[mid]) / 2
    else:
        return sorted_values[mid]


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate string to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def validate_email(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(value, max_val))


def get_sri_lankan_holidays_2024() -> Dict[Tuple[int, int], str]:
    """Get Sri Lankan public holidays for 2024"""
    return {
        (1, 1): "New Year's Day",
        (1, 14): "Thai Pongal",
        (2, 4): "Independence Day",
        (2, 23): "Maha Shivaratri",
        (3, 29): "Good Friday",
        (4, 12): "Eid ul-Fitr (Ramadan Festival)",
        (5, 1): "May Day",
        (5, 23): "Vesak Full Moon Poya Day",
        (5, 24): "Day after Vesak",
        (6, 18): "Eid ul-Adha (Hajj Festival)",
        (8, 19): "Nikini Full Moon Poya Day",
        (10, 31): "Deepavali",
        (12, 25): "Christmas Day"
    }


def is_sri_lankan_holiday(date: datetime) -> bool:
    """Check if date is a Sri Lankan public holiday"""
    holidays = get_sri_lankan_holidays_2024()
    return (date.month, date.day) in holidays


def format_sri_lankan_currency(amount: float) -> str:
    """Format amount in Sri Lankan Rupees"""
    return f"Rs. {amount:,.2f}"


def calculate_fuel_cost(distance_km: float, fuel_efficiency_kmpl: float = 15,
                        fuel_price_per_liter: float = 350) -> float:
    """Calculate estimated fuel cost for journey"""
    liters_needed = distance_km / fuel_efficiency_kmpl
    return liters_needed * fuel_price_per_liter


def get_time_of_day(hour: int) -> str:
    """Get descriptive time of day"""
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening"
    else:
        return "Night"


def calculate_confidence_interval(mean: float, std: float,
                                  confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate confidence interval"""
    import math
    z_score = 1.96  # For 95% confidence
    margin = z_score * std
    return (mean - margin, mean + margin)


# Export all utility functions
__all__ = [
    'format_time_minutes', 'format_distance_km', 'calculate_percentage_change',
    'validate_hour', 'validate_coordinates', 'parse_time_string',
    'calculate_travel_time_from_speed', 'sanitize_route_name', 'generate_cache_key',
    'format_timestamp', 'is_rush_hour', 'calculate_eta', 'get_day_type_from_datetime',
    'convert_to_json', 'parse_json_safe', 'calculate_average', 'calculate_median',
    'truncate_string', 'format_file_size', 'validate_email', 'clamp',
    'get_sri_lankan_holidays_2024', 'is_sri_lankan_holiday', 'format_sri_lankan_currency',
    'calculate_fuel_cost', 'get_time_of_day', 'calculate_confidence_interval'
]