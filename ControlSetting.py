CONTROL_RANGES = {
    "ppO2": {"min": 21.4, "max": 21.6},
    "ppCO2": {"min": 0.39, "max": 0.41},
    "water": {"min": 10, "max": 120},
}

def check_limits_and_control(cabin, subsystems):
    """
    Adjusts subsystem status based on monitored cabin parameters.
    """
    if cabin["ppO2"] > CONTROL_RANGES["ppO2"]["max"]:
        subsystems["OGS"]["status"] = False
    elif cabin["ppO2"] < CONTROL_RANGES["ppO2"]["min"]:
        subsystems["OGS"]["status"] = True

    if cabin["ppCO2"] > CONTROL_RANGES["ppCO2"]["max"]:
        subsystems["CDRS"]["status"] = True
    elif cabin["ppCO2"] < CONTROL_RANGES["ppCO2"]["min"]:
        subsystems["CDRS"]["status"] = False

    if cabin["water"] < CONTROL_RANGES["water"]["min"]:
        subsystems["WRS"]["status"] = True
    elif cabin["water"] > CONTROL_RANGES["water"]["max"]:
        subsystems["WRS"]["status"] = False

    return subsystems