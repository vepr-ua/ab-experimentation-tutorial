"""
Metrics Module: Computing experiment metrics from raw events

In production systems, you typically have:
1. Raw events (page views, clicks, purchases)
2. Metric definitions (how to aggregate events into metrics)
3. Computed metrics per user/variant

Common metric types:
- Conversion rate: users who did X / total users
- Mean: average of some value per user
- Ratio: sum(X) / sum(Y)
"""

from dataclasses import dataclass
from typing import Callable
import pandas as pd
import numpy as np


@dataclass
class MetricDefinition:
    """Defines how to compute a metric from user-level data."""
    name: str
    description: str
    compute_fn: Callable[[pd.DataFrame], pd.Series]
    metric_type: str  # "conversion", "mean", "ratio"


def conversion_rate(df: pd.DataFrame, event_column: str) -> pd.Series:
    """
    Compute conversion rate: 1 if user has event, 0 otherwise.
    Returns a Series indexed by user_id.
    """
    return df.groupby("user_id")[event_column].max().clip(0, 1)


def mean_metric(df: pd.DataFrame, value_column: str) -> pd.Series:
    """
    Compute mean of a value per user.
    Returns a Series indexed by user_id.
    """
    return df.groupby("user_id")[value_column].mean()


def sum_metric(df: pd.DataFrame, value_column: str) -> pd.Series:
    """
    Compute sum of a value per user.
    Returns a Series indexed by user_id.
    """
    return df.groupby("user_id")[value_column].sum()


@dataclass
class MetricResult:
    """Results of computing a metric for a variant."""
    variant: str
    metric_name: str
    n: int              # Sample size
    mean: float         # Mean value
    std: float          # Standard deviation
    se: float           # Standard error of the mean
    
    def __repr__(self):
        return (f"MetricResult({self.variant}: n={self.n}, "
                f"mean={self.mean:.4f}, std={self.std:.4f}, se={self.se:.4f})")


def compute_metric_by_variant(
    user_data: pd.DataFrame,
    metric_values: pd.Series,
    variant_column: str = "variant"
) -> dict[str, MetricResult]:
    """
    Compute metric statistics grouped by variant.
    
    Args:
        user_data: DataFrame with user_id and variant columns
        metric_values: Series with metric value per user (indexed by user_id)
        variant_column: Name of the variant column
    
    Returns:
        Dict mapping variant name to MetricResult
    """
    # Join metric values to user data
    df = user_data.set_index("user_id").join(metric_values.rename("metric_value"))
    
    # Fill NaN with 0 (users who didn't trigger any events)
    df["metric_value"] = df["metric_value"].fillna(0)
    
    results = {}
    for variant, group in df.groupby(variant_column):
        values = group["metric_value"]
        n = len(values)
        mean = values.mean()
        std = values.std(ddof=1)  # Sample std
        se = std / np.sqrt(n) if n > 0 else 0
        
        results[variant] = MetricResult(
            variant=variant,
            metric_name="metric",
            n=n,
            mean=mean,
            std=std,
            se=se
        )
    
    return results


# --- Demonstration ---

if __name__ == "__main__":
    # Create sample data
    np.random.seed(42)
    
    # User assignments
    users = pd.DataFrame({
        "user_id": [f"user_{i}" for i in range(1000)],
        "variant": np.random.choice(["control", "treatment"], 1000)
    })
    
    # Event data: purchases with amounts
    # Treatment has slightly higher conversion and purchase amounts
    events = []
    for _, row in users.iterrows():
        base_rate = 0.10 if row["variant"] == "control" else 0.12
        if np.random.random() < base_rate:
            amount = np.random.lognormal(3.5, 0.5)  # ~$30-50 purchases
            if row["variant"] == "treatment":
                amount *= 1.05  # 5% higher in treatment
            events.append({
                "user_id": row["user_id"],
                "event": "purchase",
                "amount": amount
            })
    
    events_df = pd.DataFrame(events)
    
    print("=== Sample Event Data ===\n")
    print(events_df.head(10))
    print(f"\nTotal events: {len(events_df)}")
    
    # Compute conversion metric
    print("\n=== Conversion Rate by Variant ===\n")
    
    # Add 'converted' column (1 if any purchase)
    conversion_values = events_df.groupby("user_id").size().clip(0, 1)
    
    conversion_results = compute_metric_by_variant(users, conversion_values)
    for variant, result in conversion_results.items():
        print(f"{variant}: {result.mean:.2%} (n={result.n}, SE={result.se:.4f})")
    
    # Compute revenue metric  
    print("\n=== Revenue Per User by Variant ===\n")
    
    revenue_values = events_df.groupby("user_id")["amount"].sum()
    
    revenue_results = compute_metric_by_variant(users, revenue_values)
    for variant, result in revenue_results.items():
        print(f"{variant}: ${result.mean:.2f} (n={result.n}, SE=${result.se:.2f})")
