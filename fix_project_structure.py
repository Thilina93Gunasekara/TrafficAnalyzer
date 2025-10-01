# fix_project_structure.py
# Diagnose and fix PyCharm project structure issues

import os
import shutil


def diagnose_project():
    """Check what exists and what's missing"""
    print("=" * 70)
    print("PROJECT STRUCTURE DIAGNOSTIC")
    print("=" * 70)

    # Check critical folders
    folders_to_check = [
        'data_access',
        'business_logic',
        'config',
        'utilities',
        'external_services',
        'presentation',
        'database',
        'logs',
        'outputs'
    ]

    print("\nFolder Status:")
    print("-" * 70)
    for folder in folders_to_check:
        exists = os.path.exists(folder)
        status = "EXISTS" if exists else "MISSING"
        print(f"  {folder:<25} : {status}")

        if exists:
            # List files in folder
            files = os.listdir(folder)
            py_files = [f for f in files if f.endswith('.py')]
            if py_files:
                print(f"    Python files: {', '.join(py_files)}")

    # Check for .idea folder (PyCharm settings)
    print("\nPyCharm Configuration:")
    print("-" * 70)
    if os.path.exists('.idea'):
        print("  .idea folder: EXISTS")
        if os.path.exists('.idea/workspace.xml'):
            print("  workspace.xml: EXISTS")
    else:
        print("  .idea folder: NOT FOUND")

    # Check if utilities has __init__.py
    print("\nPackage Initialization Files:")
    print("-" * 70)
    for folder in folders_to_check:
        if os.path.exists(folder):
            init_file = os.path.join(folder, '__init__.py')
            exists = os.path.exists(init_file)
            print(f"  {folder}/__init__.py : {'EXISTS' if exists else 'MISSING'}")

    print("\n" + "=" * 70)


def fix_missing_init_files():
    """Ensure all Python packages have __init__.py"""
    print("\nFixing missing __init__.py files...")

    folders = [
        'data_access',
        'business_logic',
        'config',
        'utilities',
        'external_services',
        'presentation'
    ]

    for folder in folders:
        if os.path.exists(folder):
            init_file = os.path.join(folder, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('# Package initialization\n')
                print(f"  Created: {init_file}")
            else:
                print(f"  Exists: {init_file}")


def remove_problematic_folders():
    """Remove folders that might be causing issues"""
    print("\nChecking for problematic folders...")

    # assignment_submission might be confusing PyCharm
    if os.path.exists('assignment_submission'):
        response = input("\nFound 'assignment_submission' folder. Remove it? (y/n): ")
        if response.lower() == 'y':
            shutil.rmtree('assignment_submission')
            print("  Removed: assignment_submission/")
        else:
            print("  Kept: assignment_submission/")


def create_pycharm_config():
    """Create/fix PyCharm configuration"""
    print("\nPyCharm Configuration:")

    if os.path.exists('.idea'):
        print("  .idea folder exists")
        print("\nRecommendation:")
        print("  1. Close PyCharm")
        print("  2. Delete .idea folder: rm -rf .idea/")
        print("  3. Reopen project in PyCharm")
        print("\nThis will force PyCharm to rescan everything.")
    else:
        print("  No .idea folder found")
        print("  Project will be indexed when opened in PyCharm")


def verify_utilities_folder():
    """Specifically check utilities folder"""
    print("\n" + "=" * 70)
    print("UTILITIES FOLDER VERIFICATION")
    print("=" * 70)

    if os.path.exists('utilities'):
        print("\nutilities/ folder EXISTS")
        files = os.listdir('utilities')
        print(f"\nContents ({len(files)} items):")
        for f in sorted(files):
            filepath = os.path.join('utilities', f)
            size = os.path.getsize(filepath)
            print(f"  {f:<30} ({size:>8} bytes)")

        # Check if it's a proper Python package
        if '__init__.py' in files:
            print("\n  Status: Proper Python package")
        else:
            print("\n  WARNING: Missing __init__.py")
            print("  Creating it now...")
            with open('utilities/__init__.py', 'w') as f:
                f.write('# Utilities package\n')
            print("  Created: utilities/__init__.py")
    else:
        print("\nERROR: utilities/ folder does NOT exist!")
        print("Creating it now...")
        os.makedirs('utilities', exist_ok=True)
        print("Created: utilities/")


def main():
    """Run all diagnostics and fixes"""
    print("\n" + "=" * 70)
    print("PROJECT STRUCTURE FIX TOOL")
    print("=" * 70)

    # Step 1: Diagnose
    diagnose_project()

    # Step 2: Fix init files
    fix_missing_init_files()

    # Step 3: Verify utilities specifically
    verify_utilities_folder()

    # Step 4: Check for problematic folders
    remove_problematic_folders()

    # Step 5: PyCharm config advice
    create_pycharm_config()

    print("\n" + "=" * 70)
    print("RECOMMENDATIONS:")
    print("=" * 70)
    print("""
1. Close PyCharm completely
2. Run this command:
   rm -rf .idea/
3. Reopen your project in PyCharm
4. PyCharm will rebuild its index - this may take 1-2 minutes
5. Your utilities folder should now be visible

If still not visible:
- Right-click project root in PyCharm
- Select "Reload from Disk"
- Or go to: File → Invalidate Caches → Invalidate and Restart
    """)
    print("=" * 70)


if __name__ == "__main__":
    main()