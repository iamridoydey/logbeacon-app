from app.models import Analysis
from app.db import db


def find_by_log_id(log_id):
    return Analysis.query.filter_by(log_id=log_id).first()


def save(analysis):
    db.session.add(analysis)
    return analysis


def commit():
    db.session.commit()


def rollback():
    db.session.rollback()