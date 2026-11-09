"""
IIN (Individual Identification Number) Validation Service for Republic of Kazakhstan.
Implements birth date, century/gender classification, and official checksum calculation.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from datetime import datetime
from typing import Any

W1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
W2 = [3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2]


def validate_iin(iin_code: str) -> tuple[bool, str]:
    """
    Validates a 12-digit Kazakhstani Individual Identification Number (ИИН).

    Rules:
    1. Exactly 12 numeric digits.
    2. Digits 1-6: YYMMDD date.
    3. Digit 7: Century and gender:
       1 - Male, born 1801-1900
       2 - Female, born 1801-1900
       3 - Male, born 1901-2000
       4 - Female, born 1901-2000
       5 - Male, born 2001-2100
       6 - Female, born 2001-2100
    4. Digit 12: Cyclic checksum using W1 and W2.
    """
    if not isinstance(iin_code, str):
        return False, "ИИН должен быть строкой"

    clean_iin = iin_code.strip()
    if len(clean_iin) != 12:
        return False, f"Длина ИИН должна составлять 12 цифр (получено {len(clean_iin)})"

    if not clean_iin.isdigit():
        return False, "ИИН должен содержать только арабские цифры"

    century_digit = int(clean_iin[6])
    if century_digit not in (1, 2, 3, 4, 5, 6):
        return False, f"Некорректный разряд века/пола в ИИН: {century_digit}"

    year_short = int(clean_iin[0:2])
    month = int(clean_iin[2:4])
    day = int(clean_iin[4:6])

    if not (1 <= month <= 12):
        return False, f"Некорректный месяц рождения в ИИН: {month:02d}"

    if not (1 <= day <= 31):
        return False, f"Некорректный день рождения в ИИН: {day:02d}"

    # Calculate full year
    if century_digit in (1, 2):
        full_year = 1800 + year_short
    elif century_digit in (3, 4):
        full_year = 1900 + year_short
    else:
        full_year = 2000 + year_short

    # Check calendar date validity
    try:
        datetime(year=full_year, month=month, day=day)
    except ValueError:
        return False, f"Несуществующая календарная дата в ИИН: {day:02d}.{month:02d}.{full_year}"

    digits = [int(c) for c in clean_iin]

    # Stage 1: Weight W1
    s1 = sum(d * w for d, w in zip(digits[:11], W1)) % 11
    if s1 < 10:
        control_digit = s1
    else:
        # Stage 2: Weight W2
        s2 = sum(d * w for d, w in zip(digits[:11], W2)) % 11
        if s2 < 10:
            control_digit = s2
        else:
            return (
                False,
                "Недействительный ИИН (контрольная сумма не формируется по алгоритму КГД МФ РК)",
            )

    if control_digit != digits[11]:
        return (
            False,
            f"Несовпадение контрольного разряда ИИН: ожидалось {control_digit}, указано {digits[11]}",
        )

    return True, "ИИН валиден"


def parse_iin_info(iin_code: str) -> dict[str, Any]:
    """Extracts demographic metadata encoded within the IIN."""
    is_valid, msg = validate_iin(iin_code)
    if not is_valid:
        return {"valid": False, "error": msg, "iin": iin_code}

    clean_iin = iin_code.strip()
    century_digit = int(clean_iin[6])
    year_short = int(clean_iin[0:2])
    month = int(clean_iin[2:4])
    day = int(clean_iin[4:6])

    if century_digit in (1, 2):
        full_year = 1800 + year_short
    elif century_digit in (3, 4):
        full_year = 1900 + year_short
    else:
        full_year = 2000 + year_short

    gender = "Мужской" if century_digit % 2 != 0 else "Женский"
    birthdate_str = f"{day:02d}.{month:02d}.{full_year}"

    return {
        "valid": True,
        "iin": clean_iin,
        "birthdate": birthdate_str,
        "gender": gender,
        "year": full_year,
        "month": month,
        "day": day,
    }
