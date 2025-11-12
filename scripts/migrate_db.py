"""
Database migration script to add agent_id and base_url columns to sessions table
"""
import sqlite3
import os

def migrate_database():
    """Add new columns to existing database"""
    db_path = "data/db.sqlite3"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if sessions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("⚠️  Sessions table does not exist yet.")
            print("It will be created automatically when the app starts with the new schema.")
            return
        
        # Check if agent_id column exists
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'agent_id' not in columns:
            print("Adding agent_id column to sessions table...")
            cursor.execute("ALTER TABLE sessions ADD COLUMN agent_id INTEGER")
            print("✓ agent_id column added")
        else:
            print("✓ agent_id column already exists")
        
        if 'base_url' not in columns:
            print("Adding base_url column to sessions table...")
            cursor.execute("ALTER TABLE sessions ADD COLUMN base_url VARCHAR")
            print("✓ base_url column added")
        else:
            print("✓ base_url column already exists")
        
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
