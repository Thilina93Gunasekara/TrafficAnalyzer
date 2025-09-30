# external_services/weather_service.py
# Specialized weather data service with Sri Lankan context

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
import sys
import os

# Add parent directory to path if needed
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from data_access.models import WeatherData, WeatherCondition
from config.settings import APIConfig
from utilities.logger import get_logger


class SriLankanWeatherService:
    """
    Weather service specialized for Sri Lankan weather patterns and conditions
    """

    def __init__(self):
        self.api_key = APIConfig.OPENWEATHER_API_KEY
        self.base_url = APIConfig.OPENWEATHER_URL
        self.forecast_url = "http://api.openweathermap.org/data/2.5/forecast"
        self.logger = get_logger(__name__)

        # Sri Lankan weather stations and regions
        self.weather_stations = {
            'colombo': {'lat': 6.9271, 'lon': 79.8612, 'name': 'Colombo'},
            'maharagama': {'lat': 6.8431, 'lon': 79.9186, 'name': 'Maharagama'},
            'mount_lavinia': {'lat': 6.8300, 'lon': 79.8640, 'name': 'Mount Lavinia'},
            'kesbewa': {'lat': 6.8108, 'lon': 79.9289, 'name': 'Kesbewa'}
        }

        # Sri Lankan monsoon patterns
        self.monsoon_calendar = {
            'southwest': {'start': (5, 15), 'end': (9, 30)},  # May 15 - Sep 30
            'northeast': {'start': (10, 15), 'end': (1, 31)},  # Oct 15 - Jan 31
            'inter_monsoon_1': {'start': (3, 1), 'end': (5, 14)},  # Mar 1 - May 14
            'inter_monsoon_2': {'start': (10, 1), 'end': (10, 14)}  # Oct 1 - Oct 14
        }

    def get_current_weather_colombo_region(self) -> WeatherData:
        """Get current weather for Colombo region (covers our route area)"""
        try:
            # Try multiple weather stations for better coverage
            stations = ['colombo', 'maharagama', 'mount_lavinia']
            weather_data = []

            for station in stations:
                station_info = self.weather_stations[station]
                weather = self._get_weather_by_coordinates(
                    station_info['lat'],
                    station_info['lon']
                )
                if weather:
                    weather_data.append(weather)

            # If we have multiple readings, average them
            if weather_data:
                return self._average_weather_data(weather_data)
            else:
                # Fallback to simulated data
                return self._get_sri_lankan_simulated_weather()

        except Exception as e:
            self.logger.error(f"Error getting Colombo region weather: {e}")
            return self._get_sri_lankan_simulated_weather()

    def get_weather_forecast_for_route(self, hours_ahead: int = 6) -> List[WeatherData]:
        """Get weather forecast for the next few hours affecting the route"""
        try:
            if self.api_key == 'your_api_key_here':
                return self._get_simulated_forecast(hours_ahead)

            # Get forecast for Colombo area
            params = {
                'lat': self.weather_stations['colombo']['lat'],
                'lon': self.weather_stations['colombo']['lon'],
                'appid': self.api_key,
                'units': 'metric',
                'cnt': max(1, hours_ahead // 3)  # API gives 3-hour intervals
            }

            response = requests.get(
                self.forecast_url,
                params=params,
                timeout=APIConfig.REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_forecast_response(data, hours_ahead)
            else:
                self.logger.warning(f"Weather API error: {response.status_code}")
                return self._get_simulated_forecast(hours_ahead)

        except Exception as e:
            self.logger.error(f"Error getting weather forecast: {e}")
            return self._get_simulated_forecast(hours_ahead)

    def get_monsoon_info(self, date: datetime = None) -> Dict[str, Any]:
        """Get current monsoon season information"""
        try:
            if date is None:
                date = datetime.now()

            current_date = (date.month, date.day)

            # Determine current monsoon season
            current_season = None
            for season, period in self.monsoon_calendar.items():
                start = period['start']
                end = period['end']

                if start <= end:  # Same year season
                    if start <= current_date <= end:
                        current_season = season
                        break
                else:  # Cross-year season (like northeast monsoon)
                    if current_date >= start or current_date <= end:
                        current_season = season
                        break

            if not current_season:
                current_season = 'dry_period'

            # Get season-specific information
            season_info = self._get_monsoon_season_details(current_season)

            return {
                'current_season': current_season,
                'season_name': season_info['name'],
                'expected_rainfall': season_info['rainfall'],
                'traffic_impact': season_info['traffic_impact'],
                'recommendations': season_info['recommendations'],
                'next_season_starts': self._get_next_season_start(current_season, date)
            }

        except Exception as e:
            self.logger.error(f"Error getting monsoon info: {e}")
            return {
                'current_season': 'unknown',
                'season_name': 'Unknown Season',
                'expected_rainfall': 'Moderate',
                'traffic_impact': 'Normal',
                'recommendations': ['Check weather before travel']
            }

    def analyze_weather_impact_on_traffic(self, weather: WeatherData) -> Dict[str, Any]:
        """Analyze how current weather conditions affect traffic"""
        try:
            impact_analysis = {
                'severity_level': 'Low',
                'expected_delay': 0,
                'affected_routes': [],
                'recommendations': [],
                'visibility': 'Good',
                'road_conditions': 'Normal'
            }

            # Analyze based on weather condition
            if weather.condition == WeatherCondition.HEAVY_RAIN:
                impact_analysis.update({
                    'severity_level': 'High',
                    'expected_delay': 15,  # minutes
                    'affected_routes': ['Marine Drive', 'Galle Road', 'Low Level Road'],
                    'recommendations': [
                        'Allow extra 20-30 minutes for travel',
                        'Avoid flood-prone routes',
                        'Drive with headlights on',
                        'Maintain safe following distance'
                    ],
                    'visibility': 'Poor',
                    'road_conditions': 'Wet and slippery'
                })

            elif weather.condition == WeatherCondition.RAINY:
                impact_analysis.update({
                    'severity_level': 'Medium',
                    'expected_delay': 8,  # minutes
                    'affected_routes': ['Marine Drive', 'Low Level Road'],
                    'recommendations': [
                        'Allow extra 10-15 minutes',
                        'Use headlights',
                        'Check for minor flooding'
                    ],
                    'visibility': 'Reduced',
                    'road_conditions': 'Wet'
                })

            elif weather.condition == WeatherCondition.CLOUDY:
                impact_analysis.update({
                    'severity_level': 'Low',
                    'expected_delay': 2,  # minutes
                    'recommendations': [
                        'Normal driving conditions',
                        'Watch for sudden rain'
                    ]
                })

            # Temperature-based analysis
            if weather.temperature_celsius > 35:
                impact_analysis['recommendations'].append('High temperature - ensure vehicle cooling')
            elif weather.temperature_celsius < 20:
                impact_analysis['recommendations'].append('Cool weather - good for travel')

            # Humidity analysis
            if weather.humidity_percent > 90:
                impact_analysis['recommendations'].append('High humidity - reduced visibility possible')

            return impact_analysis

        except Exception as e:
            self.logger.error(f"Error analyzing weather impact: {e}")
            return {
                'severity_level': 'Unknown',
                'expected_delay': 0,
                'recommendations': ['Check weather conditions before travel']
            }

    def check_flood_risk_for_routes(self) -> Dict[str, str]:
        """Check flood risk for each route based on historical patterns"""
        try:
            flood_risk_map = {
                'High Level Road': 'Low',
                'Low Level Road': 'Medium',  # Lower elevation, prone to waterlogging
                'Baseline Road': 'Low',
                'Galle Road': 'Medium',  # Coastal area
                'Marine Drive': 'High',  # Coastal and low-lying
                'Other Roads': 'Medium'
            }

            # Adjust based on current weather
            current_weather = self.get_current_weather_colombo_region()

            if current_weather.condition in [WeatherCondition.HEAVY_RAIN, WeatherCondition.RAINY]:
                # Increase all risk levels during rain
                adjusted_risk = {}
                for route, risk in flood_risk_map.items():
                    if risk == 'Low':
                        adjusted_risk[route] = 'Medium'
                    elif risk == 'Medium':
                        adjusted_risk[route] = 'High'
                    else:
                        adjusted_risk[route] = 'Very High'
                return adjusted_risk

            return flood_risk_map

        except Exception as e:
            self.logger.error(f"Error checking flood risk: {e}")
            return {route: 'Unknown' for route in ['High Level Road', 'Low Level Road',
                                                   'Baseline Road', 'Galle Road', 'Marine Drive', 'Other Roads']}

    # Helper methods
    def _get_weather_by_coordinates(self, lat: float, lon: float) -> Optional[WeatherData]:
        """Get weather data for specific coordinates"""
        try:
            if self.api_key == 'your_api_key_here':
                return None  # Will fall back to simulated data

            params = {
                'lat': lat,
                'lon': lon,
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

            return None

        except Exception as e:
            self.logger.warning(f"Error getting weather by coordinates: {e}")
            return None

    def _parse_weather_response(self, data: Dict) -> WeatherData:
        """Parse OpenWeatherMap API response"""
        try:
            weather_desc = data['weather'][0]['main'].lower()

            # Map weather descriptions to our conditions
            if 'rain' in weather_desc or 'drizzle' in weather_desc:
                rainfall = data.get('rain', {}).get('1h', 0)
                if 'heavy' in weather_desc or rainfall > 10:
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
                wind_speed_kmh=data['wind'].get('speed', 0) * 3.6
            )

        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing weather response: {e}")
            return self._get_sri_lankan_simulated_weather()

    def _parse_forecast_response(self, data: Dict, hours_ahead: int) -> List[WeatherData]:
        """Parse weather forecast response"""
        try:
            forecast_list = []

            for forecast_item in data.get('list', [])[:hours_ahead // 3]:
                weather_desc = forecast_item['weather'][0]['main'].lower()

                if 'rain' in weather_desc:
                    condition = WeatherCondition.RAINY
                elif 'cloud' in weather_desc:
                    condition = WeatherCondition.CLOUDY
                else:
                    condition = WeatherCondition.CLEAR

                weather = WeatherData(
                    condition=condition,
                    temperature_celsius=forecast_item['main']['temp'],
                    humidity_percent=forecast_item['main']['humidity'],
                    wind_speed_kmh=forecast_item['wind'].get('speed', 0) * 3.6,
                    timestamp=datetime.fromtimestamp(forecast_item['dt'])
                )
                forecast_list.append(weather)

            return forecast_list

        except Exception as e:
            self.logger.error(f"Error parsing forecast response: {e}")
            return self._get_simulated_forecast(hours_ahead)

    def _average_weather_data(self, weather_list: List[WeatherData]) -> WeatherData:
        """Average multiple weather readings"""
        try:
            # Use most common condition
            conditions = [w.condition for w in weather_list]
            most_common_condition = max(set(conditions), key=conditions.count)

            # Average numeric values
            avg_temp = sum(w.temperature_celsius for w in weather_list) / len(weather_list)
            avg_humidity = int(sum(w.humidity_percent for w in weather_list) / len(weather_list))
            avg_wind = sum(w.wind_speed_kmh for w in weather_list) / len(weather_list)

            return WeatherData(
                condition=most_common_condition,
                temperature_celsius=avg_temp,
                humidity_percent=avg_humidity,
                wind_speed_kmh=avg_wind
            )

        except Exception as e:
            self.logger.warning(f"Error averaging weather data: {e}")
            return weather_list[0] if weather_list else self._get_sri_lankan_simulated_weather()

    def _get_sri_lankan_simulated_weather(self) -> WeatherData:
        """Generate realistic Sri Lankan weather data"""
        current_time = datetime.now()
        month = current_time.month
        hour = current_time.hour

        # Sri Lankan weather patterns by month
        if month in [5, 6, 7, 8, 9]:  # Southwest monsoon
            rain_probability = 0.6
            conditions = [WeatherCondition.CLEAR, WeatherCondition.CLOUDY,
                          WeatherCondition.RAINY, WeatherCondition.HEAVY_RAIN]
            probabilities = [0.2, 0.2, 0.4, 0.2]
        elif month in [10, 11, 12, 1]:  # Northeast monsoon
            rain_probability = 0.5
            conditions = [WeatherCondition.CLEAR, WeatherCondition.CLOUDY,
                          WeatherCondition.RAINY, WeatherCondition.HEAVY_RAIN]
            probabilities = [0.25, 0.25, 0.35, 0.15]
        else:  # Inter-monsoon
            rain_probability = 0.3
            conditions = [WeatherCondition.CLEAR, WeatherCondition.CLOUDY,
                          WeatherCondition.RAINY, WeatherCondition.HEAVY_RAIN]
            probabilities = [0.4, 0.35, 0.2, 0.05]

        # Afternoon rain is more common
        if 14 <= hour <= 17:
            probabilities = [p * 0.8 if c in [WeatherCondition.CLEAR, WeatherCondition.CLOUDY]
                             else p * 1.2 for c, p in zip(conditions, probabilities)]
            # Normalize
            total = sum(probabilities)
            probabilities = [p / total for p in probabilities]

        condition = random.choices(conditions, weights=probabilities)[0]

        # Temperature based on time and condition
        if 10 <= hour <= 16:  # Daytime
            base_temp = random.uniform(29, 33)
        elif 18 <= hour <= 22:  # Evening
            base_temp = random.uniform(26, 29)
        else:  # Night/early morning
            base_temp = random.uniform(24, 27)

        # Adjust for weather condition
        if condition in [WeatherCondition.RAINY, WeatherCondition.HEAVY_RAIN]:
            base_temp -= random.uniform(2, 4)
        elif condition == WeatherCondition.CLOUDY:
            base_temp -= random.uniform(0.5, 1.5)

        # Humidity (Sri Lanka is generally humid)
        if condition in [WeatherCondition.RAINY, WeatherCondition.HEAVY_RAIN]:
            humidity = random.randint(85, 95)
        elif condition == WeatherCondition.CLOUDY:
            humidity = random.randint(75, 85)
        else:
            humidity = random.randint(65, 80)

        return WeatherData(
            condition=condition,
            temperature_celsius=round(base_temp, 1),
            humidity_percent=humidity,
            wind_speed_kmh=random.uniform(5, 20)
        )

    def _get_simulated_forecast(self, hours_ahead: int) -> List[WeatherData]:
        """Generate simulated weather forecast"""
        forecast = []
        current_weather = self._get_sri_lankan_simulated_weather()

        for i in range(max(1, hours_ahead // 3)):
            # Gradually change weather conditions
            if random.random() < 0.3:  # 30% chance of change
                forecast_weather = self._get_sri_lankan_simulated_weather()
            else:
                forecast_weather = current_weather

            # Set timestamp
            forecast_weather.timestamp = datetime.now() + timedelta(hours=(i + 1) * 3)
            forecast.append(forecast_weather)

            current_weather = forecast_weather

        return forecast

    def _get_monsoon_season_details(self, season: str) -> Dict[str, Any]:
        """Get detailed information about a monsoon season"""
        season_details = {
            'southwest': {
                'name': 'Southwest Monsoon (Yala)',
                'rainfall': 'High',
                'traffic_impact': 'Moderate to High',
                'recommendations': [
                    'Afternoon travel may be affected by heavy rain',
                    'Check flood warnings for low-lying areas',
                    'Allow extra time for journey',
                    'Avoid Marine Drive during heavy rain'
                ]
            },
            'northeast': {
                'name': 'Northeast Monsoon (Maha)',
                'rainfall': 'Moderate to High',
                'traffic_impact': 'Moderate',
                'recommendations': [
                    'Evening and night rain common',
                    'Morning travel generally better',
                    'Watch for waterlogging in usual spots'
                ]
            },
            'inter_monsoon_1': {
                'name': 'First Inter-Monsoon Period',
                'rainfall': 'Low to Moderate',
                'traffic_impact': 'Low',
                'recommendations': [
                    'Generally good travel conditions',
                    'Occasional afternoon thunderstorms',
                    'Best time for predictable commutes'
                ]
            },
            'inter_monsoon_2': {
                'name': 'Second Inter-Monsoon Period',
                'rainfall': 'Moderate',
                'traffic_impact': 'Low to Moderate',
                'recommendations': [
                    'Transition period - variable conditions',
                    'Prepare for northeast monsoon',
                    'Check weather forecasts regularly'
                ]
            },
            'dry_period': {
                'name': 'Dry Period',
                'rainfall': 'Low',
                'traffic_impact': 'Low',
                'recommendations': [
                    'Excellent travel conditions',
                    'Hot weather - stay hydrated',
                    'Good visibility and road conditions'
                ]
            }
        }

        return season_details.get(season, {
            'name': 'Unknown Season',
            'rainfall': 'Variable',
            'traffic_impact': 'Unknown',
            'recommendations': ['Check current weather conditions']
        })

    def _get_next_season_start(self, current_season: str, current_date: datetime) -> str:
        """Calculate when the next monsoon season starts"""
        try:
            season_order = ['southwest', 'inter_monsoon_2', 'northeast', 'inter_monsoon_1']

            if current_season in season_order:
                current_index = season_order.index(current_season)
                next_season = season_order[(current_index + 1) % len(season_order)]
            else:
                next_season = 'southwest'

            next_start = self.monsoon_calendar[next_season]['start']
            next_date = datetime(current_date.year, next_start[0], next_start[1])

            # If date has passed this year, use next year
            if next_date < current_date:
                next_date = datetime(current_date.year + 1, next_start[0], next_start[1])

            days_until = (next_date - current_date).days

            return f"{next_date.strftime('%B %d, %Y')} (in {days_until} days)"

        except Exception as e:
            self.logger.warning(f"Error calculating next season: {e}")
            return "Date calculation unavailable"