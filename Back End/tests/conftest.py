"""
Pytest configuration and shared fixtures for Inbox Copilot tests.
"""
import sys
from pathlib import Path

# Add parent directory to path so we can import backend modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
