# test_system.py
# Comprehensive test suite for traffic analysis system
# Demonstrates validation and testing for assignment

import sys
import os
import unittest
from datetime import datetime
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from data_access.database_manager import DatabaseManager, TrafficRecordRepository
from data_access.models import (
    PredictionRequest, Route, TrafficRecord,
    DayType, WeatherCondition, SeasonType, TrafficDensity
)
from business_logic.traffic_analyzer import TrafficAnalysisService
from business_logic.prediction_service import AdvancedPredictionService
from utilities.logger import get_logger


class TestDatabaseOperations(unittest.TestCase):
    """Test database operations and data integrity"""

    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        cls.db_manager = DatabaseManager()
        cls.logger = get_logger(__name__)

    def test_database_connectivity(self):
        """Test 1: Database connection is established"""
        self.assertIsNotNone(self.db_manager)
        stats = self.db_manager.get_database_stats()
        self.assertIsNotNone(stats)
        self.logger.info("✓ Test 1 Passed: Database connectivity")

    def test_routes_exist(self):
        """Test 2: Routes are loaded in database"""
        routes = self.db_manager.get_all_routes()
        self.assertGreater(len(routes), 0, "No routes found in database")
        self.assertIsInstance(routes[0], Route)
        self.logger.info(f"✓ Test 2 Passed: {len(routes)} routes found")

    def test_traffic_records_exist(self):
        """Test 3: Traffic records are present"""
        stats = self.db_manager.get_database_stats()
        self.assertGreater(stats['records_count'], 0, "No traffic records found")
        self.logger.info(f"✓ Test 3 Passed: {stats['records_count']} records found")

    def test_data_integrity(self):
        """Test 4: Data integrity checks"""
        routes = self.db_manager.get_all_routes()

        for route in routes[:5]:  # Test first 5 routes
            # Check route has valid data
            self.assertIsNotNone(route.name)
            self.assertGreater(route.distance_km, 0)
            self.assertGreater(route.typical_speed_kmh, 0)

            # Check records exist for route
            records = self.db_manager.get_traffic_records(route.name, days_back=7, limit=10)
            if records:  # Some routes might not have records yet
                record = records[0]
                self.assertGreater(record.travel_time_minutes, 0)
                self.assertGreater(record.distance_km, 0)

        self.logger.info("✓ Test 4 Passed: Data integrity verified")


class TestPredictionAccuracy(unittest.TestCase):
    """Test prediction algorithms and accuracy"""

    @classmethod
    def setUpClass(cls):
        """Set up test services"""
        cls.db_manager = DatabaseManager()
        cls.traffic_service = TrafficAnalysisService(cls.db_manager)
        cls.prediction_service = AdvancedPredictionService(cls.db_manager)
        cls.logger = get_logger(__name__)

    def test_basic_prediction(self):
        """Test 5: Basic prediction returns valid results"""
        request = PredictionRequest(
            route_name='High Level Road',
            day_type=DayType.WEEKDAY,
            hour=8,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        prediction = self.traffic_service.predict_travel_time(request)

        self.assertIsNotNone(prediction)
        self.assertGreater(prediction.predicted_time_minutes, 0)
        self.assertLessEqual(prediction.predicted_time_minutes, 180)  # Max 3 hours
        self.assertGreaterEqual(prediction.confidence_level, 0)
        self.assertLessEqual(prediction.confidence_level, 1)

        self.logger.info(f"✓ Test 5 Passed: Prediction = {prediction.predicted_time_minutes} min "
                         f"(confidence: {prediction.confidence_level:.2%})")

    def test_peak_hour_slower_than_offpeak(self):
        """Test 6: Peak hours should have longer travel times"""
        route_name = 'High Level Road'

        # Peak hour prediction (8 AM)
        peak_request = PredictionRequest(
            route_name=route_name,
            day_type=DayType.WEEKDAY,
            hour=8,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )
        peak_prediction = self.traffic_service.predict_travel_time(peak_request)

        # Off-peak prediction (2 PM)
        offpeak_request = PredictionRequest(
            route_name=route_name,
            day_type=DayType.WEEKDAY,
            hour=14,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )
        offpeak_prediction = self.traffic_service.predict_travel_time(offpeak_request)

        self.assertGreater(
            peak_prediction.predicted_time_minutes,
            offpeak_prediction.predicted_time_minutes,
            f"Peak hour ({peak_prediction.predicted_time_minutes} min) should be slower than "
            f"off-peak ({offpeak_prediction.predicted_time_minutes} min)"
        )

        difference = peak_prediction.predicted_time_minutes - offpeak_prediction.predicted_time_minutes
        self.logger.info(f"✓ Test 6 Passed: Peak is {difference} min slower than off-peak")

    def test_rainy_weather_impact(self):
        """Test 7: Rainy weather should increase travel time"""
        route_name = 'High Level Road'
        hour = 10

        # Clear weather
        clear_request = PredictionRequest(
            route_name=route_name,
            day_type=DayType.WEEKDAY,
            hour=hour,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )
        clear_prediction = self.traffic_service.predict_travel_time(clear_request)

        # Rainy weather
        rainy_request = PredictionRequest(
            route_name=route_name,
            day_type=DayType.WEEKDAY,
            hour=hour,
            weather_condition=WeatherCondition.HEAVY_RAIN,
            season_type=SeasonType.REGULAR
        )
        rainy_prediction = self.traffic_service.predict_travel_time(rainy_request)

        self.assertGreater(
            rainy_prediction.predicted_time_minutes,
            clear_prediction.predicted_time_minutes,
            "Rain should increase travel time"
        )

        impact = ((rainy_prediction.predicted_time_minutes - clear_prediction.predicted_time_minutes)
                  / clear_prediction.predicted_time_minutes * 100)
        self.logger.info(f"✓ Test 7 Passed: Rain increases time by {impact:.1f}%")

    def test_weekend_lighter_than_weekday(self):
        """Test 8: Weekend traffic should be lighter than weekday"""
        route_name = 'High Level Road'
        hour = 10

        # Weekday
        weekday_request = PredictionRequest(
            route_name=route_name,
            day_type=DayType.WEEKDAY,
            hour=hour,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )
        weekday_prediction = self.traffic_service.predict_travel_time(weekday_request)

        # Weekend
        weekend_request = PredictionRequest(
            route_name=route_name,
            day_type=DayType.WEEKEND,
            hour=hour,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )
        weekend_prediction = self.traffic_service.predict_travel_time(weekend_request)

        self.assertLess(
            weekend_prediction.predicted_time_minutes,
            weekday_prediction.predicted_time_minutes,
            "Weekend should have lighter traffic"
        )

        self.logger.info(f"✓ Test 8 Passed: Weekend ({weekend_prediction.predicted_time_minutes} min) "
                         f"lighter than weekday ({weekday_prediction.predicted_time_minutes} min)")

    def test_route_comparison(self):
        """Test 9: Route comparison returns valid results"""
        request = PredictionRequest(
            route_name='',  # Compare all routes
            day_type=DayType.WEEKDAY,
            hour=8,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        comparison = self.traffic_service.compare_all_routes(request)

        self.assertIsNotNone(comparison)
        self.assertGreater(len(comparison.predictions), 0)
        self.assertIsNotNone(comparison.best_route)
        self.assertGreater(len(comparison.recommendations), 0)

        # Verify predictions are sorted
        times = [p.predicted_time_minutes for p in comparison.predictions]
        self.assertEqual(times, sorted(times), "Routes should be sorted by time")

        self.logger.info(f"✓ Test 9 Passed: Compared {len(comparison.predictions)} routes, "
                         f"best: {comparison.best_route}")

    def test_prediction_consistency(self):
        """Test 10: Multiple predictions with same parameters should be consistent"""
        request = PredictionRequest(
            route_name='High Level Road',
            day_type=DayType.WEEKDAY,
            hour=8,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        predictions = []
        for _ in range(5):
            prediction = self.traffic_service.predict_travel_time(request)
            predictions.append(prediction.predicted_time_minutes)

        # All predictions should be the same (deterministic)
        self.assertEqual(len(set(predictions)), 1,
                         f"Predictions should be consistent, got: {predictions}")

        self.logger.info(f"✓ Test 10 Passed: Predictions are consistent ({predictions[0]} min)")


class TestAdvancedPredictions(unittest.TestCase):
    """Test advanced prediction service"""

    @classmethod
    def setUpClass(cls):
        """Set up advanced prediction service"""
        cls.db_manager = DatabaseManager()
        cls.prediction_service = AdvancedPredictionService(cls.db_manager)
        cls.logger = get_logger(__name__)

    def test_multi_model_prediction(self):
        """Test 11: Multi-model prediction works"""
        request = PredictionRequest(
            route_name='High Level Road',
            day_type=DayType.WEEKDAY,
            hour=8,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        prediction = self.prediction_service.predict_with_multiple_models(request)

        self.assertIsNotNone(prediction)
        self.assertGreater(prediction.predicted_time_minutes, 0)
        self.assertGreater(len(prediction.factors_considered), 1)

        self.logger.info(f"✓ Test 11 Passed: Multi-model prediction = {prediction.predicted_time_minutes} min, "
                         f"using {len(prediction.factors_considered)} factors")

    def test_prediction_confidence(self):
        """Test 12: Confidence levels are reasonable"""
        request = PredictionRequest(
            route_name='High Level Road',
            day_type=DayType.WEEKDAY,
            hour=8,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        prediction = self.prediction_service.predict_with_multiple_models(request)

        self.assertGreaterEqual(prediction.confidence_level, 0.0)
        self.assertLessEqual(prediction.confidence_level, 1.0)
        self.assertGreater(prediction.confidence_level, 0.2, "Confidence too low")

        self.logger.info(f"✓ Test 12 Passed: Confidence level = {prediction.confidence_level:.2%}")


class TestDataQuality(unittest.TestCase):
    """Test data quality and integrity"""

    @classmethod
    def setUpClass(cls):
        """Set up database"""
        cls.db_manager = DatabaseManager()
        cls.logger = get_logger(__name__)

    def test_no_negative_times(self):
        """Test 13: No negative travel times in database"""
        routes = self.db_manager.get_all_routes()

        for route in routes[:10]:  # Check first 10 routes
            records = self.db_manager.get_traffic_records(route.name, days_back=30, limit=100)
            for record in records:
                self.assertGreater(record.travel_time_minutes, 0,
                                   f"Negative time found: {record.travel_time_minutes}")

        self.logger.info("✓ Test 13 Passed: No negative travel times found")

    def test_reasonable_time_ranges(self):
        """Test 14: Travel times are within reasonable ranges"""
        routes = self.db_manager.get_all_routes()

        for route in routes[:10]:
            records = self.db_manager.get_traffic_records(route.name, days_back=30, limit=100)
            for record in records:
                self.assertLess(record.travel_time_minutes, 300,
                                f"Unreasonably high time: {record.travel_time_minutes}")
                self.assertGreater(record.travel_time_minutes, 5,
                                   f"Unreasonably low time: {record.travel_time_minutes}")

        self.logger.info("✓ Test 14 Passed: All travel times within reasonable ranges (5-300 min)")

    def test_speed_calculations(self):
        """Test 15: Speed calculations are correct"""
        routes = self.db_manager.get_all_routes()

        for route in routes[:5]:
            records = self.db_manager.get_traffic_records(route.name, days_back=7, limit=10)
            for record in records:
                if record.distance_km > 0 and record.travel_time_minutes > 0:
                    expected_speed = (record.distance_km / (record.travel_time_minutes / 60))
                    self.assertAlmostEqual(record.average_speed_kmh, expected_speed, places=1,
                                           msg="Speed calculation incorrect")

        self.logger.info("✓ Test 15 Passed: Speed calculations are accurate")


class TestSystemPerformance(unittest.TestCase):
    """Test system performance"""

    @classmethod
    def setUpClass(cls):
        """Set up services"""
        cls.db_manager = DatabaseManager()
        cls.traffic_service = TrafficAnalysisService(cls.db_manager)
        cls.logger = get_logger(__name__)

    def test_prediction_speed(self):
        """Test 16: Predictions complete in reasonable time"""
        import time

        request = PredictionRequest(
            route_name='High Level Road',
            day_type=DayType.WEEKDAY,
            hour=8,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        start_time = time.time()
        prediction = self.traffic_service.predict_travel_time(request)
        elapsed = time.time() - start_time

        self.assertLess(elapsed, 2.0, f"Prediction too slow: {elapsed:.2f}s")

        self.logger.info(f"✓ Test 16 Passed: Prediction completed in {elapsed:.3f}s")

    def test_route_comparison_speed(self):
        """Test 17: Route comparison completes in reasonable time"""
        import time

        request = PredictionRequest(
            route_name='',
            day_type=DayType.WEEKDAY,
            hour=8,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        start_time = time.time()
        comparison = self.traffic_service.compare_all_routes(request)
        elapsed = time.time() - start_time

        self.assertLess(elapsed, 5.0, f"Comparison too slow: {elapsed:.2f}s")

        self.logger.info(f"✓ Test 17 Passed: Compared {len(comparison.predictions)} routes in {elapsed:.3f}s")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    @classmethod
    def setUpClass(cls):
        """Set up services"""
        cls.db_manager = DatabaseManager()
        cls.traffic_service = TrafficAnalysisService(cls.db_manager)
        cls.logger = get_logger(__name__)

    def test_midnight_hour(self):
        """Test 18: Midnight hour (0) works correctly"""
        request = PredictionRequest(
            route_name='High Level Road',
            day_type=DayType.WEEKDAY,
            hour=0,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        prediction = self.traffic_service.predict_travel_time(request)
        self.assertIsNotNone(prediction)
        self.assertGreater(prediction.predicted_time_minutes, 0)

        self.logger.info(f"✓ Test 18 Passed: Midnight prediction = {prediction.predicted_time_minutes} min")

    def test_late_night_hour(self):
        """Test 19: Late night hour (23) works correctly"""
        request = PredictionRequest(
            route_name='High Level Road',
            day_type=DayType.WEEKDAY,
            hour=23,
            weather_condition=WeatherCondition.CLEAR,
            season_type=SeasonType.REGULAR
        )

        prediction = self.traffic_service.predict_travel_time(request)
        self.assertIsNotNone(prediction)
        self.assertGreater(prediction.predicted_time_minutes, 0)

        self.logger.info(f"✓ Test 19 Passed: Late night prediction = {prediction.predicted_time_minutes} min")

    def test_all_weather_conditions(self):
        """Test 20: All weather conditions work"""
        weather_conditions = [WeatherCondition.CLEAR, WeatherCondition.CLOUDY,
                              WeatherCondition.RAINY, WeatherCondition.HEAVY_RAIN]

        for weather in weather_conditions:
            request = PredictionRequest(
                route_name='High Level Road',
                day_type=DayType.WEEKDAY,
                hour=10,
                weather_condition=weather,
                season_type=SeasonType.REGULAR
            )

            prediction = self.traffic_service.predict_travel_time(request)
            self.assertIsNotNone(prediction)
            self.assertGreater(prediction.predicted_time_minutes, 0)

        self.logger.info(f"✓ Test 20 Passed: All {len(weather_conditions)} weather conditions work")


def run_all_tests():
    """Run complete test suite with summary"""
    print("\n" + "=" * 70)
    print("TRAFFIC ANALYSIS SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestPredictionAccuracy))
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedPredictions))
    suite.addTests(loader.loadTestsFromTestCase(TestDataQuality))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
        print("System is ready for demonstration and submission.")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please review the failures above and fix the issues.")

    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)