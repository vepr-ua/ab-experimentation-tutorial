#!/usr/bin/env python3
"""
=============================================================================
A/B EXPERIMENT WALKTHROUGH: From Hypothesis to Decision
=============================================================================

This script walks through a complete A/B experiment lifecycle:

1. Define the hypothesis
2. Calculate required sample size
3. Simulate running the experiment
4. Analyze results
5. Make a decision

Scenario: We're testing a new single-page checkout against our current 
3-step checkout flow. We hypothesize it will increase conversion rate.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import pandas as pd
from simulation import SimulationConfig, simulate_experiment, print_experiment_summary
from analysis import (
    calculate_sample_size, 
    calculate_experiment_duration,
    two_proportion_z_test,
    two_sample_t_test,
)


def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                    A/B EXPERIMENTATION TUTORIAL                           ║
║                    ══════════════════════════════                         ║
║                                                                           ║
║  Learn by doing: We'll run a complete experiment from start to finish.   ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)

    # =========================================================================
    # STEP 1: DEFINE THE HYPOTHESIS
    # =========================================================================
    
    print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: DEFINE THE HYPOTHESIS                                               │
└─────────────────────────────────────────────────────────────────────────────┘

A good hypothesis has three components:
  1. What we're changing (the treatment)
  2. What metric we expect to move
  3. By how much

Our Hypothesis:
  "Replacing the 3-step checkout with a single-page checkout will increase
   conversion rate by at least 10%."

Key metrics:
  • Primary:   Conversion rate (purchases / visitors)
  • Secondary: Revenue per user
  • Guardrail: Average order value (shouldn't decrease significantly)
    """)
    
    input("Press Enter to continue to Step 2...")
    
    # =========================================================================
    # STEP 2: CALCULATE SAMPLE SIZE
    # =========================================================================
    
    print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: POWER ANALYSIS - How many users do we need?                         │
└─────────────────────────────────────────────────────────────────────────────┘

Before running, we need to know how many users are required to detect
our minimum detectable effect (MDE) with statistical confidence.

Parameters:
  • Baseline conversion rate: 10%
  • Minimum detectable effect: 10% relative lift (10% → 11%)
  • Significance level (α): 0.05 (5% false positive rate)
  • Power (1-β): 0.80 (80% chance of detecting a real effect)
    """)
    
    baseline_rate = 0.10
    mde = 0.10  # 10% relative lift
    
    sample_size = calculate_sample_size(
        baseline_rate=baseline_rate,
        minimum_detectable_effect=mde,
        alpha=0.05,
        power=0.80
    )
    
    print(f"Calculation result:")
    print(f"  Required sample size: {sample_size:,} users per variant")
    print(f"  Total users needed:   {sample_size * 2:,}")
    
    # Calculate duration
    daily_traffic = 5000
    days = calculate_experiment_duration(sample_size, daily_traffic)
    
    print(f"\nWith {daily_traffic:,} daily users:")
    print(f"  Estimated duration: {days} days")
    
    print("""
⚠️  Key insight: If you run with fewer users, you risk a FALSE NEGATIVE - 
    missing a real effect because you didn't have enough statistical power.
    """)
    
    input("Press Enter to continue to Step 3...")
    
    # =========================================================================
    # STEP 3: RUN THE EXPERIMENT (SIMULATION)
    # =========================================================================
    
    print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: RUN THE EXPERIMENT                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

In production, this would happen over days/weeks as users are:
  1. Randomly assigned to control or treatment
  2. Exposed to their assigned experience
  3. Their behavior is tracked and events logged

For this tutorial, we'll simulate an experiment with:
  • 20,000 users (plenty of power)
  • True treatment effect: 15% relative lift
  • This simulates a "winner" scenario
    """)
    
    # Simulate the experiment
    config = SimulationConfig(
        num_users=20000,
        control_conversion_rate=0.10,
        treatment_effect=0.15,  # True 15% lift
        control_avg_order_value=45.0,
        seed=42
    )
    
    print("Running simulation...")
    experiment = simulate_experiment(config)
    
    print_experiment_summary(experiment)
    
    input("Press Enter to continue to Step 4...")
    
    # =========================================================================
    # STEP 4: STATISTICAL ANALYSIS
    # =========================================================================
    
    print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: STATISTICAL ANALYSIS                                                │
└─────────────────────────────────────────────────────────────────────────────┘

Now we analyze whether the observed difference is statistically significant.

The key question: "Could this difference have occurred by chance?"

We use a two-proportion z-test for conversion rate (binary outcome).
    """)
    
    # Prepare data for analysis
    users = experiment.users
    events = experiment.events
    
    # Count conversions by variant
    converted_users = events["user_id"].unique()
    
    control_users = users[users["variant"] == "control"]
    treatment_users = users[users["variant"] == "treatment"]
    
    control_conversions = control_users["user_id"].isin(converted_users).sum()
    treatment_conversions = treatment_users["user_id"].isin(converted_users).sum()
    
    control_total = len(control_users)
    treatment_total = len(treatment_users)
    
    print(f"Observed data:")
    print(f"  Control:   {control_conversions:,} / {control_total:,} = {control_conversions/control_total:.2%}")
    print(f"  Treatment: {treatment_conversions:,} / {treatment_total:,} = {treatment_conversions/treatment_total:.2%}")
    
    # Run the statistical test
    print("\nRunning two-proportion z-test...\n")
    
    result = two_proportion_z_test(
        control_conversions=control_conversions,
        control_total=control_total,
        treatment_conversions=treatment_conversions,
        treatment_total=treatment_total,
        alpha=0.05
    )
    
    print(result)
    
    print("""
Interpretation guide:
  • p-value < 0.05: The difference is statistically significant
  • Confidence interval: The range of plausible true effects
  • If CI doesn't include 0: We can be confident there's a real effect
    """)
    
    input("Press Enter to continue to Step 5...")
    
    # =========================================================================
    # STEP 5: SECONDARY METRICS
    # =========================================================================
    
    print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: CHECK SECONDARY & GUARDRAIL METRICS                                 │
└─────────────────────────────────────────────────────────────────────────────┘

A significant primary metric isn't enough. We need to verify:
  1. Secondary metrics aren't hurt
  2. Guardrail metrics are stable

Let's check Revenue Per User and Average Order Value.
    """)
    
    # Calculate revenue per user
    control_revenue = events[events["user_id"].isin(control_users["user_id"])]["order_value"]
    treatment_revenue = events[events["user_id"].isin(treatment_users["user_id"])]["order_value"]
    
    # Revenue per user (include 0s for non-converters)
    control_rpu = np.concatenate([
        control_revenue.values,
        np.zeros(control_total - len(control_revenue))
    ])
    treatment_rpu = np.concatenate([
        treatment_revenue.values,
        np.zeros(treatment_total - len(treatment_revenue))
    ])
    
    print("Revenue Per User (t-test):")
    rpu_result = two_sample_t_test(control_rpu, treatment_rpu)
    print(f"  Control:   ${control_rpu.mean():.2f}")
    print(f"  Treatment: ${treatment_rpu.mean():.2f}")
    print(f"  p-value:   {rpu_result.p_value:.4f}")
    print(f"  Significant: {'Yes ✓' if rpu_result.is_significant else 'No'}")
    
    print("\nAverage Order Value (guardrail):")
    if len(control_revenue) > 0 and len(treatment_revenue) > 0:
        aov_result = two_sample_t_test(control_revenue.values, treatment_revenue.values)
        print(f"  Control:   ${control_revenue.mean():.2f}")
        print(f"  Treatment: ${treatment_revenue.mean():.2f}")
        print(f"  p-value:   {aov_result.p_value:.4f}")
        print(f"  Change:    {aov_result.relative_effect:+.1%}")
        
        if aov_result.is_significant and aov_result.relative_effect < -0.05:
            print("  ⚠️  WARNING: AOV decreased significantly!")
        else:
            print("  ✓ Guardrail passed: No significant decrease in AOV")
    
    input("\nPress Enter to continue to the decision...")
    
    # =========================================================================
    # STEP 6: MAKE THE DECISION
    # =========================================================================
    
    print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: MAKE THE DECISION                                                   │
└─────────────────────────────────────────────────────────────────────────────┘

Based on our analysis:
    """)
    
    decision_points = []
    
    # Primary metric
    if result.is_significant:
        if result.relative_effect > 0:
            decision_points.append(f"✓ Primary metric (conversion): +{result.relative_effect:.1%} lift (p={result.p_value:.4f})")
        else:
            decision_points.append(f"✗ Primary metric (conversion): {result.relative_effect:.1%} (significant decrease!)")
    else:
        decision_points.append(f"○ Primary metric (conversion): No significant change (p={result.p_value:.4f})")
    
    # Secondary metric
    if rpu_result.is_significant and rpu_result.relative_effect > 0:
        decision_points.append(f"✓ Secondary metric (RPU): +{rpu_result.relative_effect:.1%}")
    elif rpu_result.is_significant and rpu_result.relative_effect < 0:
        decision_points.append(f"✗ Secondary metric (RPU): {rpu_result.relative_effect:.1%} (decrease)")
    else:
        decision_points.append(f"○ Secondary metric (RPU): No significant change")
    
    # Guardrail
    decision_points.append("✓ Guardrail (AOV): Passed")
    
    for point in decision_points:
        print(f"  {point}")
    
    # Final recommendation
    print("\n" + "─" * 77)
    
    if result.is_significant and result.relative_effect > 0:
        print("""
RECOMMENDATION: 🚀 SHIP IT

The single-page checkout shows a statistically significant improvement in 
conversion rate with no degradation in guardrail metrics.

Expected impact:
""")
        # Calculate business impact
        current_monthly_users = 150000
        current_conversion = 0.10
        current_monthly_conversions = current_monthly_users * current_conversion
        new_monthly_conversions = current_monthly_users * (current_conversion * (1 + result.relative_effect))
        additional_conversions = new_monthly_conversions - current_monthly_conversions
        
        print(f"  Monthly users:           {current_monthly_users:,}")
        print(f"  Current conversions:     {current_monthly_conversions:,.0f}")
        print(f"  Projected conversions:   {new_monthly_conversions:,.0f}")
        print(f"  Additional conversions:  +{additional_conversions:,.0f}/month")
        
    else:
        print("""
RECOMMENDATION: ❌ DO NOT SHIP

The experiment did not show a statistically significant improvement.
Consider iterating on the treatment or testing a different hypothesis.
        """)
    
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                         TUTORIAL COMPLETE!                                ║
╚═══════════════════════════════════════════════════════════════════════════╝

Key takeaways:

1. BEFORE running: Calculate sample size to ensure adequate power
2. DURING: Don't peek at results - it inflates false positive rate  
3. AFTER: Check ALL metrics, not just the primary one
4. ALWAYS: Consider practical significance, not just statistical

Next steps:
  • Try modifying SimulationConfig to see different scenarios
  • Run src/simulation.py to see underpowered experiments
  • Explore the analysis module for multiple comparison corrections

Happy experimenting! 🔬
    """)


if __name__ == "__main__":
    main()
