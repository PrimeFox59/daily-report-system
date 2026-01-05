"""Add ReportTemplate table to database."""
from app import create_app
from models import db

def migrate_db():
    app = create_app()
    with app.app_context():
        # Create new tables without dropping existing ones
        db.create_all()
        print('Database migration completed! ReportTemplate table created.')

if __name__ == '__main__':
    migrate_db()
