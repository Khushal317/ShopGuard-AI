import os
import sys

# Add the backend directory to the Python path so it can find the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.main import app
