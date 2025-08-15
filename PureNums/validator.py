import math
from collections import Counter
import textwrap
import pandas as pd
import numpy as np

class Color:
    """A helper class for adding color to terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class BenchmarkValidator:
    """
    Validates a new set of numbers against a large, trusted benchmark dataset.
    """
    def __init__(self, benchmark_filepath, verbose=True):
        self.verbose = verbose
        self._log("\n" + "="*60, color=Color.HEADER)
        self._log("  INITIALIZING BENCHMARK VALIDATOR", color=Color.HEADER)
        self._log("="*60, color=Color.HEADER)
        self._log(f"Loading benchmark data from '{benchmark_filepath}' to create a statistical profile...")

        try:
            df = pd.read_csv(benchmark_filepath)
            if 'number' not in df.columns:
                raise ValueError("Benchmark file must contain a column named 'number'.")

            self.benchmark_data = df['number'].astype(float).astype(int).tolist()
            self.benchmark_size = len(self.benchmark_data)
            self.max_val = max(self.benchmark_data)

            self.benchmark_proportions = {num: count / self.benchmark_size for num, count in Counter(self.benchmark_data).items()}
            self.benchmark_median = np.median(self.benchmark_data)

            self._log(f"Successfully created benchmark profile from {self.benchmark_size} numbers.", color=Color.GREEN)
            self._log(f"  - Max value in benchmark: {self.max_val}")
            self._log(f"  - Benchmark median: {self.benchmark_median}")

        except FileNotFoundError:
            raise
        except Exception as e:
            print(f"An error occurred while loading the benchmark file: {e}")
            raise

    def _log(self, message, color=Color.ENDC):
        if self.verbose:
            print(textwrap.fill(f"{color}{message}{Color.ENDC}", width=80))

    def validate_new_set(self, new_data, set_number=None):
        header = f"  VALIDATING SET {set_number}  " if set_number else "  VALIDATING NEW DATASET  "
        self._log("\n" + f"--- {header} ---", color=Color.BLUE)
        self._log(f"Analyzing a new dataset of {len(new_data)} numbers...")

        freq_consistent = self._frequency_consistency_test(new_data)
        runs_consistent = self._runs_consistency_test(new_data)

        self._log("\n" + "-"*25 + " REPORT " + "-"*25, color=Color.BLUE)
        test_results = [res for res in [freq_consistent, runs_consistent] if res is not None]
        if not test_results:
            self._log("Conclusion: Could not run tests, dataset is likely too small.", color=Color.WARNING)
        elif all(test_results):
            self._log("Conclusion: The new dataset is statistically CONSISTENT with the benchmark.", color=Color.GREEN)
        else:
            self._log("Conclusion: The new dataset shows significant DEVIATION from the benchmark.", color=Color.FAIL)
        self._log("-" * 60, color=Color.BLUE)

    def _frequency_consistency_test(self, new_data):
        self._log("\n--- Test 1: Frequency Consistency ---", color=Color.CYAN)
        self._log("Insight: Checks if numbers appear with the same frequency as the benchmark.")

        new_counts = Counter(new_data)
        new_size = len(new_data)

        expected_counts = {num: prop * new_size for num, prop in self.benchmark_proportions.items()}
        chi_squared_stat = sum((new_counts.get(i, 0) - expected_counts.get(i, 0))**2 / expected_counts.get(i, 1) for i in range(1, self.max_val + 1))
        degrees_of_freedom = self.max_val - 1
        critical_value = degrees_of_freedom + math.sqrt(2 * degrees_of_freedom)

        self._log(f"  - Chi-Squared Statistic: {chi_squared_stat:.2f}")

        if chi_squared_stat < critical_value:
            self._log(f"  - Result: {Color.GREEN}PASS{Color.ENDC}. The distribution is consistent.", color=Color.GREEN)
            return True
        else:
            self._log(f"  - Result: {Color.FAIL}FAIL{Color.ENDC}. The distribution deviates from the benchmark.", color=Color.FAIL)
            return False

    def _runs_consistency_test(self, new_data):
        self._log("\n--- Test 2: Runs Consistency (Clustering) ---", color=Color.CYAN)
        self._log("Insight: Checks for suspicious streaks of high or low numbers.")

        if len(new_data) < 20:
            self._log(f"  - Result: {Color.WARNING}SKIP{Color.ENDC}. Dataset is too small for a meaningful Runs Test.", color=Color.WARNING)
            return None

        runs_sequence = ['+' if x > self.benchmark_median else '-' for x in new_data if x != self.benchmark_median]
        num_runs = 1 + sum(1 for i in range(1, len(runs_sequence)) if runs_sequence[i] != runs_sequence[i-1])
        n1 = runs_sequence.count('+')
        n2 = runs_sequence.count('-')

        if n1 == 0 or n2 == 0:
            self._log(f"  - Result: {Color.WARNING}SKIP{Color.ENDC}. All data is on one side of the benchmark median.", color=Color.WARNING)
            return None

        expected_runs = ((2 * n1 * n2) / (n1 + n2)) + 1
        variance = (2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / (((n1 + n2)**2) * (n1 + n2 - 1))
        z_score = (num_runs - expected_runs) / math.sqrt(variance)

        self._log(f"  - Number of Runs: {num_runs} (Expected: {expected_runs:.2f})")
        self._log(f"  - Z-score: {z_score:.2f}")

        if -1.96 <= z_score <= 1.96:
            self._log(f"  - Result: {Color.GREEN}PASS{Color.ENDC}. The sequence appears independent.", color=Color.GREEN)
            return True
        else:
            self._log(f"  - Result: {Color.FAIL}FAIL{Color.ENDC}. The sequence shows non-random clustering.", color=Color.FAIL)
            return False
