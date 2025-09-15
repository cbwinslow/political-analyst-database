#!/usr/bin/env python3
"""
Test script to validate database connectivity and basic functionality.
This script tests the core components of the Political Intelligence Platform.
"""

import psycopg2
import requests
import sys
import time
from neo4j import GraphDatabase

def test_postgres():
    """Test PostgreSQL connection and schema."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="policydocs",
            user="poladmin",
            password="please_change_me_to_a_secure_password"
        )
        cur = conn.cursor()
        
        # Test schema exists
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'legislative' LIMIT 5;")
        tables = cur.fetchall()
        print(f"✓ PostgreSQL: Found {len(tables)} legislative tables")
        
        # Test pgvector extension
        cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        vector_ext = cur.fetchone()
        if vector_ext:
            print("✓ PostgreSQL: pgvector extension installed")
        else:
            print("✗ PostgreSQL: pgvector extension not found")
        
        conn.close()
        return True
    except Exception as e:
        print(f"✗ PostgreSQL: {e}")
        return False

def test_neo4j():
    """Test Neo4j connection."""
    try:
        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "please_change_me_to_a_secure_password")
        )
        
        with driver.session() as session:
            result = session.run("RETURN 'Hello Neo4j' as message")
            record = result.single()
            print(f"✓ Neo4j: {record['message']}")
        
        driver.close()
        return True
    except Exception as e:
        print(f"✗ Neo4j: {e}")
        return False

def test_localai():
    """Test LocalAI API."""
    try:
        response = requests.get("http://localhost:8080/v1/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"✓ LocalAI: API responding, {len(models.get('data', []))} models available")
            return True
        else:
            print(f"✗ LocalAI: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ LocalAI: {e}")
        return False

def test_ollama():
    """Test Ollama API."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"✓ Ollama: API responding, {len(models.get('models', []))} models available")
            return True
        else:
            print(f"✗ Ollama: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Ollama: {e}")
        return False

def main():
    print("Testing Political Intelligence Platform components...")
    print("=" * 50)
    
    results = []
    results.append(test_postgres())
    results.append(test_neo4j())
    results.append(test_localai())
    results.append(test_ollama())
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All core services are working correctly!")
        sys.exit(0)
    else:
        print("✗ Some services need attention")
        sys.exit(1)

if __name__ == "__main__":
    main()