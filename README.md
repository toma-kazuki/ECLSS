# ECLSS (Environmental Control and Life Support System) Simulation

This repository contains a comprehensive CDRA (Carbon Dioxide Removal Assembly) simulation system with advanced similarity analysis capabilities for spacecraft fault diagnosis.

## Project Structure

### Core Components

- **`cdra_simulator.py`** - Main simulation engine with comprehensive CDRA modeling
  - `CDRASimulator` class - Core simulation functionality
  - `CDRATelemetryData` class - Data handling and visualization
  - Built-in plotting methods for comprehensive analysis

- **`similarity_agent.py`** - Advanced similarity analysis engine
  - Multiple similarity methods: MSE, MAE, Pearson, Spearman, DTW, ARIMA, FFT
  - Time series alignment and comparison
  - Ranking and visualization capabilities

### Demo Scripts

- **`example_usage.py`** - Basic usage examples and demonstrations
- **`plotting_demo.py`** - Comprehensive plotting capabilities showcase
- **`mc_evaluation.py`** - Monte Carlo robustness evaluation for fault diagnosis

### Configuration

- **`requirements.txt`** - Python dependencies
- **`venv/`** - Virtual environment (excluded from version control)

## Features

### Simulation Capabilities
- 7 fault scenarios (Valve, Fan, Filter, and combinations)
- Realistic CDRA physics modeling
- Configurable severity levels and duration
- Unit conversions (mmHg, kg/kg air, ppm, percent)

### Similarity Analysis Methods
- **MSE/MAE** - Mean Squared/Absolute Error
- **Pearson/Spearman** - Linear and rank correlation
- **DTW** - Dynamic Time Warping for time series alignment
- **ARIMA** - Time series forecasting-based similarity
- **FFT** - Frequency domain analysis

### Visualization
- CO2 concentration plots with detection thresholds
- Component state analysis (saturation, efficiency, heaters)
- System overview (4-panel comprehensive view)
- Multi-scenario comparisons
- Analysis summaries with key metrics

## Usage

### Basic Simulation
```python
from cdra_simulator import CDRASimulator

simulator = CDRASimulator()
telemetry_data = simulator.generate_telemetry_data(
    scenario="filter saturation",
    severity=0.5,
    duration_seconds=1000,
    baseline_co2_mmHg=3.0
)

# Plot results
telemetry_data.plot_co2_concentration()
```

### Similarity Analysis
```python
from similarity_agent import SimilarityAgent

agent = SimilarityAgent(method="MSE")
results = agent.compare_multiple_simulations(
    telemetry_data, 
    simulation_scenarios,
    segment_length=400,
    find_best_alignment=True
)
ranking = agent.get_ranking(results)
```

### Monte Carlo Evaluation
```python
python MCevaluation.py
```

## Dependencies

- numpy
- matplotlib
- scipy
- scikit-learn
- dtaidistance
- statsmodels (optional, for ARIMA)

## Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run demos:
```bash
python example_usage.py
python plotting_demo.py
python mc_evaluation.py
```

## Recent Updates

- Integrated all similarity methods from individual modules into `SimilarityAgent`
- Removed redundant files (`cdra_sim_adapter.py`, `CDRA.py`, `cdra_similarity_demo.py`)
- Consolidated Similarity folder methods into main similarity agent
- Streamlined project structure for better maintainability
