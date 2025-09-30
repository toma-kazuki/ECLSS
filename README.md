# CDRA Fault Diagnosis

**Initial Development of A Physics-Based Agent for Real-Time Collaborative Fault Diagnosis in Space Habitats**

This repository contains a comprehensive CDRA (Carbon Dioxide Removal Assembly) simulation system with advanced similarity analysis capabilities for spacecraft fault diagnosis. The generated plots and analysis results are used in the **IEEE Aerospace Conference 2026** paper.

## Abstract

Planned human exploration missions to the Moon and Mars will require significant crew autonomy to handle long communication delays, particularly for urgent tasks such as diagnosing faults in the habitat. This paper presents the initial development of a physics-based diagnosis agent in space habitats and the preliminary simulation results of the case study of CO₂ removal systems. This research addresses the need for autonomous system fault management in future deep space missions and characterizes the performance of the physics-based diagnosis agent, in terms of accuracy and robustness to noise and to anomalies with similar signatures. The approach is meant to be used by a virtual assistant in an iterative, human-agent collaborative fault diagnosis process. The case study demonstrated explainable causal inference between subcomponent failure of CO₂ removal systems and the progression trend of partial pressure of CO₂ (ppCO₂) in cabin with the interpretable ranked similarity scores. The misclassification tendency and noise robustness was also shown.

## Research Objectives

The primary objectives of this research are:

1. **Develop Physics-Based Diagnostic Agent**: Create an intuitive design of physics-based collaborative agent with systematic FDIR (Fault Detection, Isolation, and Recovery) support that is executable by commonly available programming.

2. **Characterize Performance**: Evaluate the performance of the physics-based diagnosis agent in terms of:
   - Accuracy in identifying different failure modes
   - Robustness to sensor noise
   - Handling of anomalies with similar signatures

3. **Enable Collaborative Diagnosis**: Design the agent to work as a virtual assistant in an iterative, human-agent collaborative fault diagnosis process for deep space missions.

4. **Provide Explainable Results**: Generate interpretable ranked similarity scores and causal inference between subcomponent failures and system behavior trends.

## Quick Start

### Prerequisites
- Python 3.7+
- Virtual environment (recommended)

### Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd cdra-fault-diagnosis
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run basic demos**:
   ```bash
   # Basic simulation and analysis
   python data_analysis_demo.py
   python plotting_demo.py
   
   # Generate paper figures
   python paper_trend_generator.py
   python paper_mc_evaluation.py
   ```

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

- **`data_analysis_demo.py`** - Data analysis and template building examples
- **`plotting_demo.py`** - Comprehensive plotting capabilities showcase
- **`paper_mc_evaluation.py`** - Monte Carlo robustness evaluation for fault diagnosis (generates paper figures)
- **`paper_trend_generator.py`** - Generates specific trend images for IEEE Aerospace Conference 2026 paper

### Configuration

- **`requirements.txt`** - Python dependencies
- **`venv/`** - Virtual environment (excluded from version control)

