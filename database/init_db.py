"""
Database Initialization Script
Run this to create the database and tables
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    """Create the database if it doesn't exist"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "")
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database
            db_name = os.getenv("DB_NAME", "pc_builder_agent")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            print(f"✅ Database '{db_name}' created or already exists")
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print(f"❌ Error creating database: {e}")
        return False

def main():
    """Main initialization function"""
    print("🚀 Initializing PC Builder Agent Database...")
    print("=" * 50)
    
    # Step 1: Create database
    if not create_database():
        print("❌ Failed to create database")
        return
    
    # Step 2: Create tables
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from database.db_manager import db_manager
    
    if not db_manager.connect():
        print("❌ Failed to connect to database")
        return
    
    if not db_manager.create_tables():
        print("❌ Failed to create tables")
        return
    
    print("\n✅ Database initialization complete!")
    print("\n📊 Created tables:")
    print("  - users")
    print("  - chat_sessions")
    print("  - messages")
    print("  - pc_builds")
    print("  - approvals")
    print("  - analytics")
    print("  - component_popularity")
    
    db_manager.disconnect()

if __name__ == "__main__":
    main()
