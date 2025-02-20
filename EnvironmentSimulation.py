MOLAR_MASS_O2 = 32.0
MOLAR_MASS_CO2 = 44.0
MOLAR_VOLUME = 22.4
CABIN_VOLUME = 100.0
SECONDS_PER_DAY = 86400

RESPIRATION = {
    "O2_consumption_per_day": 0.84*100,
    "CO2_production_per_day": 1.0,
    "water_consumption_per_day": 3.0,
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
    Calculates human water consumption.
    """
    water_consumed = (RESPIRATION["water_consumption_per_day"] / SECONDS_PER_DAY) * RESPIRATION["crew_size"] * time_step
    cabin["water"] -= water_consumed
    return water_consumed

def water_recovery_system(cabin, subsystems, water_consumed, time_step=1):
    """
    Simulates water recovery.
    """
    if subsystems["WRS"].get("status", False):
        cabin["water"] += water_consumed * subsystems["WRS"]["water_recovery_rate"]
    return cabin

def simulate_step(cabin, subsystems, current_step, time_step=1):
    """
    Simulates one time step in the ECLSS system.
    """
    from FailureSetting import apply_failures

    subsystems = apply_failures(subsystems, current_step)
    cabin = human_respiration_effect(cabin, time_step)
    water_consumed = human_water_consumption(cabin, time_step)
    cabin = water_recovery_system(cabin, subsystems, water_consumed, time_step)

    return cabin, subsystems