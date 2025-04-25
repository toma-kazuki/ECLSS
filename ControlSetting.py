CONTROL_RANGES = {
    "OGS": {"ppO2_lower_control_limit": 21.4, "ppO2_upper_control_limit": 21.6},
    "CDRS": {"ppCO2_lower_control_limit": 0.39, "ppCO2_upper_control_limit": 0.41}
}

PROCESS_CONTROL_RANGES = {
    "Sabatier": {"param": "CO2"},
}

def check_limits_and_control(cabin, subsystems):
    """
    Adjusts subsystem status based on monitored cabin parameters.
    """

    #Carbon Dioxide Removal System  
    if cabin["water_tank"] < subsystems["CDRS"]["CO2_removal_rate"]:
        subsystems["OGS"]["status"] = False
    else:      
        if cabin["ppCO2"] > CONTROL_RANGES["CDRS"]["ppCO2_upper_control_limit"]:
            subsystems["CDRS"]["status"] = True 
        elif cabin["ppCO2"] < CONTROL_RANGES["CDRS"]["ppCO2_lower_control_limit"]:
            subsystems["CDRS"]["status"] = False

    # Oxygen Generator
    if cabin["water_tank"] < subsystems["OGS"]["water_consumption"]:
        subsystems["OGS"]["status"] = False
    else:
        if cabin["ppO2"] < CONTROL_RANGES["OGS"]["ppO2_lower_control_limit"]:
            subsystems["OGS"]["status"] = True
        elif cabin["ppO2"] > CONTROL_RANGES["OGS"]["ppO2_upper_control_limit"]:
            subsystems["OGS"]["status"] = False

    # Sabatier Reactor
    if subsystems["CDRS"]["CO2_removal_delta"] > 0:
        subsystems["Sabatier"]["status"] = True
    else:
        subsystems["Sabatier"]["status"] = False

    # Water Recovery System
    if cabin["wasted_water"]["storage"] < cabin["wasted_water"]["storage"]:
        subsystems["WRS"]["status"] = False
    else:
        subsystems["WRS"]["status"] = True
        subsystems["WRS"]["water_process_input"] = cabin["wasted_water"]["input"]


    return subsystems, CONTROL_RANGES
