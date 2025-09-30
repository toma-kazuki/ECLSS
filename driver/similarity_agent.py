import numpy as np
import time
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy.stats import pearsonr, spearmanr
from dtaidistance import dtw
from dtaidistance import dtw_visualisation as dtwvis
try:
    from statsmodels.tsa.arima.model import ARIMA
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False
    print("Warning: statsmodels not available. ARIMA method will not work.")
from typing import Dict, List, Tuple, Union, Optional
import matplotlib.pyplot as plt
from color_scheme import get_color, get_line_style


class SimilarityAgent:
    """
    An agent that computes similarity scores between actual telemetry data and simulation data
    using various statistical methods including MSE, Pearson correlation, and DTW.
    """
    
    def __init__(self, method: str = "MSE"):
        """
        Initialize the SimilarityAgent.
        
        Args:
            method (str): The similarity method to use. Options: "MSE", "Pearson", "DTW"
        """
        self.method = method.upper()
        self.available_methods = ["MSE", "MAE", "PEARSON", "SPEARMAN", "DTW", "ARIMA", "FFT"]
        
        if self.method not in self.available_methods:
            raise ValueError(f"Method {method} not supported. Available methods: {self.available_methods}")
    
    def compute_multiple_similarities(
        self, 
        telemetry_data: np.ndarray, 
        simulation_data_dict: Dict[str, np.ndarray],
        segment_length: Optional[int] = None,
        find_best_alignment: bool = True
    ) -> Dict[str, Dict]:
        """
        Compute similarity scores between telemetry data and multiple simulation scenarios.
        """
        results = {}
        for scenario_name, simulation_data in simulation_data_dict.items():
            results[scenario_name] = self.compute_similarity(
                telemetry_data, 
                simulation_data, 
                segment_length, 
                find_best_alignment
            )
        return results
        
    def compute_similarity(
        self, 
        telemetry_data: np.ndarray, 
        simulation_data: np.ndarray,
        segment_length: Optional[int] = None,
        find_best_alignment: bool = True
    ) -> Dict:
        """
        Compute similarity score between telemetry and simulation data.
        
        Args:
            telemetry_data (np.ndarray): Actual telemetry data
            simulation_data (np.ndarray): Simulation data to compare against
            segment_length (int, optional): Length of segments to compare. If None, uses full length
            find_best_alignment (bool): Whether to find the best time alignment between datasets
            
        Returns:
            Dict: Dictionary containing similarity score, runtime, and alignment info
        """
        if segment_length is None:
            segment_length = min(len(telemetry_data), len(simulation_data))
        
        start_time = time.time()
        
        if self.method == "MSE":
            result = self._compute_mse(telemetry_data, simulation_data, segment_length, find_best_alignment)
        elif self.method == "MAE":
            result = self._compute_mae(telemetry_data, simulation_data, segment_length, find_best_alignment)
        elif self.method == "PEARSON":
            result = self._compute_pearson(telemetry_data, simulation_data, segment_length, find_best_alignment)
        elif self.method == "SPEARMAN":
            result = self._compute_spearman(telemetry_data, simulation_data, segment_length, find_best_alignment)
        elif self.method == "DTW":
            result = self._compute_dtw(telemetry_data, simulation_data, segment_length, find_best_alignment)
        elif self.method == "ARIMA":
            result = self._compute_arima(telemetry_data, simulation_data, segment_length, find_best_alignment)
        elif self.method == "FFT":
            result = self._compute_fft(telemetry_data, simulation_data, segment_length, find_best_alignment)
        
        elapsed_time = round(time.time() - start_time, 4)
        result['runtime'] = elapsed_time
        result['method'] = self.method
        
        return result
    
    def _compute_mse(
        self, 
        telemetry_data: np.ndarray, 
        simulation_data: np.ndarray, 
        segment_length: int,
        find_best_alignment: bool
    ) -> Dict:
        """Compute Mean Squared Error between datasets."""
        if find_best_alignment:
            best_score = float("inf")
            best_shift = 0
            
            for shift in range(len(telemetry_data) - segment_length + 1):
                telemetry_segment = telemetry_data[shift:shift + segment_length]
                simulation_segment = simulation_data[:segment_length]
                score = mean_squared_error(telemetry_segment, simulation_segment)
                
                if score < best_score:
                    best_score = score
                    best_shift = shift
            
            return {
                'score': best_score,
                'shift': best_shift,
                'aligned_telemetry': telemetry_data[best_shift:best_shift + segment_length],
                'aligned_simulation': simulation_data[:segment_length]
            }
        else:
            # Use the first segment_length elements from both datasets
            telemetry_segment = telemetry_data[:segment_length]
            simulation_segment = simulation_data[:segment_length]
            score = mean_squared_error(telemetry_segment, simulation_segment)
            
            return {
                'score': score,
                'shift': 0,
                'aligned_telemetry': telemetry_segment,
                'aligned_simulation': simulation_segment
            }
    
    def _compute_pearson(
        self, 
        telemetry_data: np.ndarray, 
        simulation_data: np.ndarray, 
        segment_length: int,
        find_best_alignment: bool
    ) -> Dict:
        """Compute Pearson correlation between datasets."""
        if find_best_alignment:
            best_score = -1
            best_shift = 0
            
            for shift in range(len(telemetry_data) - segment_length + 1):
                telemetry_segment = telemetry_data[shift:shift + segment_length]
                simulation_segment = simulation_data[:segment_length]
                score, _ = pearsonr(telemetry_segment, simulation_segment)
                
                if score > best_score:
                    best_score = score
                    best_shift = shift
            
            return {
                'score': best_score,
                'shift': best_shift,
                'aligned_telemetry': telemetry_data[best_shift:best_shift + segment_length],
                'aligned_simulation': simulation_data[:segment_length]
            }
        else:
            # Use the first segment_length elements from both datasets
            telemetry_segment = telemetry_data[:segment_length]
            simulation_segment = simulation_data[:segment_length]
            score, _ = pearsonr(telemetry_segment, simulation_segment)
            
            return {
                'score': score,
                'shift': 0,
                'aligned_telemetry': telemetry_segment,
                'aligned_simulation': simulation_segment
            }
    
    def _compute_dtw(
        self, 
        telemetry_data: np.ndarray, 
        simulation_data: np.ndarray, 
        segment_length: int,
        find_best_alignment: bool
    ) -> Dict:
        """Compute Dynamic Time Warping distance between datasets."""
        if find_best_alignment:
            best_score = float("inf")
            best_shift = 0
            
            for shift in range(len(telemetry_data) - segment_length + 1):
                telemetry_segment = telemetry_data[shift:shift + segment_length]
                simulation_segment = simulation_data[:segment_length]
                score = dtw.distance(telemetry_segment, simulation_segment)
                
                if score < best_score:
                    best_score = score
                    best_shift = shift
            
            return {
                'score': best_score,
                'shift': best_shift,
                'aligned_telemetry': telemetry_data[best_shift:best_shift + segment_length],
                'aligned_simulation': simulation_data[:segment_length]
            }
        else:
            # Use the first segment_length elements from both datasets
            telemetry_segment = telemetry_data[:segment_length]
            simulation_segment = simulation_data[:segment_length]
            score = dtw.distance(telemetry_segment, simulation_segment)
            
            return {
                'score': score,
                'shift': 0,
                'aligned_telemetry': telemetry_segment,
                'aligned_simulation': simulation_segment
            }
    
    def _compute_mae(
        self, 
        telemetry_data: np.ndarray, 
        simulation_data: np.ndarray, 
        segment_length: int,
        find_best_alignment: bool
    ) -> Dict:
        """Compute Mean Absolute Error between datasets."""
        if find_best_alignment:
            best_score = float("inf")
            best_shift = 0
            
            for shift in range(len(telemetry_data) - segment_length + 1):
                telemetry_segment = telemetry_data[shift:shift + segment_length]
                simulation_segment = simulation_data[:segment_length]
                score = mean_absolute_error(telemetry_segment, simulation_segment)
                
                if score < best_score:
                    best_score = score
                    best_shift = shift
            
            return {
                'score': best_score,
                'shift': best_shift,
                'aligned_telemetry': telemetry_data[best_shift:best_shift + segment_length],
                'aligned_simulation': simulation_data[:segment_length]
            }
        else:
            # Use the first segment_length elements from both datasets
            telemetry_segment = telemetry_data[:segment_length]
            simulation_segment = simulation_data[:segment_length]
            score = mean_absolute_error(telemetry_segment, simulation_segment)
            
            return {
                'score': score,
                'shift': 0,
                'aligned_telemetry': telemetry_segment,
                'aligned_simulation': simulation_segment
            }
    
    def _compute_spearman(
        self, 
        telemetry_data: np.ndarray, 
        simulation_data: np.ndarray, 
        segment_length: int,
        find_best_alignment: bool
    ) -> Dict:
        """Compute Spearman rank correlation between datasets."""
        if find_best_alignment:
            best_score = -1
            best_shift = 0
            
            for shift in range(len(telemetry_data) - segment_length + 1):
                telemetry_segment = telemetry_data[shift:shift + segment_length]
                simulation_segment = simulation_data[:segment_length]
                score, _ = spearmanr(telemetry_segment, simulation_segment)
                
                if score > best_score:
                    best_score = score
                    best_shift = shift
            
            return {
                'score': best_score,
                'shift': best_shift,
                'aligned_telemetry': telemetry_data[best_shift:best_shift + segment_length],
                'aligned_simulation': simulation_data[:segment_length]
            }
        else:
            # Use the first segment_length elements from both datasets
            telemetry_segment = telemetry_data[:segment_length]
            simulation_segment = simulation_data[:segment_length]
            score, _ = spearmanr(telemetry_segment, simulation_segment)
            
            return {
                'score': score,
                'shift': 0,
                'aligned_telemetry': telemetry_segment,
                'aligned_simulation': simulation_segment
            }
    
    def _compute_arima(
        self, 
        telemetry_data: np.ndarray, 
        simulation_data: np.ndarray, 
        segment_length: int,
        find_best_alignment: bool
    ) -> Dict:
        """Compute ARIMA-based similarity by fitting model on simulation and forecasting telemetry."""
        if not ARIMA_AVAILABLE:
            return {
                'score': float("inf"),
                'shift': 0,
                'aligned_telemetry': telemetry_data[:segment_length],
                'aligned_simulation': simulation_data[:segment_length],
                'error': 'statsmodels not available'
            }
        
        try:
            if find_best_alignment:
                best_score = float("inf")
                best_shift = 0
                
                for shift in range(len(telemetry_data) - segment_length + 1):
                    telemetry_segment = telemetry_data[shift:shift + segment_length]
                    simulation_segment = simulation_data[:segment_length]
                    
                    # Fit ARIMA model on simulation data
                    model = ARIMA(simulation_segment, order=(2, 1, 0)).fit()
                    forecast = model.predict(start=1, end=len(telemetry_segment) - 1)
                    observed_trimmed = telemetry_segment[1:]
                    score = mean_squared_error(observed_trimmed, forecast)
                    
                    if score < best_score:
                        best_score = score
                        best_shift = shift
                
                return {
                    'score': best_score,
                    'shift': best_shift,
                    'aligned_telemetry': telemetry_data[best_shift:best_shift + segment_length],
                    'aligned_simulation': simulation_data[:segment_length]
                }
            else:
                # Use the first segment_length elements from both datasets
                telemetry_segment = telemetry_data[:segment_length]
                simulation_segment = simulation_data[:segment_length]
                
                # Fit ARIMA model on simulation data
                model = ARIMA(simulation_segment, order=(2, 1, 0)).fit()
                forecast = model.predict(start=1, end=len(telemetry_segment) - 1)
                observed_trimmed = telemetry_segment[1:]
                score = mean_squared_error(observed_trimmed, forecast)
                
                return {
                    'score': score,
                    'shift': 0,
                    'aligned_telemetry': telemetry_segment,
                    'aligned_simulation': simulation_segment
                }
        except Exception as e:
            # Return high error score if ARIMA fails
            return {
                'score': float("inf"),
                'shift': 0,
                'aligned_telemetry': telemetry_data[:segment_length],
                'aligned_simulation': simulation_data[:segment_length],
                'error': str(e)
            }
    
    def _compute_fft(
        self, 
        telemetry_data: np.ndarray, 
        simulation_data: np.ndarray, 
        segment_length: int,
        find_best_alignment: bool
    ) -> Dict:
        """Compute FFT-based similarity using cross-power spectrum."""
        if find_best_alignment:
            best_score = float("inf")
            best_shift = 0
            
            for shift in range(len(telemetry_data) - segment_length + 1):
                telemetry_segment = telemetry_data[shift:shift + segment_length]
                simulation_segment = simulation_data[:segment_length]
                
                # Compute FFT
                fft_telemetry = np.fft.fft(telemetry_segment)
                fft_simulation = np.fft.fft(simulation_segment)
                
                # Cross power spectrum
                cross_spectrum = fft_telemetry * np.conj(fft_simulation)
                
                # Use negative correlation of cross-spectrum magnitude as similarity
                # (higher correlation = lower score)
                score = -np.corrcoef(np.abs(fft_telemetry), np.abs(fft_simulation))[0, 1]
                
                if score < best_score:
                    best_score = score
                    best_shift = shift
            
            return {
                'score': best_score,
                'shift': best_shift,
                'aligned_telemetry': telemetry_data[best_shift:best_shift + segment_length],
                'aligned_simulation': simulation_data[:segment_length]
            }
        else:
            # Use the first segment_length elements from both datasets
            telemetry_segment = telemetry_data[:segment_length]
            simulation_segment = simulation_data[:segment_length]
            
            # Compute FFT
            fft_telemetry = np.fft.fft(telemetry_segment)
            fft_simulation = np.fft.fft(simulation_segment)
            
            # Cross power spectrum
            cross_spectrum = fft_telemetry * np.conj(fft_simulation)
            
            # Use negative correlation of cross-spectrum magnitude as similarity
            score = -np.corrcoef(np.abs(fft_telemetry), np.abs(fft_simulation))[0, 1]
            
            return {
                'score': score,
                'shift': 0,
                'aligned_telemetry': telemetry_segment,
                'aligned_simulation': simulation_segment
            }
    
    def compare_multiple_simulations(
        self, 
        telemetry_data: np.ndarray, 
        simulation_data_dict: Dict[str, np.ndarray],
        segment_length: Optional[int] = None,
        find_best_alignment: bool = True
    ) -> Dict[str, Dict]:
        """
        Compare telemetry data against multiple simulation scenarios.
        
        Args:
            telemetry_data (np.ndarray): Actual telemetry data
            simulation_data_dict (Dict[str, np.ndarray]): Dictionary of simulation data with scenario names as keys
            segment_length (int, optional): Length of segments to compare
            find_best_alignment (bool): Whether to find the best time alignment
            
        Returns:
            Dict[str, Dict]: Dictionary of results for each simulation scenario
        """
        results = {}
        
        for scenario_name, simulation_data in simulation_data_dict.items():
            print(f"Computing {self.method} similarity for scenario: {scenario_name}")
            result = self.compute_similarity(
                telemetry_data, 
                simulation_data, 
                segment_length, 
                find_best_alignment
            )
            results[scenario_name] = result
        
        return results
    
    def plot_comparison(
        self, 
        telemetry_data: np.ndarray, 
        simulation_data: np.ndarray,
        result: Dict,
        title: str = "Similarity Comparison"
    ) -> None:
        """
        Plot the comparison between telemetry and simulation data.
        
        Args:
            telemetry_data (np.ndarray): Original telemetry data
            simulation_data (np.ndarray): Original simulation data
            result (Dict): Result from compute_similarity method
            title (str): Plot title
        """
        plt.figure(figsize=(12, 8))
        
        # Plot original data
        time_series = np.arange(len(telemetry_data))
        plt.plot(time_series, telemetry_data, label="Telemetry Data", linewidth=2, color=get_color('telemetry_data'))
        
        # Plot aligned simulation data
        aligned_time = np.arange(result['shift'], result['shift'] + len(result['aligned_simulation']))
        plt.plot(aligned_time, result['aligned_simulation'], 
                label=f"Simulation (shift={result['shift']})", 
                linestyle=get_line_style('dashed'), linewidth=2, color=get_color('simulation_data'))
        
        # Highlight the comparison segment
        segment_start = result['shift']
        segment_end = result['shift'] + len(result['aligned_simulation'])
        plt.axvspan(segment_start, segment_end, alpha=0.2, color=get_color('comparison_segment'), 
                   label=f"Comparison Segment (Score: {result['score']:.4f})")
        
        plt.title(f"{title} - {self.method} Method\nRuntime: {result['runtime']}s", fontsize=16)
        plt.xlabel("Time [s]", fontsize=14)
        plt.ylabel("Parameter Value", fontsize=14)
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.7)
        plt.tight_layout()
        plt.show()
    
    def get_ranking(self, results: Dict[str, Dict]) -> List[Tuple[str, float]]:
        """
        Get ranked list of simulation scenarios based on similarity scores.
        
        Args:
            results (Dict[str, Dict]): Results from compare_multiple_simulations
            
        Returns:
            List[Tuple[str, float]]: List of (scenario_name, score) tuples, ranked by similarity
        """
        if self.method in ["MSE", "MAE", "DTW", "ARIMA", "FFT"]:
            # Lower scores are better for MSE, MAE, DTW, ARIMA, and FFT
            ranking = sorted(results.items(), key=lambda x: x[1]['score'])
        else:  # Pearson and Spearman correlation
            # Higher scores are better for correlation methods
            ranking = sorted(results.items(), key=lambda x: x[1]['score'], reverse=True)
        
        return [(name, result['score']) for name, result in ranking]


# Example usage and testing
if __name__ == "__main__":
    # Generate sample data for testing
    np.random.seed(42)
    time_length = 1000
    
    # Generate "telemetry" data (baseline + anomaly)
    baseline = np.ones(200)
    anomaly = np.exp(np.linspace(0, 2, 800))  # Exponential growth
    telemetry_data = np.concatenate([baseline, anomaly]) + np.random.normal(0, 0.1, time_length)
    
    # Generate different simulation hypotheses
    simulations = {
        "H1_Exponential_Slow": np.exp(np.linspace(0, 1.5, time_length)),
        "H2_Exponential_Fast": np.exp(np.linspace(0, 2.5, time_length)),
        "H3_Linear": np.linspace(1, 8, time_length),
        "H4_Logarithmic": np.log(np.e + np.linspace(0, 10, time_length))
    }
    
    # Test different similarity methods
    methods = ["MSE", "Pearson", "DTW"]
    
    for method in methods:
        print(f"\n{'='*50}")
        print(f"Testing {method} method")
        print(f"{'='*50}")
        
        agent = SimilarityAgent(method=method)
        results = agent.compare_multiple_simulations(
            telemetry_data, 
            simulations, 
            segment_length=800,
            find_best_alignment=True
        )
        
        # Print results
        for scenario, result in results.items():
            print(f"{scenario}: Score = {result['score']:.4f}, Shift = {result['shift']}, Runtime = {result['runtime']}s")
        
        # Get ranking
        ranking = agent.get_ranking(results)
        print(f"\nRanking (best to worst):")
        for i, (scenario, score) in enumerate(ranking, 1):
            print(f"{i}. {scenario}: {score:.4f}")
        
        # Plot best match
        best_scenario = ranking[0][0]
        best_result = results[best_scenario]
        agent.plot_comparison(telemetry_data, simulations[best_scenario], best_result, 
                            f"Best Match - {best_scenario}")
