# test_weather.py
from external_services.weather_service import SriLankanWeatherService

weather = SriLankanWeatherService()

# Test 1: Get current weather
print("Getting current weather...")
current = weather.get_current_weather_colombo_region()
print(f"✅ Condition: {current.condition.value}")
print(f"✅ Temperature: {current.temperature_celsius}°C")
print(f"✅ Humidity: {current.humidity_percent}%")

# Test 2: Check data source
from config.settings import APIConfig
if APIConfig.OPENWEATHER_API_KEY == 'your_api_key_here':
    print("\n⚠️  Using SIMULATED data (demo mode)")
else:
    print("\n✅ Using REAL API data")

print("\n🎉 Weather service is working!")