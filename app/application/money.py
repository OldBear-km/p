def format_rub(amount_cents: int) -> str:
    """
    amount_cents: целое число в копейках (может быть отрицательным).
    """
    sign = "-" if amount_cents < 0 else ""
    amount_cents = abs(int(amount_cents))
    rub = amount_cents // 100
    kop = amount_cents % 100

    # 1 234 567,89 ₽
    rub_str = f"{rub:,}".replace(",", " ")
    return f"{sign}{rub_str},{kop:02d} ₽"
