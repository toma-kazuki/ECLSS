MOLAR_MASS_O2 = 32.0 # g/mol
MOLAR_MASS_CO2 = 44.0 # g/mol
MOLAR_MASS_H2 = 2.0 # g/mol
MOLAR_MASS_H2O = 18.0 # g/mol
MOLAR_VOLUME = 22.4 
CABIN_VOLUME = 100.0 
SECONDS_PER_DAY = 86400

RESPIRATION = {
    "O2_consumption_per_day": 0.84,  # kg/day
    "CO2_production_per_day": 1.0,   # kg/day
    "water_consumption_per_day": 3.0,  # L/day
    "crew_size": 4,
}

def human_respiration_effect(cabin, time_step=1):
    """
    Updates the oxygen and CO2 levels in the cabin due to human respiration.
    """
    O2_consumed = (RESPIRATION["O2_consumption_per_day"] * 1000 / MOLAR_MASS_O2 / SECONDS_PER_DAY) * RESPIRATION["crew_size"] * time_step # mol/s
    CO2_produced = (RESPIRATION["CO2_production_per_day"] * 1000 / MOLAR_MASS_CO2 / SECONDS_PER_DAY) * RESPIRATION["crew_size"] * time_step

    cabin["ppO2"] -= (O2_consumed * MOLAR_VOLUME) / CABIN_VOLUME
    cabin["ppCO2"] += (CO2_produced * MOLAR_VOLUME) / CABIN_VOLUME

    return cabin

def human_water_consumption(cabin, time_step=1):
    """
    Calculates human water consumption and updates water tank.
    """
    water_consumed = (RESPIRATION["water_consumption_per_day"] / SECONDS_PER_DAY) * RESPIRATION["crew_size"] * time_step
    if cabin["water_tank"] >= water_consumed:
        cabin["water_tank"] -= water_consumed
        cabin["wasted_water"]["input"] = water_consumed
        cabin["wasted_water"]["storage"] += water_consumed
    else:
        print("WATER SHORTAGE -> MISSION FAILURE!!!")
        cabin["mission_mode"] = "failure"
    return cabin

def water_recovery_system(cabin, subsystems, time_step=1):
    """
    Simulates water recovery, storing recovered water in the water tank.
    """
    if subsystems["WRS"]["status"]:
        input_water = subsystems["WRS"]["water_process_capability"]
        cabin["wasted_water"] -= input_water
        recovered_water = input_water * subsystems["WRS"]["water_recovery_rate"]
        cabin["water_tank"] += recovered_water
    return cabin

def oxygen_generation_system(cabin, subsystems, time_step=1):
    """
    Simulates the Oxygen Generation System (OGS) which generates oxygen and consumes water from the water tank.
    """
    if subsystems["OGS"]["status"]:
        water_consumed = subsystems["OGS"]["water_consumption"] * time_step
        cabin["water_tank"] -= water_consumed
        #subsystems["OGS"]["O2_rate"] = #####
        O2_generated = subsystems["OGS"]["O2_rate"] * time_step
        cabin["ppO2"] += (O2_generated * MOLAR_VOLUME) / CABIN_VOLUME
    return cabin

def carbon_dioxide_removal_system(cabin, subsystems, time_step=1):
    """
    Simulates the Carbon Dioxide Removal System (CDRS) which removes CO2 from the cabin.
    """
    CO2_removed = 0.0
    if subsystems["CDRS"]["status"]:
        CO2_removed = subsystems["CDRS"]["CO2_removal_rate"] * time_step
        cabin["ppCO2"] -= (CO2_removed * MOLAR_VOLUME) / CABIN_VOLUME
    subsystems["CDRS"]["CO2_removal_delta"] = CO2_removed
    return cabin

def sabatier_reactor(cabin, subsystems, time_step=1):
    """
    Simulates the Sabatier Reactor, converting CO2 and H2 into water.
    Reaction: CO2 + 4H2 → CH4 + 2H2O
    """
    if subsystems["Sabatier"]["status"]:
        # Water produced from CO2 (2 mol H2O per 1 mol CO2)
        H2O_produced = (subsystems["CDRS"]["CO2_removal_delta"] * 2 * MOLAR_MASS_H2O) / MOLAR_MASS_CO2
        cabin["water_tank"] += H2O_produced  # Store generated water in the water tank
    return cabin

def simulate_init():
    cabin = {
        "ppO2": 21.0, 
        "ppCO2": 0.4, 
        "wasted_water": {
            "storage": 0.0, 
            "input": 0.0}, 
        "water_tank": 100.0, 
        "mission_mode": "nominal"}
    subsystems = {
        "OGS":{
            "status": True, 
            "O2_rate": 0.5, 
            "water_consumption": 1.0},
        "CDRS": {
            "status": True, 
            "CO2_removal_rate": 0.003, 
            "CO2_removal_delta": 0},
        "WRS": {
            "status": True, 
            "water_process_capability": 0, 
            "water_recovery_rate": 0.95},
        "Sabatier": {
            "status": True}
    }
    return cabin, subsystems


def simulate_step(cabin, subsystems, current_step, time_step=1):
    """
    Simulates one time step in the ECLSS system, including human respiration,
    water consumption, and subsystem effects such as OGS, CDRS, and Sabatier Reactor.
    """
    from FailureSetting import apply_failures

    # Apply system failures
    subsystems = apply_failures(subsystems, current_step)

    # Human respiration effects
    cabin = human_respiration_effect(cabin, time_step)
    
    # Human water consumption (from water tank)
    cabin = human_water_consumption(cabin, time_step)
    
    # WRS effects
    cabin = water_recovery_system(cabin, subsystems, time_step)

    # CDRS effects
    cabin = carbon_dioxide_removal_system(cabin, subsystems, time_step)
    
    # OGS effects
    cabin = oxygen_generation_system(cabin, subsystems, time_step)

    # Sabatier effects
    cabin = sabatier_reactor(cabin, subsystems, time_step)

    return cabin, subsystems
