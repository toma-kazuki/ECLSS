import numpy as np
import matplotlib.pyplot as plt
import requests
import os
import json
import copy
import time
from datetime import datetime
from ControlSetting import check_limits_and_control
from EnvironmentSimulation import simulate_init, simulate_step

# Simulation settings
real_time_mode = False  # Set to False to run as fast as possible
simulation_speed = 1.0  # 1.0 = real-time (1 second per step), 2.0 = 2x faster, etc.

# Simulate over time
SECONDS_PER_MIN = 60
MIN_PER_HOUR = 60
time_steps = SECONDS_PER_MIN * MIN_PER_HOUR * 1

# File path to the JSON file
json_file_path = 'temp.json'

# URL to post to
url = 'https://daphne-at-lab.selva-research.com/api/at/receiveHeraFeed'
data_history = []

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

def plot_result(data_history):
    # Extract time series data
    time_steps = [entry["time_step"] for entry in data_history]
    ppO2_values = [entry["cabin"]["ppO2"] for entry in data_history]
    ppCO2_values = [entry["cabin"]["ppCO2"] for entry in data_history]
    H2storage_values = [entry["cabin"]["H2storage"] for entry in data_history]
    water_tank_values = [entry["cabin"]["water_tank"] for entry in data_history]
    wasted_water_values = [entry["cabin"]["wasted_water"]["storage"] for entry in data_history]

    # Extract subsystem status (convert True to 1, False to 0)
    OGS_status = [int(entry["subsystems"]["OGS"]["status"]) for entry in data_history]
    CDRS_status = [int(entry["subsystems"]["CDRS"]["status"]) for entry in data_history]
    WRS_status = [int(entry["subsystems"]["WRS"]["status"]) for entry in data_history]
    Sabatier_status = [int(entry["subsystems"]["Sabatier"]["status"]) for entry in data_history]

    # Extract control range for each subsystem 
    control_ranges_ppO2_min = [entry["control_ranges"]["OGS"]["ppO2_lower_control_limit"] for entry in data_history]
    control_ranges_ppO2_max = [entry["control_ranges"]["OGS"]["ppO2_upper_control_limit"] for entry in data_history]
    control_ranges_ppCO2_min = [entry["control_ranges"]["CDRS"]["ppCO2_lower_control_limit"] for entry in data_history]
    control_ranges_ppCO2_max = [entry["control_ranges"]["CDRS"]["ppCO2_upper_control_limit"] for entry in data_history]
    #control_ranges_WRS_min = [entry["control_ranges"]["WRS"]["min"] for entry in data_history]
    #control_ranges_WRS_max = [entry["control_ranges"]["WRS"]["max"] for entry in data_history]

    MONITOR_RANGES = {
        "ppO2": {"min": 19.5, "max": 23.5},  # kPa
        "ppCO2": {"min": 0.0, "max": 0.5},   # kPa
        "water": {"min": 10, "max": 120},    # liters
        "temperature": {"min": 18, "max": 26},  # °C
    }

    # Create figure for plotting
    plt.figure(figsize=(12, 8))

    # (1,1) Partial Pressure of O2
    plt.subplot(2, 5, 1)
    plt.plot(time_steps, ppO2_values, label="ppO2 (kPa)")
    plt.plot(time_steps, control_ranges_ppO2_min, color="b", linestyle="--", label="Min Safe ppO2")
    plt.plot(time_steps, control_ranges_ppO2_max, color="b", linestyle="--", label="Max Safe ppO2")
    plt.axhline(MONITOR_RANGES["ppO2"]["min"], color="r", linestyle="--", label="Min Safe ppO2")
    plt.axhline(MONITOR_RANGES["ppO2"]["max"], color="r", linestyle="--", label="Max Safe ppO2")
    plt.title("Partial Pressure of O2")
    plt.xlabel("Time Steps")
    plt.ylabel("kPa")
    plt.legend()

    # (1,2) Partial Pressure of CO2
    plt.subplot(2, 5, 2)
    plt.plot(time_steps, ppCO2_values, label="ppCO2 (kPa)", color="orange")
    plt.plot(control_ranges_ppCO2_min, color="b", linestyle="--", label="Min Control ppCO2")
    plt.plot(control_ranges_ppCO2_max, color="b", linestyle="--", label="Max Control ppCO2")
    plt.axhline(MONITOR_RANGES["ppCO2"]["min"], color="r", linestyle="--", label="Min Safe ppCO2")
    plt.axhline(MONITOR_RANGES["ppCO2"]["max"], color="r", linestyle="--", label="Max Safe ppCO2")
    plt.title("Partial Pressure of CO2")
    plt.xlabel("Time Steps")
    plt.ylabel("kPa")
    plt.legend()

    # (1,3) Water Availability
    plt.subplot(2, 5, 3)
    plt.plot(time_steps, water_tank_values, color="blue")
    plt.axhline(MONITOR_RANGES["water"]["min"], color="r", linestyle="--", label="Min Safe Water")
    plt.axhline(MONITOR_RANGES["water"]["max"], color="r", linestyle="--", label="Max Safe Water")
    plt.title("Water Availability")
    plt.xlabel("Time Steps")
    plt.ylabel("Liters")
    plt.legend()

    # (1,3) Wasted Water Storage
    plt.subplot(2, 5, 4)
    plt.plot(time_steps, wasted_water_values, color="blue")
    plt.title("Wasted Water Storage")
    plt.xlabel("Time Steps")
    plt.ylabel("Liters")
    plt.legend()

    # (1,4) Hydrogen Availability
    plt.subplot(2, 5, 5)
    plt.plot(time_steps, H2storage_values, color="blue")
    plt.title("H2 Availability")
    plt.xlabel("Time Steps")
    plt.ylabel("mols")
    plt.legend()

    # (2,1) OGS Status
    plt.subplot(2, 5, 6)
    plt.plot(time_steps, OGS_status)
    plt.title("OGS Status")
    plt.xlabel("Time Steps")
    plt.ylabel("Active (1) / Inactive (0)")

    # (2,2) CDRS Status
    plt.subplot(2, 5, 7)
    plt.plot(time_steps, CDRS_status)
    plt.title("CDRS Status")
    plt.xlabel("Time Steps")
    plt.ylabel("Active (1) / Inactive (0)")

    # (2,3) WRS Status
    plt.subplot(2, 5, 8)
    plt.plot(time_steps, WRS_status)
    plt.title("WRS Status")
    plt.xlabel("Time Steps")
    plt.ylabel("Active (1) / Inactive (0)")

    # (2,3) WRS Status
    plt.subplot(2, 5, 9)
    plt.plot(time_steps, Sabatier_status)
    plt.title("Sabatier Status")
    plt.xlabel("Time Steps")
    plt.ylabel("Active (1) / Inactive (0)")

    # Adjust layout to prevent overlap
    plt.tight_layout()
    plt.show()

def main():# Main simulation loop with controlled or unrestricted time steps
    
    cabin, subsystems = simulate_init()

    for t in range(time_steps):
        start_time = time.time()  # Record start time of the timestep
    
        subsystems, control_ranges = check_limits_and_control(cabin, subsystems)
        cabin, subsystems = simulate_step(cabin, subsystems, current_step=t)

        # Control execution speed if real_time_mode is enabled
        if real_time_mode:
            # Save telemetry data
            create_json(cabin)
            elapsed_time = time.time() - start_time
            sleep_time = max(0, (1.0 / simulation_speed) - elapsed_time)  # Ensure non-negative sleep time
            time.sleep(sleep_time)  # Pause before next timestep
        else:
            print(f"Step {t}: ppO2={cabin['ppO2']}, ppCO2={cabin['ppCO2']}, water_tank={cabin['water_tank']}")


        # Store history
        data_history.append({
            "time_step": t,
            "cabin": copy.deepcopy(cabin),
            "subsystems": copy.deepcopy(subsystems),
            "control_ranges": copy.deepcopy(control_ranges)
        })

        if cabin["mission_mode"] == "failure":
            break


    print("<<<<<<<<<Simulation Completed!!!>>>>>>>>>>")
    plot_result(data_history)

if __name__ == "__main__":
    main()