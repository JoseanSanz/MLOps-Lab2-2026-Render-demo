"""
Calculator library: the business logic shared by the CLI and the API.
"""


def add(a: float, b: float) -> float:
    """Returns the sum of a and b."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Returns the subtraction of b from a."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Returns the multiplication of a and b."""
    return a * b


def divide(a: float, b: float) -> float:
    """Returns the division of a by b (raises ZeroDivisionError if b is 0)."""
    return a / b


def power(a: float, b: float) -> float | complex:
    """Returns a raised to the power of b.

    The result can be complex (e.g., a negative base with a fractional exponent)
    or raise OverflowError if it is too large.
    """
    return a**b
