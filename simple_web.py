# simple_web.py
# Simple web server that definitely works

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from main import TrafficAnalysisApplication
from data_access.models import PredictionRequest, DayType, WeatherCondition, SeasonType

# Initialize application
print("🚀 Initializing application...")
app_instance = TrafficAnalysisApplication()
if not app_instance.initialize():
    print("❌ Failed to initialize")
    exit(1)

app_instance.populate_sample_data()

# Create Flask app
app = Flask(__name__)
CORS(app)

# HTML Template (embedded)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Traffic Analyzer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { color: #667eea; text-align: center; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #666; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
        select, input { 
            width: 100%; 
            padding: 12px; 
            border: 2px solid #ddd; 
            border-radius: 8px; 
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 20px;
        }
        button:hover { opacity: 0.9; }
        .results {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        .results.active { display: block; }
        .best-route {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .route-card {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .loading { text-align: center; padding: 20px; display: none; }
        .loading.active { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚗 Traffic Analyzer</h1>
        <p class="subtitle">Maharagama to Town Hall Route Optimization</p>

        <form id="trafficForm">
            <div class="form-group">
                <label>Select Route:</label>
                <select id="route" name="route">
                    <option value="">Compare All Routes</option>
                    <option value="High Level Road">High Level Road</option>
                    <option value="Low Level Road">Low Level Road</option>
                    <option value="Baseline Road">Baseline Road</option>
                    <option value="Galle Road">Galle Road</option>
                    <option value="Marine Drive">Marine Drive</option>
                    <option value="Other Roads">Other Roads</option>
                </select>
            </div>

            <div class="form-group">
                <label>Day Type:</label>
                <select id="dayType" name="dayType">
                    <option value="Week Day">Week Day</option>
                    <option value="Weekend Day">Weekend Day</option>
                    <option value="Raine Day">Rainy Day</option>
                </select>
            </div>

            <div class="form-group">
                <label>Hour (0-23):</label>
                <input type="number" id="hour" name="hour" min="0" max="23" value="8">
            </div>

            <div class="form-group">
                <label>Weather:</label>
                <select id="weather" name="weather">
                    <option value="Clear">Clear</option>
                    <option value="Cloudy">Cloudy</option>
                    <option value="Rainy">Rainy</option>
                    <option value="Heavy Rain">Heavy Rain</option>
                </select>
            </div>

            <div class="form-group">
                <label>Season:</label>
                <select id="season" name="season">
                    <option value="Regular Season">Regular Season</option>
                    <option value="School holidays">School Holidays</option>
                    <option value="Public Holiday">Public Holiday</option>
                </select>
            </div>

            <button type="submit">🔍 Analyze Traffic</button>
        </form>

        <div class="loading" id="loading">
            <p>⏳ Analyzing traffic patterns...</p>
        </div>

        <div class="results" id="results"></div>
    </div>

    <script>
        document.getElementById('trafficForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const route = document.getElementById('route').value;
            const dayType = document.getElementById('dayType').value;
            const hour = parseInt(document.getElementById('hour').value);
            const weather = document.getElementById('weather').value;
            const season = document.getElementById('season').value;

            document.getElementById('loading').classList.add('active');
            document.getElementById('results').classList.remove('active');

            const endpoint = route ? '/api/predict' : '/api/compare';

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        route_name: route,
                        day_type: dayType,
                        hour: hour,
                        weather_condition: weather,
                        season_type: season
                    })
                });

                const data = await response.json();

                document.getElementById('loading').classList.remove('active');

                if (data.success) {
                    displayResults(data, route !== '');
                } else {
                    alert('Error: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                document.getElementById('loading').classList.remove('active');
                alert('Failed to connect to server: ' + error);
            }
        });

        function displayResults(data, isSingle) {
            const resultsDiv = document.getElementById('results');

            if (isSingle) {
                const pred = data.prediction;
                resultsDiv.innerHTML = `
                    <div class="best-route">
                        <h2>${pred.route_name}</h2>
                        <h1>${pred.predicted_time_minutes} minutes</h1>
                        <p>Confidence: ${(pred.confidence_level * 100).toFixed(0)}%</p>
                    </div>
                `;
            } else {
                const sorted = data.predictions.sort((a, b) => a.predicted_time - b.predicted_time);
                const best = sorted[0];

                let html = `
                    <div class="best-route">
                        <h3>🏆 Best Route</h3>
                        <h2>${best.route_name}</h2>
                        <h1>${best.predicted_time} minutes</h1>
                    </div>
                    <h3>All Routes:</h3>
                `;

                sorted.forEach((route, idx) => {
                    const icon = idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : '📍';
                    html += `
                        <div class="route-card">
                            <strong>${icon} ${route.route_name}</strong>
                            <div style="float: right;">${route.predicted_time} min</div>
                        </div>
                    `;
                });

                resultsDiv.innerHTML = html;
            }

            resultsDiv.classList.add('active');
        }
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/predict', methods=['POST'])
def predict():
    """Predict travel time"""
    try:
        data = request.json

        req = PredictionRequest(
            route_name=data['route_name'],
            day_type=DayType(data['day_type']),
            hour=int(data['hour']),
            weather_condition=WeatherCondition(data['weather_condition']),
            season_type=SeasonType(data['season_type'])
        )

        prediction = app_instance.traffic_service.predict_travel_time(req)

        return jsonify({
            'success': True,
            'prediction': {
                'route_name': prediction.route_name,
                'predicted_time_minutes': prediction.predicted_time_minutes,
                'confidence_level': prediction.confidence_level,
                'factors_considered': prediction.factors_considered
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/compare', methods=['POST'])
def compare():
    """Compare all routes"""
    try:
        data = request.json

        req = PredictionRequest(
            route_name='',
            day_type=DayType(data['day_type']),
            hour=int(data['hour']),
            weather_condition=WeatherCondition(data['weather_condition']),
            season_type=SeasonType(data['season_type'])
        )

        comparison = app_instance.traffic_service.compare_all_routes(req)

        return jsonify({
            'success': True,
            'best_route': comparison.best_route,
            'predictions': [
                {
                    'route_name': p.route_name,
                    'predicted_time': p.predicted_time_minutes,
                    'confidence': p.confidence_level
                }
                for p in comparison.predictions
            ],
            'recommendations': comparison.recommendations
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🌐 Web Server Starting")
    print("=" * 60)
    print("📍 Open browser: http://localhost:5000")
    print("=" * 60)
    print("\nPress Ctrl+C to stop\n")

    app.run(host='0.0.0.0', port=5001, debug=True)