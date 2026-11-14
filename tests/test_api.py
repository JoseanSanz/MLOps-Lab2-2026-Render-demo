"""
Integration testing with the API
"""

import pytest
from fastapi.testclient import TestClient

from api.api import app


@pytest.fixture
def client():
    """Testing client from FastAPI."""
    return TestClient(app)


def test_home_endpoint(client):
    """Verify that the endpoint / returns the home page."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Calculator" in response.text


def test_health_endpoint(client):
    """Verify that the health check answers."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "op, a, b, expected",
    [
        ("add", 5, 3, 8),
        ("subtract", 5, 3, 2),
        ("multiply", 5, 3, 15),
        ("divide", 6, 3, 2),
        ("power", 2, 3, 8),
        ("ADD", 1, 1, 2),  # the operation is case-insensitive
    ],
)
def test_calculate_operations(client, op, a, b, expected):
    """Verify that the endpoint /calculate performs every operation correctly."""
    response = client.post("/calculate", data={"op": op, "a": a, "b": b})
    assert response.status_code == 200
    assert response.json() == {"result": expected}


def test_calculate_divide_by_zero(client):
    """Verify that the division by zero is rejected."""
    response = client.post("/calculate", data={"op": "divide", "a": 5, "b": 0})
    assert response.status_code == 400
    assert response.json()["detail"] == "Zero division not allowed"


def test_calculate_invalid_operation(client):
    """Verify that unknown operations are rejected."""
    response = client.post("/calculate", data={"op": "invalid_op", "a": 5, "b": 3})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid operation"


def test_calculate_overflow(client):
    """Verify that a result too large to represent is rejected."""
    response = client.post("/calculate", data={"op": "power", "a": 10, "b": 1000})
    assert response.status_code == 400
    assert response.json()["detail"] == "Result too large"


def test_calculate_complex_result(client):
    """Verify that a complex result (negative base, fractional exponent) is rejected."""
    response = client.post("/calculate", data={"op": "power", "a": -8, "b": 0.5})
    assert response.status_code == 400
    assert response.json()["detail"] == "The result is not a finite real number"


def test_calculate_invalid_parameters(client):
    """Verify that non-numeric parameters are rejected."""
    response = client.post("/calculate", data={"op": "add", "a": "five", "b": 3})
    assert response.status_code == 422  # FastAPI returns 422 for validation errors
    assert "detail" in response.json()


def test_calculate_missing_parameters(client):
    """Verify that missing parameters are rejected."""
    response = client.post("/calculate", data={"op": "add", "a": 5})  # 'b' missed
    assert response.status_code == 422  # FastAPI returns 422 for validation errors
    assert "detail" in response.json()
