FAILURE_SCENARIOS = [
    # {"subsystem": "OGS", 
    #  "failure_step": 2000, 
    #  "recovery_step": 4000, 
    #  "failure_mode": "on", 
    #  "reduction_factor": 0.0},
    # {"subsystem": "CDRS", 
    #  "failure_step": 1000, 
    #  "recovery_step": 6000, 
    #  "failure_mode": "on", 
    #  "reduction_factor": 0.0}
    ]

def apply_failures(subsystems, current_step):
    """
    Applies the configured failure scenarios to the subsystems at the given time step.
    """
    for scenario in FAILURE_SCENARIOS:
        subsystem_name = scenario["subsystem"]
        if subsystem_name not in subsystems:
            continue  # 無効な subsystem の場合スキップ

        if scenario["failure_step"] <= current_step and (
            scenario["recovery_step"] is None or current_step < scenario["recovery_step"]
        ):
            if scenario["failure_mode"] == "off":
                subsystems[subsystem_name]["status"] = False
            elif scenario["failure_mode"] == "reduced":
                subsystems[subsystem_name]["CO2_removal_rate"] *= scenario["reduction_factor"]
            elif scenario["failure_mode"] == "on":
                subsystems[subsystem_name]["status"] = True
        elif scenario["recovery_step"] is not None and current_step == scenario["recovery_step"]:
            subsystems[subsystem_name]["status"] = True
            if scenario["failure_mode"] == "reduced":
                subsystems[subsystem_name]["CO2_removal_rate"] = 0.003  # Reset to default rate
    return subsystems
