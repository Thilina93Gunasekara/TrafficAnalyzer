# business_logic/prediction_service.py
# Advanced prediction service with statistical and ML techniques

# business_logic/prediction_service.py
# Advanced prediction service with statistical and ML techniques

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import statistics
from dataclasses import dataclass
import sys
import os

# Add parent directory to path if needed
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_access.models import (
    TrafficRecord, PredictionRequest, PredictionResult,
    DayType, WeatherCondition, SeasonType, Route
)
from data_access.database_manager import DatabaseManager, TrafficRecordRepository
from utilities.logger import get_logger


@dataclass
class PredictionMetrics:
    """Metrics for evaluating prediction accuracy"""
    mae: float  # Mean Absolute Error
    rmse: float  # Root Mean Square Error
    mape: float  # Mean Absolute Percentage Error
    accuracy_score: float  # Custom accuracy score
    confidence_level: float


class AdvancedPredictionService:
    """
    Advanced prediction service using multiple statistical and ML techniques
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.traffic_repo = TrafficRecordRepository(db_manager)
        self.logger = get_logger(__name__)
        self.prediction_cache = {}
        self.cache_expiry = timedelta(minutes=15)

    def predict_with_multiple_models(self, request: PredictionRequest) -> PredictionResult:
        """
        Use multiple prediction models and ensemble them for better accuracy
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(request)
            if self._is_cache_valid(cache_key):
                cached_result = self.prediction_cache[cache_key]
                self.logger.debug(f"Using cached prediction for {request.route_name}")
                return cached_result['result']

            # Get historical data
            historical_data = self.traffic_repo.get_similar_conditions_records(request, days_back=90)

            if len(historical_data) < 3:
                # Fall back to simple prediction if insufficient data
                return self._simple_prediction(request)

            # Apply multiple prediction models
            predictions = []
            confidences = []
            methods = []

            # 1. Time Series Average
            ts_pred, ts_conf = self._time_series_prediction(historical_data, request)
            predictions.append(ts_pred)
            confidences.append(ts_conf)
            methods.append("Time series analysis")

            # 2. Weighted Historical Average
            wh_pred, wh_conf = self._weighted_historical_prediction(historical_data, request)
            predictions.append(wh_pred)
            confidences.append(wh_conf)
            methods.append("Weighted historical average")

            # 3. Seasonal Decomposition
            sd_pred, sd_conf = self._seasonal_decomposition_prediction(historical_data, request)
            predictions.append(sd_pred)
            confidences.append(sd_conf)
            methods.append("Seasonal pattern analysis")

            # 4. Regression-based Prediction
            rg_pred, rg_conf = self._regression_prediction(historical_data, request)
            predictions.append(rg_pred)
            confidences.append(rg_conf)
            methods.append("Statistical regression")

            # Ensemble the predictions
            final_prediction, final_confidence = self._ensemble_predictions(
                predictions, confidences
            )

            # Create result
            result = PredictionResult(
                route_name=request.route_name,
                predicted_time_minutes=final_prediction,
                confidence_level=final_confidence,
                factors_considered=methods + [f"Ensemble of {len(predictions)} models"]
            )

            # Cache the result
            self.prediction_cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now()
            }

            self.logger.info(f"Multi-model prediction for {request.route_name}: {final_prediction} min")
            return result

        except Exception as e:
            self.logger.error(f"Error in multi-model prediction: {e}")
            return self._simple_prediction(request)

    def _time_series_prediction(self, data: List[TrafficRecord],
                                request: PredictionRequest) -> Tuple[int, float]:
        """Time series based prediction using moving averages"""
        try:
            # Convert to time series
            df = pd.DataFrame([{
                'timestamp': record.timestamp,
                'travel_time': record.travel_time_minutes,
                'hour': record.hour,
                'day_of_week': record.day_of_week
            } for record in data])

            df = df.sort_values('timestamp')

            # Calculate moving averages with different windows
            windows = [3, 7, 14]  # 3, 7, 14 days
            predictions = []

            for window in windows:
                if len(df) >= window:
                    moving_avg = df['travel_time'].rolling(window=window).mean().iloc[-1]
                    if not np.isnan(moving_avg):
                        predictions.append(moving_avg)

            if predictions:
                prediction = int(np.mean(predictions))
                confidence = min(0.8, 0.4 + len(predictions) * 0.1)
            else:
                prediction = int(df['travel_time'].mean())
                confidence = 0.3

            return prediction, confidence

        except Exception as e:
            self.logger.warning(f"Time series prediction failed: {e}")
            return int(np.mean([r.travel_time_minutes for r in data])), 0.2

    def _weighted_historical_prediction(self, data: List[TrafficRecord],
                                        request: PredictionRequest) -> Tuple[int, float]:
        """Weighted prediction giving more weight to recent and similar conditions"""
        try:
            current_time = datetime.now()
            weighted_sum = 0
            weight_total = 0

            for record in data:
                # Time decay weight (recent data is more valuable)
                days_old = (current_time - record.timestamp).days
                time_weight = np.exp(-days_old / 30)  # Exponential decay over 30 days

                # Condition similarity weight
                similarity_weight = 1.0

                # Hour similarity
                hour_diff = abs(record.hour - request.hour)
                if hour_diff == 0:
                    similarity_weight *= 2.0
                elif hour_diff <= 1:
                    similarity_weight *= 1.5
                elif hour_diff <= 2:
                    similarity_weight *= 1.2

                # Day type similarity
                if record.day_type == request.day_type:
                    similarity_weight *= 1.8

                # Weather similarity
                if record.weather_condition == request.weather_condition:
                    similarity_weight *= 1.6

                # Season similarity
                if record.season_type == request.season_type:
                    similarity_weight *= 1.3

                # Combined weight
                total_weight = time_weight * similarity_weight
                weighted_sum += record.travel_time_minutes * total_weight
                weight_total += total_weight

            if weight_total > 0:
                prediction = int(weighted_sum / weight_total)
                confidence = min(0.9, 0.5 + (len(data) / 50))
            else:
                prediction = int(np.mean([r.travel_time_minutes for r in data]))
                confidence = 0.3

            return prediction, confidence

        except Exception as e:
            self.logger.warning(f"Weighted prediction failed: {e}")
            return int(np.mean([r.travel_time_minutes for r in data])), 0.2

    def _seasonal_decomposition_prediction(self, data: List[TrafficRecord],
                                           request: PredictionRequest) -> Tuple[int, float]:
        """Seasonal pattern analysis for prediction"""
        try:
            # Group by hour and day of week to find patterns
            hourly_patterns = {}
            daily_patterns = {}

            for record in data:
                # Hourly patterns
                if record.hour not in hourly_patterns:
                    hourly_patterns[record.hour] = []
                hourly_patterns[record.hour].append(record.travel_time_minutes)

                # Daily patterns
                if record.day_of_week not in daily_patterns:
                    daily_patterns[record.day_of_week] = []
                daily_patterns[record.day_of_week].append(record.travel_time_minutes)

            # Calculate pattern-based prediction
            base_prediction = np.mean([r.travel_time_minutes for r in data])

            # Hour pattern adjustment
            if request.hour in hourly_patterns:
                hourly_avg = np.mean(hourly_patterns[request.hour])
                hourly_adjustment = hourly_avg - base_prediction
            else:
                hourly_adjustment = 0

            # Day pattern adjustment (from request conditions)
            day_of_week = datetime.now().weekday()  # Simplified
            if day_of_week in daily_patterns:
                daily_avg = np.mean(daily_patterns[day_of_week])
                daily_adjustment = daily_avg - base_prediction
            else:
                daily_adjustment = 0

            # Combine adjustments
            prediction = int(base_prediction + (hourly_adjustment * 0.6) + (daily_adjustment * 0.4))
            confidence = min(0.7, 0.3 + len(data) / 100)

            return prediction, confidence

        except Exception as e:
            self.logger.warning(f"Seasonal decomposition failed: {e}")
            return int(np.mean([r.travel_time_minutes for r in data])), 0.2

    def _regression_prediction(self, data: List[TrafficRecord],
                               request: PredictionRequest) -> Tuple[int, float]:
        """Simple linear regression-based prediction"""
        try:
            if len(data) < 5:
                return int(np.mean([r.travel_time_minutes for r in data])), 0.2

            # Prepare features
            X = []
            y = []

            for record in data:
                features = [
                    record.hour,
                    record.day_of_week,
                    1 if record.day_type == DayType.WEEKEND else 0,
                    1 if record.weather_condition in [WeatherCondition.RAINY, WeatherCondition.HEAVY_RAIN] else 0,
                    1 if record.season_type == SeasonType.SCHOOL_HOLIDAY else 0
                ]
                X.append(features)
                y.append(record.travel_time_minutes)

            X = np.array(X)
            y = np.array(y)

            # Simple linear regression using normal equation
            # Add bias term
            X_with_bias = np.column_stack([np.ones(X.shape[0]), X])

            try:
                # Calculate coefficients: theta = (X^T * X)^-1 * X^T * y
                XtX = np.dot(X_with_bias.T, X_with_bias)
                XtX_inv = np.linalg.inv(XtX)
                Xty = np.dot(X_with_bias.T, y)
                theta = np.dot(XtX_inv, Xty)

                # Make prediction
                request_features = [
                    1,  # bias
                    request.hour,
                    datetime.now().weekday(),  # Simplified
                    1 if request.day_type == DayType.WEEKEND else 0,
                    1 if request.weather_condition in [WeatherCondition.RAINY, WeatherCondition.HEAVY_RAIN] else 0,
                    1 if request.season_type == SeasonType.SCHOOL_HOLIDAY else 0
                ]

                prediction = int(np.dot(theta, request_features))

                # Calculate R-squared for confidence
                y_pred = np.dot(X_with_bias, theta)
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

                confidence = min(0.8, max(0.2, r_squared))

                return max(15, prediction), confidence

            except np.linalg.LinAlgError:
                # Matrix is singular, fall back to mean
                return int(np.mean(y)), 0.3

        except Exception as e:
            self.logger.warning(f"Regression prediction failed: {e}")
            return int(np.mean([r.travel_time_minutes for r in data])), 0.2

    def _ensemble_predictions(self, predictions: List[int],
                              confidences: List[float]) -> Tuple[int, float]:
        """Ensemble multiple predictions using confidence-weighted average"""
        try:
            if not predictions:
                return 30, 0.1  # Default fallback

            # Weight predictions by their confidence levels
            weighted_sum = 0
            weight_total = 0

            for pred, conf in zip(predictions, confidences):
                weight = conf ** 2  # Square confidence for more emphasis on high-confidence predictions
                weighted_sum += pred * weight
                weight_total += weight

            if weight_total > 0:
                final_prediction = int(weighted_sum / weight_total)
            else:
                final_prediction = int(np.mean(predictions))

            # Calculate ensemble confidence
            # Higher confidence if models agree, lower if they disagree
            pred_std = np.std(predictions) if len(predictions) > 1 else 0
            agreement_factor = max(0.1, 1 - (pred_std / np.mean(predictions))) if np.mean(predictions) > 0 else 0.1

            avg_confidence = np.mean(confidences)
            final_confidence = min(0.95, avg_confidence * agreement_factor * 1.1)  # Slight boost for ensemble

            return final_prediction, final_confidence

        except Exception as e:
            self.logger.warning(f"Ensemble failed: {e}")
            return int(np.mean(predictions)) if predictions else 30, 0.3

    def _simple_prediction(self, request: PredictionRequest) -> PredictionResult:
        """Fallback simple prediction when advanced methods fail"""
        try:
            # Get route information
            route = self.db_manager.get_route(request.route_name)

            if route and route.distance_km > 0 and route.typical_speed_kmh > 0:
                base_time = (route.distance_km / route.typical_speed_kmh) * 60
            else:
                # Default base times
                base_times = {
                    'High Level Road': 25, 'Low Level Road': 28, 'Baseline Road': 27,
                    'Galle Road': 32, 'Marine Drive': 35, 'Other Roads': 22
                }
                base_time = base_times.get(request.route_name, 30)

            # Apply condition multipliers
            multiplier = 1.0
            factors = ["Base route calculation"]

            # Time adjustments
            if 7 <= request.hour <= 9 or 17 <= request.hour <= 19:
                multiplier *= 1.6
                factors.append("Rush hour adjustment")
            elif 10 <= request.hour <= 16:
                multiplier *= 1.1
                factors.append("Daytime adjustment")
            else:
                multiplier *= 0.9
                factors.append("Off-peak adjustment")

            # Day type adjustments
            if request.day_type == DayType.WEEKEND:
                multiplier *= 0.8
                factors.append("Weekend reduction")
            elif request.day_type == DayType.RAINY_DAY:
                multiplier *= 1.4
                factors.append("Rainy day increase")

            # Weather adjustments
            if request.weather_condition == WeatherCondition.HEAVY_RAIN:
                multiplier *= 1.3
                factors.append("Heavy rain impact")
            elif request.weather_condition == WeatherCondition.RAINY:
                multiplier *= 1.2
                factors.append("Rain impact")

            predicted_time = max(15, int(base_time * multiplier))

            return PredictionResult(
                route_name=request.route_name,
                predicted_time_minutes=predicted_time,
                confidence_level=0.4,  # Lower confidence for simple prediction
                factors_considered=factors
            )

        except Exception as e:
            self.logger.error(f"Even simple prediction failed: {e}")
            return PredictionResult(
                route_name=request.route_name,
                predicted_time_minutes=30,
                confidence_level=0.1,
                factors_considered=["Emergency fallback prediction"]
            )

    def evaluate_prediction_accuracy(self, days_back: int = 30) -> Dict[str, PredictionMetrics]:
        """Evaluate the accuracy of predictions against historical data"""
        try:
            routes = self.db_manager.get_all_routes()
            evaluation_results = {}

            for route in routes:
                # Get historical data for evaluation
                historical_data = self.db_manager.get_traffic_records(
                    route_name=route.name,
                    days_back=days_back
                )

                if len(historical_data) < 10:
                    continue  # Skip routes with insufficient data

                # Split data: use first 80% for training context, last 20% for testing
                split_point = int(len(historical_data) * 0.8)
                test_data = historical_data[split_point:]

                predictions = []
                actuals = []

                for record in test_data:
                    # Create prediction request
                    request = PredictionRequest(
                        route_name=route.name,
                        day_type=record.day_type,
                        hour=record.hour,
                        weather_condition=record.weather_condition,
                        season_type=record.season_type
                    )

                    # Make prediction
                    pred_result = self.predict_with_multiple_models(request)
                    predictions.append(pred_result.predicted_time_minutes)
                    actuals.append(record.travel_time_minutes)

                # Calculate metrics
                if predictions and actuals:
                    metrics = self._calculate_prediction_metrics(actuals, predictions)
                    evaluation_results[route.name] = metrics

            self.logger.info(f"Evaluated prediction accuracy for {len(evaluation_results)} routes")
            return evaluation_results

        except Exception as e:
            self.logger.error(f"Error evaluating prediction accuracy: {e}")
            return {}

    def _calculate_prediction_metrics(self, actuals: List[int],
                                      predictions: List[int]) -> PredictionMetrics:
        """Calculate various prediction accuracy metrics"""
        try:
            actuals = np.array(actuals)
            predictions = np.array(predictions)

            # Mean Absolute Error
            mae = np.mean(np.abs(actuals - predictions))

            # Root Mean Square Error
            rmse = np.sqrt(np.mean((actuals - predictions) ** 2))

            # Mean Absolute Percentage Error
            mape = np.mean(np.abs((actuals - predictions) / actuals)) * 100

            # Custom accuracy score (percentage of predictions within 20% of actual)
            within_20_percent = np.abs((actuals - predictions) / actuals) <= 0.2
            accuracy_score = np.mean(within_20_percent) * 100

            # Confidence level based on accuracy
            confidence_level = min(0.95, accuracy_score / 100)

            return PredictionMetrics(
                mae=mae,
                rmse=rmse,
                mape=mape,
                accuracy_score=accuracy_score,
                confidence_level=confidence_level
            )

        except Exception as e:
            self.logger.warning(f"Error calculating metrics: {e}")
            return PredictionMetrics(0.0, 0.0, 0.0, 0.0, 0.0)

    def _generate_cache_key(self, request: PredictionRequest) -> str:
        """Generate cache key for prediction requests"""
        return f"{request.route_name}_{request.day_type.value}_{request.hour}_{request.weather_condition.value}_{request.season_type.value}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached prediction is still valid"""
        if cache_key not in self.prediction_cache:
            return False

        cached_time = self.prediction_cache[cache_key]['timestamp']
        return datetime.now() - cached_time < self.cache_expiry

    def clear_cache(self):
        """Clear prediction cache"""
        self.prediction_cache.clear()
        self.logger.info("Prediction cache cleared")