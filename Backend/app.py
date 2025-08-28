from app import create_app
from pathlib import Path
import os

# Create the Flask application
app = create_app()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Additional utility routes that don't fit into blueprints
@app.route('/Backend/<path:filename>')
def backend_static(filename):
    """Serve static files from the Backend folder."""
    backend_dir = Path(__file__).resolve().parent
    file_path = backend_dir / filename
    print(f"Requested file: {filename}")
    print(f"Full path: {file_path}")
    print(f"File exists: {file_path.exists()}")
    from flask import send_from_directory
    return send_from_directory(backend_dir, filename)

@app.route('/test-logo')
def test_logo():
    """Test route to check if logo file exists."""
    logo_path = Path(__file__).resolve().parent.parent / "Frontend" / "static" / "logo.png"
    from flask import jsonify
    return jsonify({
        'logo_exists': logo_path.exists(),
        'logo_path': str(logo_path),
        'logo_size': logo_path.stat().st_size if logo_path.exists() else None
    })

@app.route('/api/debug/disk-status')
def debug_disk_status():
    """Debug endpoint to check disk status and user data."""
    try:
        import shutil
        import os
        from flask import jsonify
        from auth import get_current_user_data_dir
        
        # Get user data directory
        user_data_base = BASE_DIR / "user_data"
        current_user_dir = get_current_user_data_dir()
        
        # Get disk usage
        total, used, free = shutil.disk_usage(user_data_base)
        
        # List all files in user directory
        files_info = []
        if current_user_dir.exists():
            for root, dirs, files in os.walk(current_user_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path)
                    files_info.append({
                        'path': file_path,
                        'size': size,
                        'relative_path': os.path.relpath(file_path, current_user_dir)
                    })
        
        return jsonify({
            'success': True,
            'disk_info': {
                'total_gb': round(total / (1024**3), 2),
                'used_mb': round(used / (1024**2), 2),
                'free_gb': round(free / (1024**3), 2)
            },
            'paths': {
                'base_dir': str(BASE_DIR),
                'user_data_base': str(user_data_base),
                'current_user_dir': str(current_user_dir),
                'current_user_exists': current_user_dir.exists()
            },
            'files': files_info,
            'total_files': len(files_info),
            'total_user_data_size': sum(f['size'] for f in files_info)
        })
    except Exception as e:
        print(f"Error in debug_disk_status: {str(e)}")
        from flask import jsonify
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Check if we're in production (Render sets PORT environment variable)
    port = int(os.environ.get('PORT', 5001))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    if debug_mode:
        # Development mode - use Flask's built-in server
        # Use localhost only to avoid the warning and multiple addresses
        app.run(debug=True, host='127.0.0.1', port=port)
    else:
        # Production mode - use Gunicorn (this should be called by gunicorn)
        app.run(host='0.0.0.0', port=port, debug=False)
