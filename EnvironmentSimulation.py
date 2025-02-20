MOLAR_MASS_O2 = 32.0
MOLAR_MASS_CO2 = 44.0
MOLAR_VOLUME = 22.4
CABIN_VOLUME = 100.0
SECONDS_PER_DAY = 86400

RESPIRATION = {
    "O2_consumption_per_day": 0.84,  # kg/日
    "CO2_production_per_day": 1.0,   # kg/日
    "water_consumption_per_day": 3.0,  # L/日
    "crew_size": 4,
}

def human_respiration_effect(cabin, time_step=1):
    """
    Updates the oxygen and CO2 levels in the cabin due to human respiration.
    """
    O2_consumed = (RESPIRATION["O2_consumption_per_day"] * 1000 / MOLAR_MASS_O2 / SECONDS_PER_DAY) * RESPIRATION["crew_size"] * time_step
    CO2_produced = (RESPIRATION["CO2_production_per_day"] * 1000 / MOLAR_MASS_CO2 / SECONDS_PER_DAY) * RESPIRATION["crew_size"] * time_step

    cabin["ppO2"] -= (O2_consumed * MOLAR_VOLUME) / CABIN_VOLUME
    cabin["ppCO2"] += (CO2_produced * MOLAR_VOLUME) / CABIN_VOLUME

    return cabin

def human_water_consumption(cabin, time_step=1):
    """
    Calculates human water consumption and updates water tank.
    """
    water_consumed = (RESPIRATION["water_consumption_per_day"] / SECONDS_PER_DAY) * RESPIRATION["crew_size"] * time_step
    cabin["water_tank"] -= water_consumed  # Use water from the tank
    cabin["water_tank"] = max(cabin["water_tank"], 0)  # Prevent negative values
    return water_consumed

def water_recovery_system(cabin, subsystems, water_consumed, time_step=1):
    """
    Simulates water recovery, storing recovered water in the water tank.
    """
    if subsystems["WRS"].get("status", False):
        recovered_water = water_consumed * subsystems["WRS"]["water_recovery_rate"]
        cabin["water_tank"] += recovered_water  # Store in water tank
    return cabin

def oxygen_generation_system(cabin, subsystems, time_step=1):
    """
    Simulates the Oxygen Generation System (OGS) which generates oxygen and consumes water from the water tank.
    """
    if subsystems["OGS"]["status"] and cabin["water_tank"] > subsystems["OGS"]["water_consumption"] * time_step:
        O2_generated = subsystems["OGS"]["O2_rate"] * time_step
        cabin["ppO2"] += (O2_generated * MOLAR_VOLUME) / CABIN_VOLUME
        cabin["water_tank"] -= subsystems["OGS"]["water_consumption"] * time_step  # Use water from water tank
        cabin["water_tank"] = max(cabin["water_tank"], 0)  # Prevent negative values
    return cabin

def carbon_dioxide_removal_system(cabin, subsystems, time_step=1):
    """
    Simulates the Carbon Dioxide Removal System (CDRS) which removes CO2 from the cabin.
    """
    if subsystems["CDRS"]["status"]:
        CO2_removed = subsystems["CDRS"]["CO2_removal_rate"] * time_step
        cabin["ppCO2"] -= (CO2_removed * MOLAR_VOLUME) / CABIN_VOLUME
        cabin["ppCO2"] = max(cabin["ppCO2"], 0)  # Prevent negative ppCO2
    return cabin

def simulate_step(cabin, subsystems, current_step, time_step=1):
    """
    Simulates one time step in the ECLSS system, including human respiration,
    water consumption, and subsystem effects such as OGS and CDRS.
    """
    from FailureSetting import apply_failures

    # Apply system failures
    subsystems = apply_failures(subsystems, current_step)

    # Human respiration effects
    cabin = human_respiration_effect(cabin, time_step)
    
    # Human water consumption (from water tank)
    water_consumed = human_water_consumption(cabin, time_step)
    
    # Water recovery system (restored water goes into water tank)
    cabin = water_recovery_system(cabin, subsystems, water_consumed, time_step)

    # OGS and CDRS effects in one line each
    cabin = oxygen_generation_system(cabin, subsystems, time_step)
    cabin = carbon_dioxide_removal_system(cabin, subsystems, time_step)

    return cabin, subsystems
