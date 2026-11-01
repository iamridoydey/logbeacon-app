from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.jobs.cleanup_logs import cleanup_logs


def _old_created_at(days_ago=30):
    """Naive UTC timestamp older than the retention window."""
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).replace(tzinfo=None)


@patch("app.jobs.cleanup_logs._send_email")
@patch("app.jobs.cleanup_logs.user_repository")
@patch("app.jobs.cleanup_logs.log_repository")
@patch("app.jobs.cleanup_logs.create_app")
def test_returns_early_when_log_missing(mock_create_app, mock_log_repo, mock_user_repo, mock_send, app):
    mock_create_app.return_value = app
    mock_log_repo.find_by_id.return_value = None

    cleanup_logs(999)

    mock_user_repo.find_by_id.assert_not_called()
    mock_send.assert_not_called()
    mock_log_repo.delete.assert_not_called()


@patch("app.jobs.cleanup_logs._send_email")
@patch("app.jobs.cleanup_logs.user_repository")
@patch("app.jobs.cleanup_logs.log_repository")
@patch("app.jobs.cleanup_logs.create_app")
def test_skips_when_user_missing(mock_create_app, mock_log_repo, mock_user_repo, mock_send, app):
    mock_create_app.return_value = app
    fake_log = MagicMock(id=1, user_id=5, created_at=_old_created_at())
    mock_log_repo.find_by_id.return_value = fake_log
    mock_user_repo.find_by_id.return_value = None

    cleanup_logs(1)

    mock_send.assert_not_called()
    mock_log_repo.delete.assert_not_called()


@patch("app.jobs.cleanup_logs._send_email")
@patch("app.jobs.cleanup_logs.user_repository")
@patch("app.jobs.cleanup_logs.log_repository")
@patch("app.jobs.cleanup_logs.create_app")
def test_skips_when_log_not_old_enough(mock_create_app, mock_log_repo, mock_user_repo, mock_send, app):
    mock_create_app.return_value = app
    # created just now — younger than retention
    fake_log = MagicMock(
        id=1,
        user_id=5,
        error_log="boom",
        error_solution="fix it",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    fake_user = MagicMock(id=5, email="test@example.com")
    mock_log_repo.find_by_id.return_value = fake_log
    mock_user_repo.find_by_id.return_value = fake_user

    cleanup_logs(1)

    mock_send.assert_not_called()
    mock_log_repo.delete.assert_not_called()


@patch("app.jobs.cleanup_logs._send_email")
@patch("app.jobs.cleanup_logs.user_repository")
@patch("app.jobs.cleanup_logs.log_repository")
@patch("app.jobs.cleanup_logs.create_app")
def test_deletes_log_only_after_successful_send(mock_create_app, mock_log_repo, mock_user_repo, mock_send, app):
    mock_create_app.return_value = app
    fake_log = MagicMock(
        id=1,
        user_id=5,
        error_log="boom",
        error_solution="fix it",
        created_at=_old_created_at(),
    )
    fake_user = MagicMock(id=5, email="test@example.com")
    mock_log_repo.find_by_id.return_value = fake_log
    mock_user_repo.find_by_id.return_value = fake_user

    cleanup_logs(1)

    mock_send.assert_called_once_with("test@example.com", "boom", "fix it")
    mock_log_repo.delete.assert_called_once_with(fake_log)
    mock_log_repo.commit.assert_called_once()


@patch("app.jobs.cleanup_logs._send_email")
@patch("app.jobs.cleanup_logs.user_repository")
@patch("app.jobs.cleanup_logs.log_repository")
@patch("app.jobs.cleanup_logs.create_app")
def test_log_survives_when_send_fails(mock_create_app, mock_log_repo, mock_user_repo, mock_send, app):
    mock_create_app.return_value = app
    fake_log = MagicMock(
        id=1,
        user_id=5,
        error_log="boom",
        error_solution="fix it",
        created_at=_old_created_at(),
    )
    fake_user = MagicMock(id=5, email="test@example.com")
    mock_log_repo.find_by_id.return_value = fake_log
    mock_user_repo.find_by_id.return_value = fake_user
    mock_send.side_effect = RuntimeError("SMTP down")

    with pytest.raises(RuntimeError):
        cleanup_logs(1)

    mock_log_repo.delete.assert_not_called()
    mock_log_repo.commit.assert_not_called()
