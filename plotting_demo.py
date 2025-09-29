#!/usr/bin/env python3
"""
CDRA Simulator Plotting Demo

This script demonstrates the comprehensive plotting capabilities
of the CDRATelemetryData class.
"""
import matplotlib.pyplot as plt

from cdra_simulator import CDRASimulator

def main():
    print("🚀 CDRA Simulator Plotting Demo")
    print("=" * 50)
    
    # Create simulator
    simulator = CDRASimulator()
    
    # Generate telemetry data for different scenarios
    print("📊 Generating telemetry data for multiple scenarios...")
    
    scenarios = [
        ("filter saturation", 0.8),
        ("valve stuck", 0.6),
        ("heater failure", 0.7),
        ("fan degraded", 0.5)
    ]
    
    telemetry_data = {}
    for scenario, severity in scenarios:
        print(f"  - Generating {scenario} (severity: {severity})...")
        telemetry_data[scenario] = simulator.generate_telemetry_data(
            scenario=scenario,
            severity=severity,
            duration_seconds=10007,
            baseline_co2_mmHg=3.0
        )
    
    print("\n📈 Plotting Examples:")
    print("=" * 30)
    
    # Example 1: Basic CO2 concentration plot
    print("1. Basic CO2 Concentration Plot")
    print("   - Shows CO2 over time with detection threshold")
    print("   - Highlights detection point")
    telemetry_data["filter saturation"].plot_co2_concentration(
        title="Filter Saturation Scenario",
        detection_threshold=4.0
    )
    
    # Example 2: Component states
    print("\n2. Component States Plot")
    print("   - Shows saturation, efficiency, and heater states for all components")
    telemetry_data["heater failure"].plot_component_states()
    
    # Example 3: System overview
    print("\n3. System Overview Plot")
    print("   - Comprehensive view of CO2, flow rate, heaters, and valve paths")
    telemetry_data["valve stuck"].plot_system_overview()
    
    # Example 4: Analysis summary
    print("\n4. Analysis Summary Plot")
    print("   - Time series with annotations and key metrics bar chart")
    telemetry_data["fan degraded"].plot_analysis_summary()
    
    # Example 5: Comparison plot
    print("\n5. Comparison Plot")
    print("   - Compare two different scenarios")
    telemetry_data["filter saturation"].plot_comparison(
        telemetry_data["valve stuck"]
    )
    
    # Example 6: Multiple scenarios
    print("\n6. Multiple Scenarios Plot")
    print("   - Compare all scenarios on one plot")
    scenario_list = list(telemetry_data.values())
    telemetry_data["filter saturation"].plot_multiple_scenarios(scenario_list)
    
    print("\n✅ Plotting demo completed!")
    print("\nAvailable plotting methods:")
    print("  - plot_co2_concentration()     : Basic CO2 time series")
    print("  - plot_component_states()      : Component saturation/efficiency")
    print("  - plot_system_overview()       : Comprehensive system view")
    print("  - plot_comparison()            : Compare two scenarios")
    print("  - plot_multiple_scenarios()    : Compare multiple scenarios")
    print("  - plot_analysis_summary()      : Analysis with key metrics")
    plt.show()

if __name__ == "__main__":
    main()
