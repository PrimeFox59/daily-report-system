from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    department = db.Column(db.String(120))
    section = db.Column(db.String(120))
    job = db.Column(db.String(120))
    shift = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, default=False)
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reports = db.relationship('Report', backref='user', lazy=True)
    templates = db.relationship('ReportTemplate', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(20), default='primary')  # Bootstrap color classes
    icon = db.Column(db.String(50), default='bi-tag')  # Bootstrap icons
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time = db.Column(db.String(20))
    category = db.Column(db.String(50))
    title = db.Column(db.String(200))
    notes = db.Column(db.Text)
    item_name = db.Column(db.String(200), nullable=True)
    part_number = db.Column(db.String(200), nullable=True)
    customer = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ReportTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))
    title = db.Column(db.String(200))
    notes = db.Column(db.Text)
    item_name = db.Column(db.String(200), nullable=True)
    part_number = db.Column(db.String(200), nullable=True)
    customer = db.Column(db.String(200), nullable=True)
    color = db.Column(db.String(20), default='yellow')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], backref='audit_logs', lazy=True)
    actor = db.relationship('User', foreign_keys=[actor_id], lazy=True)


class ItemLibrary(db.Model):
    """Library of items with part numbers and customers for quick reporting"""
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(200), nullable=False)
    part_number = db.Column(db.String(200), nullable=True)
    customer = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

