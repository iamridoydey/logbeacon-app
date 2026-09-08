from sqlalchemy.sql import func
from app.db import db

class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    error_log = db.Column(db.Text, nullable=False)
    error_solution = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=func.now())

    # Analysis association
    analysis = db.relationship(
        'Analysis',
        back_populates='log',
        uselist=False,
        cascade='all, delete-orphan',
    )

    # Log association
    user = db.relationship('User', back_populates='logs')

