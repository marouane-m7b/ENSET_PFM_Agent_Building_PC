"""
Database Manager for PC Builder Agent
Handles MySQL database operations for chat history, builds, and analytics
"""

import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

class DatabaseManager:
    """Manages all database operations for the PC Builder system"""
    
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "3306"))
        self.database = os.getenv("DB_NAME", "pc_builder_agent")
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        self.pool = None
        
    def connect(self):
        """Establish database connection pool"""
        try:
            self.pool = MySQLConnectionPool(
                pool_name="pc_builder_pool",
                pool_size=5,
                pool_reset_session=True,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                autocommit=False,
                use_pure=True,
                ssl_disabled=True
            )
            print(f"✅ Connected to MySQL database: {self.database}")
            return True
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            return False
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        connection = None
        try:
            connection = self.pool.get_connection()
            yield connection
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            print("🔌 Database connection pool closed")
    
    def create_tables(self):
        """Create all necessary tables"""
        with self.get_connection() as connection:
            cursor = connection.cursor(buffered=True)
            
            try:
                # Users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INT AUTO_INCREMENT PRIMARY KEY,
                        session_id VARCHAR(255) UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        total_requests INT DEFAULT 0,
                        INDEX idx_session (session_id)
                    )
                """)
                
                # Chat sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        session_id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT,
                        thread_id VARCHAR(255) UNIQUE NOT NULL,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ended_at TIMESTAMP NULL,
                        total_messages INT DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                        INDEX idx_thread (thread_id)
                    )
                """)
                
                # Messages table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        message_id INT AUTO_INCREMENT PRIMARY KEY,
                        session_id INT,
                        role ENUM('user', 'assistant', 'system') NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
                        INDEX idx_session_time (session_id, timestamp)
                    )
                """)
                
                # PC builds table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pc_builds (
                        build_id INT AUTO_INCREMENT PRIMARY KEY,
                        session_id INT,
                        user_request TEXT NOT NULL,
                        budget DECIMAL(10, 2) NOT NULL,
                        use_case VARCHAR(50),
                        performance_level VARCHAR(20),
                        total_price DECIMAL(10, 2) NOT NULL,
                        components JSON NOT NULL,
                        build_quote TEXT,
                        llm_strategy TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        approved BOOLEAN DEFAULT FALSE,
                        approval_feedback TEXT,
                        FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
                        INDEX idx_budget (budget),
                        INDEX idx_use_case (use_case),
                        INDEX idx_created (created_at)
                    )
                """)
                
                # Approvals table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS approvals (
                        approval_id INT AUTO_INCREMENT PRIMARY KEY,
                        build_id INT,
                        request_id VARCHAR(255) UNIQUE NOT NULL,
                        status ENUM('pending', 'approved', 'rejected', 'timeout') NOT NULL,
                        feedback TEXT,
                        decided_at TIMESTAMP NULL,
                        decision_time_seconds INT,
                        FOREIGN KEY (build_id) REFERENCES pc_builds(build_id) ON DELETE CASCADE,
                        INDEX idx_status (status),
                        INDEX idx_decided (decided_at)
                    )
                """)
                
                # Analytics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analytics (
                        analytics_id INT AUTO_INCREMENT PRIMARY KEY,
                        date DATE NOT NULL,
                        total_requests INT DEFAULT 0,
                        total_builds INT DEFAULT 0,
                        total_approvals INT DEFAULT 0,
                        total_rejections INT DEFAULT 0,
                        avg_budget DECIMAL(10, 2),
                        avg_response_time DECIMAL(10, 2),
                        popular_use_case VARCHAR(50),
                        UNIQUE KEY unique_date (date),
                        INDEX idx_date (date)
                    )
                """)
                
                # Component popularity table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS component_popularity (
                        component_id INT AUTO_INCREMENT PRIMARY KEY,
                        category VARCHAR(50) NOT NULL,
                        brand VARCHAR(100) NOT NULL,
                        model VARCHAR(200) NOT NULL,
                        times_selected INT DEFAULT 1,
                        avg_price DECIMAL(10, 2),
                        last_selected TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_category (category),
                        INDEX idx_popularity (times_selected DESC)
                    )
                """)
                
                connection.commit()
                print("✅ All tables created successfully")
                return True
                
            except Error as e:
                print(f"❌ Error creating tables: {e}")
                connection.rollback()
                return False
            finally:
                cursor.close()
    
    def get_or_create_user(self, session_id: str) -> Optional[int]:
        """Get existing user or create new one"""
        with self.get_connection() as connection:
            cursor = connection.cursor(buffered=True)
            
            try:
                # Check if user exists
                cursor.execute("SELECT user_id FROM users WHERE session_id = %s", (session_id,))
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                
                # Create new user
                cursor.execute(
                    "INSERT INTO users (session_id) VALUES (%s)",
                    (session_id,)
                )
                connection.commit()
                return cursor.lastrowid
                
            except Error as e:
                print(f"❌ Error in get_or_create_user: {e}")
                connection.rollback()
                return None
            finally:
                cursor.close()
    
    def create_chat_session(self, user_id: int, thread_id: str) -> Optional[int]:
        """Create a new chat session"""
        with self.get_connection() as connection:
            cursor = connection.cursor(buffered=True)
            
            try:
                cursor.execute(
                    "INSERT INTO chat_sessions (user_id, thread_id) VALUES (%s, %s)",
                    (user_id, thread_id)
                )
                connection.commit()
                return cursor.lastrowid
                
            except Error as e:
                print(f"❌ Error creating chat session: {e}")
                connection.rollback()
                return None
            finally:
                cursor.close()
    
    def save_message(self, session_id: int, role: str, content: str) -> bool:
        """Save a chat message"""
        with self.get_connection() as connection:
            cursor = connection.cursor(buffered=True)
            
            try:
                cursor.execute(
                    "INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s)",
                    (session_id, role, content)
                )
                
                # Update message count
                cursor.execute(
                    "UPDATE chat_sessions SET total_messages = total_messages + 1 WHERE session_id = %s",
                    (session_id,)
                )
                
                connection.commit()
                return True
                
            except Error as e:
                print(f"❌ Error saving message: {e}")
                connection.rollback()
                return False
            finally:
                cursor.close()
    
    def save_build(self, session_id: int, build_data: Dict[str, Any]) -> Optional[int]:
        """Save a PC build"""
        with self.get_connection() as connection:
            cursor = connection.cursor(buffered=True)
            
            try:
                cursor.execute("""
                    INSERT INTO pc_builds 
                    (session_id, user_request, budget, use_case, performance_level, 
                     total_price, components, build_quote, llm_strategy)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    session_id,
                    build_data.get('user_request', ''),
                    build_data.get('budget', 0),
                    build_data.get('use_case', 'general'),
                    build_data.get('performance_level', 'medium'),
                    build_data.get('total_price', 0),
                    json.dumps(build_data.get('components', {})),
                    build_data.get('build_quote', ''),
                    build_data.get('llm_strategy', '')
                ))
                
                connection.commit()
                return cursor.lastrowid
                
            except Error as e:
                print(f"❌ Error saving build: {e}")
                connection.rollback()
                return None
            finally:
                cursor.close()
    
    def save_approval(self, build_id: int, approval_data: Dict[str, Any]) -> bool:
        """Save approval decision"""
        with self.get_connection() as connection:
            cursor = connection.cursor(buffered=True)
            
            try:
                cursor.execute("""
                    INSERT INTO approvals 
                    (build_id, request_id, status, feedback, decided_at, decision_time_seconds)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    build_id,
                    approval_data.get('request_id', ''),
                    approval_data.get('status', 'pending'),
                    approval_data.get('feedback', ''),
                    approval_data.get('decided_at'),
                    approval_data.get('decision_time_seconds', 0)
                ))
                
                # Update build approval status
                cursor.execute(
                    "UPDATE pc_builds SET approved = %s, approval_feedback = %s WHERE build_id = %s",
                    (approval_data.get('status') == 'approved', approval_data.get('feedback', ''), build_id)
                )
                
                connection.commit()
                return True
                
            except Error as e:
                print(f"❌ Error saving approval: {e}")
                connection.rollback()
                return False
            finally:
                cursor.close()
    
    def get_chat_history(self, session_id: int, limit: int = 50) -> List[Dict]:
        """Get chat history for a session"""
        with self.get_connection() as connection:
            cursor = connection.cursor(dictionary=True, buffered=True)
            
            try:
                cursor.execute("""
                    SELECT role, content, timestamp 
                    FROM messages 
                    WHERE session_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (session_id, limit))
                
                return list(reversed(cursor.fetchall()))
                
            except Error as e:
                print(f"❌ Error getting chat history: {e}")
                connection.rollback()
                return []
            finally:
                cursor.close()
    
    def get_user_builds(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's previous builds"""
        with self.get_connection() as connection:
            cursor = connection.cursor(dictionary=True, buffered=True)
            
            try:
                cursor.execute("""
                    SELECT b.*, cs.thread_id
                    FROM pc_builds b
                    JOIN chat_sessions cs ON b.session_id = cs.session_id
                    WHERE cs.user_id = %s
                    ORDER BY b.created_at DESC
                    LIMIT %s
                """, (user_id, limit))
                
                return cursor.fetchall()
                
            except Error as e:
                print(f"❌ Error getting user builds: {e}")
                connection.rollback()
                return []
            finally:
                cursor.close()
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        with self.get_connection() as connection:
            cursor = connection.cursor(dictionary=True, buffered=True)
            
            try:
                # Total stats
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT u.user_id) as total_users,
                        COUNT(DISTINCT cs.session_id) as total_sessions,
                        COUNT(m.message_id) as total_messages,
                        COUNT(b.build_id) as total_builds,
                        COUNT(CASE WHEN a.status = 'approved' THEN 1 END) as total_approvals,
                        COUNT(CASE WHEN a.status = 'rejected' THEN 1 END) as total_rejections,
                        AVG(b.budget) as avg_budget,
                        AVG(b.total_price) as avg_build_price
                    FROM users u
                    LEFT JOIN chat_sessions cs ON u.user_id = cs.user_id
                    LEFT JOIN messages m ON cs.session_id = m.session_id
                    LEFT JOIN pc_builds b ON cs.session_id = b.session_id
                    LEFT JOIN approvals a ON b.build_id = a.build_id
                """)
                
                stats = cursor.fetchone()
                
                # Popular use cases
                cursor.execute("""
                    SELECT use_case, COUNT(*) as count
                    FROM pc_builds
                    GROUP BY use_case
                    ORDER BY count DESC
                    LIMIT 5
                """)
                
                use_cases = cursor.fetchall()
                
                # Popular components
                cursor.execute("""
                    SELECT category, brand, model, times_selected
                    FROM component_popularity
                    ORDER BY times_selected DESC
                    LIMIT 10
                """)
                
                components = cursor.fetchall()
                
                return {
                    'stats': stats,
                    'popular_use_cases': use_cases,
                    'popular_components': components
                }
                
            except Error as e:
                print(f"❌ Error getting analytics: {e}")
                connection.rollback()
                return {}
            finally:
                cursor.close()
    
    def update_component_popularity(self, components: Dict[str, Dict]) -> bool:
        """Update component popularity tracking"""
        with self.get_connection() as connection:
            cursor = connection.cursor(buffered=True)
            
            try:
                for category, component in components.items():
                    cursor.execute("""
                        INSERT INTO component_popularity (category, brand, model, times_selected, avg_price)
                        VALUES (%s, %s, %s, 1, %s)
                        ON DUPLICATE KEY UPDATE 
                            times_selected = times_selected + 1,
                            avg_price = (avg_price * times_selected + %s) / (times_selected + 1)
                    """, (
                        category,
                        component.get('Brand', ''),
                        component.get('Model', ''),
                        component.get('Price_MAD', 0),
                        component.get('Price_MAD', 0)
                    ))
                
                connection.commit()
                return True
                
            except Error as e:
                print(f"❌ Error updating component popularity: {e}")
                connection.rollback()
                return False
            finally:
                cursor.close()

# Global database instance
db_manager = DatabaseManager()
