from app import create_app
from models import db, Category

app = create_app()

with app.app_context():
    # Create Category table
    db.create_all()
    
    # Add default categories if none exist
    if Category.query.count() == 0:
        default_categories = [
            {'name': 'Quality', 'color': 'success', 'icon': 'bi-check-circle'},
            {'name': 'Cost', 'color': 'warning', 'icon': 'bi-currency-dollar'},
            {'name': 'Delivery', 'color': 'danger', 'icon': 'bi-truck'},
            {'name': 'Productivity', 'color': 'info', 'icon': 'bi-graph-up'}
        ]
        
        for cat_data in default_categories:
            category = Category(**cat_data)
            db.session.add(category)
        
        db.session.commit()
        print("✓ Default categories created successfully!")
    else:
        print("✓ Categories already exist")
    
    print(f"Total categories: {Category.query.count()}")
