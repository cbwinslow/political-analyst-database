#!/usr/bin/env python3
"""
Simple test script to validate the political analyst database setup.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from political_analyst.core.config import settings
from political_analyst.database import create_tables, SessionLocal
from political_analyst.database.models import Document, Politician

def test_configuration():
    """Test configuration loading."""
    print("Testing configuration...")
    print(f"App Name: {settings.app.name}")
    print(f"App Version: {settings.app.version}")
    print(f"Database URL: {settings.database.url}")
    print(f"Embedding Model: {settings.vector.embedding_model}")
    print("✓ Configuration loaded successfully")

def test_database_connection():
    """Test database connection and table creation."""
    print("\nTesting database connection...")
    try:
        # Create tables
        create_tables()
        print("✓ Database tables created successfully")
        
        # Test session
        db = SessionLocal()
        try:
            # Test basic query
            count = db.query(Document).count()
            print(f"✓ Database connection successful (found {count} documents)")
        finally:
            db.close()
            
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False
    
    return True

def test_imports():
    """Test that all modules can be imported."""
    print("\nTesting module imports...")
    
    modules_to_test = [
        "political_analyst.core.config",
        "political_analyst.database",
        "political_analyst.crawling",
        "political_analyst.ingestion",
        "political_analyst.vectorization",
        "political_analyst.analysis",
        "political_analyst.entities",
        "political_analyst.social_media",
        "political_analyst.api",
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            return False
    
    return True

def main():
    """Run all tests."""
    print("Political Analyst Database - Setup Validation")
    print("=" * 50)
    
    try:
        # Test configuration
        test_configuration()
        
        # Test imports
        if not test_imports():
            print("\n❌ Import tests failed")
            return 1
        
        # Test database (optional, may fail if database not set up)
        try:
            if not test_database_connection():
                print("\n⚠️  Database tests failed (this is expected if database is not configured)")
        except Exception as e:
            print(f"\n⚠️  Database tests skipped: {e}")
        
        print("\n✅ Basic setup validation completed successfully!")
        print("\nNext steps:")
        print("1. Configure your database connection in .env file")
        print("2. Install required dependencies: pip install -r requirements.txt")
        print("3. Set up your API keys (OpenAI, Twitter) in .env file")
        print("4. Run the API server: python -m uvicorn political_analyst.api.main:app --reload")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Setup validation failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())