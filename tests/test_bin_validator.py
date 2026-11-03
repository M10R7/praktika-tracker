"""
Unit tests for Kazakhstani BIN validation service.
"""

import pytest

from src.services.bin_validator import parse_bin_info, validate_bin


@pytest.mark.parametrize(
    "bin_code",
    [
        "081240012740",  # Kaspi Bank
        "941240000193",  # Kazakhtelecom
        "200540001235",  # Computed valid BIN
    ],
)
def test_valid_bins(bin_code: str):
    is_valid, msg = validate_bin(bin_code)
    assert is_valid is True
    assert "БИН валиден" in msg


@pytest.mark.parametrize(
    "bin_code,expected_error",
    [
        ("123", "Длина БИН должна быть 12 цифр"),
        ("1234567890123", "Длина БИН должна быть 12 цифр"),
        ("08124001274A", "БИН должен состоять только из арабских цифр"),
        ("201340001235", "Некорректный месяц"),
        ("200540001239", "Несовпадение контрольного разряда"),
    ],
)
def test_invalid_bins(bin_code: str, expected_error: str):
    is_valid, msg = validate_bin(bin_code)
    assert is_valid is False
    assert expected_error in msg


def test_invalid_type_input():
    is_valid, msg = validate_bin(123456789012)  # type: ignore
    assert is_valid is False
    assert "строкой" in msg


def test_parse_bin_info_valid():
    info = parse_bin_info("081240012740")
    assert info["valid"] is True
    assert info["bin"] == "081240012740"
    assert info["registration_year"] == 2008
    assert info["registration_month"] == 12
    assert "Юридическое лицо" in info["legal_type"]


def test_parse_bin_info_invalid():
    info = parse_bin_info("000000000000")
    assert info["valid"] is False
    assert "error" in info
