from app.models import User
from app.db import db


def find_by_id(user_id):
    return User.query.filter_by(id=user_id).first()


def find_by_username(username):
    return User.query.filter_by(username=username).first()


def find_by_email(email):
    return User.query.filter_by(email=email).first()


def find_by_api_key_hash(api_key_hash):
    return User.query.filter_by(api_key_hash=api_key_hash).first()


def save(user):
    db.session.add(user)
    db.session.commit()
    return user


def rollback():
    db.session.rollback()