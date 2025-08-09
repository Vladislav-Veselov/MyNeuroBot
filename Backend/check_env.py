#!/usr/bin/env python3
"""
Environment variables checker for Render deployment.
This script will be printed during startup to debug environment issues.
"""

import os

def check_environment():
    print("🔍 [ENV DEBUG] Environment Variables Check")
    print("=" * 50)
    
    # Check critical environment variables
    env_vars = [
        'DATABASE_URL',
        'OPENAI_API_KEY', 
        'SECRET_KEY',
        'FLASK_ENV',
        'PORT'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if var == 'DATABASE_URL':
                # Show only first 50 chars for security
                print(f"✅ {var}: {value[:50]}...")
            elif var in ['OPENAI_API_KEY', 'SECRET_KEY']:
                # Show only first 10 chars for security
                print(f"✅ {var}: {value[:10]}...")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
    
    print("=" * 50)
    
    # Additional system info
    print(f"🔍 [ENV DEBUG] Python version: {os.sys.version}")
    print(f"🔍 [ENV DEBUG] Current working directory: {os.getcwd()}")
    print(f"🔍 [ENV DEBUG] Environment type: {'Production' if os.getenv('FLASK_ENV') == 'production' else 'Development'}")

if __name__ == "__main__":
    check_environment()
