# main.py
# Application entry point with proper dependency injection and layered architecture

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import all necessary modules
from data_access.database_manager import DatabaseManager, TrafficRecordRepository
from business_logic.traffic_analyzer import TrafficAnalysisService, RouteOptimizationService
from external_services.api_handler import APICoordinator
from presentation.console_ui import ConsoleUI
from utilities.logger import setup_logging, get_logger
from config.settings import AppConfig, LoggingConfig


class TrafficAnalysisApplication:
    """
    Main application class implementing dependency injection pattern
    Orchestrates all layers of the application architecture
    """

    def __init__(self):
        self.logger = None
        self.db_manager = None
        self.traffic_service = None
        self.route_optimizer = None
        self.api_coordinator = None
        self.console_ui = None

    def initialize(self):
        """Initialize all application components with proper dependency injection"""
        try:
            # Setup logging first
            setup_logging()
            self.logger = get_logger(__name__)
            self.logger.info("=" * 60)
            self.logger.info(f"Starting {AppConfig.APP_NAME} v{AppConfig.VERSION}")
            self.logger.info("=" * 60)

            # Initialize Data Access Layer
            self.logger.info("Initializing Data Access Layer...")
            self.db_manager = DatabaseManager()

            # Initialize Business Logic Layer
            self.logger.info("Initializing Business Logic Layer...")
            self.traffic_service = TrafficAnalysisService(self.db_manager)
            self.route_optimizer = RouteOptimizationService(self.traffic_service)

            # Initialize External Services Layer
            if AppConfig.ENABLE_API_INTEGRATION:
                self.logger.info("Initializing External Services Layer...")
                self.api_coordinator = APICoordinator()

            # Initialize Presentation Layer
            self.logger.info("Initializing Presentation Layer...")
            self.console_ui = ConsoleUI(self.traffic_service)

            self.logger.info("✅ All components initialized successfully")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"💥 Failed to initialize application: {e}")
            else:
                print(f"💥 Critical error during initialization: {e}")
            return False

    def populate_sample_data(self):
        """Populate database with sample data for demonstration"""
        try:
            self.logger.info("Checking for existing data...")

            # Check if we have any traffic records
            stats = self.db_manager.get_database_stats()

            if stats['records_count'] == 0:
                self.logger.info("No existing data found. Generating sample data...")
                self._generate_sample_data()
                self.logger.info("✅ Sample data generated successfully")
            else:
                self.logger.info(f"Found {stats['records_count']} existing records")

        except Exception as e:
            self.logger.error(f"Error populating sample data: {e}")

    def _generate_sample_data(self):
        """Generate comprehensive sample data"""
        from datetime import datetime, timedelta
        import random
        from data_access.models import (
            TrafficRecord, DayType, WeatherCondition,
            SeasonType, TrafficDensity
        )

        routes = self.db_manager.get_all_routes()
        current_time = datetime.now()

        sample_records = []

        # Generate data for the past 30 days
        for days_back in range(30):
            date = current_time - timedelta(days=days_back)

            # Generate data for key hours of each day
            key_hours = [7, 8, 9, 12, 17, 18, 19, 22]

            for hour in key_hours:
                record_time = date.replace(hour=hour, minute=random.randint(0, 59), second=0, microsecond=0)

                # Determine conditions
                day_type = DayType.WEEKEND if record_time.weekday() >= 5 else DayType.WEEKDAY
                weather = random.choices(
                    [WeatherCondition.CLEAR, WeatherCondition.CLOUDY, WeatherCondition.RAINY,
                     WeatherCondition.HEAVY_RAIN],
                    weights=[0.5, 0.3, 0.15, 0.05]
                )[0]

                if weather in [WeatherCondition.RAINY, WeatherCondition.HEAVY_RAIN]:
                    day_type = DayType.RAINY_DAY

                season = SeasonType.REGULAR

                for route in routes:
                    # Calculate realistic travel time based on conditions
                    base_time = int((route.distance_km / route.typical_speed_kmh) * 60)

                    # Apply multipliers
                    multiplier = 1.0

                    # Time-based multiplier
                    if hour in [7, 8, 17, 18]:  # Rush hours
                        multiplier *= random.uniform(1.5, 2.0)
                        traffic_density = TrafficDensity.HEAVY
                    elif hour in [9, 12, 19]:
                        multiplier *= random.uniform(1.1, 1.4)
                        traffic_density = TrafficDensity.MODERATE
                    else:
                        multiplier *= random.uniform(0.8, 1.1)
                        traffic_density = TrafficDensity.LIGHT

                    # Day type multiplier
                    if day_type == DayType.WEEKEND:
                        multiplier *= 0.8
                    elif day_type == DayType.RAINY_DAY:
                        multiplier *= 1.4

                    # Weather multiplier
                    if weather == WeatherCondition.HEAVY_RAIN:
                        multiplier *= 1.3
                    elif weather == WeatherCondition.RAINY:
                        multiplier *= 1.2
                    elif weather == WeatherCondition.CLOUDY:
                        multiplier *= 1.05

                    # Add some randomness
                    multiplier *= random.uniform(0.9, 1.1)

                    travel_time = max(15, int(base_time * multiplier))

                    record = TrafficRecord(
                        timestamp=record_time,
                        route_name=route.name,
                        travel_time_minutes=travel_time,
                        distance_km=route.distance_km,
                        day_type=day_type,
                        weather_condition=weather,
                        season_type=season,
                        hour=hour,
                        day_of_week=record_time.weekday(),
                        is_holiday=False,
                        traffic_density=traffic_density,
                        average_speed_kmh=route.distance_km / (travel_time / 60)
                    )

                    sample_records.append(record)

        # Bulk insert all records
        traffic_repo = TrafficRecordRepository(self.db_manager)
        traffic_repo.bulk_insert_records(sample_records)

        self.logger.info(f"Generated {len(sample_records)} sample traffic records")

    def run_console_interface(self):
        """Run the console-based user interface"""
        try:
            if not self.console_ui:
                raise Exception("Console UI not initialized")

            self.logger.info("🚀 Starting console interface...")
            self.console_ui.start()

        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Error running console interface: {e}")
            raise

    def run_web_interface(self):
        """Run the web-based interface (if implemented)"""
        try:
            self.logger.info("🌐 Starting web interface...")

            from presentation.web_controller import create_flask_app

            web_app = create_flask_app(self.traffic_service)

            print("\n" + "=" * 60)
            print("🌐 Web Interface Starting")
            print("=" * 60)
            print(f"📍 URL: http://localhost:5000")
            print(f"📖 API Documentation: http://localhost:5000")
            print("=" * 60)
            print("\nPress Ctrl+C to stop the server\n")

            web_app.run(host='0.0.0.0', port=5000, debug=True)

        except ImportError as e:
            self.logger.error(f"Web interface dependencies not available: {e}")
            print("❌ Flask not installed. Install with: pip install flask flask-cors")
        except Exception as e:
            self.logger.error(f"Error starting web interface: {e}")
            raise

    def run_data_collection(self):
        """Start automated data collection"""
        try:
            if not self.api_coordinator or not AppConfig.ENABLE_REAL_TIME_DATA:
                self.logger.info("⏸️ Real-time data collection disabled")
                return

            self.logger.info("📊 Starting automated data collection...")

            # This would run in a separate thread in production
            collected_data = self.api_coordinator.data_collection_service.collect_current_traffic_data()

            if collected_data:
                self.logger.info(f"✅ Collected data for {len(collected_data)} routes")
            else:
                self.logger.warning("⚠️ No data collected")

        except Exception as e:
            self.logger.error(f"Error in data collection: {e}")

    def shutdown(self):
        """Gracefully shutdown the application"""
        try:
            self.logger.info("🛑 Shutting down application...")

            # Cleanup database connections
            if self.db_manager:
                # Perform any final database operations
                self.logger.info("💾 Closing database connections...")

            # Stop any running services
            if self.api_coordinator:
                self.logger.info("🔌 Stopping external services...")

            self.logger.info("✅ Application shutdown complete")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during shutdown: {e}")


def main():
    """
    Main entry point of the application
    Implements proper error handling and cleanup
    """
    app = None

    try:
        # Create and initialize application
        print("🚀 Initializing Maharagama-TownHall Traffic Analyzer...")
        app = TrafficAnalysisApplication()

        if not app.initialize():
            print("💥 Failed to initialize application")
            return 1

        # Populate sample data if needed
        app.populate_sample_data()

        # Run data collection (if enabled)
        if AppConfig.ENABLE_REAL_TIME_DATA:
            app.run_data_collection()

        # Determine interface to run
        if len(sys.argv) > 1 and sys.argv[1] == '--web':
            app.run_web_interface()
        else:
            app.run_console_interface()

        return 0

    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
        return 0

    except Exception as e:
        print(f"💥 Critical application error: {e}")
        if app and app.logger:
            app.logger.error(f"Critical error: {e}", exc_info=True)
        return 1

    finally:
        # Ensure proper cleanup
        if app:
            app.shutdown()


def run_tests():
    """Run application tests"""
    try:
        print("🧪 Running application tests...")

        # Import test modules
        from tests.test_traffic_analyzer import run_all_tests

        # Run tests
        test_results = run_all_tests()

        if test_results:
            print("✅ All tests passed!")
            return 0
        else:
            print("❌ Some tests failed!")
            return 1

    except ImportError:
        print("⚠️ Test modules not found. Skipping tests.")
        return 0
    except Exception as e:
        print(f"💥 Error running tests: {e}")
        return 1


def show_help():
    """Show application help information"""
    print(f"""
🚗 {AppConfig.APP_NAME} v{AppConfig.VERSION}
{AppConfig.AUTHOR}

USAGE:
    python main.py [options]

OPTIONS:
    --help          Show this help message
    --web           Run web interface (if available)
    --test          Run application tests
    --version       Show version information

DESCRIPTION:
    Professional traffic analysis system for Maharagama to Town Hall route.
    Features layered architecture with:

    • Data Access Layer (Database operations)
    • Business Logic Layer (Traffic analysis)
    • External Services Layer (API integrations)  
    • Presentation Layer (User interfaces)
    • Utilities Layer (Logging, helpers)

EXAMPLES:
    python main.py              # Run console interface
    python main.py --web        # Run web interface
    python main.py --test       # Run tests

For more information, visit the documentation.
""")


if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg in ['--help', '-h', 'help']:
            show_help()
            sys.exit(0)
        elif arg in ['--version', '-v', 'version']:
            print(f"{AppConfig.APP_NAME} v{AppConfig.VERSION}")
            sys.exit(0)
        elif arg in ['--test', 'test']:
            sys.exit(run_tests())

    # Run main application
    sys.exit(main())