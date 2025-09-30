# business_logic/route_optimizer.py
# Advanced route optimization algorithms and services

import numpy as np
# business_logic/route_optimizer.py
# Advanced route optimization algorithms and services

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import itertools
import sys
import os

# Add parent directory to path if needed
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_access.models import (
    TrafficRecord, PredictionRequest, PredictionResult,
    Route, DayType, WeatherCondition, SeasonType
)
from business_logic.traffic_analyzer import TrafficAnalysisService
from utilities.logger import get_logger


@dataclass
class OptimizationResult:
    """Result of route optimization"""
    recommended_route: str
    estimated_time: int
    confidence: float
    alternatives: List[Tuple[str, int]]
    optimization_factors: List[str]
    savings: Dict[str, Any]


@dataclass
class DepartureOptimization:
    """Result of departure time optimization"""
    optimal_departure_time: str
    arrival_time: str
    travel_time: int
    buffer_minutes: int
    alternatives: List[Dict[str, Any]]
    route_name: str


class AdvancedRouteOptimizer:
    """
    Advanced route optimization service with multiple optimization algorithms
    """

    def __init__(self, traffic_analyzer: TrafficAnalysisService):
        self.traffic_analyzer = traffic_analyzer
        self.logger = get_logger(__name__)

    def optimize_multi_objective(self, request: PredictionRequest,
                                 objectives: Dict[str, float]) -> OptimizationResult:
        """
        Multi-objective optimization considering time, reliability, and other factors

        Args:
            request: Prediction request parameters
            objectives: Dictionary of objectives with weights
                       e.g., {'time': 0.6, 'reliability': 0.3, 'comfort': 0.1}
        """
        try:
            routes = self.traffic_analyzer.db_manager.get_all_routes()
            route_evaluations = []

            for route in routes:
                route_request = PredictionRequest(
                    route_name=route.name,
                    day_type=request.day_type,
                    hour=request.hour,
                    weather_condition=request.weather_condition,
                    season_type=request.season_type
                )

                # Get prediction and analytics
                prediction = self.traffic_analyzer.predict_travel_time(route_request)
                analytics = self.traffic_analyzer.analyze_route_performance(route.name)

                # Calculate objective scores
                scores = self._calculate_objective_scores(
                    route, prediction, analytics, objectives
                )

                route_evaluations.append({
                    'route': route,
                    'prediction': prediction,
                    'scores': scores,
                    'total_score': sum(objectives.get(obj, 0) * score
                                       for obj, score in scores.items())
                })

            # Sort by total score (higher is better)
            route_evaluations.sort(key=lambda x: x['total_score'], reverse=True)

            # Build result
            best_route = route_evaluations[0]
            alternatives = [(eval['route'].name, eval['prediction'].predicted_time_minutes)
                            for eval in route_evaluations[1:4]]  # Top 3 alternatives

            # Calculate savings
            if len(route_evaluations) > 1:
                second_best_time = route_evaluations[1]['prediction'].predicted_time_minutes
                time_savings = second_best_time - best_route['prediction'].predicted_time_minutes
            else:
                time_savings = 0

            optimization_factors = self._generate_optimization_factors(
                best_route, objectives
            )

            result = OptimizationResult(
                recommended_route=best_route['route'].name,
                estimated_time=best_route['prediction'].predicted_time_minutes,
                confidence=best_route['prediction'].confidence_level,
                alternatives=alternatives,
                optimization_factors=optimization_factors,
                savings={
                    'time_minutes': time_savings,
                    'reliability_improvement': best_route['scores'].get('reliability', 0),
                    'comfort_score': best_route['scores'].get('comfort', 0)
                }
            )

            self.logger.info(f"Multi-objective optimization completed: {result.recommended_route}")
            return result

        except Exception as e:
            self.logger.error(f"Error in multi-objective optimization: {e}")
            # Fallback to simple optimization
            return self._simple_route_optimization(request)

    def optimize_departure_time_window(self, route_name: str, target_arrival: int,
                                       conditions: PredictionRequest,
                                       window_minutes: int = 60) -> DepartureOptimization:
        """
        Optimize departure time within a specified window to meet arrival target
        """
        try:
            departure_options = []
            target_arrival_dt = datetime.now().replace(hour=target_arrival, minute=0, second=0)

            # Check departure times within the window
            for minutes_before in range(30, window_minutes + 30, 15):  # 15-minute intervals
                departure_time = target_arrival_dt - timedelta(minutes=minutes_before)
                departure_hour = departure_time.hour

                # Skip invalid hours
                if departure_hour < 0 or departure_hour > 23:
                    continue

                # Create request for this departure time
                dep_request = PredictionRequest(
                    route_name=route_name,
                    day_type=conditions.day_type,
                    hour=departure_hour,
                    weather_condition=conditions.weather_condition,
                    season_type=conditions.season_type
                )

                prediction = self.traffic_analyzer.predict_travel_time(dep_request)

                # Calculate expected arrival
                expected_arrival = departure_time + timedelta(minutes=prediction.predicted_time_minutes)
                arrival_buffer = (target_arrival_dt - expected_arrival).total_seconds() / 60

                # Score this option
                score = self._score_departure_option(
                    arrival_buffer, prediction.confidence_level, prediction.predicted_time_minutes
                )

                departure_options.append({
                    'departure_time': departure_time.strftime("%H:%M"),
                    'departure_hour': departure_hour,
                    'travel_time': prediction.predicted_time_minutes,
                    'expected_arrival': expected_arrival.strftime("%H:%M"),
                    'buffer_minutes': int(arrival_buffer),
                    'confidence': prediction.confidence_level,
                    'score': score,
                    'factors': prediction.factors_considered
                })

            # Sort by score (higher is better)
            departure_options.sort(key=lambda x: x['score'], reverse=True)

            if departure_options:
                optimal = departure_options[0]
                alternatives = departure_options[1:5]  # Top 4 alternatives

                result = DepartureOptimization(
                    optimal_departure_time=optimal['departure_time'],
                    arrival_time=optimal['expected_arrival'],
                    travel_time=optimal['travel_time'],
                    buffer_minutes=optimal['buffer_minutes'],
                    alternatives=alternatives,
                    route_name=route_name
                )

                self.logger.info(f"Departure optimization for {route_name}: {optimal['departure_time']}")
                return result
            else:
                raise ValueError("No valid departure options found")

        except Exception as e:
            self.logger.error(f"Error in departure time optimization: {e}")
            # Return default recommendation
            default_departure = max(0, target_arrival - 1)
            return DepartureOptimization(
                optimal_departure_time=f"{default_departure:02d}:00",
                arrival_time=f"{target_arrival:02d}:00",
                travel_time=60,
                buffer_minutes=0,
                alternatives=[],
                route_name=route_name
            )

    def find_optimal_multi_stop_route(self, stops: List[str],
                                      conditions: PredictionRequest) -> Dict[str, Any]:
        """
        Find optimal route when multiple stops are involved (Traveling Salesman Problem variant)
        """
        try:
            if len(stops) < 2:
                raise ValueError("At least 2 stops required for multi-stop optimization")

            # For demonstration, we'll use a simplified approach
            # In production, you'd use more sophisticated TSP algorithms

            all_routes = self.traffic_analyzer.db_manager.get_all_routes()
            route_names = [route.name for route in all_routes]

            # Generate all possible route combinations between stops
            route_combinations = []

            # For simplicity, assume each "stop" corresponds to a route choice
            for route_combo in itertools.permutations(route_names[:len(stops)]):
                total_time = 0
                total_confidence = 0
                route_details = []

                for i, route_name in enumerate(route_combo):
                    route_request = PredictionRequest(
                        route_name=route_name,
                        day_type=conditions.day_type,
                        hour=conditions.hour + (total_time // 60),  # Adjust hour based on cumulative time
                        weather_condition=conditions.weather_condition,
                        season_type=conditions.season_type
                    )

                    prediction = self.traffic_analyzer.predict_travel_time(route_request)

                    total_time += prediction.predicted_time_minutes
                    total_confidence += prediction.confidence_level

                    route_details.append({
                        'stop': stops[i] if i < len(stops) else f"Stop {i + 1}",
                        'route': route_name,
                        'time': prediction.predicted_time_minutes,
                        'confidence': prediction.confidence_level
                    })

                avg_confidence = total_confidence / len(route_combo)

                route_combinations.append({
                    'combination': route_combo,
                    'total_time': total_time,
                    'avg_confidence': avg_confidence,
                    'route_details': route_details,
                    'score': self._score_multi_stop_route(total_time, avg_confidence)
                })

            # Sort by score (lower total time with higher confidence is better)
            route_combinations.sort(key=lambda x: x['score'], reverse=True)

            optimal_combo = route_combinations[0]

            result = {
                'optimal_route_sequence': optimal_combo['combination'],
                'total_travel_time': optimal_combo['total_time'],
                'average_confidence': optimal_combo['avg_confidence'],
                'route_details': optimal_combo['route_details'],
                'alternatives': route_combinations[1:3],  # Top 2 alternatives
                'optimization_method': 'Multi-stop route optimization',
                'stops_count': len(stops)
            }

            self.logger.info(f"Multi-stop optimization completed for {len(stops)} stops")
            return result

        except Exception as e:
            self.logger.error(f"Error in multi-stop optimization: {e}")
            return {
                'error': str(e),
                'fallback_recommendation': 'Use single route optimization for each segment'
            }

    def optimize_for_fuel_efficiency(self, request: PredictionRequest,
                                     vehicle_type: str = 'car') -> OptimizationResult:
        """
        Optimize route considering fuel efficiency factors
        """
        try:
            routes = self.traffic_analyzer.db_manager.get_all_routes()
            route_evaluations = []

            # Fuel efficiency factors
            fuel_factors = {
                'car': {'stop_go_penalty': 1.3, 'highway_bonus': 0.9, 'distance_weight': 0.4},
                'motorcycle': {'stop_go_penalty': 1.2, 'highway_bonus': 0.95, 'distance_weight': 0.3},
                'truck': {'stop_go_penalty': 1.5, 'highway_bonus': 0.85, 'distance_weight': 0.6}
            }

            vehicle_factors = fuel_factors.get(vehicle_type, fuel_factors['car'])

            for route in routes:
                route_request = PredictionRequest(
                    route_name=route.name,
                    day_type=request.day_type,
                    hour=request.hour,
                    weather_condition=request.weather_condition,
                    season_type=request.season_type
                )

                prediction = self.traffic_analyzer.predict_travel_time(route_request)
                analytics = self.traffic_analyzer.analyze_route_performance(route.name)

                # Calculate fuel efficiency score
                fuel_score = self._calculate_fuel_efficiency_score(
                    route, prediction, analytics, vehicle_factors
                )

                route_evaluations.append({
                    'route': route,
                    'prediction': prediction,
                    'fuel_score': fuel_score,
                    'fuel_efficiency_factors': self._get_fuel_factors(route, prediction)
                })

            # Sort by fuel efficiency score (higher is better)
            route_evaluations.sort(key=lambda x: x['fuel_score'], reverse=True)

            best_route = route_evaluations[0]
            alternatives = [(eval['route'].name, eval['prediction'].predicted_time_minutes)
                            for eval in route_evaluations[1:]]

            optimization_factors = [
                                       f"Optimized for {vehicle_type} fuel efficiency",
                                       f"Fuel efficiency score: {best_route['fuel_score']:.2f}",
                                   ] + best_route['fuel_efficiency_factors']

            result = OptimizationResult(
                recommended_route=best_route['route'].name,
                estimated_time=best_route['prediction'].predicted_time_minutes,
                confidence=best_route['prediction'].confidence_level,
                alternatives=alternatives,
                optimization_factors=optimization_factors,
                savings={
                    'estimated_fuel_savings': f"{(1 - best_route['fuel_score']) * 100:.1f}%",
                    'distance_km': best_route['route'].distance_km,
                    'efficiency_rating': 'High' if best_route['fuel_score'] > 0.8 else 'Medium' if best_route[
                                                                                                       'fuel_score'] > 0.6 else 'Low'
                }
            )

            self.logger.info(f"Fuel efficiency optimization completed: {result.recommended_route}")
            return result

        except Exception as e:
            self.logger.error(f"Error in fuel efficiency optimization: {e}")
            return self._simple_route_optimization(request)

    def optimize_for_comfort(self, request: PredictionRequest,
                             comfort_preferences: Dict[str, float]) -> OptimizationResult:
        """
        Optimize route based on comfort preferences

        Args:
            comfort_preferences: Dict with preferences like:
                {'avoid_traffic': 0.8, 'prefer_highways': 0.6, 'scenic_route': 0.3}
        """
        try:
            routes = self.traffic_analyzer.db_manager.get_all_routes()
            route_evaluations = []

            for route in routes:
                route_request = PredictionRequest(
                    route_name=route.name,
                    day_type=request.day_type,
                    hour=request.hour,
                    weather_condition=request.weather_condition,
                    season_type=request.season_type
                )

                prediction = self.traffic_analyzer.predict_travel_time(route_request)
                analytics = self.traffic_analyzer.analyze_route_performance(route.name)

                # Calculate comfort score
                comfort_score = self._calculate_comfort_score(
                    route, prediction, analytics, comfort_preferences
                )

                route_evaluations.append({
                    'route': route,
                    'prediction': prediction,
                    'comfort_score': comfort_score,
                    'comfort_factors': self._get_comfort_factors(route, prediction, analytics)
                })

            # Sort by comfort score (higher is better)
            route_evaluations.sort(key=lambda x: x['comfort_score'], reverse=True)

            best_route = route_evaluations[0]
            alternatives = [(eval['route'].name, eval['prediction'].predicted_time_minutes)
                            for eval in route_evaluations[1:]]

            optimization_factors = [
                                       "Optimized for travel comfort",
                                       f"Comfort score: {best_route['comfort_score']:.2f}",
                                   ] + best_route['comfort_factors']

            result = OptimizationResult(
                recommended_route=best_route['route'].name,
                estimated_time=best_route['prediction'].predicted_time_minutes,
                confidence=best_route['prediction'].confidence_level,
                alternatives=alternatives,
                optimization_factors=optimization_factors,
                savings={
                    'comfort_rating': 'High' if best_route['comfort_score'] > 0.8 else 'Medium' if best_route[
                                                                                                       'comfort_score'] > 0.6 else 'Low',
                    'stress_reduction': f"{best_route['comfort_score'] * 100:.1f}%",
                    'route_type': best_route['route'].route_type
                }
            )

            self.logger.info(f"Comfort optimization completed: {result.recommended_route}")
            return result

        except Exception as e:
            self.logger.error(f"Error in comfort optimization: {e}")
            return self._simple_route_optimization(request)

    def optimize_for_weather_conditions(self, request: PredictionRequest) -> OptimizationResult:
        """
        Optimize route specifically for current weather conditions
        """
        try:
            routes = self.traffic_analyzer.db_manager.get_all_routes()
            route_evaluations = []

            for route in routes:
                route_request = PredictionRequest(
                    route_name=route.name,
                    day_type=request.day_type,
                    hour=request.hour,
                    weather_condition=request.weather_condition,
                    season_type=request.season_type
                )

                prediction = self.traffic_analyzer.predict_travel_time(route_request)

                # Calculate weather suitability score
                weather_score = self._calculate_weather_suitability_score(
                    route, request.weather_condition
                )

                # Combined score: time efficiency + weather suitability
                combined_score = (0.6 / max(prediction.predicted_time_minutes, 1)) + (0.4 * weather_score)

                route_evaluations.append({
                    'route': route,
                    'prediction': prediction,
                    'weather_score': weather_score,
                    'combined_score': combined_score,
                    'weather_factors': self._get_weather_factors(route, request.weather_condition)
                })

            # Sort by combined score (higher is better)
            route_evaluations.sort(key=lambda x: x['combined_score'], reverse=True)

            best_route = route_evaluations[0]
            alternatives = [(eval['route'].name, eval['prediction'].predicted_time_minutes)
                            for eval in route_evaluations[1:]]

            optimization_factors = [
                                       f"Optimized for {request.weather_condition.value} conditions",
                                       f"Weather suitability: {best_route['weather_score']:.2f}",
                                   ] + best_route['weather_factors']

            result = OptimizationResult(
                recommended_route=best_route['route'].name,
                estimated_time=best_route['prediction'].predicted_time_minutes,
                confidence=best_route['prediction'].confidence_level,
                alternatives=alternatives,
                optimization_factors=optimization_factors,
                savings={
                    'weather_safety_rating': 'High' if best_route['weather_score'] > 0.8 else 'Medium' if best_route[
                                                                                                              'weather_score'] > 0.6 else 'Low',
                    'weather_condition': request.weather_condition.value,
                    'route_safety_features': self._get_safety_features(best_route['route'])
                }
            )

            self.logger.info(f"Weather-optimized route: {result.recommended_route}")
            return result

        except Exception as e:
            self.logger.error(f"Error in weather optimization: {e}")
            return self._simple_route_optimization(request)

    # Helper methods for optimization calculations
    def _calculate_objective_scores(self, route: Route, prediction: PredictionResult,
                                    analytics: Any, objectives: Dict[str, float]) -> Dict[str, float]:
        """Calculate scores for different optimization objectives"""
        scores = {}

        # Time efficiency score (inverse of travel time, normalized)
        max_time = 60  # Assume max reasonable time is 60 minutes
        scores['time'] = max(0, (max_time - prediction.predicted_time_minutes) / max_time)

        # Reliability score based on variability
        if hasattr(analytics, 'get_variability'):
            variability = analytics.get_variability()
            scores['reliability'] = max(0, (100 - variability) / 100)
        else:
            scores['reliability'] = prediction.confidence_level

        # Comfort score based on route characteristics
        comfort_base = 0.5  # Base comfort score
        if 'highway' in route.route_type.lower() or 'main' in route.route_type.lower():
            comfort_base += 0.3
        if 'scenic' in route.route_type.lower():
            comfort_base += 0.2
        scores['comfort'] = min(1.0, comfort_base)

        # Distance efficiency (shorter routes get higher scores)
        max_distance = 20  # Assume max reasonable distance is 20km
        scores['distance'] = max(0, (max_distance - route.distance_km) / max_distance)

        return scores

    def _generate_optimization_factors(self, best_route: Dict, objectives: Dict[str, float]) -> List[str]:
        """Generate human-readable optimization factors"""
        factors = []

        # Primary objective
        primary_obj = max(objectives.items(), key=lambda x: x[1])
        factors.append(f"Primary objective: {primary_obj[0]} (weight: {primary_obj[1]})")

        # Route characteristics
        route = best_route['route']
        factors.append(f"Route distance: {route.distance_km:.1f} km")
        factors.append(f"Route type: {route.route_type}")

        # Prediction factors
        pred_confidence = best_route['prediction'].confidence_level
        factors.append(f"Prediction confidence: {pred_confidence:.1%}")

        return factors

    def _score_departure_option(self, buffer_minutes: float, confidence: float, travel_time: int) -> float:
        """Score a departure time option"""
        # Ideal buffer is 10-15 minutes
        if 10 <= buffer_minutes <= 15:
            buffer_score = 1.0
        elif 5 <= buffer_minutes < 10:
            buffer_score = 0.8
        elif 15 < buffer_minutes <= 20:
            buffer_score = 0.9
        elif buffer_minutes < 5:
            buffer_score = max(0, buffer_minutes / 5)
        else:
            buffer_score = max(0.3, 1 - ((buffer_minutes - 20) / 30))

        # Combine buffer score with confidence and prefer shorter travel times
        time_score = max(0.1, 1 - (travel_time / 120))  # Normalize against 2 hours

        return (buffer_score * 0.5) + (confidence * 0.3) + (time_score * 0.2)

    def _score_multi_stop_route(self, total_time: int, avg_confidence: float) -> float:
        """Score a multi-stop route combination"""
        # Prefer shorter total time and higher confidence
        time_score = max(0.1, 1 - (total_time / 180))  # Normalize against 3 hours
        confidence_score = avg_confidence

        return (time_score * 0.7) + (confidence_score * 0.3)

    def _calculate_fuel_efficiency_score(self, route: Route, prediction: PredictionResult,
                                         analytics: Any, vehicle_factors: Dict) -> float:
        """Calculate fuel efficiency score for a route"""
        base_score = 0.5

        # Distance factor (shorter routes are more fuel efficient)
        distance_penalty = route.distance_km * vehicle_factors['distance_weight'] * 0.05

        # Traffic factor (stop-and-go traffic reduces fuel efficiency)
        if prediction.predicted_time_minutes > (route.distance_km / route.typical_speed_kmh * 60 * 1.3):
            traffic_penalty = vehicle_factors['stop_go_penalty'] * 0.2
        else:
            traffic_penalty = 0

        # Route type bonus
        highway_bonus = 0
        if 'highway' in route.route_type.lower() or 'main' in route.route_type.lower():
            highway_bonus = vehicle_factors['highway_bonus'] * 0.3

        fuel_score = base_score - distance_penalty - traffic_penalty + highway_bonus
        return max(0.1, min(1.0, fuel_score))

    def _get_fuel_factors(self, route: Route, prediction: PredictionResult) -> List[str]:
        """Get human-readable fuel efficiency factors"""
        factors = []

        factors.append(f"Route distance: {route.distance_km:.1f} km")

        expected_time_no_traffic = route.distance_km / route.typical_speed_kmh * 60
        if prediction.predicted_time_minutes > expected_time_no_traffic * 1.2:
            factors.append("Heavy traffic may increase fuel consumption")
        else:
            factors.append("Moderate traffic conditions")

        if 'highway' in route.route_type.lower():
            factors.append("Highway route - better fuel efficiency")

        return factors

    def _calculate_comfort_score(self, route: Route, prediction: PredictionResult,
                                 analytics: Any, preferences: Dict[str, float]) -> float:
        """Calculate comfort score based on preferences"""
        base_score = 0.5

        # Traffic avoidance
        if preferences.get('avoid_traffic', 0) > 0:
            expected_time = route.distance_km / route.typical_speed_kmh * 60
            if prediction.predicted_time_minutes <= expected_time * 1.1:
                base_score += preferences['avoid_traffic'] * 0.3

        # Highway preference
        if preferences.get('prefer_highways', 0) > 0:
            if 'highway' in route.route_type.lower() or 'main' in route.route_type.lower():
                base_score += preferences['prefer_highways'] * 0.2

        # Scenic route preference
        if preferences.get('scenic_route', 0) > 0:
            if 'scenic' in route.route_type.lower() or 'marine' in route.name.lower():
                base_score += preferences['scenic_route'] * 0.25

        return max(0.1, min(1.0, base_score))

    def _get_comfort_factors(self, route: Route, prediction: PredictionResult, analytics: Any) -> List[str]:
        """Get comfort-related factors"""
        factors = []

        if 'highway' in route.route_type.lower():
            factors.append("Highway route - smoother traffic flow")

        if 'scenic' in route.route_type.lower() or 'marine' in route.name.lower():
            factors.append("Scenic route - pleasant driving experience")

        if hasattr(analytics, 'get_variability'):
            variability = analytics.get_variability()
            if variability < 20:
                factors.append("Consistent travel times - predictable journey")
            else:
                factors.append("Variable travel times - less predictable")

        return factors

    def _calculate_weather_suitability_score(self, route: Route, weather: WeatherCondition) -> float:
        """Calculate how suitable a route is for specific weather conditions"""
        base_score = 0.7

        # Route-specific weather adjustments
        if weather in [WeatherCondition.HEAVY_RAIN, WeatherCondition.RAINY]:
            if 'highway' in route.route_type.lower():
                base_score += 0.2  # Highways typically have better drainage
            if 'marine' in route.name.lower():
                base_score -= 0.3  # Coastal routes may have more flooding
            if 'main' in route.route_type.lower():
                base_score += 0.1  # Main roads better maintained

        elif weather == WeatherCondition.CLEAR:
            if 'scenic' in route.route_type.lower():
                base_score += 0.2  # Scenic routes better in good weather

        return max(0.1, min(1.0, base_score))

    def _get_weather_factors(self, route: Route, weather: WeatherCondition) -> List[str]:
        """Get weather-related route factors"""
        factors = []

        if weather in [WeatherCondition.HEAVY_RAIN, WeatherCondition.RAINY]:
            factors.append("Rainy conditions - checking route suitability")

            if 'highway' in route.route_type.lower():
                factors.append("Highway route - generally better drainage")
            if 'marine' in route.name.lower():
                factors.append("Coastal route - monitor for flooding")
            if 'main' in route.route_type.lower():
                factors.append("Main road - priority for maintenance")

        return factors

    def _get_safety_features(self, route: Route) -> List[str]:
        """Get safety features of a route"""
        features = []

        if 'highway' in route.route_type.lower():
            features.append("Divided highway")
        if 'main' in route.route_type.lower():
            features.append("Well-maintained main road")
        if route.distance_km < 15:
            features.append("Shorter distance reduces exposure")

        return features

    def _simple_route_optimization(self, request: PredictionRequest) -> OptimizationResult:
        """Fallback simple optimization"""
        try:
            comparison = self.traffic_analyzer.compare_all_routes(request)

            best_prediction = comparison.get_sorted_routes()[0]
            alternatives = [(p.route_name, p.predicted_time_minutes)
                            for p in comparison.get_sorted_routes()[1:]]

            return OptimizationResult(
                recommended_route=best_prediction.route_name,
                estimated_time=best_prediction.predicted_time_minutes,
                confidence=best_prediction.confidence_level,
                alternatives=alternatives,
                optimization_factors=["Simple time-based optimization"],
                savings={'time_minutes': 0, 'method': 'fallback'}
            )

        except Exception as e:
            self.logger.error(f"Even simple optimization failed: {e}")
            # Last resort fallback
            return OptimizationResult(
                recommended_route="High Level Road",
                estimated_time=30,
                confidence=0.3,
                alternatives=[],
                optimization_factors=["Emergency fallback recommendation"],
                savings={}
            )