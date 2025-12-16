"""
Simulation Module: End-to-end A/B experiment simulation

Demonstrates the full experiment lifecycle:
1. Hypothesis  - Define what we're testing
2. Design      - Power analysis and sample size
3. Assignment  - Randomize users to variants
4. Exposure    - Simulate user behavior
5. Measurement - Compute metrics
6. Analysis    - Statistical significance tests
7. Decision    - Ship, iterate, or kill
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from assignment import Experiment, Variant, assign_variant, get_assignment_bucket
from metrics import compute_metric_by_variant
from analysis import (
    two_proportion_z_test,
    two_sample_t_test,
    calculate_sample_size,
    calculate_mde,
    calculate_experiment_duration,
    bonferroni_correction,
    TestResult,
)


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class Hypothesis:
    """Defines what we're testing."""
    name: str
    description: str
    baseline_rate: float
    expected_lift: float
    primary_metric: str = "conversion_rate"
    secondary_metrics: list[str] = field(default_factory=lambda: ["revenue_per_user"])


@dataclass
class ExperimentDesign:
    """Pre-experiment planning results."""
    hypothesis: Hypothesis
    planned_users: int
    users_per_variant: int
    required_sample_size: int
    actual_mde: float
    is_adequately_powered: bool
    power_shortage: int
    estimated_days: int


@dataclass
class ExperimentData:
    """Raw experiment data."""
    users: pd.DataFrame
    events: pd.DataFrame
    config: "ExperimentConfig"


@dataclass
class ExperimentResults:
    """Complete experiment results."""
    design: ExperimentDesign
    data: ExperimentData
    conversion_test: TestResult
    revenue_test: TestResult
    recommendation: str


@dataclass
class ExperimentConfig:
    """Configuration for experiment simulation."""
    num_users: int = 10000
    control_conversion_rate: float = 0.10
    treatment_lift: float = 0.15
    control_avg_order_value: float = 45.0
    treatment_aov_lift: float = 0.0
    daily_traffic: int = 1000
    seed: Optional[int] = 42


# =============================================================================
# Lifecycle Phases
# =============================================================================

def design_experiment(hypothesis: Hypothesis, config: ExperimentConfig) -> ExperimentDesign:
    """Phase 2: Calculate sample size and power analysis."""
    users_per_variant = config.num_users // 2

    # Handle null hypothesis testing (0% expected lift)
    if hypothesis.expected_lift == 0:
        return ExperimentDesign(
            hypothesis=hypothesis,
            planned_users=config.num_users,
            users_per_variant=users_per_variant,
            required_sample_size=0,
            actual_mde=calculate_mde(users_per_variant, hypothesis.baseline_rate),
            is_adequately_powered=True,  # N/A for null tests
            power_shortage=0,
            estimated_days=0,
        )

    required_sample_size = calculate_sample_size(
        baseline_rate=hypothesis.baseline_rate,
        minimum_detectable_effect=hypothesis.expected_lift,
    )

    actual_mde = calculate_mde(
        sample_size_per_variant=users_per_variant,
        baseline_rate=hypothesis.baseline_rate,
    )

    is_powered = users_per_variant >= required_sample_size
    shortage = max(0, required_sample_size - users_per_variant)

    estimated_days = calculate_experiment_duration(
        sample_size_per_variant=required_sample_size,
        daily_traffic=config.daily_traffic,
    )

    return ExperimentDesign(
        hypothesis=hypothesis,
        planned_users=config.num_users,
        users_per_variant=users_per_variant,
        required_sample_size=required_sample_size,
        actual_mde=actual_mde,
        is_adequately_powered=is_powered,
        power_shortage=shortage,
        estimated_days=estimated_days,
    )


def assign_users(config: ExperimentConfig) -> pd.DataFrame:
    """Phase 3: Assign users to variants deterministically."""
    experiment = Experiment(
        id="exp_checkout_2024_q1",
        name="Single-Page Checkout Test",
        variants=[Variant("control", 50), Variant("treatment", 50)],
    )

    assignments = [
        {
            "user_id": f"user_{i:06d}",
            "variant": assign_variant(f"user_{i:06d}", experiment).name,
        }
        for i in range(config.num_users)
    ]

    return pd.DataFrame(assignments)


def simulate_exposure(users: pd.DataFrame, config: ExperimentConfig) -> pd.DataFrame:
    """Phase 4: Simulate user behavior based on variant assignment."""
    treatment_rate = config.control_conversion_rate * (1 + config.treatment_lift)
    treatment_aov = config.control_avg_order_value * (1 + config.treatment_aov_lift)

    events = []
    for _, user in users.iterrows():
        is_treatment = user["variant"] == "treatment"
        conv_rate = treatment_rate if is_treatment else config.control_conversion_rate
        avg_aov = treatment_aov if is_treatment else config.control_avg_order_value

        if np.random.random() < conv_rate:
            order_value = np.random.lognormal(np.log(avg_aov) - 0.125, 0.5)
            events.append({
                "user_id": user["user_id"],
                "event_type": "purchase",
                "order_value": round(order_value, 2),
                "converted": 1,
            })

    return pd.DataFrame(events) if events else pd.DataFrame(
        columns=["user_id", "event_type", "order_value", "converted"]
    )


def measure_metrics(users: pd.DataFrame, events: pd.DataFrame) -> dict:
    """Phase 5: Compute metrics by variant."""
    conversion_values = events.groupby("user_id")["converted"].max()
    revenue_values = events.groupby("user_id")["order_value"].sum()

    return {
        "conversion": compute_metric_by_variant(users, conversion_values),
        "revenue": compute_metric_by_variant(users, revenue_values),
    }


def analyze_results(
    users: pd.DataFrame,
    events: pd.DataFrame,
    metrics: dict,
) -> tuple[TestResult, TestResult]:
    """Phase 6: Run statistical tests."""
    control_users = users[users["variant"] == "control"]
    treatment_users = users[users["variant"] == "treatment"]

    # Conversion test
    control_conv = events[events["user_id"].isin(control_users["user_id"])]["user_id"].nunique()
    treatment_conv = events[events["user_id"].isin(treatment_users["user_id"])]["user_id"].nunique()

    conversion_test = two_proportion_z_test(
        control_conversions=control_conv,
        control_total=len(control_users),
        treatment_conversions=treatment_conv,
        treatment_total=len(treatment_users),
    )

    # Revenue test
    control_revenue = (
        control_users.merge(
            events.groupby("user_id")["order_value"].sum().reset_index(),
            on="user_id",
            how="left",
        )["order_value"].fillna(0).values
    )
    treatment_revenue = (
        treatment_users.merge(
            events.groupby("user_id")["order_value"].sum().reset_index(),
            on="user_id",
            how="left",
        )["order_value"].fillna(0).values
    )

    revenue_test = two_sample_t_test(control_revenue, treatment_revenue)

    return conversion_test, revenue_test


def make_decision(conversion_test: TestResult) -> str:
    """Phase 7: Generate recommendation based on results."""
    if conversion_test.is_significant and conversion_test.relative_effect > 0:
        return f"SHIP: Treatment shows +{conversion_test.relative_effect:.1%} lift (p={conversion_test.p_value:.4f})"
    elif conversion_test.is_significant and conversion_test.relative_effect < 0:
        return f"KILL: Treatment is worse by {conversion_test.relative_effect:.1%} (p={conversion_test.p_value:.4f})"
    else:
        return f"ITERATE: No significant difference detected (p={conversion_test.p_value:.4f})"


# =============================================================================
# Report Formatting
# =============================================================================

class ExperimentReporter:
    """Formats and prints experiment results."""

    WIDTH = 70

    def __init__(self, results: ExperimentResults):
        self.results = results

    def print_full_report(self):
        """Print complete experiment report."""
        self._header("A/B EXPERIMENT REPORT")
        self._hypothesis()
        self._design()
        self._assignment()
        self._metrics()
        self._analysis()
        self._decision()

    def _header(self, title: str):
        print("\n" + "=" * self.WIDTH)
        print(title.center(self.WIDTH))
        print("=" * self.WIDTH)

    def _section(self, title: str):
        print(f"\n{title}")
        print("-" * self.WIDTH)

    def _hypothesis(self):
        h = self.results.design.hypothesis
        self._section("1. HYPOTHESIS")
        print(f"   {h.description}")
        print(f"   Baseline: {h.baseline_rate:.1%} → Target: {h.baseline_rate * (1 + h.expected_lift):.1%}")
        print(f"   Expected lift: {h.expected_lift:.1%}")

    def _design(self):
        d = self.results.design
        self._section("2. DESIGN (Power Analysis)")
        print(f"   Sample size:  {d.users_per_variant:,}/variant ({d.planned_users:,} total)")

        if d.hypothesis.expected_lift == 0:
            print(f"   Testing null hypothesis (no expected effect)")
            print(f"   Actual MDE:   {d.actual_mde:.1%} (smallest detectable effect)")
        else:
            print(f"   Required:     {d.required_sample_size:,}/variant for {d.hypothesis.expected_lift:.1%} MDE")
            print(f"   Actual MDE:   {d.actual_mde:.1%} (smallest detectable effect)")

            if d.is_adequately_powered:
                print(f"   Status:       ✓ Adequately powered")
            else:
                print(f"   Status:       ⚠ Underpowered (need {d.power_shortage:,} more/variant)")

    def _assignment(self):
        users = self.results.data.users
        counts = users["variant"].value_counts()
        self._section("3. ASSIGNMENT")
        for variant, count in sorted(counts.items()):
            pct = count / len(users)
            print(f"   {variant}: {count:,} users ({pct:.1%})")

    def _metrics(self):
        events = self.results.data.events
        users = self.results.data.users
        self._section("5. MEASUREMENT")

        total_conv = len(events)
        conv_rate = total_conv / len(users)
        print(f"   Total conversions: {total_conv:,} ({conv_rate:.2%})")
        print()

        # Conversion by variant
        print("   Conversion Rate:")
        for variant in ["control", "treatment"]:
            variant_users = users[users["variant"] == variant]["user_id"]
            variant_conv = events[events["user_id"].isin(variant_users)]["user_id"].nunique()
            rate = variant_conv / len(variant_users)
            print(f"     {variant}: {rate:.2%} (n={len(variant_users):,})")

        # Revenue by variant
        print()
        print("   Revenue per User:")
        for variant in ["control", "treatment"]:
            variant_users = users[users["variant"] == variant]
            variant_revenue = events[events["user_id"].isin(variant_users["user_id"])]["order_value"].sum()
            rpu = variant_revenue / len(variant_users)
            print(f"     {variant}: ${rpu:.2f}")

    def _analysis(self):
        self._section("6. ANALYSIS")

        # Conversion test
        ct = self.results.conversion_test
        print(f"   Conversion Rate (z-test):")
        print(f"     Effect: {ct.relative_effect:+.1%}  CI: [{ct.confidence_interval[0]:+.1%}, {ct.confidence_interval[1]:+.1%}]")
        print(f"     p-value: {ct.p_value:.4f}  {'✓ Significant' if ct.is_significant else '✗ Not significant'}")

        # Revenue test
        rt = self.results.revenue_test
        print()
        print(f"   Revenue per User (t-test):")
        print(f"     Effect: {rt.relative_effect:+.1%}  CI: [{rt.confidence_interval[0]:+.1%}, {rt.confidence_interval[1]:+.1%}]")
        print(f"     p-value: {rt.p_value:.4f}  {'✓ Significant' if rt.is_significant else '✗ Not significant'}")

        # Multiple comparisons
        p_values = [ct.p_value, rt.p_value]
        bonf = bonferroni_correction(p_values)
        print()
        print(f"   After Bonferroni correction (α=0.025):")
        print(f"     Conversion: {'✓' if bonf[0] else '✗'}  Revenue: {'✓' if bonf[1] else '✗'}")

    def _decision(self):
        self._section("7. DECISION")
        print(f"   {self.results.recommendation}")
        print()


# =============================================================================
# Main Entry Point
# =============================================================================

def run_experiment(config: Optional[ExperimentConfig] = None) -> ExperimentResults:
    """
    Run a complete A/B experiment simulation.

    Args:
        config: Experiment configuration. Uses defaults if not provided.

    Returns:
        ExperimentResults with all data and analysis.
    """
    config = config or ExperimentConfig()

    if config.seed is not None:
        np.random.seed(config.seed)

    # Phase 1: Define hypothesis
    hypothesis = Hypothesis(
        name="single_page_checkout",
        description="Single-page checkout will increase conversion rate",
        baseline_rate=config.control_conversion_rate,
        expected_lift=config.treatment_lift,
    )

    # Phase 2: Design
    design = design_experiment(hypothesis, config)

    # Phase 3: Assignment
    users = assign_users(config)

    # Phase 4: Exposure (simulate behavior)
    events = simulate_exposure(users, config)

    # Phase 5: Measurement
    metrics = measure_metrics(users, events)

    # Phase 6: Analysis
    conversion_test, revenue_test = analyze_results(users, events, metrics)

    # Phase 7: Decision
    recommendation = make_decision(conversion_test)

    return ExperimentResults(
        design=design,
        data=ExperimentData(users=users, events=events, config=config),
        conversion_test=conversion_test,
        revenue_test=revenue_test,
        recommendation=recommendation,
    )


# =============================================================================
# Preset Scenarios
# =============================================================================

def scenario_clear_winner() -> ExperimentResults:
    """Large effect with adequate sample size."""
    return run_experiment(ExperimentConfig(num_users=20000, treatment_lift=0.20))


def scenario_no_effect() -> ExperimentResults:
    """Null result - no real difference."""
    return run_experiment(ExperimentConfig(num_users=10000, treatment_lift=0.0))


def scenario_underpowered() -> ExperimentResults:
    """Real effect but insufficient sample size."""
    return run_experiment(ExperimentConfig(num_users=500, treatment_lift=0.15))


if __name__ == "__main__":
    results = run_experiment()
    # results = scenario_no_effect()
    # results = scenario_underpowered()
    # results = scenario_clear_winner()

    ExperimentReporter(results).print_full_report()
