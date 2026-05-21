def get_risk_level_color(score: int) -> str:
    """
    Returns the tailwind color classes matching the severity of risk score.
    """
    if score < 25:
        return "green"
    elif score < 45:
        return "yellow"
    elif score < 70:
        return "orange"
    elif score < 88:
        return "red"
    else:
        return "crimson"
