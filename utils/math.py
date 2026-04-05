"""Standard and scientific calculator utilities."""

import math
from typing import Any


def add(a: float, b: float) -> dict[str, float]:
    """Add two numbers."""
    return {"result": float(a) + float(b)}


def subtract(a: float, b: float) -> dict[str, float]:
    """Subtract b from a."""
    return {"result": float(a) - float(b)}


def multiply(a: float, b: float) -> dict[str, float]:
    """Multiply two numbers."""
    return {"result": float(a) * float(b)}


def divide(a: float, b: float) -> dict[str, Any]:
    """Divide a by b."""
    if b == 0:
        return {"error": "Division by zero"}
    return {"result": float(a) / float(b)}


def modulo(a: float, b: float) -> dict[str, Any]:
    """Get remainder of a divided by b."""
    if b == 0:
        return {"error": "Division by zero"}
    return {"result": float(a) % float(b)}


def power(base: float, exponent: float) -> dict[str, float]:
    """Raise base to the power of exponent."""
    return {"result": float(base) ** float(exponent)}


def square_root(a: float) -> dict[str, Any]:
    """Get the square root of a number."""
    if a < 0:
        return {"error": "Cannot compute square root of negative number"}
    return {"result": math.sqrt(float(a))}


def absolute(a: float) -> dict[str, float]:
    """Get the absolute value of a number."""
    return {"result": abs(float(a))}


def factorial(n: int) -> dict[str, Any]:
    """Get the factorial of a non-negative integer."""
    if n < 0:
        return {"error": "Factorial undefined for negative numbers"}
    return {"result": math.factorial(int(n))}


# --- Scientific ---


def log(a: float, base: float = 10.0) -> dict[str, Any]:
    """Logarithm of a with given base (default base 10)."""
    if a <= 0:
        return {"error": "Logarithm undefined for non-positive numbers"}
    if base <= 0 or base == 1:
        return {"error": "Invalid logarithm base"}
    return {"result": math.log(float(a), float(base))}


def ln(a: float) -> dict[str, Any]:
    """Natural logarithm (base e) of a."""
    if a <= 0:
        return {"error": "Logarithm undefined for non-positive numbers"}
    return {"result": math.log(float(a))}


def sin(degrees: float) -> dict[str, float]:
    """Sine of an angle in degrees."""
    return {"result": math.sin(math.radians(float(degrees)))}


def cos(degrees: float) -> dict[str, float]:
    """Cosine of an angle in degrees."""
    return {"result": math.cos(math.radians(float(degrees)))}


def tan(degrees: float) -> dict[str, float]:
    """Tangent of an angle in degrees."""
    return {"result": math.tan(math.radians(float(degrees)))}


def asin(value: float) -> dict[str, Any]:
    """Inverse sine, returns angle in degrees."""
    if not -1 <= value <= 1:
        return {"error": "Value must be between -1 and 1"}
    return {"result": math.degrees(math.asin(float(value)))}


def acos(value: float) -> dict[str, Any]:
    """Inverse cosine, returns angle in degrees."""
    if not -1 <= value <= 1:
        return {"error": "Value must be between -1 and 1"}
    return {"result": math.degrees(math.acos(float(value)))}


def atan(value: float) -> dict[str, float]:
    """Inverse tangent, returns angle in degrees."""
    return {"result": math.degrees(math.atan(float(value)))}


def degrees_to_radians(degrees: float) -> dict[str, float]:
    """Convert degrees to radians."""
    return {"result": math.radians(float(degrees))}


def radians_to_degrees(radians: float) -> dict[str, float]:
    """Convert radians to degrees."""
    return {"result": math.degrees(float(radians))}


def ceil(a: float) -> dict[str, int]:
    """Round up to the nearest integer."""
    return {"result": math.ceil(float(a))}


def floor(a: float) -> dict[str, int]:
    """Round down to the nearest integer."""
    return {"result": math.floor(float(a))}


def round_number(a: float, decimals: int = 0) -> dict[str, float]:
    """Round a number to a given number of decimal places."""
    return {"result": round(float(a), int(decimals))}


def hypotenuse(a: float, b: float) -> dict[str, float]:
    """Compute the hypotenuse of a right triangle."""
    return {"result": math.hypot(float(a), float(b))}


def constants() -> dict[str, Any]:
    """Return common mathematical constants."""
    return {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        "inf": "Infinity",
    }
