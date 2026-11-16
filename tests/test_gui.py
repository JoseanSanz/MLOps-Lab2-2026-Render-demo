"""
Unit testing of the Gradio GUI (gui/app.py).

The API is not called: requests.post is replaced by a mock, so these tests
check how the GUI builds the request and handles the answers and errors.
"""

from unittest.mock import MagicMock, patch

import requests

from gui import app as gui


def fake_response(status_code, payload):
    """Builds a fake requests.Response."""
    response = MagicMock()
    response.ok = status_code < 400
    response.status_code = status_code
    response.json.return_value = payload
    return response


def test_gui_returns_result():
    """The GUI sends the operation as form data and shows the result."""
    with patch.object(
        gui.requests, "post", return_value=fake_response(200, {"result": 8})
    ) as post:
        assert gui.calculate(5, 3, "add") == "8"
    assert post.call_args.kwargs["data"] == {"op": "add", "a": 5, "b": 3}
    assert post.call_args.args[0].endswith("/calculate")


def test_gui_shows_api_error():
    """The error message of the API is shown to the user."""
    error = fake_response(400, {"detail": "Zero division not allowed"})
    with patch.object(gui.requests, "post", return_value=error):
        assert gui.calculate(5, 0, "divide") == "Error 400: Zero division not allowed"


def test_gui_shows_error_without_json():
    """If the error body is not JSON, its text is shown."""
    error = fake_response(500, None)
    error.json.side_effect = ValueError("no JSON")
    error.text = "Internal Server Error"
    with patch.object(gui.requests, "post", return_value=error):
        assert gui.calculate(1, 2, "add") == "Error 500: Internal Server Error"


def test_gui_handles_timeout():
    """A timeout (e.g. cold start of the backend) gives a readable message."""
    with patch.object(gui.requests, "post", side_effect=requests.exceptions.Timeout()):
        assert "did not answer in time" in gui.calculate(1, 2, "add")


def test_gui_handles_connection_error():
    """A connection error gives a readable message."""
    with patch.object(
        gui.requests, "post", side_effect=requests.exceptions.ConnectionError("down")
    ):
        assert "could not connect" in gui.calculate(1, 2, "add")


def test_gui_requires_both_numbers():
    """The API is not called if a number is missing."""
    with patch.object(gui.requests, "post") as post:
        assert gui.calculate(None, 2, "add") == "Error: both numbers are required"
    post.assert_not_called()
