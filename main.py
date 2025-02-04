import numpy as np
import matplotlib.pyplot as plt
import requests
import os
import json
import time
from datetime import datetime
# Simulation settings
real_time_mode = True  # Set to False to run as fast as possible
simulation_speed = 1.0  # 1.0 = real-time (1 second per step), 2.0 = 2x faster, etc.


# File path to the JSON file
json_file_path = 'temp.json'

# URL to post to
url = 'https://daphne-at-lab.selva-research.com/api/at/receiveHeraFeed'

# Define control ranges (safe limits) for monitored parameters
CONTROL_RANGES = {
    "ppO2": {"min": 21.4, "max": 21.6},  # kPa
    "ppCO2": {"min": 0.39, "max": 0.41},   # kPa
    "water": {"min": 10, "max": 120},    # liters
    "temperature": {"min": 18, "max": 26},  # °C
}

MONITOR_RANGES = {
    "ppO2": {"min": 19.5, "max": 23.5},  # kPa
    "ppCO2": {"min": 0.0, "max": 0.5},   # kPa
    "water": {"min": 10, "max": 120},    # liters
    "temperature": {"min": 18, "max": 26},  # °C
}

# Define failure scenarios (easily configurable)
FAILURE_SCENARIOS = [
    {
        "subsystem": "CDRS",           # Subsystem to fail
        "failure_step": 2000,            # Time step when the failure occurs
        "recovery_step": 6000,           # Time step when the subsystem recovers (None if not recoverable)
        "failure_mode": "off",         # Failure mode: 'off' (completely stop) or 'reduced' (partial degradation)
        "reduction_factor": 0.0,       # Reduction factor (used only if failure_mode is 'reduced')
    },
    # Add additional failure scenarios as needed
    # {
    #     "subsystem": "OGS",
    #     "failure_step": 50,
    #     "recovery_step": 80,
    #     "failure_mode": "reduced",
    #     "reduction_factor": 0.5,
    # },
]

# Simulate over time
time_steps = 10000
json_data = {"ppO2": [], "ppCO2": [], "water": [], "temperature": [], "OGS": [], "CDRS": [], "WRS": [], "TCS": []}
history = {"ppO2": [], "ppCO2": [], "water": [], "temperature": []}
status_history = {"OGS": [], "CDRS": [], "WRS": [], "TCS": []}

# Define initial parameters of the cabin atmosphere and subsystems
cabin = {
    "ppO2": 21.0,  # Partial pressure of O2 (kPa)
    "ppCO2": 0.4,  # Partial pressure of CO2 (kPa)
    "water": 100.0,  # Total water available (liters)
    "temperature": 22.0,  # Cabin temperature (°C)
}

subsystems = {
    "OGS": {"O2_rate": 0.5, "water_consumption": 1.0, "status": True},  # moles O2/sec, liters water/sec
    "CDRS": {"CO2_removal_rate": 0.003, "status": True},  # moles CO2/sec
    "WRS": {"water_recovery_rate": 0.95, "status": True},  # Recovery efficiency (%)
    "TCS": {"temperature_stability": True, "deviation": 0.0, "status": True},  # temperature deviation (°C)
}

# Human respiration and water usage (per person)
human_respiration = {
    "O2_consumption_per_day": 0.84,  # kg/day
    "CO2_production_per_day": 1.0,  # kg/day
    "water_consumption_per_day": 3.0,  # liters/day (drinking, hygiene)
    "crew_size": 4,  # Number of crew members
}

# Constants for conversions
MOLAR_MASS_O2 = 32.0  # g/mol for O2
MOLAR_MASS_CO2 = 44.0  # g/mol for CO2
MOLAR_VOLUME = 22.4  # liters per mole at standard temperature and pressure
CABIN_VOLUME = 100.0  # cubic meters, total cabin volume
SECONDS_PER_DAY = 86400  # seconds in a day

def apply_failures(subsystems, failure_scenarios, current_step):
    """
    Applies the configured failure scenarios to the subsystems at the given time step.
    """
    for scenario in failure_scenarios:
        # Check if the current step is within the failure window
        if scenario["failure_step"] <= current_step and (
            scenario["recovery_step"] is None or current_step < scenario["recovery_step"]
        ):
            # Apply failure
            if scenario["failure_mode"] == "off":
                subsystems[scenario["subsystem"]]["status"] = False
            elif scenario["failure_mode"] == "reduced":
                subsystems[scenario["subsystem"]]["CO2_removal_rate"] *= scenario["reduction_factor"]
        elif scenario["recovery_step"] is not None and current_step == scenario["recovery_step"]:
            # Recover subsystem
            subsystems[scenario["subsystem"]]["status"] = True
            if scenario["failure_mode"] == "reduced":
                subsystems[scenario["subsystem"]]["CO2_removal_rate"] = 0.003  # Reset to default rate
    return subsystems


def human_respiration_effect(cabin, respiration, time_step=1):
    """
    Calculates the effect of human respiration on the cabin atmosphere.
    """
    # Oxygen consumption
    O2_consumed_per_second = (
        respiration["O2_consumption_per_day"] * 1000 / MOLAR_MASS_O2 / SECONDS_PER_DAY
    )
    O2_total_consumed = O2_consumed_per_second * respiration["crew_size"] * time_step
    cabin["ppO2"] -= (O2_total_consumed * MOLAR_VOLUME) / CABIN_VOLUME

    # CO2 production
    CO2_produced_per_second = (
        respiration["CO2_production_per_day"] * 1000 / MOLAR_MASS_CO2 / SECONDS_PER_DAY
    )
    CO2_total_produced = CO2_produced_per_second * respiration["crew_size"] * time_step
    cabin["ppCO2"] += (CO2_total_produced * MOLAR_VOLUME) / CABIN_VOLUME

    return cabin

def human_water_consumption(cabin, respiration, time_step=1):
    """
    Simulates human water consumption for drinking and hygiene.
    """
    water_consumed_per_second = (
        respiration["water_consumption_per_day"] / SECONDS_PER_DAY
    )
    total_water_consumed = water_consumed_per_second * respiration["crew_size"] * time_step
    cabin["water"] -= total_water_consumed
    return total_water_consumed  # Return consumed water for recovery calculation

def water_recovery_system(cabin, subsystems, water_consumed, time_step=1):
    """
    Simulates the water recovery process in the WRS.
    """
    if subsystems["WRS"]["status"]:
        recovered_water = water_consumed * subsystems["WRS"]["water_recovery_rate"]
        cabin["water"] += recovered_water  # Add recovered water back to the system
    return cabin

def check_limits_and_control(cabin, subsystems):
    """
    Checks if subsystems need to be switched on/off based on parameter limits.
    """
    # ppO2 limits
    if cabin["ppO2"] > CONTROL_RANGES["ppO2"]["max"]:
        subsystems["OGS"]["status"] = False  # Turn off OGS to stop generating O2
    elif cabin["ppO2"] < CONTROL_RANGES["ppO2"]["min"]:
        subsystems["OGS"]["status"] = True  # Turn on OGS if ppO2 drops too low

    # ppCO2 limits
    if cabin["ppCO2"] > CONTROL_RANGES["ppCO2"]["max"]:
        subsystems["CDRS"]["status"] = True  # Turn on CDRS to remove CO2
    elif cabin["ppCO2"] < CONTROL_RANGES["ppCO2"]["min"]:
        subsystems["CDRS"]["status"] = False  # Turn off CDRS if CO2 is too low

    # Water limits
    if cabin["water"] < CONTROL_RANGES["water"]["min"]:
        subsystems["WRS"]["status"] = True  # Turn on WRS to recover water
    elif cabin["water"] > CONTROL_RANGES["water"]["max"]:
        subsystems["WRS"]["status"] = False  # Turn off WRS if water is abundant

    return subsystems

def simulate_step(cabin, subsystems, respiration, failure_scenarios, current_step, time_step=1):
    """
    Simulates one time step in the ECLSS system, applying failures and subsystem dynamics.
    """
    # Apply failure scenarios at the current step
    subsystems = apply_failures(subsystems, failure_scenarios, current_step)

    # Human respiration effects
    cabin = human_respiration_effect(cabin, respiration, time_step)

    # Human water consumption
    water_consumed = human_water_consumption(cabin, respiration, time_step)

    # WRS: Recover water
    cabin = water_recovery_system(cabin, subsystems, water_consumed, time_step)

    # Subsystems effects
    # OGS: Generates O2, consumes water (if on)
    if subsystems["OGS"]["status"] and cabin["water"] > subsystems["OGS"]["water_consumption"] * time_step:
        O2_generated = subsystems["OGS"]["O2_rate"] * time_step
        cabin["ppO2"] += (O2_generated * MOLAR_VOLUME) / CABIN_VOLUME
        cabin["water"] -= subsystems["OGS"]["water_consumption"] * time_step

    # CDRS: Removes CO2 (if on)
    if subsystems["CDRS"]["status"]:
        CO2_removed = subsystems["CDRS"]["CO2_removal_rate"] * time_step
        cabin["ppCO2"] -= (CO2_removed * MOLAR_VOLUME) / CABIN_VOLUME
        cabin["ppCO2"] = max(cabin["ppCO2"], 0)  # Prevent negative ppCO2

    return cabin

# Function to save JSON data with a unique filename
def create_json():
    """Save simulation telemetry data with a specific structured format."""
    folder_path = os.path.join(os.getcwd(), "jsonfile")
    os.makedirs(folder_path, exist_ok=True)  # Ensure the directory exists

    # Generate a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"sim_data.json"
    file_path = os.path.join(folder_path, file_name)

    # Convert ppO2 to the required format (assuming it's in kPa and needs to be in mmHg)
    ppO2_mmHg = round(cabin["ppO2"] * 7.50062, 2)  # Conversion factor from kPa to mmHg

    # Define parameter structure
    habitat_status = {
        "habitatStatus": {
            "Parameters": [
                {
                    "SimulatedParameter": True,
                    "DisplayName": "Cabin_ppO2",
                    "DisplayValue": f"{ppO2_mmHg} mmHG",
                    "Id": 43,
                    "Name": "ppO2_test",
                    "ParameterGroup": "L1_test",
                    "NominalValue": 163.81,
                    "UpperCautionLimit": 175.0,
                    "UpperWarningLimit": 185.0,
                    "LowerCautionLimit": 155.0,
                    "LowerWarningLimit": 145.0,
                    "Divisor": 100,
                    "Unit": "mmHG",
                    "SimValue": ppO2_mmHg,  # Example conversion (adjust as needed)
                    "noise": 0.01,
                    "currentValue": ppO2_mmHg,
                    "CurrentValue": ppO2_mmHg,
                    "simulationValue": ppO2_mmHg,
                    "Status": {
                        "LowerWarning": ppO2_mmHg < 145.0,
                        "LowerCaution": ppO2_mmHg < 155.0,
                        "Nominal": 155.0 <= ppO2_mmHg <= 175.0,
                        "UpperCaution": ppO2_mmHg > 175.0,
                        "UpperWarning": ppO2_mmHg > 185.0,
                        "UnderLimit": ppO2_mmHg < 145.0,
                        "OverLimit": ppO2_mmHg > 185.0,
                        "Caution": ppO2_mmHg < 155.0 or ppO2_mmHg > 175.0,
                        "Warning": ppO2_mmHg < 145.0 or ppO2_mmHg > 185.0
                    },
                    "HasDuplicationError": False,
                    "DuplicationError": None
                }
            ],
            "MasterStatus": {
                "Caution": False,
                "Warning": False
            },
            "HardwareList": [],
            "SimulationList": [],
            "Timestamp": datetime.now().strftime("MD %j %H:%M:%S")  # Mission day format
        }
    }

    # Save the JSON file
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(habitat_status, json_file, indent=4)

    print(f"JSON file saved at: {file_path}")

    try:
        # Read the JSON file
        with open(file_path, 'r') as file:
            json_data = json.load(file)  # Load JSON data from the file

        # Make the POST request
        response = requests.post(url, json=json_data)

        # Print the response status and data
        if response.status_code == 200:
            print("Success:", response.json())
        else:
            print("Failed:", response.status_code)

    except KeyboardInterrupt:
        print("Stopped by user.")
    except Exception as e:
        print("An error occurred:", e)


# Main simulation loop with controlled or unrestricted time steps
for t in range(time_steps):
    start_time = time.time()  # Record start time of the timestep

    subsystems = check_limits_and_control(cabin, subsystems)
    cabin = simulate_step(cabin, subsystems, human_respiration, FAILURE_SCENARIOS, current_step=t, time_step=1)
    
    # Store history
    history["ppO2"].append(cabin["ppO2"])
    history["ppCO2"].append(cabin["ppCO2"])
    history["water"].append(cabin["water"])
    status_history["OGS"].append(subsystems["OGS"]["status"])
    status_history["CDRS"].append(subsystems["CDRS"]["status"])
    status_history["WRS"].append(subsystems["WRS"]["status"])
    status_history["TCS"].append(subsystems["TCS"]["status"])

    # Save telemetry data
    create_json()
    
    # Send data (uncomment when `post2url` function is defined)
    # post2url(jsonfile)

    # Control execution speed if real_time_mode is enabled
    if real_time_mode:
        elapsed_time = time.time() - start_time
        sleep_time = max(0, (1.0 / simulation_speed) - elapsed_time)  # Ensure non-negative sleep time
        time.sleep(sleep_time)  # Pause before next timestep

def post_json_to_url():
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as file:
            json_data = json.load(file)  # Load JSON data from the file

        # Make the POST request
        response = requests.post(url, json=json_data)

        # Print the response status and data
        if response.status_code == 200:
            print("Success:", response.json())
        else:
            print("Failed:", response.status_code)

    except KeyboardInterrupt:
        print("Stopped by user.")
    except Exception as e:
        print("An error occurred:", e)

    


save_json_file()
# def post_json_continuously():
#     try:
#         while True:
#             # Read the JSON file
#             with open(json_file_path, 'r') as file:
#                 json_data = json.load(file)  # Load JSON data from the file

#             # Make the POST request
#             response = requests.post(url, json=json_data)

#             # Print the response status and data
#             if response.status_code == 200:
#                 print("Success:", response.json())
#             else:
#                 print("Failed:", response.status_code)

#             # Wait for 1 second before the next request
#             time.sleep(1)

#     except KeyboardInterrupt:
#         print("Stopped by user.")
#         plot_result()
#     except Exception as e:
#         print("An error occurred:", e)

# # Start posting JSON data continuously
# if __name__ == '__main__':
#     post_json_continuously()

# def plot_result():
#     # Plot results
#     plt.figure(figsize=(12, 12))

#     plt.subplot(3, 2, 1)
#     plt.plot(history["ppO2"], label="ppO2 (kPa)")
#     plt.axhline(CONTROL_RANGES["ppO2"]["min"], color="b", linestyle="--", label="Min Safe ppO2")
#     plt.axhline(CONTROL_RANGES["ppO2"]["max"], color="b", linestyle="--", label="Max Safe ppO2")
#     plt.axhline(MONITOR_RANGES["ppO2"]["min"], color="r", linestyle="--", label="Min Safe ppO2")
#     plt.axhline(MONITOR_RANGES["ppO2"]["max"], color="r", linestyle="--", label="Max Safe ppO2")
#     plt.title("Partial Pressure of O2")
#     plt.xlabel("Time Steps [s]")
#     plt.ylabel("kPa")
#     plt.legend()

#     plt.subplot(3, 2, 2)
#     plt.plot(history["ppCO2"], label="ppCO2 (kPa)", color="orange")
#     plt.axhline(CONTROL_RANGES["ppCO2"]["min"], color="b", linestyle="--", label="Min Control ppCO2")
#     plt.axhline(CONTROL_RANGES["ppCO2"]["max"], color="b", linestyle="--", label="Max Control ppCO2")
#     plt.axhline(MONITOR_RANGES["ppCO2"]["min"], color="r", linestyle="--", label="Min Safe ppCO2")
#     plt.axhline(MONITOR_RANGES["ppCO2"]["max"], color="r", linestyle="--", label="Max Safe ppCO2")
#     plt.title("Partial Pressure of CO2")
#     plt.xlabel("Time Steps [s]")
#     plt.ylabel("kPa")
#     plt.legend()

#     plt.subplot(3, 2, 3)
#     plt.plot(history["water"], label="Water Available (liters)", color="blue")
#     plt.axhline(MONITOR_RANGES["water"]["min"], color="r", linestyle="--", label="Min Safe Water")
#     plt.axhline(MONITOR_RANGES["water"]["max"], color="r", linestyle="--", label="Max Safe Water")
#     plt.title("Water Availability")
#     plt.xlabel("Time Steps [s]")
#     plt.ylabel("Liters")
#     plt.legend()

#     plt.subplot(3, 2, 4)
#     plt.plot(status_history["OGS"], label="OGS Status (On/Off)", color="purple")
#     plt.title("OGS Status")
#     plt.xlabel("Time Steps [s]")
#     plt.ylabel("On/Off")
#     plt.legend()

#     plt.subplot(3, 2, 5)
#     plt.plot(status_history["CDRS"], label="CDRS Status (On/Off)", color="green")
#     plt.title("CDRS Status")
#     plt.xlabel("Time Steps [s]")
#     plt.ylabel("On/Off")
#     plt.legend()

#     plt.subplot(3, 2, 6)
#     plt.plot(status_history["WRS"], label="WRS Status (On/Off)", color="cyan")
#     plt.title("WRS Status")
#     plt.xlabel("Time Steps [s]")
#     plt.ylabel("On/Off")
#     plt.legend()

#     plt.tight_layout()
#     plt.show()