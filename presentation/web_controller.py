# presentation/web_controller.py
# Flask web controllers for REST API endpoints

# presentation/web_controller.py
# Flask web controllers for REST API endpoints

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from typing import Dict, Any
from datetime import datetime
import sys
import os

# Add parent directory to path if needed
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from business_logic.traffic_analyzer import TrafficAnalysisService
from business_logic.route_optimizer import AdvancedRouteOptimizer
from data_access.models import (
    PredictionRequest, DayType, WeatherCondition, SeasonType
)
from utilities.logger import get_logger
from utilities.helpers import format_time_minutes, format_distance_km


class WebController:
    """
    Web controller for handling HTTP requests and responses
    """

    def __init__(self, app: Flask, traffic_service: TrafficAnalysisService):
        self.app = app
        self.traffic_service = traffic_service
        self.route_optimizer = AdvancedRouteOptimizer(traffic_service)
        self.logger = get_logger(__name__)

        # Enable CORS
        CORS(app)

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all API endpoints"""

        @self.app.route('/')
        def index():
            """Main page"""
            return self._render_main_page()

        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })

        @self.app.route('/api/routes', methods=['GET'])
        def get_routes():
            """Get all available routes"""
            try:
                routes = self.traffic_service.db_manager.get_all_routes()
                return jsonify({
                    'success': True,
                    'routes': [{
                        'name': route.name,
                        'distance_km': route.distance_km,
                        'typical_speed_kmh': route.typical_speed_kmh,
                        'route_type': route.route_type
                    } for route in routes]
                })
            except Exception as e:
                self.logger.error(f"Error getting routes: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/predict', methods=['POST'])
        def predict_route():
            """Predict travel time for a specific route"""
            try:
                data = request.get_json()

                request_obj = PredictionRequest(
                    route_name=data['route_name'],
                    day_type=DayType(data['day_type']),
                    hour=int(data['hour']),
                    weather_condition=WeatherCondition(data['weather_condition']),
                    season_type=SeasonType(data.get('season_type', 'Regular Season'))
                )

                prediction = self.traffic_service.predict_travel_time(request_obj)

                return jsonify({
                    'success': True,
                    'prediction': {
                        'route_name': prediction.route_name,
                        'predicted_time_minutes': prediction.predicted_time_minutes,
                        'predicted_time_formatted': format_time_minutes(prediction.predicted_time_minutes),
                        'confidence_level': prediction.confidence_level,
                        'factors_considered': prediction.factors_considered,
                        'timestamp': prediction.timestamp.isoformat()
                    }
                })
            except Exception as e:
                self.logger.error(f"Error in prediction: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/compare', methods=['POST'])
        def compare_routes():
            """Compare all routes for given conditions"""
            try:
                data = request.get_json()

                request_obj = PredictionRequest(
                    route_name='',  # Will compare all
                    day_type=DayType(data['day_type']),
                    hour=int(data['hour']),
                    weather_condition=WeatherCondition(data['weather_condition']),
                    season_type=SeasonType(data.get('season_type', 'Regular Season'))
                )

                comparison = self.traffic_service.compare_all_routes(request_obj)

                return jsonify({
                    'success': True,
                    'best_route': comparison.best_route,
                    'predictions': [{
                        'route_name': pred.route_name,
                        'predicted_time': pred.predicted_time_minutes,
                        'confidence': pred.confidence_level
                    } for pred in comparison.predictions],
                    'recommendations': comparison.recommendations
                })
            except Exception as e:
                self.logger.error(f"Error in comparison: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/analytics/<route_name>', methods=['GET'])
        def get_analytics(route_name):
            """Get analytics for a specific route"""
            try:
                analytics = self.traffic_service.analyze_route_performance(route_name)

                return jsonify({
                    'success': True,
                    'analytics': {
                        'route_name': analytics.route_name,
                        'average_travel_time': analytics.average_travel_time,
                        'min_travel_time': analytics.min_travel_time,
                        'max_travel_time': analytics.max_travel_time,
                        'peak_hour_average': analytics.peak_hour_average,
                        'off_peak_average': analytics.off_peak_average,
                        'weekend_average': analytics.weekend_average,
                        'rainy_day_average': analytics.rainy_day_average,
                        'total_records': analytics.total_records,
                        'variability': analytics.get_variability()
                    }
                })
            except Exception as e:
                self.logger.error(f"Error getting analytics: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/optimize/departure', methods=['POST'])
        def optimize_departure():
            """Optimize departure time"""
            try:
                data = request.get_json()

                conditions = PredictionRequest(
                    route_name=data['route_name'],
                    day_type=DayType(data['day_type']),
                    hour=0,  # Will be calculated
                    weather_condition=WeatherCondition(data['weather_condition']),
                    season_type=SeasonType(data.get('season_type', 'Regular Season'))
                )

                optimization = self.route_optimizer.optimize_departure_time_window(
                    route_name=data['route_name'],
                    target_arrival=int(data['target_arrival_hour']),
                    conditions=conditions,
                    window_minutes=int(data.get('window_minutes', 60))
                )

                return jsonify({
                    'success': True,
                    'optimal_departure_time': optimization.optimal_departure_time,
                    'arrival_time': optimization.arrival_time,
                    'travel_time': optimization.travel_time,
                    'buffer_minutes': optimization.buffer_minutes,
                    'alternatives': optimization.alternatives
                })
            except Exception as e:
                self.logger.error(f"Error in departure optimization: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

    def _render_main_page(self) -> str:
        """Render main HTML page"""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Maharagama-TownHall Traffic Analyzer</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    padding: 40px;
                }
                h1 {
                    color: #667eea;
                    text-align: center;
                    margin-bottom: 10px;
                    font-size: 2.5em;
                }
                .subtitle {
                    text-align: center;
                    color: #666;
                    margin-bottom: 40px;
                    font-size: 1.1em;
                }
                .api-section {
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                }
                .api-section h2 {
                    color: #764ba2;
                    margin-bottom: 20px;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 10px;
                }
                .endpoint {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 15px;
                    border-left: 4px solid #667eea;
                }
                .endpoint-method {
                    display: inline-block;
                    padding: 5px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 0.9em;
                    margin-right: 10px;
                }
                .get { background: #28a745; color: white; }
                .post { background: #007bff; color: white; }
                .endpoint-path {
                    font-family: 'Courier New', monospace;
                    font-size: 1.1em;
                    color: #333;
                }
                .endpoint-desc {
                    margin-top: 10px;
                    color: #666;
                    line-height: 1.6;
                }
                .features {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-top: 30px;
                }
                .feature-card {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 25px;
                    border-radius: 10px;
                    color: white;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                }
                .feature-card h3 {
                    margin-bottom: 10px;
                    font-size: 1.3em;
                }
                .feature-card p {
                    font-size: 0.95em;
                    line-height: 1.5;
                }
                .footer {
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 2px solid #eee;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚗 Maharagama to Town Hall Traffic Analyzer</h1>
                <p class="subtitle">Professional Traffic Analysis System with RESTful API</p>

                <div class="api-section">
                    <h2>📡 API Endpoints</h2>

                    <div class="endpoint">
                        <span class="endpoint-method get">GET</span>
                        <span class="endpoint-path">/api/health</span>
                        <div class="endpoint-desc">Check API health status</div>
                    </div>

                    <div class="endpoint">
                        <span class="endpoint-method get">GET</span>
                        <span class="endpoint-path">/api/routes</span>
                        <div class="endpoint-desc">Get all available routes with details</div>
                    </div>

                    <div class="endpoint">
                        <span class="endpoint-method post">POST</span>
                        <span class="endpoint-path">/api/predict</span>
                        <div class="endpoint-desc">Predict travel time for specific conditions</div>
                    </div>

                    <div class="endpoint">
                        <span class="endpoint-method post">POST</span>
                        <span class="endpoint-path">/api/compare</span>
                        <div class="endpoint-desc">Compare all routes and get recommendations</div>
                    </div>

                    <div class="endpoint">
                        <span class="endpoint-method get">GET</span>
                        <span class="endpoint-path">/api/analytics/:route_name</span>
                        <div class="endpoint-desc">Get detailed analytics for a specific route</div>
                    </div>

                    <div class="endpoint">
                        <span class="endpoint-method post">POST</span>
                        <span class="endpoint-path">/api/optimize/departure</span>
                        <div class="endpoint-desc">Optimize departure time for target arrival</div>
                    </div>
                </div>

                <div class="api-section">
                    <h2>✨ Key Features</h2>
                    <div class="features">
                        <div class="feature-card">
                            <h3>🎯 Smart Predictions</h3>
                            <p>Multi-model ensemble predictions using historical data and statistical analysis</p>
                        </div>
                        <div class="feature-card">
                            <h3>📊 Analytics Dashboard</h3>
                            <p>Comprehensive traffic analytics with patterns, trends, and insights</p>
                        </div>
                        <div class="feature-card">
                            <h3>🔧 Route Optimization</h3>
                            <p>Advanced algorithms for optimal route selection and departure timing</p>
                        </div>
                        <div class="feature-card">
                            <h3>🌦️ Weather Integration</h3>
                            <p>Real-time weather data with impact analysis on travel times</p>
                        </div>
                    </div>
                </div>

                <div class="footer">
                    <p>🏗️ Built with Layered Architecture | 🐍 Python | 📈 Data-Driven</p>
                    <p>Version 1.0.0 - Maharagama to Town Hall Traffic Analysis System</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html


def create_flask_app(traffic_service: TrafficAnalysisService) -> Flask:
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False

    # Initialize web controller
    controller = WebController(app, traffic_service)

    return app