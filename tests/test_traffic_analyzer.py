# tests/test_traffic_analyzer.py
# Unit tests for the traffic analysis system

# tests/test_traffic_analyzer.py
# Unit tests for the traffic analysis system

import unittest
from datetime import datetime
import os
import sys

# Add parent directory to path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from data_access.database_manager import DatabaseManager
from data_access.models import (
    Route, TrafficRecord, PredictionRequest, PredictionResult,
    DayType, WeatherCondition, SeasonType, TrafficDensity
)
from business_logic.traffic_analyzer import TrafficAnalysisService
from business_logic.route_optimizer import AdvancedRouteOptimizer

class TestDatabaseManager(unittest.TestCase):
    """Test database operations"""

    def setUp(self):
        """Set up test database"""
        self.db_manager = DatabaseManager()

    def test_database_initialization(self):
        """Test that database initializes correctly"""
        stats = self.db_manager.get_database_stats()
        self.assertIsNotNone(stats)
        self.assertIn('routes_count', stats)

    def test_route_creation(self):
        """Test route creation"""
        test_route = Route(
            name="Test Route",
            start_latitude=6.0,
            start_longitude=79.0,
            end_latitude=7.0,
            end_longitude=80.0,
            distance_km=10.0,
            typical_speed_kmh=40
        )

        route_id = self.db_manager.create_route(test_route)
        self.assertIsNotNone(route_id)

        # Retrieve and verify
        retrieved_route = self.db_manager.get_route("Test Route")
        self.assertIsNotNone(retrieved_route)
        self.assertEqual(retrieved_route.distance_km, 10.0)


class TestTrafficAnalyzer(unittest.TestCase):
    """Test traffic analysis service"""

    def setUp(self):
        """Set up test services"""
        self.db_manager = DatabaseManager()
        self.traffic_service = TrafficAnalysisService(self.db_manager)

    def test_prediction_basic(self):
        """Test basic prediction"""
        request = PredictionRequest(
            route_name="High Level Road",
            day_type=DayType.WEEKDAY,
            hour=8,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        prediction = self.traffic_service.predict_travel_time(request)

        self.assertIsNotNone(prediction)
        self.assertGreater(prediction.predicted_time_minutes, 0)
        self.assertGreaterEqual(prediction.confidence_level, 0)
        self.assertLessEqual(prediction.confidence_level, 1)

    def test_route_comparison(self):
        """Test route comparison"""
        request = PredictionRequest(
            route_name="",
            day_type=DayType.WEEKDAY,
            hour=8,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        comparison = self.traffic_service.compare_all_routes(request)

        self.assertIsNotNone(comparison)
        self.assertIsNotNone(comparison.best_route)
        self.assertGreater(len(comparison.predictions), 0)

    def test_analytics(self):
        """Test route analytics"""
        analytics = self.traffic_service.analyze_route_performance("High Level Road")

        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.route_name, "High Level Road")


class TestRouteOptimizer(unittest.TestCase):
    """Test route optimization"""

    def setUp(self):
        """Set up test services"""
        self.db_manager = DatabaseManager()
        self.traffic_service = TrafficAnalysisService(self.db_manager)
        self.route_optimizer = AdvancedRouteOptimizer(self.traffic_service)

    def test_multi_objective_optimization(self):
        """Test multi-objective optimization"""
        request = PredictionRequest(
            route_name="",
            day_type=DayType.WEEKDAY,
            hour=8,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        objectives = {
            'time': 0.6,
            'reliability': 0.3,
            'comfort': 0.1
        }

        result = self.route_optimizer.optimize_multi_objective(request, objectives)

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.recommended_route)
        self.assertGreater(result.estimated_time, 0)

    def test_departure_optimization(self):
        """Test departure time optimization"""
        conditions = PredictionRequest(
            route_name="High Level Road",
            day_type=DayType.WEEKDAY,
            hour=8,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        optimization = self.route_optimizer.optimize_departure_time_window(
            route_name="High Level Road",
            target_arrival=9,
            conditions=conditions,
            window_minutes=60
        )

        self.assertIsNotNone(optimization)
        self.assertIsNotNone(optimization.optimal_departure_time)
        self.assertGreater(optimization.travel_time, 0)


class TestDataModels(unittest.TestCase):
    """Test data models"""

    def test_traffic_record_creation(self):
        """Test traffic record creation"""
        record = TrafficRecord(
            route_name="Test Route",
            travel_time_minutes=30,
            distance_km=10.0,
            day_type=DayType.WEEKDAY,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        self.assertEqual(record.route_name, "Test Route")
        self.assertEqual(record.travel_time_minutes, 30)
        self.assertGreater(record.average_speed_kmh, 0)

    def test_prediction_request_validation(self):
        """Test prediction request validation"""
        request = PredictionRequest(
            route_name="High Level Road",
            day_type=DayType.WEEKDAY,
            hour=8,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        self.assertEqual(request.hour, 8)
        self.assertEqual(request.day_type, DayType.WEEKDAY)


class TestUtilities(unittest.TestCase):
    """Test utility functions"""

    def test_format_time(self):
        """Test time formatting"""
        from utilities.helpers import format_time_minutes

        self.assertEqual(format_time_minutes(30), "30 minutes")
        self.assertEqual(format_time_minutes(60), "1 hour")
        self.assertEqual(format_time_minutes(90), "1 hour 30 minutes")

    def test_distance_formatting(self):
        """Test distance formatting"""
        from utilities.helpers import format_distance_km

        self.assertEqual(format_distance_km(0.5), "500 meters")
        self.assertEqual(format_distance_km(1.5), "1.5 km")

    def test_rush_hour_detection(self):
        """Test rush hour detection"""
        from utilities.helpers import is_rush_hour

        self.assertTrue(is_rush_hour(8))
        self.assertTrue(is_rush_hour(18))
        self.assertFalse(is_rush_hour(14))


def run_all_tests():
    """Run all test suites"""
    print("🧪 Running Traffic Analyzer Test Suite")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTrafficAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestRouteOptimizer))
    suite.addTests(loader.loadTestsFromTestCase(TestDataModels))
    suite.addTests(loader.loadTestsFromTestCase(TestUtilities))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)