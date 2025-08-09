# WSGI entry point for production servers
import os
import sys
from pathlib import Path

# Add Backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

# Change working directory to Backend
os.chdir(backend_dir)

try:
    from app import app
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    raise

if __name__ == "__main__":
    app.run()
