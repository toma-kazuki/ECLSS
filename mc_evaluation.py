# -*- coding: utf-8 -*-
"""
Monte Carlo robustness evaluation for spacecraft CO2 fault diagnosis
- 7 fault scenarios (simultaneous onset)
- Uncertainties: sensor noise (sigma)
- Diagnosis by template matching (RMSE, Pearson, DTW). Reports Accuracy Hit@1 and Hit@2.
- Sensitivity plots (Hit@1 / Hit@2 vs Noise) and confusion matrices per noise level.

Author: (You)
"""
import numpy as np
import matplotlib.pyplot as plt
import itertools
import os
from collections import defaultdict
from similarity_agent import SimilarityAgent
from cdra_simulator import CDRASimulator

# =========================
# Global configuration
# =========================
SEED = 42
np.random.seed(SEED)

SCENARIOS = [
    "Valve",
    "Fan",
    "Filter",
    "Valve+Fan",
    "Valve+Filter",
    "Fan+Filter",
    "Valve+Fan+Filter",
]

SCEN_IDX = {name: i for i, name in enumerate(SCENARIOS)}

# Time settings
T_SEC = 10000

# Diagnosis methods
DIAGNOSIS_METHODS = ["MSE"]
TRIGGER = 0.60    # diagnostic starts when CO2 crosses this

# Monte Carlo design
NOISE_SIGMAS = [0.0, 3*3, 7*7, 15*15]
N_TRIALS = 200
# =========================
# Templates & Diagnosis
# =========================
def build_nominal_templates():
    templates = {}
    for scenario in SCENARIOS:
        simulator = CDRASimulator()
        telemetry_data = simulator.generate_telemetry_data(
            scenario=scenario,
            severity=0.5,
            duration_seconds=T_SEC,
            baseline_co2_mmHg=3.0
        )
        # telemetry_data.plot_co2_concentration()
        templates[scenario] = telemetry_data.get_co2_time_series_mmhg()
    return templates

def find_detection_index(template, trigger):
    print(template)
    return np.argmax(template > trigger)

def apply_uncertainty(series, noise):
    return series + np.random.normal(0, noise, len(series))

def diagnose_by_templates(series, templates, method):
    """
    1) Detect trigger on measured_series (target parameter crosses threshold)
    2) Compute similarity between measured_series and each template (MSE, Pearson, DTW)
    3) Rank scenarios by ascending similarity score
    """

    similarity_agent = SimilarityAgent(method)
    report = similarity_agent.compare_multiple_simulations(
        series,
        templates,
        segment_length=len(series),
        find_best_alignment=True
    )
    ranked = similarity_agent.get_ranking(report)
    # scores = similarity_agent.get_scores(report)
    return ranked, 
# =========================
# Experiment Runner
# =========================

def evaluate_hit_at_k(ranked_list, true_scenario, k):
    topk = [name for name, _ in ranked_list[:k]]
    return True if true_scenario in topk else False

def run_trials(noise, templates, n_trials, method):
    """
    For a given noise level, run trials across all 7 scenarios.
    Returns:
      - confusion: 7x7 count matrix (rows=true, cols=pred Top-1)
      - hit1_per_scenario: array [7] of Hit@1 rate
      - hit2_per_scenario: array [7] of Hit@2 rate
    """
    confusion = np.zeros((len(SCENARIOS), len(SCENARIOS)), dtype=int)
    hit1_counts = np.zeros(len(SCENARIOS), dtype=int)
    hit2_counts = np.zeros(len(SCENARIOS), dtype=int)

    for s_idx,scenario in enumerate(SCENARIOS):
        for _ in range(n_trials):
            # Simulate "true" measured series with uncertainty
            true_series = apply_uncertainty(templates[scenario], noise)

            # Diagnose
            ranked, = diagnose_by_templates(true_series, templates, method)

            pred_hit1 = ranked[0][0]
            pred_idx = SCEN_IDX[pred_hit1]

            confusion[s_idx, pred_idx] += 1
            if evaluate_hit_at_k(ranked, scenario, k=1):
                hit1_counts[s_idx] += 1
            if evaluate_hit_at_k(ranked, scenario, k=2):
                hit2_counts[s_idx] += 1

    hit1_by_scenario = hit1_counts / float(n_trials)
    hit2_by_scenario = hit2_counts / float(n_trials)
    print(hit1_by_scenario)
    print(hit2_by_scenario)
    # breakpoint()
    return confusion, hit1_by_scenario, hit2_by_scenario

# =========================
# Plotting
# =========================
def plot_sensitivity(noise_levels, hit1_per_noise, hit2_per_noise):
    """
    Overall (macro-averaged across scenarios) sensitivity curves.
    """
    plt.figure(figsize=(7, 5))
    plt.plot(noise_levels, hit1_per_noise, marker='o', label='Hit@1')
    plt.plot(noise_levels, hit2_per_noise, marker='s', label='Hit@2')
    plt.xlabel("Sensor noise σ")
    plt.ylabel("Performance")
    plt.title("Sensitivity to Sensor Noise")
    plt.ylim(0.0, 1.05)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    # plt.show()
    print(f"Plot completed for: Sensitivity to Sensor Noise")

def plot_sensitivity_per_scenario(noise_levels, hit1_by_scenario, hit2_by_scenario):
    """
    Per-scenario curves.
    hit1_by_scenario: shape [n_noise, 7]
    hit2_by_scenario: shape [n_noise, 7]
    """
    # Accuracy per scenario
    plt.figure(figsize=(8, 6))
    for j, scenario in enumerate(SCENARIOS):
        plt.plot(noise_levels, hit1_by_scenario[:, j], marker='o', label=scenario)
    plt.xlabel("Sensor noise σ")
    plt.ylabel("Hit@1")
    plt.title("Hit@1 vs Noise by Scenario")
    plt.ylim(0.0, 1.05)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(loc='best', fontsize=9)
    # plt.show()
    print(f"Plot completed for: Hit@1 vs Noise by Scenario")

    # Hit@2 per scenario
    plt.figure(figsize=(8, 6))
    for j, scenario in enumerate(SCENARIOS):
        plt.plot(noise_levels, hit2_by_scenario[:, j], marker='s', label=scenario)
    plt.xlabel("Sensor noise σ")
    plt.ylabel("Hit@2")
    plt.title("Hit@2 vs Noise by Scenario")
    plt.ylim(0.0, 1.05)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(loc='best', fontsize=9)
    # plt.show()
    print(f"Plot completed for: Hit@2 vs Noise by Scenario")

def plot_confusion_matrix(conf_mat, class_names, title):
    """
    Matplotlib-only confusion heatmap with integer annotations.
    conf_mat: 2D array (rows=true, cols=pred)
    """
    cm = conf_mat.astype(float)
    vmax = cm.max() if cm.max() > 0 else 1.0

    plt.figure(figsize=(7.5, 6.0))
    im = plt.imshow(cm, interpolation='nearest', aspect='auto')
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45, ha='right')
    plt.yticks(tick_marks, class_names)

    # annotate counts
    thresh = vmax / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = int(conf_mat[i, j])
            color = 'white' if cm[i, j] > thresh else 'black'
            plt.text(j, i, str(val), ha='center', va='center', color=color, fontsize=9)

    plt.ylabel('True Scenario')
    plt.xlabel('Predicted Scenario')
    plt.tight_layout()
    # plt.show()
    print(f"Plot completed for: {title}")


def main():
    templates = build_nominal_templates()
    # print(templates)
    # breakpoint()
    # for scenario in SCENARIOS:
    #     t_detection = find_detection_index(templates[scenario], TRIGGER)
    #     print(f"Detection time for {scenario}: {t_detection} seconds")


    for method in DIAGNOSIS_METHODS:
        # For each noise, run trials and produce confusion matrices

        # Accumulaterss
        hit1_overall = []
        hit2_overall = []
        hit1_by_scenario_all = []
        hit2_by_scenario_all = []
        for noise in NOISE_SIGMAS:
            print(f"\n===Running trials with noise sigma = {noise:.3f}===")
            confusion, hit1_by_scenario, hit2_by_scenario = run_trials(noise, templates, N_TRIALS, method)
            print(confusion)
            # print(hit1_by_scenario)
            # print(hit2_by_scenario)

            # breakpoint()

            # Macro-average (average across scenarios)
            hit1_macro = float(np.mean(hit1_by_scenario))
            hit2_macro = float(np.mean(hit2_by_scenario))
            hit1_overall.append(hit1_macro)
            hit2_overall.append(hit2_macro)
            hit1_by_scenario_all.append(hit1_by_scenario)
            hit2_by_scenario_all.append(hit2_by_scenario)
            
            print(f"Hit@1: {hit1_macro:.3f}, Hit@2: {hit2_macro:.3f}")

            # Plot confusion matrix for this noise level
            title = f"Confusion Matrix (sigma = {noise:.3f})"
            plot_confusion_matrix(confusion, SCENARIOS, title)
        
        # Sensitivity plots
        hit1_by_scenario_all = np.vstack(hit1_by_scenario_all)
        hit2_by_scenario_all = np.vstack(hit2_by_scenario_all)
        # breakpoint()
        plot_sensitivity(NOISE_SIGMAS, hit1_overall, hit2_overall)
        plot_sensitivity_per_scenario(NOISE_SIGMAS, hit1_by_scenario_all, hit2_by_scenario_all)
    plt.show()
    print("\nDone.")

if __name__ == "__main__":
    main()