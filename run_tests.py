#!/usr/bin/env python3
"""
Test runner script that sets up the proper Python path and runs tests.
"""

import sys
import os
import subprocess

# Add src to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')

# Set PYTHONPATH environment variable
env = os.environ.copy()
current_path = env.get('PYTHONPATH', '')
new_paths = [src_path]
if current_path:
    new_paths.append(current_path)
env['PYTHONPATH'] = os.pathsep.join(new_paths)

def run_tests():
    """Run all tests using pytest."""
    try:
        # Try to run with pytest first
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 'tests/', '-v'
        ], env=env, check=True)
        return result.returncode
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("pytest not available, running tests individually...")
        
        # Fallback to running tests individually
        test_files = [
            'tests/test_markdown_converter.py',
            'tests/test_integration.py',
            'tests/test_notion_operations.py',
            'tests/test_timestamp_enrichment.py',
            'tests/test_end_to_end_timestamps.py'
        ]
        
        for test_file in test_files:
            print(f"\n=== Running {test_file} ===")
            result = subprocess.run([sys.executable, test_file], env=env)
            if result.returncode != 0:
                return result.returncode
        
        return 0

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)