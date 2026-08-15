from app.db import db

class Analysis(db.Model):
    __tablename__ = 'analysis'

    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.Integer, db.ForeignKey('logs.id', ondelete='CASCADE'), unique=True, nullable=False)
    input_tokens = db.Column(db.Integer, nullable=False)
    output_tokens = db.Column(db.Integer, nullable=False)
    latency = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Numeric(10, 6), nullable=False)
    status = db.Column(db.Boolean, nullable=False)

    log = db.relationship('Log', back_populates='analysis')