# WSGI entry point for production servers
import os
import sys
from pathlib import Path

# Add Backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app import app

if __name__ == "__main__":
    app.run()
