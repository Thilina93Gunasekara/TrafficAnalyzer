# presentation/console_ui.py
# Console-based user interface for the traffic analysis system

import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from data_access.models import (
    PredictionRequest, PredictionResult, RouteComparison,
    DayType, WeatherCondition, SeasonType
)
from business_logic.traffic_analyzer import TrafficAnalysisService
from utilities.logger import get_logger
from config.settings import TrafficConfig


class ConsoleUI:
    """
    Console-based user interface for the traffic analysis system.
    Provides an interactive command-line interface for users.
    """

    def __init__(self, traffic_service: TrafficAnalysisService):
        self.traffic_service = traffic_service
        self.logger = get_logger(__name__)
        self.running = True

    def start(self):
        """Start the console application"""
        self.clear_screen()
        self.show_welcome()

        try:
            while self.running:
                self.show_main_menu()
                choice = self.get_user_input("Enter your choice (1-7): ").strip()

                if choice == '1':
                    self.find_best_route()
                elif choice == '2':
                    self.predict_specific_route()
                elif choice == '3':
                    self.compare_all_routes()
                elif choice == '4':
                    self.show_traffic_analytics()
                elif choice == '5':
                    self.show_route_optimization()
                elif choice == '6':
                    self.show_system_status()
                elif choice == '7':
                    self.exit_application()
                else:
                    self.show_error("Invalid choice. Please enter 1-7.")

                if self.running:
                    self.wait_for_continue()

        except KeyboardInterrupt:
            self.show_info("\nApplication interrupted by user")
        except Exception as e:
            self.show_error(f"Unexpected error: {e}")
            self.logger.error(f"Console UI error: {e}")
        finally:
            self.cleanup()

    def show_welcome(self):
        """Display welcome message"""
        print("=" * 70)
        print("COLOMBO TRAFFIC ANALYZER")
        print("=" * 70)
        print("Professional Traffic Analysis System")
        print("Version 1.0.0 - Layered Architecture Implementation")
        print("=" * 70)
        print("")

    def show_main_menu(self):
        """Display the main menu"""
        print("\nMAIN MENU")
        print("-" * 40)
        print("1. Find Best Route")
        print("2. Predict Specific Route Time")
        print("3. Compare All Routes")
        print("4. View Traffic Analytics")
        print("5. Route Optimization Tools")
        print("6. System Status")
        print("7. Exit")
        print("-" * 40)

    def find_best_route(self):
        """Handle best route finding workflow"""
        try:
            self.clear_screen()
            print("FIND BEST ROUTE")
            print("=" * 50)

            # Get user input for conditions
            request = self.get_prediction_request()
            if not request:
                return

            print("\nAnalyzing routes...")
            comparison = self.traffic_service.compare_all_routes(request)

            self.display_route_comparison(comparison)

        except Exception as e:
            self.show_error(f"Error finding best route: {e}")
            self.logger.error(f"Error in find_best_route: {e}")

    def predict_specific_route(self):
        """Handle specific route prediction"""
        try:
            self.clear_screen()
            print("PREDICT SPECIFIC ROUTE TIME")
            print("=" * 50)

            # Get route selection
            route_name = self.get_route_selection()
            if not route_name:
                return

            # Get conditions
            request = self.get_prediction_request()
            if not request:
                return

            # Update request with selected route
            request.route_name = route_name

            print(f"\nAnalyzing {route_name}...")
            prediction = self.traffic_service.predict_travel_time(request)

            self.display_single_prediction(prediction, request)

        except Exception as e:
            self.show_error(f"Error predicting route time: {e}")
            self.logger.error(f"Error in predict_specific_route: {e}")

    def compare_all_routes(self):
        """Handle route comparison"""
        try:
            self.clear_screen()
            print("COMPARE ALL ROUTES")
            print("=" * 50)

            request = self.get_prediction_request()
            if not request:
                return

            print("\nComparing all available routes...")
            comparison = self.traffic_service.compare_all_routes(request)

            self.display_detailed_comparison(comparison)

        except Exception as e:
            self.show_error(f"Error comparing routes: {e}")
            self.logger.error(f"Error in compare_all_routes: {e}")

    def show_traffic_analytics(self):
        """Display traffic analytics"""
        try:
            self.clear_screen()
            print("TRAFFIC ANALYTICS")
            print("=" * 50)

            print("Select analysis type:")
            print("1. Single Route Analytics")
            print("2. All Routes Overview")
            print("3. Traffic Patterns")

            choice = self.get_user_input("Enter choice (1-3): ").strip()

            if choice == '1':
                self.show_single_route_analytics()
            elif choice == '2':
                self.show_all_routes_analytics()
            elif choice == '3':
                self.show_traffic_patterns()
            else:
                self.show_error("Invalid choice")

        except Exception as e:
            self.show_error(f"Error showing analytics: {e}")
            self.logger.error(f"Error in show_traffic_analytics: {e}")

    def show_route_optimization(self):
        """Show route optimization tools"""
        try:
            self.clear_screen()
            print("ROUTE OPTIMIZATION TOOLS")
            print("=" * 50)

            print("Available tools:")
            print("1. Optimal Departure Time Calculator")
            print("2. Alternative Routes for Incidents")
            print("3. Travel Time Predictions")

            choice = self.get_user_input("Enter choice (1-3): ").strip()

            if choice == '1':
                self.show_departure_time_optimizer()
            elif choice == '2':
                self.show_incident_alternatives()
            elif choice == '3':
                self.show_prediction_analysis()
            else:
                self.show_error("Invalid choice")

        except Exception as e:
            self.show_error(f"Error in optimization tools: {e}")
            self.logger.error(f"Error in show_route_optimization: {e}")

    def show_system_status(self):
        """Display system status and statistics"""
        try:
            self.clear_screen()
            print("SYSTEM STATUS")
            print("=" * 50)

            # Get database statistics
            db_stats = self.traffic_service.db_manager.get_database_stats()

            print("DATABASE STATISTICS:")
            print(f"  Total Routes: {db_stats['routes_count']}")
            print(f"  Traffic Records: {db_stats['records_count']:,}")
            print(f"  Database Size: {db_stats['database_size_mb']:.2f} MB")
            print(f"  Earliest Record: {db_stats['earliest_record']}")
            print(f"  Latest Record: {db_stats['latest_record']}")

            print("\nAVAILABLE ROUTES:")
            routes = self.traffic_service.db_manager.get_all_routes()
            for route in routes:
                print(f"  {route.name} ({route.distance_km:.1f} km)")

            print("\nSYSTEM INFORMATION:")
            print(f"  Application: Colombo Traffic Analyzer")
            print(f"  Database Path: {db_stats['database_path']}")
            print(f"  System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            self.show_error(f"Error getting system status: {e}")
            self.logger.error(f"Error in show_system_status: {e}")

    def get_prediction_request(self) -> Optional[PredictionRequest]:
        """Get prediction request parameters from user"""
        try:
            print("\nEnter Trip Conditions:")
            print("-" * 30)

            # Get day type
            day_type = self.get_day_type_selection()
            if not day_type:
                return None

            # Get hour
            hour = self.get_hour_selection()
            if hour is None:
                return None

            # Get weather condition
            weather = self.get_weather_selection()
            if not weather:
                return None

            # Get season type
            season = self.get_season_selection()
            if not season:
                return None

            return PredictionRequest(
                route_name="",  # Will be set by calling method
                day_type=day_type,
                hour=hour,
                weather_condition=weather,
                season_type=season
            )

        except Exception as e:
            self.show_error(f"Error getting prediction request: {e}")
            return None

    def get_route_selection(self) -> Optional[str]:
        """Get route selection from user"""
        try:
            routes = TrafficConfig.DEFAULT_ROUTES

            print("\nAvailable Routes:")
            for i, route in enumerate(routes, 1):
                print(f"{i}. {route}")

            while True:
                choice = self.get_user_input(f"Select route (1-{len(routes)}): ").strip()

                try:
                    index = int(choice) - 1
                    if 0 <= index < len(routes):
                        return routes[index]
                    else:
                        self.show_error(f"Please enter a number between 1 and {len(routes)}")
                except ValueError:
                    self.show_error("Please enter a valid number")

        except Exception as e:
            self.show_error(f"Error in route selection: {e}")
            return None

    def get_day_type_selection(self) -> Optional[DayType]:
        """Get day type selection from user"""
        try:
            print("\nDay Type:")
            print("1. Week Day")
            print("2. Weekend Day")
            print("3. Rainy Day")

            choice = self.get_user_input("Select day type (1-3): ").strip()

            day_types = {
                '1': DayType.WEEKDAY,
                '2': DayType.WEEKEND,
                '3': DayType.RAINY_DAY
            }

            return day_types.get(choice)

        except Exception as e:
            self.show_error(f"Error in day type selection: {e}")
            return None

    def get_hour_selection(self) -> Optional[int]:
        """Get hour selection from user"""
        try:
            current_hour = datetime.now().hour

            hour_input = self.get_user_input(f"Enter hour (0-23, current: {current_hour}): ").strip()

            if not hour_input:  # Use current hour if empty
                return current_hour

            try:
                hour = int(hour_input)
                if 0 <= hour <= 23:
                    return hour
                else:
                    self.show_error("Hour must be between 0 and 23")
                    return None
            except ValueError:
                self.show_error("Please enter a valid hour number")
                return None

        except Exception as e:
            self.show_error(f"Error in hour selection: {e}")
            return None

    def get_weather_selection(self) -> Optional[WeatherCondition]:
        """Get weather condition selection from user"""
        try:
            print("\nWeather Condition:")
            print("1. Clear")
            print("2. Cloudy")
            print("3. Rainy")
            print("4. Heavy Rain")

            choice = self.get_user_input("Select weather (1-4): ").strip()

            weather_conditions = {
                '1': WeatherCondition.CLEAR,
                '2': WeatherCondition.CLOUDY,
                '3': WeatherCondition.RAINY,
                '4': WeatherCondition.HEAVY_RAIN
            }

            return weather_conditions.get(choice)

        except Exception as e:
            self.show_error(f"Error in weather selection: {e}")
            return None

    def get_season_selection(self) -> Optional[SeasonType]:
        """Get season type selection from user"""
        try:
            print("\nSeason Type:")
            print("1. Regular Season")
            print("2. School Holidays")
            print("3. Public Holiday")

            choice = self.get_user_input("Select season (1-3): ").strip()

            season_types = {
                '1': SeasonType.REGULAR,
                '2': SeasonType.SCHOOL_HOLIDAY,
                '3': SeasonType.PUBLIC_HOLIDAY
            }

            return season_types.get(choice)

        except Exception as e:
            self.show_error(f"Error in season selection: {e}")
            return None

    def display_route_comparison(self, comparison: RouteComparison):
        """Display route comparison results"""
        print("\nROUTE COMPARISON RESULTS")
        print("=" * 60)

        sorted_routes = comparison.get_sorted_routes()

        print("\nROUTE RANKINGS:")
        print("-" * 45)
        for i, prediction in enumerate(sorted_routes):
            rank = f"#{i+1}" if i < 3 else f"  {i+1}"
            confidence_pct = int(prediction.confidence_level * 100)

            print(f"{rank} {prediction.route_name:<25} : {prediction.predicted_time_minutes:2d} min ({confidence_pct}%)")

        print(f"\nBEST ROUTE: {comparison.best_route}")
        print(f"ESTIMATED TIME: {sorted_routes[0].predicted_time_minutes} minutes")

        if len(sorted_routes) > 1:
            time_saved = sorted_routes[1].predicted_time_minutes - sorted_routes[0].predicted_time_minutes
            print(f"TIME SAVED: {time_saved} minutes vs second best")

        print("\nRECOMMENDATIONS:")
        print("-" * 25)
        for rec in comparison.recommendations:
            print(f"  {rec}")

    def display_single_prediction(self, prediction: PredictionResult, request: PredictionRequest):
        """Display single route prediction"""
        print("\nPREDICTION RESULTS")
        print("=" * 50)

        print(f"\nROUTE: {prediction.route_name}")
        print(f"PREDICTED TIME: {prediction.predicted_time_minutes} minutes")
        print(f"CONFIDENCE: {prediction.confidence_level:.1%}")

        print(f"\nCONDITIONS ANALYZED:")
        print(f"  Day Type: {request.day_type.value}")
        print(f"  Time: {request.hour:02d}:00")
        print(f"  Weather: {request.weather_condition.value}")
        print(f"  Season: {request.season_type.value}")

        print(f"\nFACTORS CONSIDERED:")
        for factor in prediction.factors_considered:
            print(f"  {factor}")

    def display_detailed_comparison(self, comparison: RouteComparison):
        """Display detailed route comparison"""
        self.display_route_comparison(comparison)

        print("\nDETAILED ANALYSIS:")
        print("-" * 30)

        sorted_routes = comparison.get_sorted_routes()
        best_time = sorted_routes[0].predicted_time_minutes

        for prediction in sorted_routes:
            time_diff = prediction.predicted_time_minutes - best_time
            percentage_diff = (time_diff / best_time) * 100 if best_time > 0 else 0

            print(f"\n{prediction.route_name}:")
            print(f"   Time: {prediction.predicted_time_minutes} min (+{time_diff} min, +{percentage_diff:.1f}%)")
            print(f"   Confidence: {prediction.confidence_level:.1%}")
            print(f"   Factors: {len(prediction.factors_considered)} considered")

    def show_single_route_analytics(self):
        """Show analytics for a single route"""
        try:
            route_name = self.get_route_selection()
            if not route_name:
                return

            print(f"\nANALYTICS FOR {route_name}")
            print("=" * 50)

            analytics = self.traffic_service.analyze_route_performance(route_name)

            print(f"\nPERFORMANCE METRICS:")
            print(f"  Average Travel Time: {analytics.average_travel_time:.1f} minutes")
            print(f"  Range: {analytics.min_travel_time}-{analytics.max_travel_time} minutes")
            print(f"  Variability: {analytics.get_variability():.1f}%")
            print(f"  Data Points: {analytics.total_records:,} records")

            print(f"\nTIME-BASED ANALYSIS:")
            print(f"  Peak Hours Average: {analytics.peak_hour_average:.1f} minutes")
            print(f"  Off-Peak Average: {analytics.off_peak_average:.1f} minutes")
            print(f"  Weekend Average: {analytics.weekend_average:.1f} minutes")
            print(f"  Rainy Day Average: {analytics.rainy_day_average:.1f} minutes")

        except Exception as e:
            self.show_error(f"Error showing single route analytics: {e}")

    def show_all_routes_analytics(self):
        """Show overview analytics for all routes"""
        try:
            routes = TrafficConfig.DEFAULT_ROUTES

            print("\nALL ROUTES OVERVIEW")
            print("=" * 50)

            route_analytics = []
            for route in routes:
                analytics = self.traffic_service.analyze_route_performance(route)
                route_analytics.append(analytics)

            # Sort by average travel time
            route_analytics.sort(key=lambda x: x.average_travel_time)

            print("\nROUTES BY AVERAGE SPEED (FASTEST TO SLOWEST):")
            print("-" * 55)

            for i, analytics in enumerate(route_analytics):
                rank = f"#{i+1}"
                reliability = "High" if analytics.get_variability() < 20 else "Medium" if analytics.get_variability() < 40 else "Low"

                print(f"{rank} {analytics.route_name:<25} : {analytics.average_travel_time:5.1f} min (Reliability: {reliability})")
                print(f"    Range: {analytics.min_travel_time}-{analytics.max_travel_time} min, Records: {analytics.total_records:,}")

        except Exception as e:
            self.show_error(f"Error showing all routes analytics: {e}")

    def show_traffic_patterns(self):
        """Show traffic patterns analysis"""
        try:
            print("\nTRAFFIC PATTERNS ANALYSIS")
            print("=" * 50)

            patterns = self.traffic_service.get_traffic_patterns()

            print("\nPEAK HOURS IDENTIFICATION:")
            peak_hours = patterns.get('peak_hours', [])
            off_peak_hours = patterns.get('off_peak_hours', [])

            print(f"  Peak Hours: {', '.join(f'{h:02d}:00' for h in peak_hours)}")
            print(f"  Off-Peak Hours: {', '.join(f'{h:02d}:00' for h in off_peak_hours)}")

            hourly_patterns = patterns.get('hourly_patterns', {})
            if hourly_patterns:
                print(f"\nHOURLY TRAFFIC INTENSITY:")
                print("-" * 30)

                for hour in sorted(hourly_patterns.keys()):
                    avg_time = hourly_patterns[hour]
                    intensity = "High" if hour in peak_hours else "Medium" if avg_time > 30 else "Low"
                    bar_length = min(20, int(avg_time / 3))
                    bar = "#" * bar_length

                    print(f"{hour:2d}:00 | {bar:<20} | {avg_time:5.1f} min | {intensity}")

        except Exception as e:
            self.show_error(f"Error showing traffic patterns: {e}")

    def show_departure_time_optimizer(self):
        """Show departure time optimization tool"""
        try:
            print("\nDEPARTURE TIME OPTIMIZER")
            print("=" * 50)

            route_name = self.get_route_selection()
            if not route_name:
                return

            arrival_hour = self.get_user_input("Enter desired arrival hour (0-23): ").strip()
            try:
                arrival_hour = int(arrival_hour)
                if not 0 <= arrival_hour <= 23:
                    self.show_error("Invalid arrival hour")
                    return
            except ValueError:
                self.show_error("Please enter a valid hour")
                return

            day_type = self.get_day_type_selection()
            weather = self.get_weather_selection()

            if not day_type or not weather:
                return

            print(f"\nOptimizing departure time for {route_name}...")
            print(f"Target arrival: {arrival_hour:02d}:00")

            # Simple optimization logic
            best_departure_times = []

            for dep_hour in range(max(0, arrival_hour - 3), arrival_hour):
                request = PredictionRequest(route_name, day_type, dep_hour, weather, SeasonType.REGULAR)
                prediction = self.traffic_service.predict_travel_time(request)

                expected_arrival = dep_hour + (prediction.predicted_time_minutes / 60)
                buffer = arrival_hour - expected_arrival

                if 0.1 <= buffer <= 0.5:  # 6-30 minute buffer
                    best_departure_times.append({
                        'departure': f"{dep_hour:02d}:00",
                        'travel_time': prediction.predicted_time_minutes,
                        'buffer': buffer * 60,
                        'confidence': prediction.confidence_level
                    })

            if best_departure_times:
                print(f"\nOPTIMAL DEPARTURE TIMES:")
                print("-" * 40)
                for dep in sorted(best_departure_times, key=lambda x: x['buffer'], reverse=True):
                    print(f"  {dep['departure']} -> {dep['travel_time']} min -> {dep['buffer']:.0f} min buffer")
            else:
                print(f"\nNo optimal departure times found. Consider:")
                print(f"  Leaving earlier (before {arrival_hour - 2:02d}:00)")
                print(f"  Adjusting arrival time expectations")

        except Exception as e:
            self.show_error(f"Error in departure time optimizer: {e}")

    def show_incident_alternatives(self):
        """Show alternative routes for incidents"""
        try:
            print("\nINCIDENT ALTERNATIVE ROUTES")
            print("=" * 50)

            blocked_route = self.get_route_selection()
            if not blocked_route:
                return

            print(f"Route blocked: {blocked_route}")

            request = self.get_prediction_request()
            if not request:
                return

            print(f"\nFinding alternatives to {blocked_route}...")

            # Get comparison excluding blocked route
            all_comparison = self.traffic_service.compare_all_routes(request)
            alternatives = [p for p in all_comparison.predictions if p.route_name != blocked_route]

            if alternatives:
                alternatives.sort(key=lambda x: x.predicted_time_minutes)

                print(f"\nALTERNATIVE ROUTES:")
                print("-" * 35)

                for i, alt in enumerate(alternatives):
                    rank = f"#{i+1}"
                    print(f"{rank} {alt.route_name:<25} : {alt.predicted_time_minutes} min")

                print(f"\nINCIDENT RECOMMENDATIONS:")
                print(f"  Best Alternative: {alternatives[0].route_name}")
                print(f"  Expected Delay: +{alternatives[0].predicted_time_minutes - 25} min (compared to normal)")
                print(f"  Allow extra time for increased traffic")
                print(f"  Check real-time updates before departing")
            else:
                print("No alternative routes available")

        except Exception as e:
            self.show_error(f"Error showing incident alternatives: {e}")

    def show_prediction_analysis(self):
        """Show prediction analysis details"""
        try:
            print("\nPREDICTION ANALYSIS")
            print("=" * 50)

            request = self.get_prediction_request()
            if not request:
                return

            route_name = self.get_route_selection()
            if not route_name:
                return

            request.route_name = route_name

            print(f"\nDetailed prediction analysis for {route_name}...")

            prediction = self.traffic_service.predict_travel_time(request)

            print(f"\nPREDICTION BREAKDOWN:")
            print(f"  Route: {prediction.route_name}")
            print(f"  Predicted Time: {prediction.predicted_time_minutes} minutes")
            print(f"  Confidence Level: {prediction.confidence_level:.1%}")
            print(f"  Generated: {prediction.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

            print(f"\nANALYSIS FACTORS:")
            for i, factor in enumerate(prediction.factors_considered, 1):
                print(f"  {i}. {factor}")

            # Additional context
            route = self.traffic_service.db_manager.get_route(route_name)
            if route:
                print(f"\nROUTE INFORMATION:")
                print(f"  Distance: {route.distance_km:.1f} km")
                print(f"  Typical Speed: {route.typical_speed_kmh} km/h")
                print(f"  Route Type: {route.route_type}")

        except Exception as e:
            self.show_error(f"Error in prediction analysis: {e}")

    # Utility methods
    def clear_screen(self):
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def get_user_input(self, prompt: str) -> str:
        """Get user input with prompt"""
        try:
            return input(f"> {prompt}")
        except (EOFError, KeyboardInterrupt):
            print("\n")
            raise

    def wait_for_continue(self):
        """Wait for user to continue"""
        try:
            input("\nPress Enter to continue...")
        except (EOFError, KeyboardInterrupt):
            print("\n")
            self.running = False

    def show_info(self, message: str):
        """Show informational message"""
        print(f"INFO: {message}")

    def show_error(self, message: str):
        """Show error message"""
        print(f"ERROR: {message}")

    def show_success(self, message: str):
        """Show success message"""
        print(f"SUCCESS: {message}")

    def exit_application(self):
        """Handle application exit"""
        print("\nThank you for using the Traffic Analysis System!")
        print("Drive safely and have a great journey!")
        print("=" * 50)
        self.running = False

    def cleanup(self):
        """Cleanup resources before exit"""
        try:
            self.logger.info("Console UI shutting down")
        except:
            pass