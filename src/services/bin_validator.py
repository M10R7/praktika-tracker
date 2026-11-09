"""
BIN (Business Identification Number) Validation Service for Republic of Kazakhstan.
Implements the official checksum calculation algorithm using weights W1 and W2.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from typing import Any

W1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
W2 = [3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2]

LEGAL_ENTITY_TYPES = {
    "4": "Юридическое лицо - резидент",
    "5": "Юридическое лицо - нерезидент",
    "6": "Филиал или представительство",
}


def validate_bin(bin_code: str) -> tuple[bool, str]:
    """
    Validates a 12-digit Kazakhstani Business Identification Number (БИН).

    Rules:
    1. Must contain exactly 12 numeric digits.
    2. Digits 1-2: Year of registration (last 2 digits).
    3. Digits 3-4: Month of registration (01-12).
    4. Digit 5: Legal entity indicator (usually 4, 5, or 6).
    5. Digit 12: Control checksum digit computed using cyclic weights.

    Returns:
        (True, "БИН валиден") or (False, error_description)
    """
    if not isinstance(bin_code, str):
        return False, "БИН должен быть строкой"

    clean_bin = bin_code.strip()

    if len(clean_bin) != 12:
        return False, f"Длина БИН должна быть 12 цифр (получено {len(clean_bin)})"

    if not clean_bin.isdigit():
        return False, "БИН должен состоять только из арабских цифр"

    month = int(clean_bin[2:4])
    if not (1 <= month <= 12):
        return False, f"Некорректный месяц регистрации в БИН: {month:02d}"

    digits = [int(c) for c in clean_bin]

    # Stage 1: Weight W1
    s1 = sum(d * w for d, w in zip(digits[:11], W1)) % 11
    if s1 < 10:
        control_digit = s1
    else:
        # Stage 2: Weight W2 if remainder is 10
        s2 = sum(d * w for d, w in zip(digits[:11], W2)) % 11
        if s2 < 10:
            control_digit = s2
        else:
            return (
                False,
                "Недействительный БИН (контрольная сумма не формируется по алгоритму КГД МФ РК)",
            )

    if control_digit != digits[11]:
        return False, (
            f"Несовпадение контрольного разряда: ожидалось {control_digit}, "
            f"в БИН указано {digits[11]}"
        )

    return True, "БИН валиден и соответствует алгоритму КГД МФ РК"


def parse_bin_info(bin_code: str) -> dict[str, Any]:
    """
    Parses metadata encoded within the BIN structure.
    """
    is_valid, message = validate_bin(bin_code)
    if not is_valid:
        return {"valid": False, "error": message, "bin": bin_code}

    clean_bin = bin_code.strip()
    year_short = int(clean_bin[0:2])
    month = int(clean_bin[2:4])
    type_code = clean_bin[4]

    # Assume year >= 90 is 1990s, < 90 is 2000s
    full_year = (1900 + year_short) if year_short >= 90 else (2000 + year_short)

    return {
        "valid": True,
        "bin": clean_bin,
        "registration_year": full_year,
        "registration_month": month,
        "legal_type": LEGAL_ENTITY_TYPES.get(type_code, "Юридическое лицо (прочее)"),
        "status": "Verified",
    }
