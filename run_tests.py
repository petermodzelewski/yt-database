#!/usr/bin/env python3
"""
Unit test runner script that sets up the proper Python path and runs unit tests only.

Unit tests are fast, isolated tests that don't require external dependencies or API keys.
They use mock implementations and should complete in under 10 seconds.

Usage:
    python run_tests.py
"""

import sys
import os
import subprocess

# Add src to Python path (only path setup, no environment loading)
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')

# Set PYTHONPATH environment variable (minimal environment setup)
env = os.environ.copy()
current_path = env.get('PYTHONPATH', '')
new_paths = [src_path]
if current_path:
    new_paths.append(current_path)
env['PYTHONPATH'] = os.pathsep.join(new_paths)

def run_unit_tests():
    """Run unit tests only using pytest."""
    try:
        print("Running unit tests (fast, no external dependencies)...")
        cmd = [sys.executable, '-m', 'pytest', 'tests/unit/', '-v']
        result = subprocess.run(cmd, env=env, check=True)
        return result.returncode
    except subprocess.CalledProcessError:
        return 1
    except FileNotFoundError:
        print("Error: pytest not available. Please install pytest: pip install pytest")
        return 1

if __name__ == '__main__':
    exit_code = run_unit_tests()
    sys.exit(exit_code)