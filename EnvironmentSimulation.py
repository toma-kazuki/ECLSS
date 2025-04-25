import scipy.constants as const

MOLAR_MASS_O2 = 32.0  # g/mol
MOLAR_MASS_CO2 = 44.0  # g/mol
MOLAR_MASS_H2 = 2.0  # g/mol
MOLAR_MASS_H2O = 18.0  # g/mol
CABIN_VOLUME = 100.0  # m^3 
# HERA Total space: 148.1 m3 (about 636 ft2)
#   Core (56.0 m3)
#   Loft (69.9 m3)
#   Airlock (8.6 m3)
#   Hygiene Module (14.1 m3)
CABIN_TEMPERATURE = 293.15  # K (約20°C)
H2_TANK_VOLUME = 5.0  # m^3 (仮定)
R = const.R  # J/(mol K) ≈ 8.314
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
    Uses the ideal gas law for pressure change calculations.
    """
    O2_consumed = (RESPIRATION["O2_consumption_per_day"] * 1000 / MOLAR_MASS_O2 / SECONDS_PER_DAY) * RESPIRATION["crew_size"] * time_step  # mol
    CO2_produced = (RESPIRATION["CO2_production_per_day"] * 1000 / MOLAR_MASS_CO2 / SECONDS_PER_DAY) * RESPIRATION["crew_size"] * time_step  # mol

    # 圧力変化を理想気体方程式から求める
    delta_pO2 = (O2_consumed * R * CABIN_TEMPERATURE) / CABIN_VOLUME  # Pa
    delta_pCO2 = (CO2_produced * R * CABIN_TEMPERATURE) / CABIN_VOLUME  # Pa

    # kPa に変換 (1 kPa = 1000 Pa)
    cabin["ppO2"] -= delta_pO2 / 1000
    cabin["ppCO2"] += delta_pCO2 / 1000

    return cabin

def human_water_consumption(cabin, time_step=1):
    """
    Calculates human water consumption and updates water tank.
    """
    water_consumed = (RESPIRATION["water_consumption_per_day"] / SECONDS_PER_DAY) * RESPIRATION["crew_size"] * time_step # L/s
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
        input_water = subsystems["WRS"]["water_process_input"]
        cabin["wasted_water"]["storage"] -= input_water
        recovered_water = input_water * subsystems["WRS"]["water_recovery_rate"]
        cabin["water_tank"] += recovered_water
    return cabin

def oxygen_generation_system(cabin, subsystems, time_step=1):
    """
    Simulates the Oxygen Generation System (OGS).
    Produces O2 and stores it in the cabin using the ideal gas law.
    Also generates H2 and stores it in the H2 tank.
    """
    if subsystems["OGS"]["status"]:
        water_consumed = subsystems["OGS"]["water_consumption"] * time_step  # L
        moles_H2O = water_consumed * 1000 / MOLAR_MASS_H2O  # mol
        O2_generated = moles_H2O / 2  # mol O2
        H2_generated = moles_H2O  # mol H2

        # 圧力変化計算
        delta_pO2 = (O2_generated * R * CABIN_TEMPERATURE) / CABIN_VOLUME  # Pa
        delta_pH2 = (H2_generated * R * CABIN_TEMPERATURE) / H2_TANK_VOLUME  # Pa

        # キャビンに酸素追加
        cabin["ppO2"] += delta_pO2 / 1000  # kPa に変換

        # 水素タンクに水素追加
        cabin["H2storage"] += H2_generated

        subsystems["OGS"]["O2_rate"] = O2_generated / time_step  # mol/s
    return cabin

def carbon_dioxide_removal_system(cabin, subsystems, time_step=1):
    """
    Simulates the Carbon Dioxide Removal System (CDRS).
    """
    if subsystems["CDRS"]["status"]:
        CO2_removed = subsystems["CDRS"]["CO2_removal_rate"] * time_step  # mol
        delta_pCO2 = (CO2_removed * R * CABIN_TEMPERATURE) / CABIN_VOLUME  # Pa
        cabin["ppCO2"] -= delta_pCO2 / 1000  # kPa に変換
        subsystems["CDRS"]["CO2_removal_delta"] = CO2_removed
    return cabin

def sabatier_reactor(cabin, subsystems, time_step=1):
    """
    Simulates the Sabatier Reactor, converting CO2 and H2 into water.
    Reaction: CO2 + 4H2 → CH4 + 2H2O
    """
    if subsystems["Sabatier"]["status"]:
        CO2_available = subsystems["CDRS"]["CO2_removal_delta"]  # mol
        H2_available = cabin["H2storage"]  # mol

        # 必要なH2量
        H2_needed = 4 * CO2_available  # 4 mol H2 per 1 mol CO2

        # 実際に反応できるCO2とH2の量
        if H2_available >= H2_needed:
            CO2_used = CO2_available
            H2_used = H2_needed
        else:
            CO2_used = H2_available / 4  # H2が足りない場合
            H2_used = H2_available

        # 生成水量
        H2O_produced = CO2_used * 2 * MOLAR_MASS_H2O / 1000  # kg ≈ L (water)
        CH4_produced = CO2_used  # mol CH4

        # 水素タンクの更新
        cabin["H2storage"] -= H2_used

        # CH4タンクの更新
        cabin["CH4storage"] -= CH4_produced

        # 水タンクに水を追加
        cabin["water_tank"] += H2O_produced

        # 反応したCO2の量をCDRSの記録として保存
        subsystems["CDRS"]["CO2_removal_delta"] -= CO2_used

    return cabin

def simulate_init():
    cabin = {
        "ppO2": 21.5, # kPa
        "ppCO2": 0.4, #kPa
        "wasted_water": {
            "storage": 0.0, # L
            "input": 0.0},  # L
        "water_tank": 100.0,  # L
        "H2storage": 100.0,  # Initialize hydrogen storage
        "CH4storage": 0.0,  # Initialize hydrogen storage
        "mission_mode": "nominal"}
    subsystems = {
        "OGS":{
            "status": False, 
            "O2_rate": 0, 
            "water_consumption": 0.1}, # L/s
        "CDRS": {
            "status": True, 
            "CO2_removal_rate": 0.003, 
            "CO2_removal_delta": 0},
        "WRS": {
            "status": True, 
            "water_process_input": 0, 
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

    # Sabatier effects
    cabin = sabatier_reactor(cabin, subsystems, time_step)

    # CDRS effects
    cabin = carbon_dioxide_removal_system(cabin, subsystems, time_step)
    
    # OGS effects
    cabin = oxygen_generation_system(cabin, subsystems, time_step)


    return cabin, subsystems
