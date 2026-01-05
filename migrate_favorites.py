"""
Migration script to add is_favorite column to User table
"""
import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(user)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'is_favorite' not in columns:
        print("Adding is_favorite column to User table...")
        cursor.execute('ALTER TABLE user ADD COLUMN is_favorite BOOLEAN DEFAULT 0')
        conn.commit()
        print("✓ Column added successfully!")
    else:
        print("✓ is_favorite column already exists")
    
    conn.close()

if __name__ == '__main__':
    migrate()
    print("Migration completed!")
