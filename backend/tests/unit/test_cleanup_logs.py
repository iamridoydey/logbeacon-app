from unittest.mock import MagicMock, patch
from app.jobs.cleanup_logs import run_cleanup


@patch("app.jobs.cleanup_logs.queue")
@patch("app.jobs.cleanup_logs.log_repository")
def test_run_cleanup_enqueues_one_job_per_expiring_log(mock_log_repo, mock_queue, app):
    fake_log_1 = MagicMock(id=1)
    fake_log_2 = MagicMock(id=2)
    mock_log_repo.find_logs_older_than.return_value = [fake_log_1, fake_log_2]

    with app.app_context():
        run_cleanup()

    assert mock_queue.enqueue.call_count == 2
    mock_queue.enqueue.assert_any_call(
        __import__("app.jobs.send_expiry_email", fromlist=["send_expiry_email"]).send_expiry_email,
        1
    )


@patch("app.jobs.cleanup_logs.queue")
@patch("app.jobs.cleanup_logs.log_repository")
def test_run_cleanup_enqueues_nothing_when_no_logs_expiring(mock_log_repo, mock_queue, app):
    mock_log_repo.find_logs_older_than.return_value = []

    with app.app_context():
        run_cleanup()

    mock_queue.enqueue.assert_not_called()