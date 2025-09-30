# external_services/api_handler.py
# External API integrations for real-time traffic and weather data

# external_services/api_handler.py
# External API integrations for real-time traffic and weather data

import requests
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
import random
import sys
import os

# Add parent directory to path if needed
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_access.models import (
    RealTimeTrafficData, WeatherData, TrafficRecord,
    TrafficDensity, WeatherCondition, DayType, SeasonType
)
from config.settings import APIConfig, TrafficConfig
from utilities.logger import get_logger


class GoogleMapsAPIService:
    """
    Service for Google Maps API integration
    Handles real-time traffic data and route calculations
    """

    def __init__(self):
        self.api_key = APIConfig.GOOGLE_MAPS_API_KEY
        self.base_url = APIConfig.GOOGLE_DIRECTIONS_URL
        self.logger = get_logger(__name__)
        self.request_count = 0
        self.last_request_time = 0

    def get_real_time_traffic(self, route_name: str, origin: str = None,
                              destination: str = None) -> Optional[RealTimeTrafficData]:
        """
        Get real-time traffic data for a specific route
        """
        try:
            # Use default coordinates if not provided
            if not origin:
                coords = TrafficConfig.ORIGIN_COORDS
                origin = f"{coords['lat']},{coords['lng']}"

            if not destination:
                coords = TrafficConfig.DESTINATION_COORDS
                destination = f"{coords['lat']},{coords['lng']}"

            # Rate limiting
            self._enforce_rate_limit()

            # For demo/development - return simulated data
            if self.api_key == 'your_api_key_here':
                return self._get_simulated_traffic_data(route_name)

            # Actual API call
            params = {
                'origin': origin,
                'destination': destination,
                'key': self.api_key,
                'departure_time': 'now',
                'traffic_model': 'best_guess',
                'alternatives': 'true',
                'units': 'metric'
            }

            response = requests.get(
                self.base_url,
                params=params,
                timeout=APIConfig.REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_directions_response(data, route_name)
            else:
                self.logger.error(f"Google Maps API error: {response.status_code}")
                return self._get_simulated_traffic_data(route_name)

        except requests.RequestException as e:
            self.logger.error(f"Network error calling Google Maps API: {e}")
            return self._get_simulated_traffic_data(route_name)
        except Exception as e:
            self.logger.error(f"Unexpected error in Google Maps API: {e}")
            return self._get_simulated_traffic_data(route_name)

    def _enforce_rate_limit(self):
        """Enforce API rate limiting to avoid quota issues"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        # Ensure minimum 1 second between requests
        if time_since_last_request < 1.0:
            time.sleep(1.0 - time_since_last_request)

        self.last_request_time = time.time()
        self.request_count += 1

    def _parse_directions_response(self, data: Dict, route_name: str) -> RealTimeTrafficData:
        """Parse Google Maps Directions API response"""
        try:
            if data['status'] != 'OK' or not data.get('routes'):
                raise ValueError(f"Invalid API response: {data.get('status', 'Unknown error')}")

            # Get the first route (best route)
            route = data['routes'][0]
            leg = route['legs'][0]

            # Extract traffic information
            duration_in_traffic = leg.get('duration_in_traffic', leg['duration'])
            normal_duration = leg['duration']
            distance = leg['distance']

            # Convert to our data model
            current_time = duration_in_traffic['value'] // 60  # Convert to minutes
            typical_time = normal_duration['value'] // 60
            distance_km = distance['value'] / 1000  # Convert to km

            # Determine traffic condition
            delay_ratio = current_time / typical_time if typical_time > 0 else 1.0
            if delay_ratio < 1.1:
                traffic_condition = TrafficDensity.LIGHT
            elif delay_ratio < 1.3:
                traffic_condition = TrafficDensity.MODERATE
            elif delay_ratio < 1.6:
                traffic_condition = TrafficDensity.HEAVY
            else:
                traffic_condition = TrafficDensity.VERY_HEAVY

            return RealTimeTrafficData(
                route_name=route_name,
                current_travel_time_minutes=current_time,
                typical_travel_time_minutes=typical_time,
                delay_minutes=current_time - typical_time,
                traffic_condition=traffic_condition,
                distance_km=distance_km,
                average_speed_kmh=distance_km / (current_time / 60) if current_time > 0 else 0
            )

        except (KeyError, ValueError, ZeroDivisionError) as e:
            self.logger.error(f"Error parsing Google Maps response: {e}")
            return self._get_simulated_traffic_data(route_name)

    def _get_simulated_traffic_data(self, route_name: str) -> RealTimeTrafficData:
        """Generate simulated traffic data for development/demo"""
        current_hour = datetime.now().hour

        # Base travel times for each route
        base_times = {
            'High Level Road': 25,
            'Low Level Road': 28,
            'Baseline Road': 27,
            'Galle Road': 32,
            'Marine Drive': 35,
            'Other Roads': 22
        }

        base_time = base_times.get(route_name, 30)

        # Apply time-based multiplier with some randomness
        if 7 <= current_hour <= 9 or 17 <= current_hour <= 19:  # Rush hours
            multiplier = random.uniform(1.4, 2.0)
            traffic_condition = TrafficDensity.HEAVY
        elif 10 <= current_hour <= 16:  # Daytime
            multiplier = random.uniform(1.0, 1.3)
            traffic_condition = TrafficDensity.MODERATE
        else:  # Off-peak
            multiplier = random.uniform(0.8, 1.1)
            traffic_condition = TrafficDensity.LIGHT

        current_time = int(base_time * multiplier)

        # Get route distance
        route_distances = {
            'High Level Road': 12.5,
            'Low Level Road': 14.2,
            'Baseline Road': 13.8,
            'Galle Road': 15.1,
            'Marine Drive': 16.3,
            'Other Roads': 11.8
        }

        distance = route_distances.get(route_name, 13.0)

        return RealTimeTrafficData(
            route_name=route_name,
            current_travel_time_minutes=current_time,
            typical_travel_time_minutes=base_time,
            delay_minutes=current_time - base_time,
            traffic_condition=traffic_condition,
            distance_km=distance,
            average_speed_kmh=distance / (current_time / 60) if current_time > 0 else 0
        )

    def get_multiple_routes_traffic(self, routes: List[str]) -> List[RealTimeTrafficData]:
        """Get traffic data for multiple routes"""
        traffic_data = []

        for route in routes:
            try:
                data = self.get_real_time_traffic(route)
                if data:
                    traffic_data.append(data)

                # Small delay between requests to be API-friendly
                time.sleep(0.5)

            except Exception as e:
                self.logger.error(f"Error getting traffic for {route}: {e}")
                continue

        return traffic_data


class WeatherAPIService:
    """
    Service for weather data integration
    """

    def __init__(self):
        self.api_key = APIConfig.OPENWEATHER_API_KEY
        self.base_url = APIConfig.OPENWEATHER_URL
        self.logger = get_logger(__name__)

    def get_current_weather(self, city: str = "Colombo") -> WeatherData:
        """Get current weather conditions"""
        try:
            # For demo/development - return simulated data
            if self.api_key == 'your_api_key_here':
                return self._get_simulated_weather()

            params = {
                'q': f"{city},LK",
                'appid': self.api_key,
                'units': 'metric'
            }

            response = requests.get(
                self.base_url,
                params=params,
                timeout=APIConfig.REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_weather_response(data)
            else:
                self.logger.error(f"Weather API error: {response.status_code}")
                return self._get_simulated_weather()

        except requests.RequestException as e:
            self.logger.error(f"Network error calling Weather API: {e}")
            return self._get_simulated_weather()
        except Exception as e:
            self.logger.error(f"Unexpected error in Weather API: {e}")
            return self._get_simulated_weather()

    def _parse_weather_response(self, data: Dict) -> WeatherData:
        """Parse OpenWeatherMap API response"""
        try:
            weather_desc = data['weather'][0]['main'].lower()

            # Map weather descriptions to our conditions
            if 'rain' in weather_desc or 'drizzle' in weather_desc:
                if 'heavy' in weather_desc or data['rain'].get('1h', 0) > 10:
                    condition = WeatherCondition.HEAVY_RAIN
                else:
                    condition = WeatherCondition.RAINY
            elif 'cloud' in weather_desc:
                condition = WeatherCondition.CLOUDY
            else:
                condition = WeatherCondition.CLEAR

            return WeatherData(
                condition=condition,
                temperature_celsius=data['main']['temp'],
                humidity_percent=data['main']['humidity'],
                wind_speed_kmh=data['wind'].get('speed', 0) * 3.6  # Convert m/s to km/h
            )

        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing weather response: {e}")
            return self._get_simulated_weather()

    def _get_simulated_weather(self) -> WeatherData:
        """Generate simulated weather data"""
        # Simulate realistic Sri Lankan weather patterns
        conditions = [WeatherCondition.CLEAR, WeatherCondition.CLOUDY,
                      WeatherCondition.RAINY, WeatherCondition.HEAVY_RAIN]
        probabilities = [0.4, 0.3, 0.2, 0.1]  # Clear weather more likely

        condition = random.choices(conditions, weights=probabilities)[0]

        # Temperature based on condition
        if condition in [WeatherCondition.RAINY, WeatherCondition.HEAVY_RAIN]:
            temperature = random.uniform(24, 29)
            humidity = random.randint(80, 95)
        else:
            temperature = random.uniform(27, 34)
            humidity = random.randint(60, 85)

        return WeatherData(
            condition=condition,
            temperature_celsius=temperature,
            humidity_percent=humidity,
            wind_speed_kmh=random.uniform(5, 20)
        )


class DataCollectionService:
    """
    Service for automated data collection from external APIs
    """

    def __init__(self, maps_service: GoogleMapsAPIService,
                 weather_service: WeatherAPIService):
        self.maps_service = maps_service
        self.weather_service = weather_service
        self.logger = get_logger(__name__)

    def collect_current_traffic_data(self) -> List[Dict[str, Any]]:
        """Collect current traffic data for all routes"""
        try:
            routes = TrafficConfig.DEFAULT_ROUTES
            current_weather = self.weather_service.get_current_weather()
            current_time = datetime.now()

            collected_data = []

            for route in routes:
                traffic_data = self.maps_service.get_real_time_traffic(route)

                if traffic_data:
                    # Convert to database format
                    db_record = {
                        'timestamp': current_time,
                        'route_name': route,
                        'travel_time_minutes': traffic_data.current_travel_time_minutes,
                        'distance_km': traffic_data.distance_km,
                        'day_type': self._determine_day_type(current_time, current_weather),
                        'weather_condition': current_weather.condition,
                        'season_type': self._determine_season_type(current_time),
                        'hour': current_time.hour,
                        'day_of_week': current_time.weekday(),
                        'is_holiday': self._is_holiday(current_time),
                        'traffic_density': traffic_data.traffic_condition,
                        'average_speed_kmh': traffic_data.average_speed_kmh
                    }

                    collected_data.append(db_record)

                # Rate limiting between requests
                time.sleep(1)

            self.logger.info(f"Collected traffic data for {len(collected_data)} routes")
            return collected_data

        except Exception as e:
            self.logger.error(f"Error collecting traffic data: {e}")
            return []

    def _determine_day_type(self, dt: datetime, weather: WeatherData) -> DayType:
        """Determine the day type based on date and weather"""
        if weather.condition in [WeatherCondition.HEAVY_RAIN]:
            return DayType.RAINY_DAY
        elif dt.weekday() >= 5:  # Weekend
            return DayType.WEEKEND
        else:
            return DayType.WEEKDAY

    def _determine_season_type(self, dt: datetime) -> SeasonType:
        """Determine season type (Sri Lankan context)"""
        if self._is_holiday(dt):
            return SeasonType.PUBLIC_HOLIDAY
        elif self._is_school_holiday(dt):
            return SeasonType.SCHOOL_HOLIDAY
        else:
            return SeasonType.REGULAR

    def _is_holiday(self, dt: datetime) -> bool:
        """Check if date is a Sri Lankan public holiday"""
        # Simplified holiday detection - in production, use a comprehensive holiday calendar
        sri_lankan_holidays_2024 = {
            (1, 1): "New Year's Day",
            (2, 4): "Independence Day",
            (5, 1): "Labour Day",
            (12, 25): "Christmas Day"
        }

        return (dt.month, dt.day) in sri_lankan_holidays_2024

    def _is_school_holiday(self, dt: datetime) -> bool:
        """Check if date falls within school holidays"""
        # Approximate Sri Lankan school holiday periods
        school_holiday_periods = [
            ((4, 1), (4, 30)),  # April vacation
            ((8, 1), (8, 31)),  # August vacation
            ((12, 15), (12, 31))  # December vacation
        ]

        current_date = (dt.month, dt.day)

        for start, end in school_holiday_periods:
            if start <= current_date <= end:
                return True

        return False


class APICoordinator:
    """
    Coordinator service for managing all external API interactions
    """

    def __init__(self):
        self.maps_service = GoogleMapsAPIService()
        self.weather_service = WeatherAPIService()
        self.data_collection_service = DataCollectionService(
            self.maps_service, self.weather_service
        )
        self.logger = get_logger(__name__)

    def get_comprehensive_traffic_update(self) -> Dict[str, Any]:
        """Get comprehensive traffic update including weather"""
        try:
            # Get current weather
            weather = self.weather_service.get_current_weather()

            # Get traffic data for all routes
            routes = TrafficConfig.DEFAULT_ROUTES
            traffic_data = self.maps_service.get_multiple_routes_traffic(routes)

            # Find best current route
            best_route = min(traffic_data,
                             key=lambda x: x.current_travel_time_minutes) if traffic_data else None

            update = {
                'timestamp': datetime.now().isoformat(),
                'weather': {
                    'condition': weather.condition.value,
                    'temperature': weather.temperature_celsius,
                    'humidity': weather.humidity_percent
                },
                'traffic_data': [
                    {
                        'route': data.route_name,
                        'current_time': data.current_travel_time_minutes,
                        'delay': data.delay_minutes,
                        'traffic_level': data.traffic_condition.value,
                        'speed': data.average_speed_kmh
                    } for data in traffic_data
                ],
                'best_route': best_route.route_name if best_route else None,
                'overall_traffic_level': self._calculate_overall_traffic_level(traffic_data)
            }

            self.logger.info("Comprehensive traffic update generated")
            return update

        except Exception as e:
            self.logger.error(f"Error generating comprehensive traffic update: {e}")
            raise

    def _calculate_overall_traffic_level(self, traffic_data: List[RealTimeTrafficData]) -> str:
        """Calculate overall traffic level across all routes"""
        if not traffic_data:
            return "Unknown"

        # Calculate average delay ratio
        delay_ratios = []
        for data in traffic_data:
            if data.typical_travel_time_minutes > 0:
                ratio = data.current_travel_time_minutes / data.typical_travel_time_minutes
                delay_ratios.append(ratio)

        if not delay_ratios:
            return "Moderate"

        avg_delay_ratio = sum(delay_ratios) / len(delay_ratios)

        if avg_delay_ratio < 1.1:
            return "Light"
        elif avg_delay_ratio < 1.3:
            return "Moderate"
        elif avg_delay_ratio < 1.6:
            return "Heavy"
        else:
            return "Very Heavy"