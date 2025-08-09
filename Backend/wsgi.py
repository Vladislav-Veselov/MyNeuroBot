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

# Debug: Print directory information
print(f"Project root: {project_root}")
print(f"User data dir: {user_data_dir}")
print(f"User data dir exists: {user_data_dir.exists()}")
print(f"User data dir is mount: {user_data_dir.is_mount()}")

# Check if it's the persistent disk mount
import shutil
total, used, free = shutil.disk_usage(user_data_dir)
print(f"Disk usage - Total: {total // (1024**3)}GB, Used: {used // (1024**2)}MB, Free: {free // (1024**3)}GB")

# Initialize users.json if it doesn't exist
users_file = user_data_dir / "users.json"
if not users_file.exists():
    import json
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=2)
    print(f"Initialized empty users.json at {users_file}")
else:
    print(f"users.json already exists at {users_file}")

# List contents of user_data directory
print(f"Contents of {user_data_dir}: {list(user_data_dir.iterdir()) if user_data_dir.exists() else 'Directory does not exist'}")

try:
    from app import app
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    raise

if __name__ == "__main__":
    app.run()
