# reorganize_project.py
# Clean up and create proper project structure

import os
import shutil


def create_proper_structure():
    """Create the correct project structure"""

    print("=" * 70)
    print("REORGANIZING PROJECT STRUCTURE")
    print("=" * 70)

    # Define the correct structure
    folders_to_create = [
        'business_logic',
        'config',
        'data',
        'data_access',
        'database',
        'external_services',
        'logs',
        'outputs',
        'outputs/charts',
        'outputs/statistics',
        'outputs/reports',
        'outputs/test_results',
        'presentation',
        'presentation/templates',
        'utilities'
    ]

    print("\nStep 1: Creating folder structure...")
    print("-" * 70)

    for folder in folders_to_create:
        os.makedirs(folder, exist_ok=True)
        print(f"  Created/Verified: {folder}/")

    print("\nStep 2: Creating __init__.py files...")
    print("-" * 70)

    packages = [
        'business_logic',
        'config',
        'data_access',
        'external_services',
        'presentation',
        'utilities'
    ]

    for package in packages:
        init_file = os.path.join(package, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write(f'# {package.replace("_", " ").title()} Package\n')
            print(f"  Created: {init_file}")
        else:
            print(f"  Exists: {init_file}")

    print("\nStep 3: Checking required files in each folder...")
    print("-" * 70)

    # Check what's in utilities
    utilities_files = ['__init__.py', 'helpers.py', 'logger.py']
    print("\nUtilities folder should contain:")
    for file in utilities_files:
        filepath = os.path.join('utilities', file)
        exists = os.path.exists(filepath)
        status = "EXISTS" if exists else "MISSING - NEEDS TO BE CREATED"
        print(f"  {file}: {status}")

    # Check business_logic
    business_logic_files = ['__init__.py', 'traffic_analyzer.py', 'prediction_service.py', 'route_optimizer.py']
    print("\nBusiness Logic folder should contain:")
    for file in business_logic_files:
        filepath = os.path.join('business_logic', file)
        exists = os.path.exists(filepath)
        status = "EXISTS" if exists else "MISSING"
        print(f"  {file}: {status}")

    # Check data_access
    data_access_files = ['__init__.py', 'database_manager.py', 'models.py']
    print("\nData Access folder should contain:")
    for file in data_access_files:
        filepath = os.path.join('data_access', file)
        exists = os.path.exists(filepath)
        status = "EXISTS" if exists else "MISSING"
        print(f"  {file}: {status}")

    # Check config
    config_files = ['__init__.py', 'settings.py']
    print("\nConfig folder should contain:")
    for file in config_files:
        filepath = os.path.join('config', file)
        exists = os.path.exists(filepath)
        status = "EXISTS" if exists else "MISSING"
        print(f"  {file}: {status}")

    # Check external_services
    external_files = ['__init__.py', 'weather_service.py', 'api_handler.py']
    print("\nExternal Services folder should contain:")
    for file in external_files:
        filepath = os.path.join('external_services', file)
        exists = os.path.exists(filepath)
        status = "EXISTS" if exists else "MISSING"
        print(f"  {file}: {status}")

    # Check presentation
    presentation_files = ['__init__.py', 'console_ui.py', 'web_controller.py', 'visualization.py']
    print("\nPresentation folder should contain:")
    for file in presentation_files:
        filepath = os.path.join('presentation', file)
        exists = os.path.exists(filepath)
        status = "EXISTS" if exists else "MISSING"
        print(f"  {file}: {status}")

    print("\n" + "=" * 70)
    print("FINAL PROJECT STRUCTURE:")
    print("=" * 70)
    print("""
TrafficAnalyzer/
├── .venv/                          (Python virtual environment)
├── business_logic/
│   ├── __init__.py
│   ├── prediction_service.py
│   ├── route_optimizer.py
│   └── traffic_analyzer.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── data/
│   └── sample_data.csv
├── data_access/
│   ├── __init__.py
│   ├── database_manager.py
│   ├── models.py
│   └── update_database.py
├── database/
│   └── traffic_data.db
├── external_services/
│   ├── __init__.py
│   ├── api_handler.py
│   └── weather_service.py
├── logs/
│   └── traffic_analyzer.log
├── outputs/
│   ├── charts/
│   ├── reports/
│   ├── statistics/
│   └── test_results/
├── presentation/
│   ├── templates/
│   │   └── index.html
│   ├── __init__.py
│   ├── console_ui.py
│   ├── visualization.py
│   └── web_controller.py
├── utilities/
│   ├── __init__.py
│   ├── helpers.py
│   └── logger.py
├── create_project_structure.py
├── enhanced_visualization.py
├── enhanced_web.py
├── fix_project_structure.py
├── generate_colombo_data.py
├── main.py
├── README.md
├── statistical_analysis.py
└── test_system.py
    """)

    print("=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("""
1. Close PyCharm completely (Cmd+Q)
2. Delete .idea folder:
   rm -rf .idea/
3. Reopen PyCharm
4. Wait for indexing to complete (1-2 minutes)
5. All folders should now be visible

If utilities folder still doesn't show:
- Right-click on TrafficAnalyzer (project root)
- Select "Reload from Disk"
    """)


def verify_utilities():
    """Specifically verify utilities folder"""
    print("\n" + "=" * 70)
    print("UTILITIES FOLDER DETAILED CHECK")
    print("=" * 70)

    if os.path.exists('utilities'):
        print("\nStatus: utilities/ EXISTS in filesystem")

        # List all files
        files = os.listdir('utilities')
        print(f"\nFiles found ({len(files)}):")
        for f in files:
            print(f"  - {f}")

        # Check if Python can import it
        try:
            import sys
            if os.path.abspath('.') not in sys.path:
                sys.path.insert(0, os.path.abspath('.'))

            import utilities
            print("\nPython Import Test: SUCCESS")
            print(f"  utilities package location: {utilities.__file__}")

            # Try importing helpers
            try:
                from utilities import helpers
                print("  utilities.helpers import: SUCCESS")
            except ImportError as e:
                print(f"  utilities.helpers import: FAILED - {e}")

            # Try importing logger
            try:
                from utilities import logger
                print("  utilities.logger import: SUCCESS")
            except ImportError as e:
                print(f"  utilities.logger import: FAILED - {e}")

        except ImportError as e:
            print(f"\nPython Import Test: FAILED - {e}")
    else:
        print("\nStatus: utilities/ DOES NOT EXIST")
        print("Creating utilities folder now...")
        os.makedirs('utilities', exist_ok=True)
        with open('utilities/__init__.py', 'w') as f:
            f.write('# Utilities package\n')
        print("Created: utilities/ with __init__.py")


if __name__ == "__main__":
    create_proper_structure()
    verify_utilities()

    print("\n" + "=" * 70)
    print("DONE!")
    print("=" * 70)
    print("\nNow close PyCharm and run:")
    print("  rm -rf .idea/")
    print("\nThen reopen PyCharm.")