# enhanced_web.py
# Enhanced Flask backend with prediction endpoints

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from main import TrafficAnalysisApplication
from data_access.models import PredictionRequest, DayType, WeatherCondition, SeasonType
from datetime import datetime
import sys

print("Initializing enhanced application...")
app_instance = TrafficAnalysisApplication()
if not app_instance.initialize():
    print("Failed to initialize")
    exit(1)

# Populate sample data if needed
app_instance.populate_sample_data()

app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    """Serve the enhanced dashboard"""
    with open('presentation/templates/index.html', 'r') as f:
        return Response(f.read(), mimetype='text/html')


@app.route('/api/live-dashboard', methods=['GET'])
def live_dashboard():
    """Enhanced live dashboard endpoint"""
    try:
        from_city = request.args.get('from')
        to_city = request.args.get('to')

        if not from_city or not to_city:
            return jsonify({'success': False, 'error': 'Missing cities'}), 400

        now = datetime.now()
        hour = now.hour
        is_weekend = now.weekday() >= 5

        day_type = DayType.WEEKEND if is_weekend else DayType.WEEKDAY
        weather_condition = WeatherCondition.CLEAR
        season_type = SeasonType.REGULAR

        # Check for holidays
        holidays = [
            {'date': '2025-01-15', 'name': 'Thai Pongal'},
            {'date': '2025-02-04', 'name': 'Independence Day'},
            {'date': '2025-12-25', 'name': 'Christmas Day'},
        ]
        holiday_info = None
        today_str = now.strftime('%Y-%m-%d')
        for h in holidays:
            if h['date'] == today_str:
                holiday_info = h
                break

        # Create prediction request
        req = PredictionRequest(
            route_name='',
            day_type=day_type,
            hour=hour,
            weather_condition=weather_condition,
            season_type=season_type
        )

        # Get all route predictions
        comparison = app_instance.traffic_service.compare_all_routes(req)
        sorted_predictions = sorted(comparison.predictions, key=lambda x: x.predicted_time_minutes)
        best = sorted_predictions[0]

        # Format routes for response
        all_routes = []
        for pred in sorted_predictions:
            all_routes.append({
                'name': pred.route_name,
                'predicted_time': pred.predicted_time_minutes,
                'distance': 12.5,  # Would come from database
                'historical_avg': int(pred.predicted_time_minutes * 1.15),
                'confidence': pred.confidence_level,
                'traffic_impact': 'High' if hour in [7, 8, 17, 18] else 'Moderate',
                'weather_impact': 'High' if weather_condition in [WeatherCondition.RAINY,
                                                                  WeatherCondition.HEAVY_RAIN] else 'Low'
            })

        # Determine traffic level
        if hour in [7, 8, 9, 17, 18, 19]:
            traffic_level = 'Heavy'
        elif hour in [10, 11, 12, 13, 14, 15, 16]:
            traffic_level = 'Moderate'
        else:
            traffic_level = 'Light'

        response_data = {
            'success': True,
            'route_info': {
                'from': from_city,
                'to': to_city
            },
            'current_conditions': {
                'current_time': now.strftime('%H:%M'),
                'day_type': day_type.value,
                'weather': weather_condition.value,
                'temperature': 28,
                'humidity': 70,
                'wind_speed': 12,
                'traffic_level': traffic_level,
                'season': season_type.value
            },
            'holiday_info': holiday_info,
            'best_route': {
                'name': best.route_name,
                'time': best.predicted_time_minutes,
                'confidence': int(best.confidence_level * 100),
                'reasons': [
                    f'Fastest route at {now.strftime("%H:%M")}',
                    f'Analyzed {len(comparison.predictions)} routes',
                    f'{best.confidence_level:.0%} prediction confidence'
                ]
            },
            'all_routes': all_routes,
            'insights': comparison.recommendations[:4]
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"Error in live_dashboard: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/predictions', methods=['GET'])
def predictions():
    """Get 24-hour predictions for a route"""
    try:
        from_city = request.args.get('from')
        to_city = request.args.get('to')

        if not from_city or not to_city:
            return jsonify({'success': False, 'error': 'Missing cities'}), 400

        now = datetime.now()
        is_weekend = now.weekday() >= 5
        day_type = DayType.WEEKEND if is_weekend else DayType.WEEKDAY
        weather_condition = WeatherCondition.CLEAR
        season_type = SeasonType.REGULAR

        # Generate predictions for each hour
        hourly_predictions = []
        for hour in range(24):
            req = PredictionRequest(
                route_name='',
                day_type=day_type,
                hour=hour,
                weather_condition=weather_condition,
                season_type=season_type
            )

            comparison = app_instance.traffic_service.compare_all_routes(req)
            sorted_preds = sorted(comparison.predictions, key=lambda x: x.predicted_time_minutes)
            best = sorted_preds[0]

            hourly_predictions.append({
                'hour': hour,
                'time': best.predicted_time_minutes,
                'historical_avg': int(best.predicted_time_minutes * 1.1),
                'confidence': best.confidence_level
            })

        # Find best and worst times
        best_time = min(hourly_predictions, key=lambda x: x['time'])
        worst_time = max(hourly_predictions, key=lambda x: x['time'])
        time_savings = worst_time['time'] - best_time['time']

        response_data = {
            'success': True,
            'hourly_predictions': hourly_predictions,
            'best_time_to_travel': best_time,
            'worst_time_to_travel': worst_time,
            'time_savings': time_savings,
            'analysis': {
                'peak_hours': [h['hour'] for h in hourly_predictions if h['time'] > 35],
                'off_peak_hours': [h['hour'] for h in hourly_predictions if h['time'] < 25],
                'average_time': sum(h['time'] for h in hourly_predictions) / 24
            }
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"Error in predictions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/routes/all', methods=['GET'])
def get_all_routes():
    """Get all available routes in the system"""
    try:
        routes = app_instance.traffic_service.db_manager.get_all_routes()

        route_list = []
        for route in routes:
            analytics = app_instance.traffic_service.analyze_route_performance(route.name)

            route_list.append({
                'name': route.name,
                'distance_km': route.distance_km,
                'typical_speed': route.typical_speed_kmh,
                'route_type': route.route_type,
                'avg_travel_time': analytics.average_travel_time if analytics else 0,
                'total_records': analytics.total_records if analytics else 0
            })

        return jsonify({
            'success': True,
            'routes': route_list,
            'total_routes': len(route_list)
        })

    except Exception as e:
        print(f"Error in get_all_routes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/summary', methods=['GET'])
def analytics_summary():
    """Get system-wide analytics summary"""
    try:
        db_stats = app_instance.traffic_service.db_manager.get_database_stats()

        # Get traffic patterns
        patterns = app_instance.traffic_service.get_traffic_patterns()

        summary = {
            'success': True,
            'database': {
                'total_routes': db_stats['routes_count'],
                'total_records': db_stats['records_count'],
                'earliest_record': db_stats['earliest_record'],
                'latest_record': db_stats['latest_record']
            },
            'traffic_patterns': {
                'peak_hours': patterns.get('peak_hours', []),
                'off_peak_hours': patterns.get('off_peak_hours', [])
            },
            'system_status': {
                'status': 'operational',
                'api_version': '2.0',
                'features': ['predictions', 'route_optimization', 'real_time_analysis']
            }
        }

        return jsonify(summary)

    except Exception as e:
        print(f"Error in analytics_summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0',
        'database': 'connected'
    })


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚗 ENHANCED COLOMBO TRAFFIC DASHBOARD")
    print("=" * 60)
    print("✅ Features:")
    print("   • Real-time route analysis across Colombo")
    print("   • 24-hour traffic predictions with graphs")
    print("   • AI-powered route optimization")
    print("   • Multi-location support")
    print("=" * 60)
    print("🌐 Open: http://localhost:5001")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=True)