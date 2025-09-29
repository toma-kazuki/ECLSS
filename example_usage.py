#!/usr/bin/env python3
"""
Example usage of the CDRASimulator class showing the streamlined workflow.
"""

from cdra_simulator import CDRASimulator
import matplotlib.pyplot as plt

def main():
    # Create simulator instance
    simulator = CDRASimulator()
    
    # Example scenarios
    scenarios = [
        "filter saturation",
        "valve stuck", 
        "heater failure",
        "fan degraded"
    ]
    
    # Build templates using the streamlined approach
    templates = {}
    for scenario in scenarios:
        # This is the pattern you wanted - single method call handles everything
        telemetry_data = simulator.generate_telemetry_data(
            scenario=scenario,
            severity=0.5,
            duration_seconds=1000,
            baseline_co2_mmHg=3.0
        )
        templates[scenario] = telemetry_data.get_co2_time_series_mmhg()
    
    # Now you can use the templates
    print("Generated templates for scenarios:")
    for scenario, co2_series in templates.items():
        print(f"  {scenario}: {len(co2_series)} data points")
        print(f"    Peak CO2: {max(co2_series):.3f} mmHg")
        print(f"    Final CO2: {co2_series[-1]:.3f} mmHg")
    
    # Example of using telemetry data analysis methods
    print("\nDetailed analysis for 'filter saturation' scenario:")
    filter_sat_data = simulator.generate_telemetry_data(
        scenario="filter saturation",
        severity=0.8,
        duration_seconds=1000,
        baseline_co2_mmHg=3.0
    )
    
    # Find detection index
    detection_idx = filter_sat_data.find_detection_index(trigger=4.0)
    print(f"  Detection at index {detection_idx} (CO2 > 4.0 mmHg)")
    
    # Get summary statistics
    summary = filter_sat_data.get_summary()
    print(f"  Summary: {summary}")
    
    # Access other telemetry data
    print(f"  Air flow rate series length: {len(filter_sat_data.get_air_flow_rate_series())}")
    print(f"  Sorbent_2 saturation series length: {len(filter_sat_data.get_saturation_series('sorbent_2'))}")
    
    # Resample to different length
    resampled_data = filter_sat_data.resample_to_length(500)
    print(f"  Resampled CO2 series length: {len(resampled_data.get_co2_time_series_mmhg())}")
    
    # Demonstrate plotting capabilities
    print("\n📊 Demonstrating plotting capabilities...")
    
    # Basic CO2 concentration plot
    print("  - Plotting CO2 concentration with detection threshold...")
    filter_sat_data.plot_co2_concentration()
    
    # Component states plot
    print("  - Plotting component states (saturation, efficiency, heaters)...")
    filter_sat_data.plot_component_states()
    
    # System overview plot
    print("  - Plotting comprehensive system overview...")
    filter_sat_data.plot_system_overview()
    
    # Analysis summary plot
    print("  - Plotting analysis summary with key metrics...")
    filter_sat_data.plot_analysis_summary()
    
    # Comparison plot (if we have multiple scenarios)
    print("  - Plotting comparison between scenarios...")
    valve_stuck_data = simulator.generate_telemetry_data(
        scenario="valve stuck",
        severity=0.6,
        duration_seconds=1000,
        baseline_co2_mmHg=3.0
    )
    filter_sat_data.plot_comparison(valve_stuck_data)
    
    # Multiple scenarios plot
    print("  - Plotting multiple scenarios comparison...")
    scenarios_data = []
    for scenario in ["filter saturation", "valve stuck", "heater failure"]:
        data = simulator.generate_telemetry_data(
            scenario=scenario,
            severity=0.5,
            duration_seconds=1000,
            baseline_co2_mmHg=3.0
        )
        scenarios_data.append(data)
    
    filter_sat_data.plot_multiple_scenarios(scenarios_data)

    plt.show()

if __name__ == "__main__":
    main()
