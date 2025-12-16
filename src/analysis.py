"""
Analysis Module: Statistical tests for A/B experiments

This module implements the core statistical machinery:
1. Power analysis (sample size calculation)
2. Two-proportion z-test (for conversion rates)
3. Two-sample t-test (for continuous metrics)
4. Confidence intervals
"""

import numpy as np
from scipy import stats
from dataclasses import dataclass
from typing import Tuple, Optional


# ============================================================================
# POWER ANALYSIS: How many users do we need?
# ============================================================================

def calculate_sample_size(
    baseline_rate: float,
    minimum_detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.8,
    two_sided: bool = True
) -> int:
    """
    Calculate required sample size per variant for a conversion rate experiment.
    
    The formula comes from inverting the z-test for two proportions.
    
    Args:
        baseline_rate: Current conversion rate (e.g., 0.10 for 10%)
        minimum_detectable_effect: Relative change to detect (e.g., 0.10 for 10% lift)
        alpha: Significance level (false positive rate)
        power: Statistical power (1 - false negative rate)
        two_sided: Whether to use a two-sided test
    
    Returns:
        Required sample size per variant
    
    Example:
        If baseline is 10% and you want to detect a 10% relative lift (to 11%):
        >>> calculate_sample_size(0.10, 0.10)
        14752  # ~15k users per variant
    """
    # Treatment rate if the effect is real
    treatment_rate = baseline_rate * (1 + minimum_detectable_effect)
    
    # Z-scores for alpha and beta
    if two_sided:
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    
    # Pooled proportion (assuming equal sample sizes)
    p_pooled = (baseline_rate + treatment_rate) / 2
    
    # Sample size formula
    numerator = (z_alpha * np.sqrt(2 * p_pooled * (1 - p_pooled)) + 
                 z_beta * np.sqrt(baseline_rate * (1 - baseline_rate) + 
                                  treatment_rate * (1 - treatment_rate))) ** 2
    denominator = (treatment_rate - baseline_rate) ** 2
    
    n = numerator / denominator
    
    return int(np.ceil(n))


def calculate_experiment_duration(
    sample_size_per_variant: int,
    daily_traffic: int,
    num_variants: int = 2,
    traffic_fraction: float = 1.0
) -> int:
    """
    Calculate how many days to run the experiment.

    Args:
        sample_size_per_variant: Required users per variant
        daily_traffic: Average daily users
        num_variants: Number of experiment variants
        traffic_fraction: Fraction of traffic in experiment (0-1)

    Returns:
        Number of days required
    """
    total_users_needed = sample_size_per_variant * num_variants
    daily_experiment_traffic = daily_traffic * traffic_fraction
    days = total_users_needed / daily_experiment_traffic
    return int(np.ceil(days))


def calculate_mde(
    sample_size_per_variant: int,
    baseline_rate: float,
    alpha: float = 0.05,
    power: float = 0.8
) -> float:
    """
    Calculate the Minimum Detectable Effect (MDE) given a sample size.

    This is the inverse of calculate_sample_size - given a fixed sample size,
    what's the smallest effect we can reliably detect?

    Uses binary search since there's no closed-form solution.

    Args:
        sample_size_per_variant: Number of users per variant
        baseline_rate: Current conversion rate (e.g., 0.10 for 10%)
        alpha: Significance level
        power: Statistical power

    Returns:
        MDE as a relative effect (e.g., 0.10 = 10% lift)

    Example:
        With 5000 users per variant and 10% baseline:
        >>> calculate_mde(5000, 0.10)
        0.178  # Can detect ~18% relative lift
    """
    # Binary search for MDE
    low, high = 0.001, 2.0  # Search between 0.1% and 200% lift

    while high - low > 0.001:
        mid = (low + high) / 2
        required_n = calculate_sample_size(baseline_rate, mid, alpha, power)

        if required_n > sample_size_per_variant:
            # Need more users than we have, so MDE must be larger
            low = mid
        else:
            # We have enough users, MDE could be smaller
            high = mid

    return round(high, 3)


# ============================================================================
# STATISTICAL TESTS
# ============================================================================

@dataclass
class TestResult:
    """Result of a statistical test."""
    test_name: str
    control_mean: float
    treatment_mean: float
    absolute_effect: float
    relative_effect: float  # As a decimal (0.05 = 5% lift)
    confidence_interval: Tuple[float, float]  # For relative effect
    p_value: float
    is_significant: bool
    alpha: float
    
    def __repr__(self):
        sig = "✓ Significant" if self.is_significant else "✗ Not significant"
        return (
            f"\n{'='*60}\n"
            f"Test: {self.test_name}\n"
            f"{'='*60}\n"
            f"Control:   {self.control_mean:.4f}\n"
            f"Treatment: {self.treatment_mean:.4f}\n"
            f"\n"
            f"Absolute effect: {self.absolute_effect:+.4f}\n"
            f"Relative effect: {self.relative_effect:+.2%}\n"
            f"95% CI:          [{self.confidence_interval[0]:+.2%}, {self.confidence_interval[1]:+.2%}]\n"
            f"\n"
            f"p-value: {self.p_value:.4f}\n"
            f"Result:  {sig} (α={self.alpha})\n"
            f"{'='*60}"
        )


def two_proportion_z_test(
    control_conversions: int,
    control_total: int,
    treatment_conversions: int,
    treatment_total: int,
    alpha: float = 0.05
) -> TestResult:
    """
    Two-proportion z-test for comparing conversion rates.
    
    H₀: p_treatment = p_control (no difference)
    H₁: p_treatment ≠ p_control (two-sided)
    
    Args:
        control_conversions: Number of conversions in control
        control_total: Total users in control
        treatment_conversions: Number of conversions in treatment
        treatment_total: Total users in treatment
        alpha: Significance level
    
    Returns:
        TestResult with statistics and interpretation
    """
    # Sample proportions
    p_control = control_conversions / control_total
    p_treatment = treatment_conversions / treatment_total
    
    # Pooled proportion (under null hypothesis)
    p_pooled = (control_conversions + treatment_conversions) / (control_total + treatment_total)
    
    # Standard error under null
    se_null = np.sqrt(p_pooled * (1 - p_pooled) * (1/control_total + 1/treatment_total))
    
    # Z-statistic
    z_stat = (p_treatment - p_control) / se_null if se_null > 0 else 0
    
    # Two-sided p-value
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    # Confidence interval for the difference (using unpooled SE)
    se_diff = np.sqrt(
        p_control * (1 - p_control) / control_total +
        p_treatment * (1 - p_treatment) / treatment_total
    )
    z_crit = stats.norm.ppf(1 - alpha / 2)
    diff = p_treatment - p_control
    ci_lower = diff - z_crit * se_diff
    ci_upper = diff + z_crit * se_diff
    
    # Convert absolute CI to relative CI
    if p_control > 0:
        relative_effect = diff / p_control
        rel_ci_lower = ci_lower / p_control
        rel_ci_upper = ci_upper / p_control
    else:
        relative_effect = 0
        rel_ci_lower = rel_ci_upper = 0
    
    return TestResult(
        test_name="Two-Proportion Z-Test",
        control_mean=p_control,
        treatment_mean=p_treatment,
        absolute_effect=diff,
        relative_effect=relative_effect,
        confidence_interval=(rel_ci_lower, rel_ci_upper),
        p_value=p_value,
        is_significant=p_value < alpha,
        alpha=alpha
    )


def two_sample_t_test(
    control_values: np.ndarray,
    treatment_values: np.ndarray,
    alpha: float = 0.05
) -> TestResult:
    """
    Welch's t-test for comparing means of continuous metrics.
    
    Uses Welch's t-test (unequal variances) which is more robust
    than the standard t-test.
    
    Args:
        control_values: Array of values for control group
        treatment_values: Array of values for treatment group
        alpha: Significance level
    
    Returns:
        TestResult with statistics and interpretation
    """
    # Basic statistics
    n_c, n_t = len(control_values), len(treatment_values)
    mean_c, mean_t = control_values.mean(), treatment_values.mean()
    var_c, var_t = control_values.var(ddof=1), treatment_values.var(ddof=1)
    
    # Welch's t-test
    t_stat, p_value = stats.ttest_ind(treatment_values, control_values, equal_var=False)
    
    # Standard error of the difference
    se_diff = np.sqrt(var_c / n_c + var_t / n_t)
    
    # Degrees of freedom (Welch-Satterthwaite)
    df = ((var_c / n_c + var_t / n_t) ** 2 /
          ((var_c / n_c) ** 2 / (n_c - 1) + (var_t / n_t) ** 2 / (n_t - 1)))
    
    # Confidence interval
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    diff = mean_t - mean_c
    ci_lower = diff - t_crit * se_diff
    ci_upper = diff + t_crit * se_diff
    
    # Relative effect
    if mean_c != 0:
        relative_effect = diff / abs(mean_c)
        rel_ci_lower = ci_lower / abs(mean_c)
        rel_ci_upper = ci_upper / abs(mean_c)
    else:
        relative_effect = 0
        rel_ci_lower = rel_ci_upper = 0
    
    return TestResult(
        test_name="Welch's T-Test",
        control_mean=mean_c,
        treatment_mean=mean_t,
        absolute_effect=diff,
        relative_effect=relative_effect,
        confidence_interval=(rel_ci_lower, rel_ci_upper),
        p_value=p_value,
        is_significant=p_value < alpha,
        alpha=alpha
    )


# ============================================================================
# MULTIPLE COMPARISONS
# ============================================================================

def bonferroni_correction(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    When testing multiple metrics, the probability of at least one false positive
    increases. Bonferroni adjusts by dividing alpha by the number of tests.
    
    This is conservative - it reduces false positives but also reduces power.
    
    Args:
        p_values: List of p-values from multiple tests
        alpha: Family-wise error rate to control
    
    Returns:
        List of booleans indicating significance after correction
    """
    adjusted_alpha = alpha / len(p_values)
    return [p < adjusted_alpha for p in p_values]


def benjamini_hochberg_correction(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """
    Apply Benjamini-Hochberg procedure for controlling False Discovery Rate.
    
    Less conservative than Bonferroni. Controls the expected proportion of
    false positives among rejected hypotheses.
    
    Args:
        p_values: List of p-values from multiple tests
        alpha: FDR level to control
    
    Returns:
        List of booleans indicating significance after correction
    """
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_pvals = np.array(p_values)[sorted_indices]
    
    # BH critical values
    critical_values = [(i + 1) / n * alpha for i in range(n)]
    
    # Find largest k where p[k] <= critical_value[k]
    significant = np.zeros(n, dtype=bool)
    for i in range(n - 1, -1, -1):
        if sorted_pvals[i] <= critical_values[i]:
            # All tests up to this one are significant
            significant[sorted_indices[:i+1]] = True
            break
    
    return list(significant)


# --- Demonstration ---

if __name__ == "__main__":
    print("=== Power Analysis ===\n")
    
    baseline = 0.10  # 10% conversion rate
    mde = 0.10       # Want to detect 10% relative lift (to 11%)
    
    sample_size = calculate_sample_size(baseline, mde)
    print(f"Baseline conversion rate: {baseline:.0%}")
    print(f"Minimum detectable effect: {mde:.0%} relative lift")
    print(f"Required sample size per variant: {sample_size:,}")
    
    # Calculate duration
    daily_traffic = 10000
    days = calculate_experiment_duration(sample_size, daily_traffic)
    print(f"\nWith {daily_traffic:,} daily users: ~{days} days to run")
    
    print("\n" + "="*60)
    print("=== Two-Proportion Z-Test Demo ===")
    
    # Simulated results: treatment has 12% vs control 10%
    result = two_proportion_z_test(
        control_conversions=500,
        control_total=5000,
        treatment_conversions=600,
        treatment_total=5000
    )
    print(result)
    
    print("\n" + "="*60)
    print("=== Multiple Comparisons Demo ===\n")
    
    # Testing 5 metrics
    p_values = [0.02, 0.04, 0.15, 0.01, 0.08]
    
    print("Original p-values:", [f"{p:.2f}" for p in p_values])
    print(f"Significant at α=0.05: {sum(p < 0.05 for p in p_values)} tests")
    
    bonf = bonferroni_correction(p_values)
    bh = benjamini_hochberg_correction(p_values)
    
    print(f"\nAfter Bonferroni (α=0.01 per test): {sum(bonf)} significant")
    print(f"After Benjamini-Hochberg (FDR=0.05): {sum(bh)} significant")
