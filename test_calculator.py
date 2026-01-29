"""
Tests for calculator module.
Some tests may be incomplete or broken - fix them!
"""

import pytest
from calculator import add, subtract, multiply, divide, power


def test_add():
    """Test addition function."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    # TODO: Add more test cases


def test_subtract():
    """Test subtraction function."""
    assert subtract(5, 3) == 2
    # TODO: Add more test cases


def test_multiply():
    """Test multiplication function."""
    assert multiply(3, 4) == 12
    # TODO: Add more test cases


def test_divide():
    """Test division function."""
    assert divide(10, 2) == 5
    # TODO: Add test for division by zero
    # TODO: Add more test cases


def test_power():
    """Test power function."""
    assert power(2, 2) == 4
    assert power(2, 3) == 8

