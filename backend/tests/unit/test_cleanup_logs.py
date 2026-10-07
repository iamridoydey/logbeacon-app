# tests/jobs/test_cleanup_logs.py

from unittest.mock import MagicMock, patch

from app.jobs.cleanup_logs import cleanup_logs


@patch("app.jobs.cleanup_logs._send_email")
@patch("app.jobs.cleanup_logs.user_repository")
@patch("app.jobs.cleanup_logs.log_repository")
@patch("app.jobs.cleanup_logs.create_app")
def test_cleanup_logs_sends_email_and_deletes_log(
    mock_create_app,
    mock_log_repo,
    mock_user_repo,
    mock_send_email,
    app,
):
    mock_create_app.return_value = app

    fake_log = MagicMock(
        id=1,
        user_id=10,
        error_log="Connection refused",
        error_solution="Restart service",
    )

    fake_user = MagicMock(
        id=10,
        email="user@example.com",
    )

    mock_log_repo.find_by_id.return_value = fake_log
    mock_user_repo.find_by_id.return_value = fake_user

    cleanup_logs(1)

    mock_send_email.assert_called_once_with(
        "user@example.com",
        "Connection refused",
        "Restart service",
    )

    mock_log_repo.delete.assert_called_once_with(fake_log)


@patch("app.jobs.cleanup_logs._send_email")
@patch("app.jobs.cleanup_logs.user_repository")
@patch("app.jobs.cleanup_logs.log_repository")
@patch("app.jobs.cleanup_logs.create_app")
def test_cleanup_logs_skips_missing_log(
    mock_create_app,
    mock_log_repo,
    mock_user_repo,
    mock_send_email,
    app,
):
    mock_create_app.return_value = app

    mock_log_repo.find_by_id.return_value = None

    cleanup_logs(999)

    mock_user_repo.find_by_id.assert_not_called()
    mock_send_email.assert_not_called()
    mock_log_repo.delete.assert_not_called()


@patch("app.jobs.cleanup_logs._send_email")
@patch("app.jobs.cleanup_logs.user_repository")
@patch("app.jobs.cleanup_logs.log_repository")
@patch("app.jobs.cleanup_logs.create_app")
def test_cleanup_logs_skips_missing_user(
    mock_create_app,
    mock_log_repo,
    mock_user_repo,
    mock_send_email,
    app,
):
    mock_create_app.return_value = app

    fake_log = MagicMock(
        id=1,
        user_id=10,
        error_log="Connection refused",
        error_solution="Restart service",
    )

    mock_log_repo.find_by_id.return_value = fake_log
    mock_user_repo.find_by_id.return_value = None

    cleanup_logs(1)

    mock_send_email.assert_not_called()
    mock_log_repo.delete.assert_not_called()


@patch("app.jobs.cleanup_logs._send_email")
@patch("app.jobs.cleanup_logs.user_repository")
@patch("app.jobs.cleanup_logs.log_repository")
@patch("app.jobs.cleanup_logs.create_app")
def test_cleanup_logs_raises_when_email_fails(
    mock_create_app,
    mock_log_repo,
    mock_user_repo,
    mock_send_email,
    app,
):
    mock_create_app.return_value = app

    fake_log = MagicMock(
        id=1,
        user_id=10,
        error_log="Connection refused",
        error_solution="Restart service",
    )

    fake_user = MagicMock(
        id=10,
        email="user@example.com",
    )

    mock_log_repo.find