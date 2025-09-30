# test_models.py - Quick test to verify models.py works

from data_access.models import (
    DayType, WeatherCondition, Route,
    TrafficRecord, PredictionRequest, SeasonType
)

print("Testing data models...")
print("=" * 50)

# Test 1: Enums
print("✅ DayType.WEEKDAY =", DayType.WEEKDAY.value)
print("✅ WeatherCondition.CLEAR =", WeatherCondition.CLEAR.value)
print("✅ SeasonType.REGULAR =", SeasonType.REGULAR.value)

# Test 2: Create a Route
route = Route(name="Test Route", distance_km=10.0, typical_speed_kmh=40)
print(f"✅ Created route: {route}")

# Test 3: Create a PredictionRequest
request = PredictionRequest(
    route_name="High Level Road",
    day_type=DayType.WEEKDAY,
    hour=8,
    weather_condition=WeatherCondition.CLEAR
)
print(f"✅ Created request: {request}")

print("=" * 50)
print("🎉 All tests passed! models.py is working perfectly!")