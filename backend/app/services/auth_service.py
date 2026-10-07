import hashlib
import logging
import secrets
import time

from flask import jsonify, session
from opentelemetry.trace import Status, StatusCode
from werkzeug.security import check_password_hash, generate_password_hash

from app.errors import AppError, AuthenticationError, ConflictError
from app.models import User
from app.observability import tracer, make_duration_histogram
from app.repositories import user_repository

logger = logging.getLogger(__name__)

# Created once, when this file is first imported.
# Labels: action=register|signin|signout
#         outcome=success|duplicate|invalid_credentials|account_disabled|no_session|error
# Counts come from the histogram's _count series, so no separate counter is needed.
# Prometheus names: logbeacon_auth_duration_seconds_{bucket,count,sum}
auth_duration = make_duration_histogram(
    "logbeacon.auth.duration",
    [0.05, 0.1, 0.25, 0.5, 1, 2, 5],
    description="Auth request time; labels action and outcome",
)


# Create user account
def create_user(username, email, password):
    start = time.perf_counter()
    outcome = "error"   # becomes something more specific on the paths below

    # set_status_on_exception=False: a duplicate username is an expected user
    # mistake, so it should not turn the span red. Real errors are marked below.
    with tracer.start_as_current_span(
        "auth.register", set_status_on_exception=False
    ) as span:
        span.set_attribute("logbeacon.flow", "register")

        try:
            api_key = secrets.token_urlsafe(32)
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Check whether the user already exists
            registered = user_repository.find_by_username(username)

            if registered:
                outcome = "duplicate"
                raise ConflictError("User already exist")

            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                api_key_hash=api_key_hash,
            )

            user_repository.save(new_user)
            outcome = "success"
            logger.info("flow=register account created")

            return jsonify({
                "message": f"User {username} created",
                "api_key": api_key,
            }), 201

        except Exception as error:
            user_repository.rollback()
            if outcome == "error":   # not an expected case like "duplicate"
                span.record_exception(error)
                span.set_status(Status(StatusCode.ERROR))
                logger.exception("flow=register failed")
            else:
                logger.info("flow=register rejected outcome=%s", outcome)
            raise

        finally:
            auth_duration.record(
                time.perf_counter() - start, {"action": "register", "outcome": outcome}
            )


# Signin user
def signin_user(username, password):
    start = time.perf_counter()
    outcome = "error"

    with tracer.start_as_current_span(
        "auth.signin", set_status_on_exception=False
    ) as span:
        span.set_attribute("logbeacon.flow", "signin")

        try:
            user = user_repository.find_by_username(username)

            if not user or not check_password_hash(user.password_hash, password):
                outcome = "invalid_credentials"
                # No username in the log line. Count these in Loki to spot guessing.
                logger.warning("flow=signin invalid credentials")
                raise AuthenticationError("Invalid username or password")

            if not user.is_active:
                outcome = "account_disabled"
                logger.warning("flow=signin disabled account user_id=%s", user.id)
                raise AppError("Account is disabled", 403)

            session['user_id'] = user.id
            outcome = "success"
            span.set_attribute("enduser.id", str(user.id))
            logger.info("flow=signin succeeded user_id=%s", user.id)

            return jsonify({"message": f"Welcome back, {user.username}"}), 200

        except AppError:
            raise   # expected outcomes, already labelled above

        except Exception as error:
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR))
            logger.exception("flow=signin failed")
            raise

        finally:
            auth_duration.record(
                time.perf_counter() - start, {"action": "signin", "outcome": outcome}
            )


# Signout user
def signout_user():
    start = time.perf_counter()

    with tracer.start_as_current_span("auth.signout") as span:
        span.set_attribute("logbeacon.flow", "signout")

        user_id = session.pop('user_id', None)

        # Signing out with no session is harmless, but worth seeing separately.
        outcome = "success" if user_id is not None else "no_session"
        if user_id is not None:
            span.set_attribute("enduser.id", str(user_id))
        logger.info("flow=signout outcome=%s", outcome)

        auth_duration.record(
            time.perf_counter() - start, {"action": "signout", "outcome": outcome}
        )
        return jsonify({"message": "Signed out successfully"}), 200