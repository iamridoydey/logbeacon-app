from unittest.mock import patch

import pytest

from app.errors import ExternalServiceError
from app.models import Analysis, Log
from app.services import analyze_service, auth_service


@patch("app.services.analyze_service.ask_groq")
def test_analyze_error_success(mock_ask_groq, app, db):
    mock_ask_groq.return_value = {
        "log_solution": "Restart the pod, the image tag is wrong.",
        "input_tokens": 100,
        "output_tokens": 50,
    }

    with app.app_context():
        auth_service.create_user("ridoy", "ridoy@email.com", "pass123")
        user_id = auth_service.User.query.filter_by(username="ridoy").first().id

        _, status = analyze_service.analyze_error(user_id, "ImagePullBackOff error")

        assert status == 201
        assert Log.query.count() == 1
        assert Analysis.query.count() == 1


@patch("app.services.analyze_service.ask_groq")
def test_analyze_error_llm_failure_raises_external_service_error(mock_ask_groq, app, db):
    mock_ask_groq.side_effect = Exception("Groq API timeout")

    with app.app_context():
        auth_service.create_user("ridoy", "ridoy@email.com", "pass123")
        user_id = auth_service.User.query.filter_by(username="ridoy").first().id

        with pytest.raises(ExternalServiceError):
            analyze_service.analyze_error(user_id, "some error log")

        assert Log.query.count() == 0