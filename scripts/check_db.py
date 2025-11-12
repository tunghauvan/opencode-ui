"""
Check database structure
"""
import sqlite3
import os

def check_database():
    """Check database tables and structure"""
    db_path = "data/db.sqlite3"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("Database tables:")
        for table in tables:
            print(f"  - {table[0]}")
            
            # Get columns for each table
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            print(f"    Columns:")
            for col in columns:
                print(f"      {col[1]} ({col[2]})")
            print()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database()
