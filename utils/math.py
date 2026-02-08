"""Standard and scientific calculator utilities."""
import math


def add(a: float, b: float) -> dict:
    """Add two numbers."""
    return {"result": a + b}


def subtract(a: float, b: float) -> dict:
    """Subtract b from a."""
    return {"result": a - b}


def multiply(a: float, b: float) -> dict:
    """Multiply two numbers."""
    return {"result": a * b}


def divide(a: float, b: float) -> dict:
    """Divide a by b."""
    if b == 0:
        return {"error": "Division by zero"}
    return {"result": a / b}


def modulo(a: float, b: float) -> dict:
    """Get remainder of a divided by b."""
    if b == 0:
        return {"error": "Division by zero"}
    return {"result": a % b}


def power(base: float, exponent: float) -> dict:
    """Raise base to the power of exponent."""
    return {"result": base ** exponent}


def square_root(a: float) -> dict:
    """Get the square root of a number."""
    if a < 0:
        return {"error": "Cannot compute square root of negative number"}
    return {"result": math.sqrt(a)}


def absolute(a: float) -> dict:
    """Get the absolute value of a number."""
    return {"result": abs(a)}


def factorial(n: int) -> dict:
    """Get the factorial of a non-negative integer."""
    if n < 0:
        return {"error": "Factorial undefined for negative numbers"}
    return {"result": math.factorial(n)}


# --- Scientific ---


def log(a: float, base: float = 10.0) -> dict:
    """Logarithm of a with given base (default base 10)."""
    if a <= 0:
        return {"error": "Logarithm undefined for non-positive numbers"}
    if base <= 0 or base == 1:
        return {"error": "Invalid logarithm base"}
    return {"result": math.log(a, base)}


def ln(a: float) -> dict:
    """Natural logarithm (base e) of a."""
    if a <= 0:
        return {"error": "Logarithm undefined for non-positive numbers"}
    return {"result": math.log(a)}


def sin(degrees: float) -> dict:
    """Sine of an angle in degrees."""
    return {"result": math.sin(math.radians(degrees))}


def cos(degrees: float) -> dict:
    """Cosine of an angle in degrees."""
    return {"result": math.cos(math.radians(degrees))}


def tan(degrees: float) -> dict:
    """Tangent of an angle in degrees."""
    return {"result": math.tan(math.radians(degrees))}


def asin(value: float) -> dict:
    """Inverse sine, returns angle in degrees."""
    if not -1 <= value <= 1:
        return {"error": "Value must be between -1 and 1"}
    return {"result": math.degrees(math.asin(value))}


def acos(value: float) -> dict:
    """Inverse cosine, returns angle in degrees."""
    if not -1 <= value <= 1:
        return {"error": "Value must be between -1 and 1"}
    return {"result": math.degrees(math.acos(value))}


def atan(value: float) -> dict:
    """Inverse tangent, returns angle in degrees."""
    return {"result": math.degrees(math.atan(value))}


def degrees_to_radians(degrees: float) -> dict:
    """Convert degrees to radians."""
    return {"result": math.radians(degrees)}


def radians_to_degrees(radians: float) -> dict:
    """Convert radians to degrees."""
    return {"result": math.degrees(radians)}


def ceil(a: float) -> dict:
    """Round up to the nearest integer."""
    return {"result": math.ceil(a)}


def floor(a: float) -> dict:
    """Round down to the nearest integer."""
    return {"result": math.floor(a)}


def round_number(a: float, decimals: int = 0) -> dict:
    """Round a number to a given number of decimal places."""
    return {"result": round(a, decimals)}


def hypotenuse(a: float, b: float) -> dict:
    """Compute the hypotenuse of a right triangle."""
    return {"result": math.hypot(a, b)}


def constants() -> dict:
    """Return common mathematical constants."""
    return {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        "inf": "Infinity",
    }
