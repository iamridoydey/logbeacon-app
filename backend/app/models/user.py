from sqlalchemy.sql import func
from app.db import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    api_key_hash = db.Column(db.String(100), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=func.now())

    # Logs association
    logs = db.relationship(
    'Log',
    back_populates='user',
    cascade='all, delete-orphan',
)
