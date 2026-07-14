def math_prices(value_a: float | None, value_b: float | None):
    if value_a is None or value_b is None:
        return {"delta": None, "percent": None, "value_a": value_a, "value_b": value_b}

    delta = value_a - value_b
    percent = (delta / value_b * 100) if value_b != 0 else 0.0

    return {
        "value_a": value_a,
        "value_b": value_b,
        "delta": round(delta, 2),
        "percent": round(percent, 2),
    }