# run_web.py
# Simple script to run the web interface

from main import TrafficAnalysisApplication
from presentation.web_controller import create_flask_app

if __name__ == "__main__":
    print("🚀 Starting Traffic Analyzer Web Interface...")
    print("=" * 60)

    # Initialize application
    app = TrafficAnalysisApplication()

    if app.initialize():
        # Generate sample data if needed
        app.populate_sample_data()

        # Create and run web app
        web_app = create_flask_app(app.traffic_service)

        print("\n✅ Web server starting...")
        print("=" * 60)
        print("📍 URL: http://localhost:5000")
        print("📍 API Docs: http://localhost:5000")
        print("=" * 60)
        print("\n💡 Press Ctrl+C to stop the server\n")

        web_app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("❌ Failed to initialize application")