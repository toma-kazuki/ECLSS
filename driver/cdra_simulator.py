from typing import Dict, List, Optional, Tuple
import math
import random
import matplotlib.pyplot as plt
import numpy as np
from color_scheme import get_color, get_line_style, get_scenario_color, get_color_by_index


class CDRASimulator:
    """
    A comprehensive CDRA (Carbon Dioxide Removal Assembly) simulator class.
    
    This class encapsulates all CDRA simulation functionality including:
    - Unit conversions for CO2 measurements
    - Simulation state management
    - Failure mode handling
    - Control logic
    - Time series generation
    """
    
    # Constants
    AIR_FLOW_RATE_NOMINAL = 1.0  # kg/s nominal
    VALVE_SWITCH_INTERVAL = 200   # s
    SATURATION_TIME_CONSTANT = 600.0
    BASE_ADSORPTION_EFF = 0.05
    MAX_ADSORPTION_EFF_INCREMENT = 0.15
    DESORPTION_MULTIPLIER = 1.05
    M_CABIN = 100.0
    CO2_INPUT_MEAN = 0.00002 * 30
    
    # Unit conversion constants for CO2
    STANDARD_PRESSURE_MMHG = 760.0
    MOLAR_MASS_CO2 = 44.01  # g/mol
    MOLAR_MASS_AIR = 28.97  # g/mol
    GAS_CONSTANT_R = 8.314  # J/(mol·K)
    STANDARD_TEMPERATURE_K = 298.15  # 25°C in Kelvin
    
    def __init__(self):
        """Initialize the CDRA simulator."""
        self.state = None
        self.simulation_history = []
    
    def mmhg_to_kg_per_kg_air(self, co2_mmhg: float) -> float:
        """
        Convert CO2 partial pressure from mmHg to kg/kg air.
        
        Args:
            co2_mmhg: CO2 partial pressure in mmHg
            
        Returns:
            CO2 concentration in kg/kg air
        """
        # Convert mmHg to Pa (1 mmHg = 133.322 Pa)
        co2_pa = co2_mmhg * 133.322
        
        # Use ideal gas law: n/V = P/(RT)
        # Then convert to mass ratio: (n_CO2 * M_CO2) / (n_air * M_air)
        # Since we're working with ratios, we can simplify
        co2_mol_per_mol_air = co2_pa / (self.STANDARD_PRESSURE_MMHG * 133.322)
        
        # Convert to mass ratio
        co2_kg_per_kg_air = co2_mol_per_mol_air * (self.MOLAR_MASS_CO2 / self.MOLAR_MASS_AIR)
        
        return co2_kg_per_kg_air

    def kg_per_kg_air_to_mmhg(self, co2_kg_per_kg_air: float) -> float:
        """
        Convert CO2 concentration from kg/kg air to mmHg.
        
        Args:
            co2_kg_per_kg_air: CO2 concentration in kg/kg air
            
        Returns:
            CO2 partial pressure in mmHg
        """
        # Convert mass ratio to molar ratio
        co2_mol_per_mol_air = co2_kg_per_kg_air * (self.MOLAR_MASS_AIR / self.MOLAR_MASS_CO2)
        
        # Convert to partial pressure in Pa
        co2_pa = co2_mol_per_mol_air * (self.STANDARD_PRESSURE_MMHG * 133.322)
        
        # Convert Pa to mmHg
        co2_mmhg = co2_pa / 133.322
        
        return co2_mmhg

    def convert_co2_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert CO2 concentration between different units.
        
        Args:
            value: CO2 concentration value
            from_unit: Source unit ('mmHg', 'kg/kg_air', 'ppm', 'percent')
            to_unit: Target unit ('mmHg', 'kg/kg_air', 'ppm', 'percent')
            
        Returns:
            Converted CO2 concentration value
            
        Raises:
            ValueError: If unsupported units are provided
        """
        # First convert to kg/kg_air as intermediate unit
        if from_unit == 'mmHg':
            intermediate = self.mmhg_to_kg_per_kg_air(value)
        elif from_unit == 'kg/kg_air':
            intermediate = value
        elif from_unit == 'ppm':
            # ppm is parts per million by volume, convert to mass ratio
            intermediate = value * 1e-6 * (self.MOLAR_MASS_CO2 / self.MOLAR_MASS_AIR)
        elif from_unit == 'percent':
            # percent by volume, convert to mass ratio
            intermediate = value * 0.01 * (self.MOLAR_MASS_CO2 / self.MOLAR_MASS_AIR)
        else:
            raise ValueError(f"Unsupported source unit: {from_unit}")
        
        # Then convert from kg/kg_air to target unit
        if to_unit == 'mmHg':
            return self.kg_per_kg_air_to_mmhg(intermediate)
        elif to_unit == 'kg/kg_air':
            return intermediate
        elif to_unit == 'ppm':
            # Convert mass ratio to volume ratio (ppm)
            volume_ratio = intermediate * (self.MOLAR_MASS_AIR / self.MOLAR_MASS_CO2)
            return volume_ratio * 1e6
        elif to_unit == 'percent':
            # Convert mass ratio to volume ratio (percent)
            volume_ratio = intermediate * (self.MOLAR_MASS_AIR / self.MOLAR_MASS_CO2)
            return volume_ratio * 100
        else:
            raise ValueError(f"Unsupported target unit: {to_unit}")

    def create_state(self, baseline_co2: float) -> 'CDRAState':
        """
        Create a new CDRA simulation state.
        
        Args:
            baseline_co2: Initial CO2 concentration in kg/kg air
            
        Returns:
            CDRAState object
        """
        return CDRAState(baseline_co2)

    def apply_failures(self, state: 'CDRAState', t: int, cfg: Dict) -> None:
        """
        Apply failures to the CDRA state.
        
        Args:
            state: CDRA simulation state
            t: Current time step
            cfg: Failure configuration dictionary
        """
        # --- Filter Saturation Handling ---
        fs_on = cfg.get('filter_saturation')
        fs_start = cfg.get('filter_saturation_start')
        fs_end = cfg.get('filter_saturation_end')

        if fs_on and fs_start <= t <= fs_end:
            for comp in state.saturation:
                state.saturation[comp] = 1.0
                state.adsorption_eff[comp] = self.BASE_ADSORPTION_EFF + self.MAX_ADSORPTION_EFF_INCREMENT * 1.0

        # --- Heater Failure Handling ---
        heater_failures = cfg.get('heater_failure', []) or []
        for h in heater_failures:
            state.heater_on[h] = False

        # --- Fan Degraded Handling ---
        fd_on = bool(cfg.get('fan_degraded', False))
        fd_start = cfg.get('fan_degraded_start')
        fd_end = cfg.get('fan_degraded_end')
        
        if fd_on and fd_start <= t <= fd_end:
            state.air_flow_rate = cfg.get('degraded_flow_rate')
        else:
            state.air_flow_rate = self.AIR_FLOW_RATE_NOMINAL

    def update_filter(self, state: 'CDRAState', component: str, dt: int) -> None:
        """
        Update filter saturation and efficiency for a component.
        
        Args:
            state: CDRA simulation state
            component: Component name
            dt: Time step duration
        """
        if state.heater_on[component]:
            state.saturation[component] = max(state.saturation[component] - (2.0 * dt) / self.SATURATION_TIME_CONSTANT, 0.0)
        else:
            state.saturation[component] = min(state.saturation[component] + dt / self.SATURATION_TIME_CONSTANT, 1.0)
        state.adsorption_eff[component] = self.BASE_ADSORPTION_EFF + self.MAX_ADSORPTION_EFF_INCREMENT * (1 - state.saturation[component])

    def timestep(self, state: 'CDRAState', dt: int) -> Tuple[float, float]:
        """
        Calculate one simulation timestep.
        
        Args:
            state: CDRA simulation state
            dt: Time step duration
            
        Returns:
            Tuple of (CO2_out, air_flow_rate)
        """
        # Update both paths
        self.update_filter(state, 'desiccant_1', dt)
        self.update_filter(state, 'sorbent_2', dt)
        self.update_filter(state, 'desiccant_3', dt)
        self.update_filter(state, 'sorbent_4', dt)

        # Choose path efficiency
        active_path = state.valve_state['path_1_active']
        if active_path:
            eta_co2 = state.adsorption_eff['sorbent_2'] if not state.heater_on['sorbent_2'] else -self.DESORPTION_MULTIPLIER
        else:
            eta_co2 = state.adsorption_eff['sorbent_4'] if not state.heater_on['sorbent_4'] else -self.DESORPTION_MULTIPLIER

        C_in = state.co2_content
        C_out = C_in * (1 - eta_co2) if eta_co2 >= 0 else C_in * eta_co2
        
        return C_out, state.air_flow_rate

    def update_cabin_concentration(self, state: 'CDRAState', C_out: float, flow: float) -> None:
        """
        Update cabin CO2 concentration.
        
        Args:
            state: CDRA simulation state
            C_out: CO2 concentration out of CDRA
            flow: Air flow rate
        """
        state.co2_content = ((1 - flow / self.M_CABIN) * state.co2_content + (flow / self.M_CABIN) * C_out + self.CO2_INPUT_MEAN / self.M_CABIN)

    def control(self, state: 'CDRAState', failure_config: Dict = None) -> None:
        """
        Apply control logic to the CDRA system.
        
        Args:
            state: CDRA simulation state
            failure_config: Optional failure configuration
        """
        # --- Valve Control Handling with failure awareness ---
        valve_stuck = False
        if failure_config:
            valve_failure = failure_config.get('valve_stuck')
            vs_start = failure_config.get('valve_stuck_start')
            vs_end = failure_config.get('valve_stuck_end')
            valve_stuck = valve_failure and vs_start <= state.time <= vs_end
        
        if not valve_stuck and state.time % self.VALVE_SWITCH_INTERVAL == 0 and state.time != 0:
            state.valve_state['path_1_active'] = not state.valve_state['path_1_active']
        
        # --- Heater Control Handling with failure awareness ---
        failed_heaters = set()
        if failure_config:
            failed_heaters = set(failure_config.get('heater_failure', []))
        
        # Only set heater states for heaters that are not failed
        if 'desiccant_1' not in failed_heaters:
            state.heater_on['desiccant_1'] = not state.valve_state['path_1_active']
        if 'desiccant_3' not in failed_heaters:
            state.heater_on['desiccant_3'] = state.valve_state['path_1_active']
        if 'sorbent_2' not in failed_heaters:
            state.heater_on['sorbent_2'] = not state.valve_state['path_1_active']
        if 'sorbent_4' not in failed_heaters:
            state.heater_on['sorbent_4'] = state.valve_state['path_1_active']

    def run_simulation(
        self,
        failure_config: Dict,
        duration_seconds: int,
        baseline_co2_mmHg: float,
    ) -> 'CDRAState':
        """
        Run CDRA simulation and return CO2 partial pressure time series in mmHg.
        
        Args:
            failure_config: Failure configuration dictionary
            duration_seconds: Total simulation time
            baseline_co2_mmHg: Starting cabin CO2 concentration in mmHg
            
        Returns:
            CDRAState with complete simulation history
        """
        dt = 1
        steps = max(1, int(duration_seconds // dt))

        # Convert input from mmHg to kg/kg air for internal simulation
        baseline_co2_kg_per_kg = self.mmhg_to_kg_per_kg_air(baseline_co2_mmHg)
        
        state = self.create_state(baseline_co2=baseline_co2_kg_per_kg)
        self.state = state

        for step in range(steps):
            # Activate failures after onset
            active_cfg = dict(failure_config)
            
            # Basic control (now with failure awareness)
            self.control(state, active_cfg)
            self.apply_failures(state, state.time, active_cfg)
            C_out, flow = self.timestep(state, dt)
            self.update_cabin_concentration(state, C_out, flow)
            state.time += dt

            # Update history for plotting
            for k in state.saturation:
                state.history['saturation'][k].append(state.saturation[k])
                state.history['adsorption_eff'][k].append(state.adsorption_eff[k])
            state.history['time'].append(state.time)
            state.history['co2_content'].append(state.co2_content)
            state.history['co2_output'].append(C_out)  # Store CO2 concentration out of CDRA
            state.history['air_flow_rate'].append(state.air_flow_rate)
            state.history['desiccant_heaters'].append((state.heater_on['desiccant_1'], state.heater_on['desiccant_3']))
            state.history['sorbent_heaters'].append((state.heater_on['sorbent_2'], state.heater_on['sorbent_4']))
            state.history['active_path'].append(state.valve_state['path_1_active'])
            state.history['desiccant_1_heater'].append(int(state.heater_on['desiccant_1']))
            state.history['desiccant_3_heater'].append(int(state.heater_on['desiccant_3']))
            state.history['sorbent_2_heater'].append(int(state.heater_on['sorbent_2']))
            state.history['sorbent_4_heater'].append(int(state.heater_on['sorbent_4']))

        return state

    def resample_series(self, values: List[float], target_len: int) -> List[float]:
        """
        Resample a time series to a target length using linear interpolation.
        
        Args:
            values: Input time series
            target_len: Target length
            
        Returns:
            Resampled time series
        """
        if target_len <= 0:
            return []
        if len(values) == target_len:
            return list(values)
        if len(values) == 0:
            return [0.0] * target_len
        
        # Handle case where target length is larger than input length
        if target_len > len(values):
            # Interpolate between existing points to increase density across the full span
            if len(values) == 1:
                # If only one value, repeat it (edge case)
                return [values[0]] * target_len
            else:
                # Create a denser interpolation across the full range
                result = []
                for i in range(target_len):
                    # Map target index to original data range
                    # This ensures we cover the full span from first to last value
                    pos = i * (len(values) - 1) / (target_len - 1)
                    lo = int(math.floor(pos))
                    hi = min(lo + 1, len(values) - 1)
                    frac = pos - lo
                    
                    # Linear interpolation between consecutive points
                    v = values[lo] * (1 - frac) + values[hi] * frac
                    result.append(v)
                
                return result
        
        # Original case: target length is smaller than or equal to input length
        # Linear resample
        result: List[float] = []
        for i in range(target_len):
            pos = i * (len(values) - 1) / (target_len - 1)
            lo = int(math.floor(pos))
            hi = min(lo + 1, len(values) - 1)
            frac = pos - lo
            v = values[lo] * (1 - frac) + values[hi] * frac
            result.append(v)
        return result

    def anomaly_to_failure_config(self, anomaly_name: str, severity: float) -> Dict:
        """
        Map common CDRA anomaly names to failure config.
        
        Args:
            anomaly_name: Name of the anomaly
            severity: Severity level (0.0 to 1.0)
            
        Returns:
            Failure configuration dictionary
        """
        print(f"[ANOMALY_CFG] Converting anomaly '{anomaly_name}' with severity {severity:.3f}")
        
        # Map common CDRA anomaly names to failure config
        name = anomaly_name.lower()
        cfg: Dict = {
            'filter_saturation': False,
            'filter_saturation_start': 0,  # Default to never
            'filter_saturation_end': 10**9,
            'valve_stuck': False,
            'valve_stuck_start': 0,  # Default to never
            'valve_stuck_end': 10**9,
            'heater_failure': [],
            'fan_degraded': False,
            'fan_degraded_start': 0,  # Default to never
            'fan_degraded_end': 10**9,
            'degraded_flow_rate': max(0.1, self.AIR_FLOW_RATE_NOMINAL * (1 - severity)),
        }
        
        print(f"[ANOMALY_CFG] Checking name '{name}' against patterns...")
        
        if 'saturat' in name or 'absorption bed' in name or 'filter' in name:
            cfg['filter_saturation'] = True
            print(f"[ANOMALY_CFG] MATCH: 'saturat' or 'absorption bed' or 'filter' -> filter_saturation=True, onset={cfg['filter_saturation_start']}")
        
        if 'valve' in name or 'leak' in name:
            cfg['valve_stuck'] = True
            print(f"[ANOMALY_CFG] MATCH: 'valve' or 'leak' -> valve_stuck=True, onset={cfg['valve_stuck_start']}")
        if 'heater' in name:
            cfg['heater_failure'] = ['desiccant_1', 'sorbent_2']
            print(f"[ANOMALY_CFG] MATCH: 'heater' -> heater_failure={cfg['heater_failure']}")
        if 'fan' in name or 'bearing' in name:
            cfg['fan_degraded'] = True
            print(f"[ANOMALY_CFG] MATCH: 'fan' or 'bearing' -> fan_degraded=True, onset={cfg['fan_degraded_start']}, flow_rate={cfg['degraded_flow_rate']:.3f}")
        if 'sensor drift' in name or 'drift' in name:
            print(f"[ANOMALY_CFG] MATCH: 'sensor drift' or 'drift' -> handled in caller by post-process drift")
            # handled in caller by post-process drift
            pass
        
        print(f"[ANOMALY_CFG] ---")
        return cfg

    def get_co2_time_series_mmhg(self) -> List[float]:
        """
        Get CO2 time series in mmHg units.
        
        Returns:
            List of CO2 concentrations in mmHg
        """
        if self.state is None:
            return []
        
        return [self.kg_per_kg_air_to_mmhg(co2) for co2 in self.state.history['co2_content']]

    def get_simulation_summary(self) -> Dict:
        """
        Get a summary of the simulation results.
        
        Returns:
            Dictionary with simulation summary statistics
        """
        if self.state is None:
            return {}
        
        co2_series_mmhg = self.get_co2_time_series_mmhg()
        
        return {
            'duration_seconds': self.state.time,
            'final_co2_mmhg': co2_series_mmhg[-1] if co2_series_mmhg else 0.0,
            'initial_co2_mmhg': co2_series_mmhg[0] if co2_series_mmhg else 0.0,
            'max_co2_mmhg': max(co2_series_mmhg) if co2_series_mmhg else 0.0,
            'min_co2_mmhg': min(co2_series_mmhg) if co2_series_mmhg else 0.0,
            'avg_co2_mmhg': sum(co2_series_mmhg) / len(co2_series_mmhg) if co2_series_mmhg else 0.0,
            'total_timesteps': len(co2_series_mmhg)
        }

    def generate_telemetry_data(
        self,
        scenario: str,
        severity: float = 0.5,
        duration_seconds: int = 1000,
        baseline_co2_mmHg: float = 3.0
    ) -> 'CDRATelemetryData':
        """
        Generate telemetry data for a specific scenario.
        
        This method combines anomaly configuration, simulation execution,
        and telemetry data processing into a single call.
        
        Args:
            scenario: Anomaly scenario name
            severity: Severity level (0.0 to 1.0)
            duration_seconds: Simulation duration
            baseline_co2_mmHg: Initial CO2 concentration
            
        Returns:
            CDRATelemetryData object with processed telemetry
        """
        # Convert scenario to failure configuration
        failure_cfg = self.anomaly_to_failure_config(scenario, severity)
        
        # Run simulation
        state = self.run_simulation(
            failure_config=failure_cfg,
            duration_seconds=duration_seconds,
            baseline_co2_mmHg=baseline_co2_mmHg
        )
        
        # Create and return telemetry data object
        return CDRATelemetryData(state, scenario, severity)

    def get_co2_time_series_mmhg(self) -> List[float]:
        """
        Get CO2 time series in mmHg units.
        
        Returns:
            List of CO2 concentrations in mmHg
        """
        if self.state is None:
            return []
        
        return [self.kg_per_kg_air_to_mmhg(co2) for co2 in self.state.history['co2_content']]


class CDRATelemetryData:
    """
    CDRA telemetry data class that handles processed simulation data.
    
    This class provides convenient access to telemetry data and analysis methods
    for CDRA simulation results.
    """
    
    def __init__(self, state: 'CDRAState', scenario: str, severity: float):
        """
        Initialize telemetry data from simulation state.
        
        Args:
            state: CDRA simulation state
            scenario: Anomaly scenario name
            severity: Severity level used in simulation
        """
        self.state = state
        self.scenario = scenario
        self.severity = severity
        self._co2_series_mmhg = None
        self._time_series = None
        
    def get_co2_time_series_mmhg(self) -> List[float]:
        """
        Get CO2 time series in mmHg units.
        
        Returns:
            List of CO2 concentrations in mmHg
        """
        if self._co2_series_mmhg is None:
            self._co2_series_mmhg = [
                self._kg_per_kg_air_to_mmhg(co2) for co2 in self.state.history['co2_content']
            ]
        return self._co2_series_mmhg
    
    def get_time_series(self) -> List[float]:
        """
        Get time series in seconds.
        
        Returns:
            List of time values in seconds
        """
        if self._time_series is None:
            self._time_series = self.state.history['time'].copy()
        return self._time_series
    
    def get_air_flow_rate_series(self) -> List[float]:
        """
        Get air flow rate time series.
        
        Returns:
            List of air flow rates
        """
        return self.state.history['air_flow_rate'].copy()
    
    def get_co2_output_series_mmhg(self) -> List[float]:
        """
        Get CO2 output concentration time series in mmHg units.
        
        Returns:
            List of CO2 output concentrations in mmHg
        """
        if self.state is None:
            return []
        
        return [self._kg_per_kg_air_to_mmhg(co2) for co2 in self.state.history['co2_output']]
    
    def get_saturation_series(self, component: str) -> List[float]:
        """
        Get saturation time series for a specific component.
        
        Args:
            component: Component name ('desiccant_1', 'desiccant_3', 'sorbent_2', 'sorbent_4')
            
        Returns:
            List of saturation values
        """
        return self.state.history['saturation'][component].copy()
    
    def get_adsorption_efficiency_series(self, component: str) -> List[float]:
        """
        Get adsorption efficiency time series for a specific component.
        
        Args:
            component: Component name ('desiccant_1', 'desiccant_3', 'sorbent_2', 'sorbent_4')
            
        Returns:
            List of adsorption efficiency values
        """
        return self.state.history['adsorption_eff'][component].copy()
    
    def get_heater_states(self, component: str) -> List[int]:
        """
        Get heater state time series for a specific component.
        
        Args:
            component: Component name ('desiccant_1', 'desiccant_3', 'sorbent_2', 'sorbent_4')
            
        Returns:
            List of heater states (0=off, 1=on)
        """
        return self.state.history[f'{component}_heater'].copy()
    
    def get_active_path_series(self) -> List[bool]:
        """
        Get active path time series.
        
        Returns:
            List of active path states (True=path_1, False=path_2)
        """
        return self.state.history['active_path'].copy()
    
    def find_detection_index(self, trigger: float) -> int:
        """
        Find the first index where CO2 exceeds the trigger threshold.
        
        Args:
            trigger: CO2 threshold in mmHg
            
        Returns:
            Index of first detection, or -1 if not found
        """
        co2_series = self.get_co2_time_series_mmhg()
        for i, co2 in enumerate(co2_series):
            if co2 > trigger:
                return i
        return -1
    
    def get_peak_co2(self) -> float:
        """
        Get the peak CO2 concentration during the simulation.
        
        Returns:
            Peak CO2 concentration in mmHg
        """
        co2_series = self.get_co2_time_series_mmhg()
        return max(co2_series) if co2_series else 0.0
    
    def get_final_co2(self) -> float:
        """
        Get the final CO2 concentration.
        
        Returns:
            Final CO2 concentration in mmHg
        """
        co2_series = self.get_co2_time_series_mmhg()
        return co2_series[-1] if co2_series else 0.0
    
    def get_average_co2(self) -> float:
        """
        Get the average CO2 concentration during the simulation.
        
        Returns:
            Average CO2 concentration in mmHg
        """
        co2_series = self.get_co2_time_series_mmhg()
        return sum(co2_series) / len(co2_series) if co2_series else 0.0
    
    def resample_to_length(self, target_length: int) -> 'CDRATelemetryData':
        """
        Create a resampled version of this telemetry data.
        
        Args:
            target_length: Target length for resampling
            
        Returns:
            New CDRATelemetryData with resampled data
        """
        # Create a new state with resampled data
        new_state = CDRAState(self.state.co2_content)
        
        # Resample all time series
        co2_series = self.get_co2_time_series_mmhg()
        resampled_co2 = self._resample_series(co2_series, target_length)
        
        # Convert back to kg/kg air for internal representation
        resampled_co2_kg_per_kg = [
            self._mmhg_to_kg_per_kg_air(co2) for co2 in resampled_co2
        ]
        
        # Update the new state's history
        new_state.history['co2_content'] = resampled_co2_kg_per_kg
        new_state.history['time'] = list(range(len(resampled_co2)))
        
        # Resample other series if needed
        for component in ['desiccant_1', 'desiccant_3', 'sorbent_2', 'sorbent_4']:
            new_state.history['saturation'][component] = self._resample_series(
                self.get_saturation_series(component), target_length
            )
            new_state.history['adsorption_eff'][component] = self._resample_series(
                self.get_adsorption_efficiency_series(component), target_length
            )
        
        new_state.history['air_flow_rate'] = self._resample_series(
            self.get_air_flow_rate_series(), target_length
        )
        
        return CDRATelemetryData(new_state, self.scenario, self.severity)
    
    def _resample_series(self, values: List[float], target_len: int) -> List[float]:
        """Helper method for resampling time series."""
        if target_len <= 0:
            return []
        if len(values) == target_len:
            return list(values)
        if len(values) == 0:
            return [0.0] * target_len
        
        if target_len > len(values):
            if len(values) == 1:
                return [values[0]] * target_len
            else:
                result = []
                for i in range(target_len):
                    pos = i * (len(values) - 1) / (target_len - 1)
                    lo = int(math.floor(pos))
                    hi = min(lo + 1, len(values) - 1)
                    frac = pos - lo
                    v = values[lo] * (1 - frac) + values[hi] * frac
                    result.append(v)
                return result
        
        result = []
        for i in range(target_len):
            pos = i * (len(values) - 1) / (target_len - 1)
            lo = int(math.floor(pos))
            hi = min(lo + 1, len(values) - 1)
            frac = pos - lo
            v = values[lo] * (1 - frac) + values[hi] * frac
            result.append(v)
        return result

    ### telemetry data methods ###
    def get_summary(self) -> Dict:
        """
        Get a summary of the telemetry data.
        
        Returns:
            Dictionary with telemetry summary statistics
        """
        co2_series = self.get_co2_time_series_mmhg()
        time_series = self.get_time_series()
        
        return {
            'scenario': self.scenario,
            'severity': self.severity,
            'duration_seconds': time_series[-1] if time_series else 0,
            'total_timesteps': len(co2_series),
            'initial_co2_mmhg': co2_series[0] if co2_series else 0.0,
            'final_co2_mmhg': co2_series[-1] if co2_series else 0.0,
            'peak_co2_mmhg': max(co2_series) if co2_series else 0.0,
            'min_co2_mmhg': min(co2_series) if co2_series else 0.0,
            'avg_co2_mmhg': sum(co2_series) / len(co2_series) if co2_series else 0.0,
        }
    
    def _kg_per_kg_air_to_mmhg(self, co2_kg_per_kg_air: float) -> float:
        """Helper method for unit conversion."""
        co2_mol_per_mol_air = co2_kg_per_kg_air * (28.97 / 44.01)
        co2_pa = co2_mol_per_mol_air * (760.0 * 133.322)
        return co2_pa / 133.322
    
    def _mmhg_to_kg_per_kg_air(self, co2_mmhg: float) -> float:
        """Helper method for unit conversion."""
        co2_pa = co2_mmhg * 133.322
        co2_mol_per_mol_air = co2_pa / (760.0 * 133.322)
        return co2_mol_per_mol_air * (44.01 / 28.97)
    

    ### plotting functions ###
    def plot_co2_concentration(self, figsize: Tuple[int, int] = (12, 8), 
                              title: str = None, show_detection: bool = True,
                              detection_threshold: float = 4.0) -> None:
        """
        Plot CO2 concentration over time.
        
        Args:
            figsize: Figure size (width, height)
            title: Plot title (defaults to scenario name)
            show_detection: Whether to show detection threshold line
            detection_threshold: CO2 threshold for detection line
        """
        co2_series = self.get_co2_time_series_mmhg()
        time_series = self.get_time_series()
        
        plt.figure(figsize=figsize)
        plt.plot(time_series, co2_series, linewidth=2, color=get_color_by_index(0), label='CO2 Concentration')
        
        if show_detection:
            plt.axhline(y=detection_threshold, color=get_color('detection_threshold'), linestyle='--', 
                       linewidth=2, label=f'Detection Threshold ({detection_threshold} mmHg)')
            
            # Find and mark detection point
            detection_idx = self.find_detection_index(detection_threshold)
            if detection_idx >= 0:
                plt.axvline(x=time_series[detection_idx], color=get_color('detection_line'), linestyle=':', 
                           alpha=0.7, label=f'Detection at t={time_series[detection_idx]:.0f}s')
        
        plt.xlabel('Time [s]', fontsize=12)
        plt.ylabel('CO2 Concentration [mmHg]', fontsize=12)
        plt.title(title or f'CO2 Concentration - {self.scenario} (Severity: {self.severity})', fontsize=14)
        plt.grid(True, alpha=0.7)
        plt.legend()
        plt.tight_layout()
        #plt.show()
    
    def plot_component_states(self, figsize: Tuple[int, int] = (15, 10)) -> None:
        """
        Plot component saturation and efficiency states.
        
        Args:
            figsize: Figure size (width, height)
        """
        time_series = self.get_time_series()
        components = ['desiccant_1', 'desiccant_3', 'sorbent_2', 'sorbent_4']
        
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        axes = axes.flatten()
        
        for i, component in enumerate(components):
            ax = axes[i]
            
            # Plot saturation
            saturation = self.get_saturation_series(component)
            ax.plot(time_series, saturation, linewidth=2, color=get_color_by_index(0), label='Saturation')
            
            # Plot efficiency on secondary y-axis
            ax2 = ax.twinx()
            efficiency = self.get_adsorption_efficiency_series(component)
            ax2.plot(time_series, efficiency, linewidth=2, color=get_color_by_index(1), label='Efficiency')
            
            # Plot heater state
            heater_states = self.get_heater_states(component)
            ax.fill_between(time_series, 0, 1, where=heater_states, 
                           alpha=0.3, color=get_color_by_index(2), label='Heater ON')
            
            ax.set_xlabel('Time [s]')
            ax.set_ylabel('Saturation', color=get_color_by_index(0))
            ax2.set_ylabel('Efficiency', color=get_color_by_index(1))
            ax.set_title(f'{component.replace("_", " ").title()}')
            ax.grid(True, alpha=0.7)
            
            # Combine legends
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        plt.suptitle(f'Component States - {self.scenario}', fontsize=16)
        plt.tight_layout()
        #plt.show()
    
    def plot_system_overview(self, figsize: Tuple[int, int] = (16, 12)) -> None:
        """
        Plot comprehensive system overview with multiple subplots.
        
        Args:
            figsize: Figure size (width, height)
        """
        time_series = self.get_time_series()
        co2_series = self.get_co2_time_series_mmhg()
        air_flow = self.get_air_flow_rate_series()
        active_path = self.get_active_path_series()
        
        fig, axes = plt.subplots(4, 1, figsize=figsize)
        
        # CO2 Concentration
        axes[0].plot(time_series, co2_series, linewidth=2, color=get_color_by_index(0))
        axes[0].set_ylabel('CO2 [mmHg]')
        axes[0].set_title('CO2 Concentration')
        axes[0].grid(True, alpha=0.7)
        
        # Air Flow Rate
        axes[1].plot(time_series, air_flow, linewidth=2, color=get_color_by_index(1))
        axes[1].set_ylabel('Flow Rate [kg/s]')
        axes[1].set_title('Air Flow Rate')
        axes[1].grid(True, alpha=0.7)
        
        # Heater States
        components = ['desiccant_1', 'desiccant_3', 'sorbent_2', 'sorbent_4']
        for i, component in enumerate(components):
            heater_states = self.get_heater_states(component)
            axes[2].plot(time_series, np.array(heater_states) + i*0.1, 
                        linewidth=2, color=get_color_by_index(i), label=component.replace('_', ' ').title())
        axes[2].set_ylabel('Heater States')
        axes[2].set_title('Heater Status')
        axes[2].legend()
        axes[2].grid(True, alpha=0.7)
        
        # Active Path
        axes[3].step(time_series, active_path, linewidth=2, color=get_color_by_index(4), where='post')
        axes[3].set_ylabel('Active Path')
        axes[3].set_xlabel('Time [s]')
        axes[3].set_title('Valve Path Selection')
        axes[3].set_yticks([0, 1])
        axes[3].set_yticklabels(['Path 2', 'Path 1'])
        axes[3].grid(True, alpha=0.7)
        
        plt.suptitle(f'CDRA System Overview - {self.scenario} (Severity: {self.severity})', fontsize=16)
        plt.tight_layout()
        #plt.show()
    
    def plot_comparison(self, other_telemetry: 'CDRATelemetryData', 
                       figsize: Tuple[int, int] = (12, 8)) -> None:
        """
        Plot comparison between two telemetry datasets.
        
        Args:
            other_telemetry: Another CDRATelemetryData object to compare with
            figsize: Figure size (width, height)
        """
        time_series = self.get_time_series()
        co2_series_1 = self.get_co2_time_series_mmhg()
        co2_series_2 = other_telemetry.get_co2_time_series_mmhg()
        
        plt.figure(figsize=figsize)
        plt.plot(time_series, co2_series_1, linewidth=2, color=get_color_by_index(0), 
                label=f'{self.scenario} (Severity: {self.severity})')
        plt.plot(time_series, co2_series_2, linewidth=2, color=get_color_by_index(1), 
                label=f'{other_telemetry.scenario} (Severity: {other_telemetry.severity})')
        
        plt.xlabel('Time [s]', fontsize=12)
        plt.ylabel('CO2 Concentration [mmHg]', fontsize=12)
        plt.title('CDRA Telemetry Comparison', fontsize=14)
        plt.grid(True, alpha=0.7)
        plt.legend()
        plt.tight_layout()
        #plt.show()
    
    def plot_multiple_scenarios(self, telemetry_list: List['CDRATelemetryData'], 
                               figsize: Tuple[int, int] = (14, 8)) -> None:
        """
        Plot multiple telemetry scenarios on the same plot.
        
        Args:
            telemetry_list: List of CDRATelemetryData objects
            figsize: Figure size (width, height)
        """
        time_series = self.get_time_series()
        
        plt.figure(figsize=figsize)
        
        for i, telemetry in enumerate(telemetry_list):
            co2_series = telemetry.get_co2_time_series_mmhg()
            plt.plot(time_series, co2_series, linewidth=2, color=get_color_by_index(i),
                    label=f'{telemetry.scenario} (Severity: {telemetry.severity})')
        
        plt.xlabel('Time [s]', fontsize=12)
        plt.ylabel('CO2 Concentration [mmHg]', fontsize=12)
        plt.title('Multiple CDRA Scenarios Comparison', fontsize=14)
        plt.grid(True, alpha=0.7)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        #plt.show()
    
    def plot_analysis_summary(self, figsize: Tuple[int, int] = (12, 8)) -> None:
        """
        Plot analysis summary with key metrics.
        
        Args:
            figsize: Figure size (width, height)
        """
        co2_series = self.get_co2_time_series_mmhg()
        time_series = self.get_time_series()
        
        # Calculate metrics
        peak_co2 = self.get_peak_co2()
        final_co2 = self.get_final_co2()
        avg_co2 = self.get_average_co2()
        detection_idx = self.find_detection_index(4.0)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # CO2 time series with annotations
        ax1.plot(time_series, co2_series, linewidth=2, color=get_color_by_index(0))
        ax1.axhline(y=4.0, color=get_color('detection_threshold'), linestyle='--', alpha=0.7, label='Detection Threshold')
        
        if detection_idx >= 0:
            ax1.axvline(x=time_series[detection_idx], color=get_color('detection_line'), linestyle=':', alpha=0.7)
            ax1.annotate(f'Detection at t={time_series[detection_idx]:.0f}s', 
                        xy=(time_series[detection_idx], co2_series[detection_idx]),
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor=get_color('detection_annotation'), alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        ax1.set_xlabel('Time [s]')
        ax1.set_ylabel('CO2 Concentration [mmHg]')
        ax1.set_title(f'CO2 Time Series - {self.scenario}')
        ax1.grid(True, alpha=0.7)
        ax1.legend()
        
        # Metrics bar chart
        metrics = ['Peak CO2', 'Final CO2', 'Average CO2']
        values = [peak_co2, final_co2, avg_co2]
        colors = [get_color_by_index(i) for i in range(len(metrics))]
        
        bars = ax2.bar(metrics, values, color=colors, alpha=0.7)
        ax2.set_ylabel('CO2 Concentration [mmHg]')
        ax2.set_title('Key Metrics')
        ax2.grid(True, alpha=0.7, axis='y')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{value:.2f}', ha='center', va='bottom')
        
        plt.suptitle(f'Analysis Summary - {self.scenario} (Severity: {self.severity})', fontsize=14)
        plt.tight_layout()
        #plt.show()


### State and Telemetry Data Classe###
class CDRAState:
    """
    CDRA simulation state class.
    
    This class holds the current state of the CDRA simulation including
    component saturations, efficiencies, and historical data.
    """
    
    def __init__(self, baseline_co2: float):
        """
        Initialize CDRA state.
        
        Args:
            baseline_co2: Initial CO2 concentration in kg/kg air
        """
        self.saturation = {k: 0.0 for k in ['desiccant_1', 'desiccant_3', 'sorbent_2', 'sorbent_4']}
        self.adsorption_eff = {k: 0.05 for k in ['desiccant_1', 'desiccant_3', 'sorbent_2', 'sorbent_4']}
        self.time = 0
        self.air_flow_rate = 1.0
        self.co2_content = baseline_co2
        self.heater_on = {'desiccant_1': False, 'desiccant_3': False, 'sorbent_2': False, 'sorbent_4': False}
        self.valve_state = {'path_1_active': True}

        # For plotting and analysis
        self.history = {
            'saturation': {k: [] for k in ['desiccant_1', 'desiccant_3', 'sorbent_2', 'sorbent_4']},
            'adsorption_eff': {k: [] for k in ['desiccant_1', 'desiccant_3', 'sorbent_2', 'sorbent_4']},
            'time': [],
            'moisture_content': [],
            'co2_content': [],
            'co2_output': [],  # CO2 concentration out of CDRA
            'co2_removed': [],
            'air_flow_rate': [],
            'desiccant_heaters': [],
            'sorbent_heaters': [],
            'active_path': [],
            'desiccant_1_heater': [],
            'desiccant_3_heater': [],
            'sorbent_2_heater': [],
            'sorbent_4_heater': []
        }
