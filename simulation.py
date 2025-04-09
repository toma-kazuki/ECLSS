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
json_file_path = 'jsonfile/sim_data.json'

# URL to post to
# url = 'https://daphne-at-lab.selva-research.com/api/at/receiveHeraFeed'
url = 'http://localhost:8002/api/at/receiveHeraFeed'

# Define control ranges (safe limits) for monitored parameters
CONTROL_RANGES = {
    "ppO2": {"min": 21.4, "max": 21.6},  # kPa
    "ppCO2": {"min": 0.39, "max": 0.41},   # kPa
    "humidity": {"min": 10, "max": 120},    # liters
    "temperature": {"min": 18, "max": 26},  # °C
}

MONITOR_RANGES = {
    "ppO2": {"min": 19.5, "max": 23.5},  # kPa
    "ppCO2": {"min": 0.0, "max": 0.5},   # kPa
    "humidity": {"min": 10, "max": 120},    # liters
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

PARAMETER_INFO = {
    "ppO2": {"DisplayName": "Cabin_ppO2", "Id": 43, "ParameterGroup": "L1", "NominalValue": 163.81,
             "UpperCautionLimit": 175.0, "UpperWarningLimit": 185.0, "LowerCautionLimit": 155.0,
             "LowerWarningLimit": 145.0, "Divisor": 100, "Name": "ppO2", "Unit":"mmHg"},
    "ppCO2": {"DisplayName": "Cabin_ppCO2", "Id": 44, "ParameterGroup": "L1", "NominalValue": 0.4,
              "UpperCautionLimit": 4.5, "UpperWarningLimit": 6.0, "LowerCautionLimit": -1.0,
              "LowerWarningLimit": -2.0, "Divisor": 100, "Name": "ppCO2", "Unit":"mmHg"},
    "humidity": {"DisplayName": "Humidity", "Id": 45, "ParameterGroup": "L1", "NominalValue": 52,
              "UpperCautionLimit": 61, "UpperWarningLimit": 70, "LowerCautionLimit": 50,
              "LowerWarningLimit": 40, "Divisor": 1, "Name": "Humidity", "Unit":"L"},
    "ppO21": {"DisplayName": "Cabin_ppO2", "Id": 43, "ParameterGroup": "L2", "NominalValue": 163.81,
             "UpperCautionLimit": 175.0, "UpperWarningLimit": 185.0, "LowerCautionLimit": 155.0,
             "LowerWarningLimit": 145.0, "Divisor": 100, "Name": "ppO2", "Unit":"mmHg"},
    "ppCO21": {"DisplayName": "Cabin_ppCO2", "Id": 44, "ParameterGroup": "L2", "NominalValue": 0.4,
              "UpperCautionLimit": 4.5, "UpperWarningLimit": 6.0, "LowerCautionLimit": -1.0,
              "LowerWarningLimit": -2.0, "Divisor": 100, "Name": "ppCO2", "Unit":"mmHg"},
    "humidity1": {"DisplayName": "Humidity", "Id": 45, "ParameterGroup": "L2", "NominalValue": 52,
              "UpperCautionLimit": 61, "UpperWarningLimit": 70, "LowerCautionLimit": 50,
              "LowerWarningLimit": 40, "Divisor": 1, "Name": "Humidity", "Unit":"L"},
    
    # "temperature": {"DisplayName": "Cabin_Temperature", "Id": 46, "ParameterGroup": "L1", "NominalValue": 100,
    #           "UpperCautionLimit": 79.0, "UpperWarningLimit": 87.7, "LowerCautionLimit": 68.0,
    #           "LowerWarningLimit": 64.0, "Divisor": 1, "Name": "Cabin Temperature", "Unit":"F"},
    # "temperature": {"DisplayName": "Cabin_Temperature", "Id": 46, "ParameterGroup": "L1", "NominalValue": 100,
    #           "UpperCautionLimit": 79.0, "UpperWarningLimit": 87.7, "LowerCautionLimit": 68.0,
    #           "LowerWarningLimit": 64.0, "Divisor": 1, "Name": "Cabin Temperature", "Unit":"F"},
}

# Simulate over time
time_steps = 10000
json_data = {"ppO2": [], "ppCO2": [], "humidity": [], "temperature": [], "OGS": [], "CDRS": [], "WRS": [], "TCS": []}
history = {"ppO2": [], "ppCO2": [], "humidity": [], "temperature": [], "ppO21": [], "ppCO21": [], "humidity1": [], "temperature1": [],}
status_history = {"OGS": [], "CDRS": [], "WRS": [], "TCS": []}

cabin = {
    "ppO2": 150, 
    "ppCO2": 5, 
    "humidity": 65, 
    "temperature": 22.0, 
     "ppO21": 165, 
    "ppCO21": 0.5, 
    "humidity1": 52, 
    "temperature1": 52.0,  
}



def simulate_step(cabin):
    """
    Simulates one time step in the ECLSS system, applying failures and subsystem dynamics.
    """
    # Apply failure scenarios at the current step
    # subsystems = apply_failures(subsystems, failure_scenarios, current_step)

    # # Human respiration effects
    # cabin = human_respiration_effect(cabin, respiration, time_step)

    # # Human water consumption
    # water_consumed = human_water_consumption(cabin, respiration, time_step)

    # # WRS: Recover water
    # cabin = water_recovery_system(cabin, subsystems, water_consumed, time_step)

    # Subsystems effects
    # OGS: Generates O2, consumes water (if on)
    # if subsystems["OGS"]["status"] and cabin["water"] > subsystems["OGS"]["water_consumption"] * time_step:
    #     O2_generated = subsystems["OGS"]["O2_rate"] * time_step
    #     cabin["ppO2"] += (O2_generated * MOLAR_VOLUME) / CABIN_VOLUME
    #     cabin["water"] -= subsystems["OGS"]["water_consumption"] * time_step

    # # CDRS: Removes CO2 (if on)
    # if subsystems["CDRS"]["status"]:
    #     CO2_removed = subsystems["CDRS"]["CO2_removal_rate"] * time_step
    #     cabin["ppCO2"] -= (CO2_removed * MOLAR_VOLUME) / CABIN_VOLUME
    #     cabin["ppCO2"] = max(cabin["ppCO2"], 0)  # Prevent negative ppCO2

    return cabin

def post_json_to_url():
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as file:
            json_data = json.load(file)  # Load JSON data from the file
            
        print(f"Sending request to: {url}")

        # Make the POST request
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=json_data, headers=headers, timeout=5)
        # response = requests.post(url, json=json_data)

        # Print the response status and data
        if response.status_code == 200:
            print("Success:", response.json())
        else:
            print("Failed:", response.status_code)
            # print(f"Response content: {response.text}")
    # except requests.exceptions.ConnectionError:
    #     print("Connection Error: Could not connect to the server. Is it running?")
    #     return False
    # except requests.exceptions.Timeout:
    #     print("Timeout: The server took too long to respond.")
    #     return False
    # except json.JSONDecodeError:
    #     print("Error: Invalid JSON data in the file.")
    #     return False
    except KeyboardInterrupt:
        print("Stopped by user.")
    except Exception as e:
        print("An error occurred:", e)


def create_parameter_entry(param_name, cabin):
    """
    Creates a parameter entry for the JSON data structure.
    Args:
        param_name (str): The name of the parameter (e.g., "ppO2", "water").
        cabin (dict): The dictionary containing the current cabin state.
    Returns:
        dict: A dictionary representing the parameter entry for the JSON structure.
    """
    print(cabin)
    param_info = PARAMETER_INFO[param_name]
    current_value = cabin[param_name]

    # Determine display value and unit
    # if param_name == "ppO2" or param_name == "ppCO2":
    #     current_value_display = round(current_value * 7.50062, 2)  # kPa to mmHg
    # else:
    #     
    current_value_display = current_value
    unit = param_info["Unit"]

    # Create the parameter entry
    parameter_entry = {
        "SimulatedParameter": True,
        "DisplayName": param_info["DisplayName"],
        "DisplayValue": f"{current_value_display} {unit}",
        "Id": param_info["Id"],
        "Name": param_info["Name"],
        "ParameterGroup": param_info["ParameterGroup"],
        "NominalValue": param_info["NominalValue"],
        "UpperCautionLimit": param_info["UpperCautionLimit"],
        "UpperWarningLimit": param_info["UpperWarningLimit"],
        "LowerCautionLimit": param_info["LowerCautionLimit"],
        "LowerWarningLimit": param_info["LowerWarningLimit"],
        "Divisor": param_info["Divisor"],
        "Unit": unit,
        "SimValue": current_value_display,
        "noise": 0.01,
        "currentValue": current_value_display,
        "CurrentValue": current_value_display,
        "simulationValue": current_value_display,
        "Status": {
            "LowerWarning": current_value < param_info["LowerWarningLimit"],
            "LowerCaution": current_value < param_info["LowerCautionLimit"],
            "Nominal": param_info["LowerCautionLimit"] <= current_value <= param_info["UpperCautionLimit"],
            "UpperCaution": current_value > param_info["UpperCautionLimit"],
            "UpperWarning": current_value > param_info["UpperWarningLimit"],
            "UnderLimit": current_value < param_info["LowerWarningLimit"],
            "OverLimit": current_value > param_info["UpperWarningLimit"],
            "Caution": current_value < param_info["LowerCautionLimit"] or current_value > param_info["UpperCautionLimit"],
            "Warning": current_value < param_info["LowerWarningLimit"] or current_value > param_info["UpperWarningLimit"]
        },
        "HasDuplicationError": False,
        "DuplicationError": None
    }
    return parameter_entry

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
    # ppO2_mmHg = round(cabin["ppO2"] * 7.50062, 2)  # Conversion factor from kPa to mmHg

    parameters_list = [create_parameter_entry(param_name, cabin) for param_name in PARAMETER_INFO]

    habitat_status = {
        "habitatStatus": {
            "Parameters": parameters_list,
            "MasterStatus": {
                "Caution": any(p["Status"]["Caution"] for p in parameters_list),
                "Warning": any(p["Status"]["Warning"] for p in parameters_list)
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

    post_json_to_url()


# Main simulation loop with controlled or unrestricted time steps
for t in range(time_steps):
    start_time = time.time()  # Record start time of the timestep

    # subsystems = check_limits_and_control(cabin, subsystems)
    cabin = simulate_step(cabin)
    
    # Store history
    history["ppO2"].append(cabin["ppO2"])
    history["ppCO2"].append(cabin["ppCO2"])
    history["humidity"].append(cabin["humidity"])

    # Save telemetry data
    create_json()
    
    # Send data (uncomment when `post2url` function is defined)
    # post2url(jsonfile)

    # Control execution speed if real_time_mode is enabled
    if real_time_mode:
        elapsed_time = time.time() - start_time
        sleep_time = max(0, (1.0 / simulation_speed) - elapsed_time)  # Ensure non-negative sleep time
        time.sleep(sleep_time)  # Pause before next timestep


    

