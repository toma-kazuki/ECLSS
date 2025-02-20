CONTROL_RANGES = {
    "OGS": {"param": "ppO2", "min": 21.4, "max": 21.6, "activate_on": "below_min"},
    "CDRS": {"param": "ppCO2", "min": 0.39, "max": 0.41, "activate_on": "above_max"},
    "WRS": {"param": "water_tank", "min": 10, "max": 120, "activate_on": "below_min"},
}

def check_limits_and_control(cabin, subsystems):
    """
    Adjusts subsystem status based on monitored cabin parameters.
    """

    # Embed control ranges within respective subsystems
    for system, control in CONTROL_RANGES.items():
        subsystems[system]["control_range"] = {"min": control["min"], "max": control["max"]}

        param = control["param"]
        if control["activate_on"] == "above_max":
            if cabin[param] > control["max"]:
                subsystems[system]["status"] = True 
            elif cabin[param] < control["min"]:
                subsystems[system]["status"] = False
        elif control["activate_on"] == "below_min":
            if cabin[param] < control["min"]:
                subsystems[system]["status"] = True
            elif cabin[param] > control["max"]:
                subsystems[system]["status"] = False

    return subsystems
