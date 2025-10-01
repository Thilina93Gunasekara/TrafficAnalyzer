# cleanup_project.py
# Remove unnecessary/duplicate files and show clean structure

import os
import shutil


def cleanup_project():
    """Remove unnecessary files from the project"""

    print("=" * 70)
    print("PROJECT CLEANUP - REMOVING UNNECESSARY FILES")
    print("=" * 70)

    # Files to DELETE (test files, duplicates, old versions)
    files_to_delete = [
        'create_project_structure.py',  # Helper script, not needed
        'explore_database.py',  # One-time exploration
        'fix_project_structure.py',  # Helper script
        'prepare_assignment_submission.py',  # Will recreate later if needed
        'quick_stats.py',  # One-time stats
        'reorganize_project.py',  # Helper script
        'run_web.py',  # Duplicate of enhanced_web.py
        'simple_web.py',  # Old version, using enhanced_web.py
        'test_models.py',  # Old test file
        'test_weather.py',  # Old test file
        'view_database.py',  # One-time viewing
        'tests/test_traffic_analyzer.py',  # Old tests, using test_system.py
        'database/__init__.py'  # Not needed, database is not a package
    ]

    print("\nFiles to DELETE:")
    print("-" * 70)

    deleted_count = 0
    for file in files_to_delete:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"  Deleted: {file}")
                deleted_count += 1
            except Exception as e:
                print(f"  ERROR deleting {file}: {e}")
        else:
            print(f"  Not found: {file}")

    # Delete empty tests folder if it exists
    if os.path.exists('tests') and not os.listdir('tests'):
        shutil.rmtree('tests')
        print(f"  Deleted: tests/ (empty folder)")
        deleted_count += 1

    print(f"\nTotal deleted: {deleted_count} items")

    print("\n" + "=" * 70)
    print("FINAL CLEAN PROJECT STRUCTURE")
    print("=" * 70)
    print("""
TrafficAnalyzer/
│
├── business_logic/              # Core traffic analysis algorithms
│   ├── __init__.py
│   ├── prediction_service.py    # Advanced prediction models
│   ├── route_optimizer.py       # Route optimization algorithms
│   └── traffic_analyzer.py      # Main traffic analysis service
│
├── config/                      # Configuration settings
│   ├── __init__.py
│   └── settings.py              # System configuration
│
├── data/                        # Sample data files
│   └── sample_data.csv
│
├── data_access/                 # Database layer
│   ├── __init__.py
│   ├── database_manager.py      # Database operations
│   ├── models.py                # Data models
│   └── update_database.py       # Database schema updates
│
├── database/                    # SQLite database
│   └── traffic_data.db          # Main database file
│
├── external_services/           # External API integrations
│   ├── __init__.py
│   ├── api_handler.py           # API management
│   └── weather_service.py       # Weather integration
│
├── logs/                        # Application logs
│   └── traffic_analyzer.log
│
├── outputs/                     # Generated outputs
│   ├── charts/                  # Generated visualizations
│   ├── reports/                 # Analysis reports
│   ├── statistics/              # Statistical reports
│   └── test_results/            # Test outputs
│
├── presentation/                # User interfaces
│   ├── templates/
│   │   └── index.html           # Web dashboard template
│   ├── __init__.py
│   ├── console_ui.py            # Command-line interface
│   ├── visualization.py         # Chart generation
│   └── web_controller.py        # Web API controller
│
├── utilities/                   # Helper functions
│   ├── __init__.py
│   ├── helpers.py               # Utility functions
│   └── logger.py                # Logging configuration
│
├── .venv/                       # Virtual environment (hidden)
│
├── enhanced_visualization.py   # Generate charts for report
├── enhanced_web.py              # Main web server (USE THIS)
├── generate_colombo_data.py    # Generate sample data
├── main.py                      # Application entry point
├── statistical_analysis.py     # Generate statistics
├── test_system.py               # Comprehensive test suite
│
├── README.md                    # Project documentation
└── requirements.txt             # Python dependencies
    """)

    print("\n" + "=" * 70)
    print("ESSENTIAL FILES TO USE")
    print("=" * 70)
    print("""
Core Application:
  main.py                      - Main application

Data Generation:
  generate_colombo_data.py     - Generate 50,000+ sample records

Web Interface:
  enhanced_web.py              - Start web server (http://localhost:5001)

Analysis & Reports:
  statistical_analysis.py      - Generate statistics for report
  enhanced_visualization.py    - Generate 8 charts for report
  test_system.py               - Run 20 comprehensive tests
    """)

    print("\n" + "=" * 70)
    print("COMMANDS TO RUN")
    print("=" * 70)
    print("""
1. Generate Data (if not done):
   python3 generate_colombo_data.py

2. Run Tests:
   python3 test_system.py

3. Generate Statistics:
   python3 statistical_analysis.py

4. Generate Charts:
   python3 enhanced_visualization.py

5. Start Web Server:
   python3 enhanced_web.py
   Then open: http://localhost:5001

6. Run Console Interface (optional):
   python3 main.py
    """)

    print("\n" + "=" * 70)
    print("FILE COUNT SUMMARY")
    print("=" * 70)

    # Count files in each folder
    folders = [
        'business_logic',
        'config',
        'data_access',
        'external_services',
        'presentation',
        'utilities'
    ]

    total_py_files = 0
    for folder in folders:
        if os.path.exists(folder):
            py_files = [f for f in os.listdir(folder) if f.endswith('.py')]
            total_py_files += len(py_files)
            print(f"  {folder:<25} : {len(py_files)} Python files")

    # Root level Python files
    root_py_files = [f for f in os.listdir('.') if f.endswith('.py') and os.path.isfile(f)]
    total_py_files += len(root_py_files)
    print(f"  Root directory{' ' * 12} : {len(root_py_files)} Python files")

    print(f"\n  TOTAL: {total_py_files} Python files")

    print("\n" + "=" * 70)
    print("CLEANUP COMPLETE!")
    print("=" * 70)
    print("\nYour project is now clean and organized.")
    print("All unnecessary test files and duplicates have been removed.")
    print("\nRecommendation: Refresh PyCharm (File → Synchronize)")


if __name__ == "__main__":
    # Show warning first
    print("\n" + "=" * 70)
    print("WARNING: This will DELETE files")
    print("=" * 70)
    print("\nThe following will be deleted:")
    print("  - Old test files (test_models.py, test_weather.py)")
    print("  - Helper scripts (create_project_structure.py, etc.)")
    print("  - Duplicate files (simple_web.py, run_web.py)")
    print("  - One-time scripts (explore_database.py, view_database.py)")

    response = input("\nContinue? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        cleanup_project()
    else:
        print("\nCleanup cancelled. No files were deleted.")