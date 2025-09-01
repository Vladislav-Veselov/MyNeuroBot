from flask import Flask
from flask_cors import CORS
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

def create_app():
    """Application factory function."""
    # Get the absolute path to the Frontend directory
    backend_dir = Path(__file__).resolve().parent.parent
    frontend_dir = backend_dir.parent / "Frontend"
    
    # Add Backend directory to Python path for imports
    import sys
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    # Initialize Flask app with absolute paths
    app = Flask(__name__, 
                template_folder=str(frontend_dir / "templates"),
                static_folder=str(frontend_dir / "static"))

    # Configure CORS for standalone HTML chatbot
    CORS(app, 
         origins=["*"],  # Allow all origins for standalone HTML
         supports_credentials=True,  # Allow cookies and authentication
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Allow all methods
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"])  # Allow necessary headers

    # Configure CORS for public widget routes with origin validation
    # Note: widget_registry import is not used in this function, so we can remove it
    
    # Apply CORS specifically to public widget routes
    CORS(app, 
         resources={r"/public/widget/*": {"origins": "*"}},  # Allow all origins for public widgets
         supports_credentials=False,  # No cookies needed for public widgets
         methods=["GET", "POST", "OPTIONS"],
         allow_headers=["Content-Type", "X-Requested-With"])
    
    # Apply CORS specifically to public custom widget routes
    CORS(app, 
         resources={r"/public/custom-widget/*": {"origins": "*"}},  # Allow all origins for custom widgets
         supports_credentials=False,  # No cookies needed for custom widgets
         methods=["GET", "POST", "OPTIONS"],
         allow_headers=["Content-Type", "X-Requested-With"])

    # Configure session
    app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")

    # Register blueprints
    from .blueprints.pages import pages_bp
    from .blueprints.auth_api import auth_api_bp
    from .blueprints.kb_api import kb_api_bp
    from .blueprints.chatbot_api import chatbot_api_bp
    from .blueprints.dialogues_api import dialogues_api_bp
    from .blueprints.admin_api import admin_api_bp
    from .blueprints.public_widget_api import public_chatbot_api_bp
    from .blueprints.public_custom_widget_api import public_custom_widget_api_bp



    app.register_blueprint(public_chatbot_api_bp)
    app.register_blueprint(public_custom_widget_api_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_api_bp, url_prefix='/api')
    app.register_blueprint(kb_api_bp, url_prefix='/api')
    app.register_blueprint(chatbot_api_bp, url_prefix='/api')
    app.register_blueprint(dialogues_api_bp, url_prefix='/api')
    app.register_blueprint(admin_api_bp, url_prefix='/api')

    return app
