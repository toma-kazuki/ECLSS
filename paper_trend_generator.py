#!/usr/bin/env python3
"""
PAPER TREND IMAGE GENERATOR
==========================

PURPOSE: Generate specific trend images for IEEE Aerospace Conference paper
OBJECTIVE: Create exactly the 3 trend images referenced in main.tex

Generated Images:
- trend_dynamics.png: Dynamic trend of ppCO2 in cabin and internal state trend
- trend_interstate.png: Internal state trends (saturation, adsorption efficiency)  
- trend_fault.png: ppCO2 trend for each fundamental fault scenario

USAGE: Run when you need to update paper figures
OUTPUT: Saves directly to paper images folder
"""

import matplotlib.pyplot as plt
import numpy as np
from driver.cdra_simulator import CDRASimulator
from color_scheme import (get_color, get_line_style, get_scenario_color, get_color_by_index)

# Paper images directory
PAPER_IMAGES_DIR = "/Users/tomakazuki/local/documents/research/paper/IEEEAeroConf2026/images"

def generate_trend_dynamics():
    """Generate three separate plots: ppCO2, saturation level, and adsorption efficiency"""
    print("Generating trend_dynamics.png...")
    
    # Create simulator
    simulator = CDRASimulator()
    
    # Generate nominal scenario data
    telemetry_data = simulator.generate_telemetry_data(
        scenario="nominal",
        severity=0.0,
        duration_seconds=1000,
        baseline_co2_mmHg=3.0
    )
    
    time_series = telemetry_data.get_time_series()
    
    # Debug: Print CO2 values
    print("\n🔍 DEBUG: CO2 Concentration Values (trend_dynamics)")
    print("=" * 60)
    co2_series = telemetry_data.get_co2_time_series_mmhg()
    co2_output_series = telemetry_data.get_co2_output_series_mmhg()
    print(f"Time points: {len(time_series)}")
    print(f"Initial cabin CO2: {co2_series[0]:.3f} mmHg")
    print(f"Initial output CO2: {co2_output_series[0]:.3f} mmHg")
    print(f"Final cabin CO2: {co2_series[-1]:.3f} mmHg")
    print(f"Final output CO2: {co2_output_series[-1]:.3f} mmHg")
    
    # Calculate efficiency from the values
    initial_efficiency = 1 - (co2_output_series[0] / co2_series[0])
    final_efficiency = 1 - (co2_output_series[-1] / co2_series[-1])
    print(f"Calculated initial efficiency: {initial_efficiency:.3f} ({initial_efficiency*100:.1f}%)")
    print(f"Calculated final efficiency: {final_efficiency:.3f} ({final_efficiency*100:.1f}%)")
    
    # Check if C_out > C_in anywhere
    higher_output = [i for i in range(len(co2_series)) if co2_output_series[i] > co2_series[i]]
    if higher_output:
        print(f"⚠️  WARNING: C_out > C_in at {len(higher_output)} time points!")
        print("First few instances:")
        for i in higher_output[:5]:
            efficiency = 1 - (co2_output_series[i] / co2_series[i])
            print(f"  t={time_series[i]:.1f}s: Cabin={co2_series[i]:.3f}, Output={co2_output_series[i]:.3f}, Efficiency={efficiency:.3f}")
    else:
        print(f"✅ Physics check passed: C_out < C_in at all {len(co2_series)} time points")
    
    # Additional debugging: Check the ratio
    print(f"\n🔍 CO2 Ratio Analysis:")
    print(f"Initial ratio (Output/Cabin): {co2_output_series[0]/co2_series[0]:.3f}")
    print(f"Final ratio (Output/Cabin): {co2_output_series[-1]/co2_series[-1]:.3f}")
    print(f"Average ratio: {np.mean([co2_output_series[i]/co2_series[i] for i in range(len(co2_series))]):.3f}")
    print(f"Max ratio: {max([co2_output_series[i]/co2_series[i] for i in range(len(co2_series))]):.3f}")
    print(f"Min ratio: {min([co2_output_series[i]/co2_series[i] for i in range(len(co2_series))]):.3f}")
    print()
    
    # Create three separate figures
    # 1. CO2 Concentration Plot
    apply_paper_style(plt)
    plt.plot(time_series, co2_series, color=get_color_by_index(0), 
             linewidth=PAPER_LINE_WIDTH, 
             label='CO2 in Cabin', linestyle=get_line_style('solid'))
    plt.plot(time_series, co2_output_series, color=get_color_by_index(1), 
             linewidth=PAPER_LINE_WIDTH, 
             label='CO2 Flow Output', linestyle=get_line_style('dashed'))
    plt.xlabel('Time [s]')
    plt.ylabel('CO2 Concentration [mmHg]')
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{PAPER_IMAGES_DIR}/trend_dynamics_co2.png", dpi=300, bbox_inches='tight')
    print(f"  Saved: trend_dynamics_co2.png")
    plt.close()
    
    # 2. Saturation Level Plot
    saturation_a = telemetry_data.get_saturation_series('sorbent_2')
    saturation_b = telemetry_data.get_saturation_series('sorbent_4')
    saturation_a_pct = [s * 100 for s in saturation_a]
    saturation_b_pct = [s * 100 for s in saturation_b]
    
    apply_paper_style(plt)
    plt.plot(time_series, saturation_a_pct, color=get_color_by_index(0), 
             linewidth=PAPER_LINE_WIDTH, 
             label='Sorbent A', linestyle=get_line_style('solid'))
    plt.plot(time_series, saturation_b_pct, color=get_color_by_index(1), 
             linewidth=PAPER_LINE_WIDTH, 
             label='Sorbent B', linestyle=get_line_style('solid'))
    plt.xlabel('Time [s]')
    plt.ylabel('Saturation Level [%]')
    plt.ylim(0, 100)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{PAPER_IMAGES_DIR}/trend_dynamics_saturation.png", dpi=300, bbox_inches='tight')
    print(f"  Saved: trend_dynamics_saturation.png")
    plt.close()
    
    # 3. Adsorption Efficiency Plot
    efficiency_a = telemetry_data.get_adsorption_efficiency_series('sorbent_2')
    efficiency_b = telemetry_data.get_adsorption_efficiency_series('sorbent_4')
    efficiency_a_pct = [e * 100 for e in efficiency_a]
    efficiency_b_pct = [e * 100 for e in efficiency_b]
    
    apply_paper_style(plt)
    plt.plot(time_series, efficiency_a_pct, color=get_color_by_index(0), 
             linewidth=PAPER_LINE_WIDTH, 
             label='Sorbent A', linestyle=get_line_style('solid'))
    plt.plot(time_series, efficiency_b_pct, color=get_color_by_index(1), 
             linewidth=PAPER_LINE_WIDTH, 
             label='Sorbent B', linestyle=get_line_style('solid'))
    plt.xlabel('Time [s]')
    plt.ylabel('Adsorption Efficiency [%]')
    plt.ylim(0, 20)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{PAPER_IMAGES_DIR}/trend_dynamics_efficiency.png", dpi=300, bbox_inches='tight')
    print(f"  Saved: trend_dynamics_efficiency.png")
    plt.close()

def generate_trend_interstate():
    """Generate separate plots for internal state trends for different scenarios"""
    print("Generating trend_interstate plots...")
    
    # Create simulator
    simulator = CDRASimulator()
    
    # Generate data for different scenarios
    scenarios = [
        ("nominal", 0.0, "Nominal Operation"),
        ("filter saturation", 0.8, "Filter Saturation")
    ]
    
    for scenario, severity, title in scenarios:
        telemetry_data = simulator.generate_telemetry_data(
            scenario=scenario,
            severity=severity,
            duration_seconds=1000,
            baseline_co2_mmHg=3.0
        )
        
        time_series = telemetry_data.get_time_series()
        co2_series = telemetry_data.get_co2_time_series_mmhg()
        co2_output_series = telemetry_data.get_co2_output_series_mmhg()
        
        # Debug: Print CO2 values
        print(f"\n🔍 DEBUG: CO2 Concentration Values (trend_interstate - {title})")
        print("=" * 60)
        print(f"Initial cabin CO2: {co2_series[0]:.3f} mmHg")
        print(f"Initial output CO2: {co2_output_series[0]:.3f} mmHg")
        print(f"Final cabin CO2: {co2_series[-1]:.3f} mmHg")
        print(f"Final output CO2: {co2_output_series[-1]:.3f} mmHg")
        higher_output = [i for i in range(len(co2_series)) if co2_output_series[i] > co2_series[i]]
        if higher_output:
            print(f"⚠️  WARNING: C_out > C_in at {len(higher_output)} time points!")
        else:
            print(f"✅ Physics check passed: C_out < C_in at all {len(co2_series)} time points")
        print()
        
        # Create separate plots for each scenario
        
        # 1. CO2 Concentration Plot
        apply_paper_style(plt)
        plt.plot(time_series, co2_series, color=get_color_by_index(0), 
                 linewidth=PAPER_LINE_WIDTH, 
                 label='CO2 in Cabin', linestyle=get_line_style('solid'))
        plt.plot(time_series, co2_output_series, color=get_color_by_index(1), 
                 linewidth=PAPER_LINE_WIDTH, 
                 label='CO2 Flow Output', linestyle=get_line_style('dashed'))
        plt.xlabel('Time [s]')
        plt.ylabel('CO2 Concentration [mmHg]')
        plt.title(f'{title} - CO2 Concentration')
        plt.legend()
        plt.tight_layout()
        
        # Save with scenario-specific filename
        scenario_name = scenario.replace(' ', '_')
        plt.savefig(f"{PAPER_IMAGES_DIR}/trend_interstate_co2_{scenario_name}.png", dpi=300, bbox_inches='tight')
        print(f"  Saved: trend_interstate_co2_{scenario_name}.png")
        plt.close()
        
        # 2. Saturation Level Plot
        saturation_a = telemetry_data.get_saturation_series('sorbent_2')
        saturation_b = telemetry_data.get_saturation_series('sorbent_4')
        saturation_a_pct = [s * 100 for s in saturation_a]
        saturation_b_pct = [s * 100 for s in saturation_b]
        
        apply_paper_style(plt)
        plt.plot(time_series, saturation_a_pct, color=get_color_by_index(0), 
                 linewidth=PAPER_LINE_WIDTH, 
                 label='Sorbent A', linestyle=get_line_style('solid'))
        plt.plot(time_series, saturation_b_pct, color=get_color_by_index(1), 
                 linewidth=PAPER_LINE_WIDTH, 
                 label='Sorbent B', linestyle=get_line_style('solid'))
        plt.xlabel('Time [s]')
        plt.ylabel('Saturation Level [%]')
        plt.title(f'{title} - Saturation Level')
        plt.ylim(0, 100)
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"{PAPER_IMAGES_DIR}/trend_interstate_saturation_{scenario_name}.png", dpi=300, bbox_inches='tight')
        print(f"  Saved: trend_interstate_saturation_{scenario_name}.png")
        plt.close()
        
        # 3. Adsorption Efficiency Plot
        efficiency_a = telemetry_data.get_adsorption_efficiency_series('sorbent_2')
        efficiency_b = telemetry_data.get_adsorption_efficiency_series('sorbent_4')
        efficiency_a_pct = [e * 100 for e in efficiency_a]
        efficiency_b_pct = [e * 100 for e in efficiency_b]
        
        apply_paper_style(plt)
        plt.plot(time_series, efficiency_a_pct, color=get_color_by_index(0), 
                 linewidth=PAPER_LINE_WIDTH, 
                 label='Sorbent A', linestyle=get_line_style('solid'))
        plt.plot(time_series, efficiency_b_pct, color=get_color_by_index(1), 
                 linewidth=PAPER_LINE_WIDTH, 
                 label='Sorbent B', linestyle=get_line_style('solid'))
        plt.xlabel('Time [s]')
        plt.ylabel('Adsorption Efficiency [%]')
        plt.title(f'{title} - Adsorption Efficiency')
        plt.ylim(0, 20)
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"{PAPER_IMAGES_DIR}/trend_interstate_efficiency_{scenario_name}.png", dpi=300, bbox_inches='tight')
        print(f"  Saved: trend_interstate_efficiency_{scenario_name}.png")
        plt.close()

def generate_trend_fault():
    """Generate trend_fault.png - ppCO2 trend for each fundamental fault scenario"""
    print("Generating trend_fault.png...")
    
    # Create simulator
    simulator = CDRASimulator()
    
    # Define fundamental fault scenarios from the paper
    fault_scenarios = [
        ("valve stuck", 0.6, "H1: Valve Stuck"),
        ("fan degraded", 0.5, "H2: Fan Degradation"), 
        ("filter saturation", 0.8, "H3: Filter Saturation")
    ]
    
    # Create figure
    apply_paper_style(plt)
    
    # Generate and plot each fault scenario
    for i, (scenario, severity, label) in enumerate(fault_scenarios):
        telemetry_data = simulator.generate_telemetry_data(
            scenario=scenario,
            severity=severity,
            duration_seconds=1000,
            baseline_co2_mmHg=3.0
        )
        
        co2_series = telemetry_data.get_co2_time_series_mmhg()
        time_series = telemetry_data.get_time_series()
        
        plt.plot(time_series, co2_series, linewidth=PAPER_LINE_WIDTH, 
                 label=label, color=get_color_by_index(i))
    
    # Add nominal for comparison
    nominal_data = simulator.generate_telemetry_data(
        scenario="nominal",
        severity=0.0,
        duration_seconds=1000,
        baseline_co2_mmHg=3.0
    )
    nominal_co2 = nominal_data.get_co2_time_series_mmhg()
    plt.plot(time_series, nominal_co2, color=get_color('nominal'), 
             linewidth=PAPER_LINE_WIDTH, 
             label='Nominal', alpha=0.7, linestyle=get_line_style('dashed'))
    
    plt.xlabel('Time [s]')
    plt.ylabel('CO2 Concentration [mmHg]')
    # plt.title('ppCO2 Trend for Each Fundamental Fault')
    plt.legend()
    
    # Save to paper images directory
    plt.savefig(f"{PAPER_IMAGES_DIR}/trend_fault.png", dpi=300, bbox_inches='tight')
    print(f"  Saved: trend_fault.png")
    plt.close()

# Fixed constants for all paper plots
PAPER_FIGSIZE = (20, 12)          # Figure size (width, height) in inches
PAPER_TITLE_FONT = 16*3             # Title font size
PAPER_FONT = 40             # Title font size
PAPER_LABEL_FONT = 40             # Axis label font size
PAPER_TICK_FONT = 40              # Tick label font size
PAPER_LEGEND_FONT = 40            # Legend font size
PAPER_ANNOTATION_FONT = 40        # Annotation font size
PAPER_LINE_WIDTH = 8              # Line width
PAPER_MARKER_SIZE = 20             # Marker size
PAPER_GRID_ALPHA = 0.3*2            # Grid transparency
PAPER_GRID_STYLE = '--'           # Grid line style
PAPER_GRID_WIDTH = 0.5*2            # Grid line width

def apply_paper_style(plt):
    """Apply standardized paper styling to a matplotlib plot."""
    plt.figure(figsize=PAPER_FIGSIZE)
    plt.rcParams.update({
        'font.size': PAPER_FONT,
        'axes.titlesize': PAPER_TITLE_FONT,
        'axes.labelsize': PAPER_LABEL_FONT,
        'xtick.labelsize': PAPER_TICK_FONT,
        'ytick.labelsize': PAPER_TICK_FONT,
        'legend.fontsize': PAPER_LEGEND_FONT,
        'figure.titlesize': PAPER_TITLE_FONT,
    })
    plt.grid(True, alpha=PAPER_GRID_ALPHA, 
             linestyle=PAPER_GRID_STYLE, 
             linewidth=PAPER_GRID_WIDTH)



def main():
    """Generate all trend images for the paper"""
    print("🎯 Generating Paper Trend Images")
    print("=" * 50)
    print(f"Images will be saved to: {PAPER_IMAGES_DIR}")
    print()
    
    # Generate all three trend images
    generate_trend_dynamics()
    generate_trend_interstate()
    generate_trend_fault()
    
    print()
    print("✅ All trend images generated successfully!")
    print("Generated images:")
    print("  - trend_dynamics_co2.png: CO2 concentration trends")
    print("  - trend_dynamics_saturation.png: Saturation level trends")
    print("  - trend_dynamics_efficiency.png: Adsorption efficiency trends")
    print("  - trend_interstate_co2_nominal.png: CO2 trends for nominal scenario")
    print("  - trend_interstate_saturation_nominal.png: Saturation trends for nominal scenario")
    print("  - trend_interstate_efficiency_nominal.png: Efficiency trends for nominal scenario")
    print("  - trend_interstate_co2_filter_saturation.png: CO2 trends for filter saturation scenario")
    print("  - trend_interstate_saturation_filter_saturation.png: Saturation trends for filter saturation scenario")
    print("  - trend_interstate_efficiency_filter_saturation.png: Efficiency trends for filter saturation scenario")
    print("  - trend_fault.png: ppCO2 trends for fundamental fault scenarios")

if __name__ == "__main__":
    main()
