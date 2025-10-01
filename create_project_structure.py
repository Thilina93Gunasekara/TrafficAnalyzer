# create_project_structure.py
# Run this to create all missing folders and structure

import os


def create_project_structure():
    """Create all necessary folders for the project"""

    folders = [
        'outputs',
        'outputs/charts',
        'outputs/statistics',
        'outputs/reports',
        'outputs/test_results',
        'logs',
        'presentation',
        'presentation/templates',
        'utilities',
        'external_services',
        'database',
        'assignment_submission',
        'assignment_submission/code',
        'assignment_submission/outputs',
        'assignment_submission/documentation'
    ]

    print("Creating project structure...")
    print("=" * 50)

    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            print(f"✓ Created: {folder}/")
        else:
            print(f"  Exists: {folder}/")

    # Create empty __init__.py files where needed
    init_files = [
        'presentation/__init__.py',
        'utilities/__init__.py',
        'external_services/__init__.py'
    ]

    print("\nCreating __init__.py files...")
    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# Python package initialization\n')
            print(f"✓ Created: {init_file}")

    print("\n" + "=" * 50)
    print("✅ Project structure created successfully!")
    print("\nYou can now run:")
    print("  python3 generate_colombo_data.py")
    print("  python3 enhanced_web.py")


if __name__ == "__main__":
    create_project_structure()