"""
Pytest configuration and fixtures.
"""

import sys
import os

# Add src to Python path for package imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))