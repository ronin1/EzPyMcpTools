"""Tests for math utilities."""

from __future__ import annotations

from utils import math as math_utils


def test_basic_math_operations() -> None:
    assert math_utils.add(1, 2)["result"] == 3
    assert math_utils.subtract(5, 3)["result"] == 2
    assert math_utils.multiply(3, 4)["result"] == 12
    assert math_utils.divide(8, 2)["result"] == 4


def test_math_error_paths() -> None:
    assert "error" in math_utils.divide(8, 0)
    assert "error" in math_utils.square_root(-1)
    assert "error" in math_utils.factorial(-1)


def test_scientific_helpers() -> None:
    assert math_utils.round_number(3.14159, 2)["result"] == 3.14
    assert math_utils.constants()["inf"] == "Infinity"
