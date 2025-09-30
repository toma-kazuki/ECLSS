#!/usr/bin/env python3
"""
CONSISTENT COLOR SCHEME FOR PAPER PLOTS
======================================

This module defines a consistent color palette for all plots in the IEEE Aerospace Conference paper.
The color scheme is designed to be:
- Professional and publication-ready
- Colorblind-friendly
- Consistent across all figures
- High contrast for both print and digital viewing

Color Palette:
- Primary Blue: #1f77b4 (matplotlib default blue)
- Primary Orange: #ff7f0e (matplotlib default orange) 
- Primary Green: #2ca02c (matplotlib default green)
- Primary Red: #d62728 (matplotlib default red)
- Primary Purple: #9467bd (matplotlib default purple)
- Primary Brown: #8c564b (matplotlib default brown)
- Primary Pink: #e377c2 (matplotlib default pink)
- Primary Gray: #7f7f7f (matplotlib default gray)
- Primary Olive: #bcbd22 (matplotlib default olive)
- Primary Cyan: #17becf (matplotlib default cyan)

Additional Colors:
- Dark Blue: #1e3a8a (for emphasis)
- Dark Orange: #ea580c (for emphasis)
- Light Blue: #93c5fd (for backgrounds)
- Light Orange: #fed7aa (for backgrounds)
- Black: #000000 (for text and lines)
- White: #ffffff (for text on dark backgrounds)
- Gray Light: #f3f4f6 (for backgrounds)
- Gray Medium: #9ca3af (for secondary elements)
- Gray Dark: #374151 (for text)
"""

# Primary color palette (matplotlib tab10 colors)
COLORS = {
    # Primary colors for main data series
    'blue': '#1f77b4',
    'orange': '#ff7f0e', 
    'green': '#2ca02c',
    'red': '#d62728',
    'purple': '#9467bd',
    'brown': '#8c564b',
    'pink': '#e377c2',
    'gray': '#7f7f7f',
    'olive': '#bcbd22',
    'cyan': '#17becf',
    
    # Emphasis colors (darker versions)
    'blue_dark': '#1e3a8a',
    'orange_dark': '#ea580c',
    'green_dark': '#166534',
    'red_dark': '#991b1b',
    'purple_dark': '#6b21a8',
    
    # Light colors (for backgrounds and fills)
    'blue_light': '#93c5fd',
    'orange_light': '#fed7aa',
    'green_light': '#bbf7d0',
    'red_light': '#fecaca',
    'purple_light': '#e9d5ff',
    
    # Neutral colors
    'black': '#000000',
    'white': '#ffffff',
    'gray_light': '#f3f4f6',
    'gray_medium': '#9ca3af',
    'gray_dark': '#374151',
    
    # Additional colors
    'yellow': '#ffd700',
    'yellow_light': '#fffacd',
}

# Color assignments for specific plot types
PLOT_COLORS = {
    # Detection and thresholds (keep these specific for clarity)
    'detection_threshold': COLORS['red'],
    'detection_line': COLORS['red'],
    'detection_annotation': COLORS['yellow'],
    
    # Nominal/reference lines (keep black for reference)
    'nominal': COLORS['black'],
    'reference': COLORS['black'],
    
    # Similarity comparison (keep these specific)
    'telemetry_data': COLORS['black'],
    'simulation_data': COLORS['red'],
    'comparison_segment': COLORS['yellow'],
}

# Line styles for different plot types
LINE_STYLES = {
    'solid': '-',
    'dashed': '--',
    'dotted': ':',
    'dashdot': '-.',
    'nominal': '--',  # Dashed for nominal/reference lines
    'fault': '-',     # Solid for fault scenarios
}

# Marker styles for scatter plots and points
MARKERS = {
    'circle': 'o',
    'square': 's',
    'triangle': '^',
    'diamond': 'D',
    'plus': '+',
    'x': 'x',
    'star': '*',
}

def get_color(color_name: str) -> str:
    """
    Get a color by name from the color scheme.
    
    Args:
        color_name: Name of the color (e.g., 'blue', 'co2_cabin')
        
    Returns:
        Hex color code
    """
    if color_name in PLOT_COLORS:
        return PLOT_COLORS[color_name]
    elif color_name in COLORS:
        return COLORS[color_name]
    else:
        print(f"Warning: Color '{color_name}' not found in color scheme. Using default blue.")
        return COLORS['blue']

def get_line_style(style_name: str) -> str:
    """
    Get a line style by name.
    
    Args:
        style_name: Name of the line style
        
    Returns:
        Matplotlib line style string
    """
    return LINE_STYLES.get(style_name, '-')

def get_marker(marker_name: str) -> str:
    """
    Get a marker style by name.
    
    Args:
        marker_name: Name of the marker
        
    Returns:
        Matplotlib marker string
    """
    return MARKERS.get(marker_name, 'o')

# Color lists for multiple series plots
COLOR_SEQUENCE = [
    COLORS['blue'],
    COLORS['orange'], 
    COLORS['green'],
    COLORS['red'],
    COLORS['purple'],
    COLORS['brown'],
    COLORS['pink'],
    COLORS['gray'],
    COLORS['olive'],
    COLORS['cyan'],
]

# Scenario-specific color mapping (using sequential colors)
SCENARIO_COLORS = {
    'nominal': PLOT_COLORS['nominal'],  # Keep black for nominal
    'valve stuck': COLOR_SEQUENCE[0],    # Blue
    'fan degraded': COLOR_SEQUENCE[1],   # Orange
    'filter saturation': COLOR_SEQUENCE[2], # Green
    'heater failure': COLOR_SEQUENCE[3],    # Red
    'valve': COLOR_SEQUENCE[0],
    'fan': COLOR_SEQUENCE[1],
    'filter': COLOR_SEQUENCE[2],
    'Valve': COLOR_SEQUENCE[0],
    'Fan': COLOR_SEQUENCE[1],
    'Filter': COLOR_SEQUENCE[2],
    'Valve+Fan': COLOR_SEQUENCE[4],      # Purple
    'Valve+Filter': COLOR_SEQUENCE[5],   # Brown
    'Fan+Filter': COLOR_SEQUENCE[6],     # Pink
    'Valve+Fan+Filter': COLOR_SEQUENCE[7], # Gray
}

def get_scenario_color(scenario_name: str) -> str:
    """
    Get color for a specific scenario.
    
    Args:
        scenario_name: Name of the scenario
        
    Returns:
        Hex color code for the scenario
    """
    return SCENARIO_COLORS.get(scenario_name, COLOR_SEQUENCE[0])

def get_color_by_index(index: int) -> str:
    """
    Get color by index from the sequential color palette.
    
    Args:
        index: Index in the color sequence (0-based)
        
    Returns:
        Hex color code for the index
    """
    return COLOR_SEQUENCE[index % len(COLOR_SEQUENCE)]

def get_colors_for_count(count: int) -> list:
    """
    Get a list of colors for a given number of items.
    
    Args:
        count: Number of colors needed
        
    Returns:
        List of hex color codes
    """
    return [get_color_by_index(i) for i in range(count)]

# =========================
# Paper Plot Constants
# =========================

# Fixed constants for all paper plots
PAPER_FIGSIZE = (10, 6)          # Figure size (width, height) in inches
PAPER_TITLE_FONT = 16*3             # Title font size
PAPER_FONT = 12*2             # Title font size
PAPER_LABEL_FONT = 14*2             # Axis label font size
PAPER_TICK_FONT = 12*2              # Tick label font size
PAPER_LEGEND_FONT = 12*2            # Legend font size
PAPER_ANNOTATION_FONT = 10*2        # Annotation font size
PAPER_LINE_WIDTH = 4              # Line width
PAPER_MARKER_SIZE = 8*2             # Marker size
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
