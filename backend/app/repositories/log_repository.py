from app.models import Log, Analysis
from app.db import db


def find_by_id(log_id):
    return Log.query.filter_by(id=log_id).first()


def find_all_by_user(user_id):
    return Log.query.filter_by(user_id=user_id).order_by(Log.created_at.desc()).all()


def find_all_by_user_with_analysis(user_id):
    return (
        db.session.query(Log, Analysis)
        .join(Analysis, Analysis.log_id == Log.id)
        .filter(Log.user_id == user_id)
        .order_by(Log.created_at.desc())
        .all()
    )

def save(log):
    db.session.add(log)
    db.session.flush()  # assigns log.id without committing — lets Analysis reference it in the same transaction
    return log


def find_logs_older_than(cutoff_date):
    return Log.query.filter(Log.created_at <= cutoff_date).all()


def delete(log):
    db.session.delete(log)
    db.session.commit()

def commit():
    db.session.commit()


def rollback():
    db.session.rollback()