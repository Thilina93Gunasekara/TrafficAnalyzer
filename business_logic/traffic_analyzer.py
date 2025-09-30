# business_logic/traffic_analyzer.py
# Core business logic for traffic analysis and route optimization

from typing import List, Dict, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
import statistics
import sys
import os

# Add parent directory to path if needed
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from data_access.database_manager import DatabaseManager, TrafficRecordRepository
from data_access.models import (
    TrafficRecord, PredictionRequest, PredictionResult,
    RouteComparison, Route, AnalyticsData,
    DayType, WeatherCondition, SeasonType, TrafficDensity
)
from config.settings import TrafficConfig
from utilities.logger import get_logger


class TrafficAnalysisService:
    """
    Core service for traffic analysis operations
    Contains the main business logic for route optimization and predictions
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.traffic_repo = TrafficRecordRepository(db_manager)
        self.logger = get_logger(__name__)

    def analyze_route_performance(self, route_name: str, days_back: int = 30) -> AnalyticsData:
        """Analyze overall performance of a specific route"""
        try:
            analytics = self.db_manager.get_route_analytics(route_name, days_back)

            if analytics is None:
                # Return default analytics if no data
                self.logger.warning(f"No analytics data found for route: {route_name}")
                return AnalyticsData(
                    route_name=route_name,
                    average_travel_time=0.0,
                    min_travel_time=0,
                    max_travel_time=0,
                    peak_hour_average=0.0,
                    off_peak_average=0.0,
                    weekend_average=0.0,
                    rainy_day_average=0.0,
                    total_records=0
                )

            self.logger.info(f"Analytics generated for {route_name}: {analytics.total_records} records")
            return analytics

        except Exception as e:
            self.logger.error(f"Error analyzing route performance: {e}")
            raise

    def compare_all_routes(self, prediction_request: PredictionRequest) -> RouteComparison:
        """Compare all available routes for given conditions"""
        try:
            routes = self.db_manager.get_all_routes()
            predictions = []

            for route in routes:
                # Create prediction request for each route
                route_request = PredictionRequest(
                    route_name=route.name,
                    day_type=prediction_request.day_type,
                    hour=prediction_request.hour,
                    weather_condition=prediction_request.weather_condition,
                    season_type=prediction_request.season_type
                )

                # Get prediction for this route
                prediction = self.predict_travel_time(route_request)
                predictions.append(prediction)

            # Sort predictions by travel time
            sorted_predictions = sorted(predictions, key=lambda x: x.predicted_time_minutes)
            best_route = sorted_predictions[0].route_name if sorted_predictions else ""

            # Generate recommendations
            recommendations = self._generate_route_recommendations(
                prediction_request, sorted_predictions
            )

            comparison = RouteComparison(
                request_params=prediction_request,
                predictions=sorted_predictions,
                best_route=best_route,
                recommendations=recommendations
            )

            self.logger.info(f"Route comparison completed. Best route: {best_route}")
            return comparison

        except Exception as e:
            self.logger.error(f"Error comparing routes: {e}")
            raise

    def predict_travel_time(self, request: PredictionRequest) -> PredictionResult:
        """Predict travel time for specific conditions using historical data"""
        try:
            # Get historical records with similar conditions
            similar_records = self.traffic_repo.get_similar_conditions_records(request)

            if not similar_records:
                # Fall back to base prediction if no historical data
                predicted_time = self._get_base_prediction(request)
                confidence = 0.3  # Low confidence without historical data
                factors = ["Base calculation (no historical data)"]
            else:
                # Calculate prediction based on historical data
                predicted_time, confidence, factors = self._calculate_historical_prediction(
                    request, similar_records
                )

            result = PredictionResult(
                route_name=request.route_name,
                predicted_time_minutes=predicted_time,
                confidence_level=confidence,
                factors_considered=factors
            )

            self.logger.debug(
                f"Prediction for {request.route_name}: {predicted_time} min (confidence: {confidence:.1%})")
            return result

        except Exception as e:
            self.logger.error(f"Error predicting travel time: {e}")
            raise

    def _calculate_historical_prediction(self, request: PredictionRequest,
                                         records: List[TrafficRecord]) -> Tuple[int, float, List[str]]:
        """Calculate prediction based on historical records"""
        travel_times = [record.travel_time_minutes for record in records]
        factors_considered = []

        # Basic statistical prediction
        if len(travel_times) >= 10:
            # Use trimmed mean to reduce outlier impact
            sorted_times = sorted(travel_times)
            trim_count = len(sorted_times) // 10  # Remove 10% from each end
            if trim_count > 0:
                trimmed_times = sorted_times[trim_count:-trim_count]
            else:
                trimmed_times = sorted_times

            predicted_time = int(statistics.mean(trimmed_times))
            confidence = min(0.9, 0.5 + (len(records) * 0.02))  # Max 90% confidence
            factors_considered.append(f"Historical average from {len(records)} similar records")

        elif len(travel_times) >= 3:
            # Use simple average for smaller datasets
            predicted_time = int(statistics.mean(travel_times))
            confidence = min(0.7, 0.3 + (len(records) * 0.05))
            factors_considered.append(f"Limited historical data ({len(records)} records)")

        else:
            # Very limited data - combine with base prediction
            historical_avg = int(statistics.mean(travel_times))
            base_prediction = self._get_base_prediction(request)
            predicted_time = int((historical_avg + base_prediction) / 2)
            confidence = 0.4
            factors_considered.append(f"Combined historical and base prediction ({len(records)} records)")

        # Apply real-time adjustments
        predicted_time = self._apply_condition_adjustments(predicted_time, request, factors_considered)

        return predicted_time, confidence, factors_considered

    def _get_base_prediction(self, request: PredictionRequest) -> int:
        """Get base prediction when no historical data is available"""
        route = self.db_manager.get_route(request.route_name)

        if route and route.distance_km > 0 and route.typical_speed_kmh > 0:
            base_time = (route.distance_km / route.typical_speed_kmh) * 60  # Convert to minutes
        else:
            # Default base times if route data not available
            base_times = {
                'High Level Road': 25,
                'Low Level Road': 28,
                'Baseline Road': 27,
                'Galle Road': 32,
                'Marine Drive': 35,
                'Other Roads': 22
            }
            base_time = base_times.get(request.route_name, 30)

        # Apply condition adjustments
        adjusted_time = self._apply_condition_adjustments(int(base_time), request, [])
        return adjusted_time

    def _apply_condition_adjustments(self, base_time: int, request: PredictionRequest,
                                     factors: List[str]) -> int:
        """Apply adjustments based on traffic conditions"""
        multiplier = 1.0

        # Time-based adjustments
        if request.hour in range(7, 9) or request.hour in range(17, 19):
            multiplier *= TrafficConfig.PEAK_TRAFFIC_MULTIPLIER
            factors.append("Rush hour adjustment")
        elif request.hour in range(10, 16):
            multiplier *= 1.1
            factors.append("Daytime traffic adjustment")
        else:
            multiplier *= TrafficConfig.OFF_PEAK_MULTIPLIER
            factors.append("Off-peak hours adjustment")

        # Day type adjustments
        if request.day_type == DayType.WEEKEND:
            multiplier *= 0.8
            factors.append("Weekend traffic reduction")
        elif request.day_type == DayType.RAINY_DAY:
            multiplier *= 1.4
            factors.append("Rainy day delay factor")

        # Weather adjustments
        weather_multiplier = TrafficConfig.WEATHER_MULTIPLIERS.get(
            request.weather_condition.value, 1.0
        )
        multiplier *= weather_multiplier
        if weather_multiplier > 1.0:
            factors.append(f"Weather impact ({request.weather_condition.value})")

        # Season adjustments
        if request.season_type == SeasonType.SCHOOL_HOLIDAY:
            multiplier *= 0.9
            factors.append("School holiday reduction")
        elif request.season_type == SeasonType.PUBLIC_HOLIDAY:
            multiplier *= 0.7
            factors.append("Public holiday reduction")

        return max(15, int(base_time * multiplier))  # Minimum 15 minutes

    def _generate_route_recommendations(self, request: PredictionRequest,
                                        predictions: List[PredictionResult]) -> List[str]:
        """Generate user-friendly recommendations"""
        recommendations = []

        if not predictions:
            return ["No route data available"]

        best_route = predictions[0]
        recommendations.append(f"🏆 Best Route: {best_route.route_name} ({best_route.predicted_time_minutes} minutes)")

        if len(predictions) > 1:
            second_best = predictions[1]
            time_diff = second_best.predicted_time_minutes - best_route.predicted_time_minutes

            if time_diff <= 5:
                recommendations.append(
                    f"🥈 Alternative: {second_best.route_name} (+{time_diff} min) - Also a good option"
                )
            else:
                recommendations.append(
                    f"🥈 Alternative: {second_best.route_name} (+{time_diff} min)"
                )

        # Time-specific recommendations
        if request.hour in range(7, 9):
            recommendations.append("⏰ Morning rush hour - consider leaving 15 minutes earlier or later")
        elif request.hour in range(17, 19):
            recommendations.append("⏰ Evening rush hour - expect heavy traffic on all routes")
        elif request.hour < 7:
            recommendations.append("🌅 Early morning - excellent time to travel with minimal traffic")
        elif request.hour > 21:
            recommendations.append("🌙 Late evening - very light traffic expected")

        # Weather-specific recommendations
        if request.weather_condition in [WeatherCondition.RAINY, WeatherCondition.HEAVY_RAIN]:
            recommendations.append("🌧️ Poor weather conditions - drive carefully and allow extra time")
            recommendations.append("💡 Consider waterproof gear and check for flood warnings")

        # Day-specific recommendations
        if request.day_type == DayType.WEEKEND:
            recommendations.append("🎾 Weekend travel - generally lighter traffic but watch for recreational areas")

        # Route-specific advice
        if best_route.route_name == "High Level Road":
            recommendations.append("🛣️ High Level Road often has better traffic flow during peak hours")
        elif best_route.route_name == "Galle Road":
            recommendations.append("🏖️ Galle Road may have slower traffic near commercial areas")
        elif best_route.route_name == "Marine Drive":
            recommendations.append("🌊 Marine Drive offers scenic views but may be slower")

        return recommendations

    def get_traffic_patterns(self, route_name: Optional[str] = None) -> Dict[str, any]:
        """Get traffic patterns for visualization"""
        try:
            # Get hourly patterns
            hourly_patterns = self.db_manager.get_peak_hours_analysis(route_name)

            # Get route analytics for all routes or specific route
            if route_name:
                routes_analytics = [self.analyze_route_performance(route_name)]
            else:
                all_routes = self.db_manager.get_all_routes()
                routes_analytics = [self.analyze_route_performance(route.name) for route in all_routes]

            patterns = {
                'hourly_patterns': hourly_patterns,
                'route_analytics': routes_analytics,
                'peak_hours': self._identify_peak_hours(hourly_patterns),
                'off_peak_hours': self._identify_off_peak_hours(hourly_patterns)
            }

            self.logger.info(f"Traffic patterns retrieved for {'all routes' if not route_name else route_name}")
            return patterns

        except Exception as e:
            self.logger.error(f"Error getting traffic patterns: {e}")
            raise

    def _identify_peak_hours(self, hourly_patterns: Dict[int, float]) -> List[int]:
        """Identify peak traffic hours"""
        if not hourly_patterns:
            return [8, 18]  # Default peak hours

        # Calculate average travel time
        avg_time = sum(hourly_patterns.values()) / len(hourly_patterns)

        # Hours with above-average travel times
        peak_hours = [hour for hour, time in hourly_patterns.items() if time > avg_time * 1.2]

        return sorted(peak_hours)

    def _identify_off_peak_hours(self, hourly_patterns: Dict[int, float]) -> List[int]:
        """Identify off-peak traffic hours"""
        if not hourly_patterns:
            return [10, 14, 22]  # Default off-peak hours

        # Calculate average travel time
        avg_time = sum(hourly_patterns.values()) / len(hourly_patterns)

        # Hours with below-average travel times
        off_peak_hours = [hour for hour, time in hourly_patterns.items() if time < avg_time * 0.8]

        return sorted(off_peak_hours)


class RouteOptimizationService:
    """
    Specialized service for route optimization algorithms
    """

    def __init__(self, traffic_analyzer: TrafficAnalysisService):
        self.traffic_analyzer = traffic_analyzer
        self.logger = get_logger(__name__)

    def optimize_departure_time(self, route_name: str, arrival_time: int,
                                day_type: DayType, weather: WeatherCondition,
                                season: SeasonType = SeasonType.REGULAR) -> Dict[str, any]:
        """Find optimal departure time to arrive by specified time"""
        try:
            optimization_results = []

            # Check departure times from 2 hours before to 30 minutes before arrival
            for departure_hour in range(max(0, arrival_time - 2), arrival_time):
                for departure_minute in [0, 15, 30, 45]:
                    departure_time_decimal = departure_hour + (departure_minute / 60)

                    # Skip if we've passed the arrival time
                    if departure_time_decimal >= arrival_time:
                        continue

                    request = PredictionRequest(
                        route_name=route_name,
                        day_type=day_type,
                        hour=departure_hour,
                        weather_condition=weather,
                        season_type=season
                    )

                    prediction = self.traffic_analyzer.predict_travel_time(request)

                    # Calculate expected arrival time
                    expected_arrival = departure_time_decimal + (prediction.predicted_time_minutes / 60)

                    optimization_results.append({
                        'departure_time': f"{departure_hour:02d}:{departure_minute:02d}",
                        'departure_decimal': departure_time_decimal,
                        'predicted_travel_time': prediction.predicted_time_minutes,
                        'expected_arrival': expected_arrival,
                        'arrival_buffer': arrival_time - expected_arrival,
                        'confidence': prediction.confidence_level
                    })

            # Find optimal departure times (arriving with 5-15 minute buffer)
            optimal_departures = [
                result for result in optimization_results
                if 5 / 60 <= result['arrival_buffer'] <= 15 / 60  # 5-15 minute buffer
            ]

            if not optimal_departures:
                # If no optimal times, find closest ones
                optimal_departures = sorted(optimization_results,
                                            key=lambda x: abs(x['arrival_buffer'] - 10 / 60))[:3]

            result = {
                'route_name': route_name,
                'target_arrival_time': f"{arrival_time:02d}:00",
                'optimal_departures': optimal_departures[:5],  # Top 5 options
                'all_options': optimization_results
            }

            self.logger.info(f"Departure time optimization completed for {route_name}")
            return result

        except Exception as e:
            self.logger.error(f"Error optimizing departure time: {e}")
            raise

    def find_alternative_routes_on_incident(self, blocked_route: str,
                                            conditions: PredictionRequest) -> RouteComparison:
        """Find alternative routes when a specific route has incidents"""
        try:
            # Get all routes except the blocked one
            all_routes = self.traffic_analyzer.db_manager.get_all_routes()
            alternative_routes = [route for route in all_routes if route.name != blocked_route]

            predictions = []
            for route in alternative_routes:
                request = PredictionRequest(
                    route_name=route.name,
                    day_type=conditions.day_type,
                    hour=conditions.hour,
                    weather_condition=conditions.weather_condition,
                    season_type=conditions.season_type
                )

                prediction = self.traffic_analyzer.predict_travel_time(request)
                # Add incident delay to other routes (spillover effect)
                prediction.predicted_time_minutes = int(prediction.predicted_time_minutes * 1.1)
                predictions.append(prediction)

            sorted_predictions = sorted(predictions, key=lambda x: x.predicted_time_minutes)
            best_route = sorted_predictions[0].route_name if sorted_predictions else ""

            recommendations = [
                f"🚨 {blocked_route} is blocked - avoid this route",
                f"🏆 Best Alternative: {best_route}",
                "⚠️ Expect slight delays on all routes due to traffic spillover",
                "📱 Check real-time traffic updates before departing"
            ]

            comparison = RouteComparison(
                request_params=conditions,
                predictions=sorted_predictions,
                best_route=best_route,
                recommendations=recommendations
            )

            self.logger.info(f"Alternative routes found for blocked {blocked_route}")
            return comparison

        except Exception as e:
            self.logger.error(f"Error finding alternative routes: {e}")
            raise