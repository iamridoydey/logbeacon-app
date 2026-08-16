from datetime import datetime, timedelta
from app.db import db
from app.models import Log

def find_logs_older_than(cutoff_date):
    return Log.query.filter(Log.created_at <= cutoff_date).all()


def delete(log):
    db.session.delete(log)
    db.session.commit()