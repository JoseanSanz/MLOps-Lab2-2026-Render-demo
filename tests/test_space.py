"""
Unit testing of the Gradio GUI (hf_space/app.py).

The API is not called: requests.post is replaced by a mock, so these tests
check how the GUI builds the request and handles the answers and errors.
"""

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

SPACE_APP = Path(__file__).resolve().parents[1] / "hf_space" / "app.py"


@pytest.fixture(scope="module")
def space():
    """Loads hf_space/app.py as a module (it is not a package)."""
    spec = importlib.util.spec_from_file_location("space_app", SPACE_APP)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fake_response(status_code, payload):
    """Builds a fake requests.Response."""
    response = MagicMock()
    response.ok = status_code < 400
    response.status_code = status_code
    response.json.return_value = payload
    return response


def test_space_returns_result(space):
    with patch.object(
        space.requests, "post", return_value=fake_response(200, {"result": 8})
    ) as post:
        assert space.calculate(5, 3, "add") == "8"
    assert post.call_args.kwargs["data"] == {"op": "add", "a": 5, "b": 3}
    assert post.call_args.args[0].endswith("/calculate")


def test_space_shows_api_error(space):
    error = fake_response(400, {"detail": "Zero division not allowed"})
    with patch.object(space.requests, "post", return_value=error):
        assert space.calculate(5, 0, "divide") == "Error 400: Zero division not allowed"


def test_space_handles_timeout(space):
    with patch.object(
        space.requests, "post", side_effect=requests.exceptions.Timeout()
    ):
        assert "did not answer in time" in space.calculate(1, 2, "add")


def test_space_handles_connection_error(space):
    with patch.object(
        space.requests, "post", side_effect=requests.exceptions.ConnectionError("down")
    ):
        assert "could not connect" in space.calculate(1, 2, "add")


def test_space_requires_both_numbers(space):
    assert space.calculate(None, 2, "add") == "Error: both numbers are required"
