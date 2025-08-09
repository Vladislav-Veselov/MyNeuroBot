#!/usr/bin/env python3
"""
Quick PostgreSQL connection test.
Use this to verify DATABASE_URL works correctly.
"""

import os
import sys
from pathlib import Path

# Add Backend directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def test_postgres_connection():
    """Test PostgreSQL connection using DATABASE_URL."""
    print("🐘 Testing PostgreSQL connection...")
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("💡 For local testing, set DATABASE_URL or it will use SQLite")
        return False
    
    print(f"🔗 Using DATABASE_URL: {database_url[:50]}..." if len(database_url) > 50 else database_url)
    
    try:
        from sqlalchemy import create_engine, text
        
        # Fix URL for SQLAlchemy compatibility
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL connection successful!")
            print(f"📋 Version: {version}")
            
            # Test basic operations
            connection.execute(text("CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name VARCHAR(50))"))
            connection.execute(text("INSERT INTO test_table (name) VALUES ('test_connection')"))
            result = connection.execute(text("SELECT COUNT(*) FROM test_table"))
            count = result.fetchone()[0]
            print(f"✅ Basic operations work - test table has {count} records")
            
            # Cleanup
            connection.execute(text("DROP TABLE test_table"))
            print("✅ Cleanup successful")
            
            connection.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def test_flask_database_integration():
    """Test Flask-SQLAlchemy integration."""
    print("\n🌶️  Testing Flask-SQLAlchemy integration...")
    
    try:
        from flask import Flask
        from database import init_database
        
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # Initialize database
        db = init_database(app)
        
        with app.app_context():
            # Test table creation
            db.create_all()
            print("✅ Flask-SQLAlchemy tables created")
            
            # Test basic model operations
            from database import User
            
            # Check if admin user exists
            admin_count = User.query.filter_by(username='admin').count()
            print(f"✅ Admin users in database: {admin_count}")
            
            # Test user count
            total_users = User.query.count()
            print(f"✅ Total users in database: {total_users}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask integration test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 PostgreSQL Connection Test")
    print("=" * 40)
    
    # Test 1: Direct PostgreSQL connection
    postgres_success = test_postgres_connection()
    
    # Test 2: Flask-SQLAlchemy integration
    flask_success = test_flask_database_integration()
    
    print("\n" + "=" * 40)
    if postgres_success and flask_success:
        print("🎉 All PostgreSQL tests passed!")
        print("✅ Ready for production deployment")
        return True
    else:
        print("❌ Some tests failed")
        if not postgres_success:
            print("  - PostgreSQL connection issues")
        if not flask_success:
            print("  - Flask-SQLAlchemy integration issues")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)
