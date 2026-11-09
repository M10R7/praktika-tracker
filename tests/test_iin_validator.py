"""
Unit tests for Kazakhstani IIN validation service.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

import pytest

from src.services.iin_validator import parse_iin_info, validate_iin


@pytest.mark.parametrize(
    "iin_code",
    [
        "030514500012",
        "030822600023",
        "031110500039",
        "030219600045",
        "030704500055",
    ],
)
def test_valid_iins(iin_code: str):
    ok, msg = validate_iin(iin_code)
    assert ok is True
    assert msg == "ИИН валиден"


@pytest.mark.parametrize(
    "iin_code,err_part",
    [
        ("123", "Длина ИИН должна составлять 12 цифр"),
        ("0305145000123", "Длина ИИН должна составлять 12 цифр"),
        ("03051450001A", "только арабские цифры"),
        ("031314500012", "Некорректный месяц"),
        ("030535500012", "Некорректный день"),
        ("030229500012", "Несуществующая календарная дата"),  # 2003 is not a leap year!
        ("030514700012", "Некорректный разряд века/пола"),
        ("030514500019", "Несовпадение контрольного разряда"),
    ],
)
def test_invalid_iins(iin_code: str, err_part: str):
    ok, msg = validate_iin(iin_code)
    assert ok is False
    assert err_part in msg


def test_invalid_type_input():
    ok, msg = validate_iin(30514500012)  # type: ignore
    assert ok is False
    assert "строкой" in msg


def test_parse_iin_info_valid():
    info = parse_iin_info("030514500012")
    assert info["valid"] is True
    assert info["year"] == 2003
    assert info["month"] == 5
    assert info["day"] == 14
    assert info["gender"] == "Мужской"
    assert info["birthdate"] == "14.05.2003"


def test_parse_iin_info_invalid():
    info = parse_iin_info("000000000000")
    assert info["valid"] is False
    assert "error" in info
