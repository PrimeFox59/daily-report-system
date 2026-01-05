"""Migration script to add ItemLibrary table"""
from app import create_app
from models import db, ItemLibrary

app = create_app()

with app.app_context():
    # Create ItemLibrary table if it doesn't exist
    db.create_all()
    print("✅ ItemLibrary table created successfully!")
    
    # Check if table exists
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'item_library' in tables:
        print(f"✅ Table 'item_library' exists")
        
        # Show columns
        columns = inspector.get_columns('item_library')
        print("\nColumns in item_library:")
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
    else:
        print("❌ Table 'item_library' not found!")
