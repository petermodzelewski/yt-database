#!/usr/bin/env python3
"""
Integration test runner script that sets up the proper Python path and runs integration tests only.

Integration tests require external dependencies (API keys, test database) and use the .env-test configuration.
They test real API interactions and may take longer to complete.

Usage:
    python run_integration_tests.py
"""

import sys
import os
import subprocess
from pathlib import Path

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

def load_test_env():
    """Load .env-test file for integration tests."""
    env_test_path = Path(project_root) / '.env-test'
    
    if not env_test_path.exists():
        print("Warning: .env-test file not found. Integration tests may fail without proper configuration.")
        print("Please copy .env.example to .env-test and configure it for testing.")
        return
    
    # Load .env-test variables into environment
    try:
        with open(env_test_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip().strip('"').strip("'")
        print(f"Loaded test configuration from {env_test_path}")
    except Exception as e:
        print(f"Warning: Could not load .env-test file: {e}")

def run_integration_tests():
    """Run integration tests only using pytest."""
    try:
        # Load test environment configuration
        load_test_env()
        
        print("Running integration tests (require API keys and external dependencies)...")
        cmd = [sys.executable, '-m', 'pytest', 'tests/integration/', '-v']
        result = subprocess.run(cmd, env=env, check=True)
        return result.returncode
    except subprocess.CalledProcessError:
        return 1
    except FileNotFoundError:
        print("Error: pytest not available. Please install pytest: pip install pytest")
        return 1

if __name__ == '__main__':
    exit_code = run_integration_tests()
    sys.exit(exit_code)