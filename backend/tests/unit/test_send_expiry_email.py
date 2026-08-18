from unittest.mock import MagicMock, patch
from app.jobs.send_expiry_email import send_expiry_email


@patch("app.jobs.send_expiry_email.log_repository")
@patch("app.jobs.send_expiry_email.user_repository")
@patch("app.jobs.send_expiry_email._send_email")
def test_returns_early_when_log_missing(mock_send, mock_user_repo, mock_log_repo, app):
    mock_log_repo.find_by_id.return_value = None

    with app.app_context():
        send_expiry_email(999)

    mock_send.assert_not_called()
    mock_log_repo.delete.assert_not_called()


@patch("app.jobs.send_expiry_email.log_repository")
@patch("app.jobs.send_expiry_email.user_repository")
@patch("app.jobs.send_expiry_email._send_email")
def test_deletes_log_only_after_successful_send(mock_send, mock_user_repo, mock_log_repo, app):
    fake_log = MagicMock(id=1, user_id=5, error_log="boom", error_solution="fix it")
    fake_user = MagicMock(id=5, email="test@example.com")
    mock_log_repo.find_by_id.return_value = fake_log
    mock_user_repo.find_by_id.return_value = fake_user

    with app.app_context():
        send_expiry_email(1)

    mock_send.assert_called_once_with("test@example.com", "boom", "fix it")
    mock_log_repo.delete.assert_called_once_with(fake_log)


@patch("app.jobs.send_expiry_email.log_repository")
@patch("app.jobs.send_expiry_email.user_repository")
@patch("app.jobs.send_expiry_email._send_email")
def test_log_survives_when_send_fails(mock_send, mock_user_repo, mock_log_repo, app):
    fake_log = MagicMock(id=1, user_id=5, error_log="boom", error_solution="fix it")
    fake_user = MagicMock(id=5, email="test@example.com")
    mock_log_repo.find_by_id.return_value = fake_log
    mock_user_repo.find_by_id.return_value = fake_user
    mock_send.side_effect = Exception("SMTP down")

    with app.app_context():
        try:
            send_expiry_email(1)
        except Exception:
            pass

    mock_log_repo.delete.assert_not_called()