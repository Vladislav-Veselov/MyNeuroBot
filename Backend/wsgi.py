# WSGI entry point for production servers
import os
import sys
from pathlib import Path

# Add Backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

# Change working directory to Backend
os.chdir(backend_dir)

# Ensure user_data directory exists
project_root = backend_dir.parent
user_data_dir = project_root / "user_data"
user_data_dir.mkdir(exist_ok=True)

# Initialize users.json if it doesn't exist
users_file = user_data_dir / "users.json"
if not users_file.exists():
    import json
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=2)
    print(f"Initialized empty users.json at {users_file}")

try:
    from app import app
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    raise

if __name__ == "__main__":
    app.run()
