"""
Simulation Module: Generate realistic A/B test data

This module creates synthetic data that mimics real experiment scenarios.
Useful for:
- Learning how experiments work
- Testing analysis pipelines
- Understanding edge cases

We simulate an e-commerce checkout optimization experiment where:
- Control: Original 3-step checkout
- Treatment: New 1-step checkout (faster, should convert better)
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta


@dataclass
class SimulationConfig:
    """Configuration for experiment simulation."""
    num_users: int = 10000
    control_conversion_rate: float = 0.10
    treatment_effect: float = 0.15  # 15% relative lift
    control_avg_order_value: float = 45.0
    treatment_aov_effect: float = 0.0  # No change in AOV
    seed: Optional[int] = 42


@dataclass
class SimulatedExperiment:
    """Container for simulated experiment data."""
    users: pd.DataFrame      # user_id, variant, signup_date
    events: pd.DataFrame     # user_id, event_type, timestamp, properties
    config: SimulationConfig


def simulate_experiment(config: SimulationConfig) -> SimulatedExperiment:
    """
    Generate a complete simulated experiment dataset.
    
    This creates realistic data with:
    - Users randomly assigned to variants
    - Conversion events based on variant-specific rates
    - Purchase amounts with realistic distributions
    - Timestamps spread over the experiment duration
    
    Args:
        config: Simulation parameters
    
    Returns:
        SimulatedExperiment with users and events DataFrames
    """
    if config.seed is not None:
        np.random.seed(config.seed)
    
    # Generate users with assignments
    users = pd.DataFrame({
        "user_id": [f"user_{i:06d}" for i in range(config.num_users)],
        "variant": np.random.choice(
            ["control", "treatment"], 
            size=config.num_users,
            p=[0.5, 0.5]
        ),
        "signup_date": pd.date_range(
            start="2024-01-01",
            periods=config.num_users,
            freq="1min"  # Spread signups over time
        )
    })
    
    # Generate conversion events
    events = []
    treatment_conversion_rate = config.control_conversion_rate * (1 + config.treatment_effect)
    
    for _, user in users.iterrows():
        # Determine conversion probability based on variant
        if user["variant"] == "control":
            conv_rate = config.control_conversion_rate
            avg_aov = config.control_avg_order_value
        else:
            conv_rate = treatment_conversion_rate
            avg_aov = config.control_avg_order_value * (1 + config.treatment_aov_effect)
        
        # Check if user converts
        if np.random.random() < conv_rate:
            # Generate purchase event
            order_value = np.random.lognormal(
                mean=np.log(avg_aov) - 0.125,  # Adjust for lognormal mean
                sigma=0.5
            )
            
            # Timestamp: some time after signup
            hours_to_convert = np.random.exponential(scale=24)  # Most convert within a day
            event_time = user["signup_date"] + timedelta(hours=hours_to_convert)
            
            events.append({
                "user_id": user["user_id"],
                "event_type": "purchase",
                "timestamp": event_time,
                "order_value": round(order_value, 2)
            })
            
            # Some users make multiple purchases (10% chance)
            if np.random.random() < 0.1:
                second_order = np.random.lognormal(
                    mean=np.log(avg_aov) - 0.125,
                    sigma=0.5
                )
                second_time = event_time + timedelta(days=np.random.exponential(7))
                events.append({
                    "user_id": user["user_id"],
                    "event_type": "purchase",
                    "timestamp": second_time,
                    "order_value": round(second_order, 2)
                })
    
    events_df = pd.DataFrame(events)
    if len(events_df) > 0:
        events_df = events_df.sort_values("timestamp").reset_index(drop=True)
    
    return SimulatedExperiment(
        users=users,
        events=events_df,
        config=config
    )


def get_experiment_summary(experiment: SimulatedExperiment) -> dict:
    """Generate summary statistics for the simulated experiment."""
    users = experiment.users
    events = experiment.events
    
    summary = {
        "total_users": len(users),
        "variants": {}
    }
    
    for variant in ["control", "treatment"]:
        variant_users = users[users["variant"] == variant]["user_id"]
        variant_events = events[events["user_id"].isin(variant_users)]
        
        conversions = variant_events["user_id"].nunique()
        total = len(variant_users)
        
        summary["variants"][variant] = {
            "users": total,
            "conversions": conversions,
            "conversion_rate": conversions / total if total > 0 else 0,
            "total_revenue": variant_events["order_value"].sum(),
            "avg_order_value": variant_events["order_value"].mean() if len(variant_events) > 0 else 0,
            "revenue_per_user": variant_events["order_value"].sum() / total if total > 0 else 0
        }
    
    return summary


def print_experiment_summary(experiment: SimulatedExperiment):
    """Pretty print experiment summary."""
    summary = get_experiment_summary(experiment)
    
    print("\n" + "=" * 70)
    print("EXPERIMENT SUMMARY")
    print("=" * 70)
    print(f"\nTotal Users: {summary['total_users']:,}")
    print(f"\nTrue treatment effect: {experiment.config.treatment_effect:.1%} relative lift")
    
    print("\n" + "-" * 70)
    print(f"{'Metric':<25} {'Control':>15} {'Treatment':>15} {'Diff':>12}")
    print("-" * 70)
    
    c = summary["variants"]["control"]
    t = summary["variants"]["treatment"]
    
    # Users
    print(f"{'Users':<25} {c['users']:>15,} {t['users']:>15,}")
    
    # Conversions
    print(f"{'Conversions':<25} {c['conversions']:>15,} {t['conversions']:>15,}")
    
    # Conversion Rate
    diff = (t['conversion_rate'] - c['conversion_rate']) / c['conversion_rate'] if c['conversion_rate'] > 0 else 0
    print(f"{'Conversion Rate':<25} {c['conversion_rate']:>14.2%} {t['conversion_rate']:>14.2%} {diff:>+11.1%}")
    
    # Revenue
    print(f"{'Total Revenue':<25} ${c['total_revenue']:>14,.2f} ${t['total_revenue']:>14,.2f}")
    
    # AOV
    if c['avg_order_value'] > 0:
        aov_diff = (t['avg_order_value'] - c['avg_order_value']) / c['avg_order_value']
    else:
        aov_diff = 0
    print(f"{'Avg Order Value':<25} ${c['avg_order_value']:>14,.2f} ${t['avg_order_value']:>14,.2f} {aov_diff:>+11.1%}")
    
    # Revenue per user
    if c['revenue_per_user'] > 0:
        rpu_diff = (t['revenue_per_user'] - c['revenue_per_user']) / c['revenue_per_user']
    else:
        rpu_diff = 0
    print(f"{'Revenue per User':<25} ${c['revenue_per_user']:>14,.2f} ${t['revenue_per_user']:>14,.2f} {rpu_diff:>+11.1%}")
    
    print("=" * 70 + "\n")


# Preset scenarios for learning
def create_clear_winner_scenario() -> SimulatedExperiment:
    """Scenario where treatment clearly wins."""
    return simulate_experiment(SimulationConfig(
        num_users=20000,
        control_conversion_rate=0.10,
        treatment_effect=0.20,  # 20% lift - very clear signal
        seed=42
    ))


def create_no_effect_scenario() -> SimulatedExperiment:
    """Scenario where there's no real effect (null result)."""
    return simulate_experiment(SimulationConfig(
        num_users=10000,
        control_conversion_rate=0.10,
        treatment_effect=0.0,  # No effect
        seed=42
    ))


def create_small_effect_scenario() -> SimulatedExperiment:
    """Scenario with small effect that may or may not be detected."""
    return simulate_experiment(SimulationConfig(
        num_users=5000,
        control_conversion_rate=0.10,
        treatment_effect=0.05,  # 5% lift - borderline detectable
        seed=42
    ))


def create_underpowered_scenario() -> SimulatedExperiment:
    """Scenario with real effect but not enough users to detect it."""
    return simulate_experiment(SimulationConfig(
        num_users=500,  # Way too small!
        control_conversion_rate=0.10,
        treatment_effect=0.15,  # Real 15% lift
        seed=42
    ))


# --- Demonstration ---

if __name__ == "__main__":
    print("\n" + "="*70)
    print("SCENARIO 1: Clear Winner")
    print("="*70)
    exp = create_clear_winner_scenario()
    print_experiment_summary(exp)
    
    print("\n" + "="*70)
    print("SCENARIO 2: No Effect (Null Result)")
    print("="*70)
    exp = create_no_effect_scenario()
    print_experiment_summary(exp)
    
    print("\n" + "="*70)
    print("SCENARIO 3: Underpowered (Real effect, too few users)")
    print("="*70)
    exp = create_underpowered_scenario()
    print_experiment_summary(exp)
