import numpy as np
import matplotlib.pyplot as plt
import requests
import os
import json
import time
from datetime import datetime
from ControlSetting import check_limits_and_control
from EnvironmentSimulation import simulate_step

# Simulation settings
real_time_mode = False  # Set to False to run as fast as possible
simulation_speed = 1.0  # 1.0 = real-time (1 second per step), 2.0 = 2x faster, etc.

# Simulate over time
time_steps = 100

# File path to the JSON file
json_file_path = 'temp.json'

# URL to post to
url = 'https://daphne-at-lab.selva-research.com/api/at/receiveHeraFeed'

json_data = {"ppO2": [], "ppCO2": [], "water": [], "temperature": [], "OGS": [], "CDRS": [], "WRS": [], "TCS": []}
cabin_history = {"ppO2": [], "ppCO2": [], "water": [], "temperature": []}
subsystem_history = {"OGS": [], "CDRS": [], "WRS": [], "TCS": []}

# Function to save JSON data with a unique filename
def create_json(cabin):
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

def main():# Main simulation loop with controlled or unrestricted time steps
    
    cabin = {"ppO2": 21.0, "ppCO2": 0.4, "water": 100.0}
    subsystems = {
        "OGS": {"status": True, "O2_rate": 0.5, "water_consumption": 1.0},
        "CDRS": {"status": True, "CO2_removal_rate": 0.003},
        "WRS": {"status": True, "water_recovery_rate": 0.95},
    }

    for t in range(time_steps):
        start_time = time.time()  # Record start time of the timestep
    
        subsystems = check_limits_and_control(cabin, subsystems)
        cabin, subsystems = simulate_step(cabin, subsystems, current_step=t)

        # Control execution speed if real_time_mode is enabled
        if real_time_mode:
            # Save telemetry data
            create_json(cabin)
            elapsed_time = time.time() - start_time
            sleep_time = max(0, (1.0 / simulation_speed) - elapsed_time)  # Ensure non-negative sleep time
            time.sleep(sleep_time)  # Pause before next timestep
        else:
            print(f"Step {t}: ppO2={cabin['ppO2']}, ppCO2={cabin['ppCO2']}, water={cabin['water']}")


        # Store history
        cabin_history["ppO2"].append(cabin["ppO2"])
        cabin_history["ppCO2"].append(cabin["ppCO2"])
        cabin_history["water"].append(cabin["water"])
        subsystem_history["OGS"].append(subsystems["OGS"]["status"])
        subsystem_history["CDRS"].append(subsystems["CDRS"]["status"])
        subsystem_history["WRS"].append(subsystems["WRS"]["status"])

    print("<<<<<<<<<Simulation Completed!!!>>>>>>>>>>")
    #plot_result()

if __name__ == "__main__":
    main()