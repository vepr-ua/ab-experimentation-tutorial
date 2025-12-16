# API Reference

Complete reference for all modules and functions.

## simulation.py

End-to-end experiment simulation following the full lifecycle.

### Quick Start

```python
from simulation import run_experiment, ExperimentConfig, ExperimentReporter

# Run with custom configuration
config = ExperimentConfig(
    num_users=20000,
    control_conversion_rate=0.10,
    treatment_lift=0.15,  # 15% relative lift
    seed=42,
)
results = run_experiment(config)
ExperimentReporter(results).print_full_report()
```

### ExperimentConfig

Configuration for experiment simulation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_users` | int | 10000 | Total users in experiment |
| `control_conversion_rate` | float | 0.10 | Baseline conversion rate |
| `treatment_lift` | float | 0.15 | Relative lift (0.15 = 15%) |
| `control_avg_order_value` | float | 45.0 | Average order value |
| `treatment_aov_lift` | float | 0.0 | Relative lift in AOV |
| `daily_traffic` | int | 1000 | Users per day |
| `seed` | int | 42 | Random seed |

### Lifecycle Functions

| Function | Phase | Description |
|----------|-------|-------------|
| `design_experiment(hypothesis, config)` | Design | Power analysis and sample size calculation |
| `assign_users(config)` | Assignment | Deterministic user → variant assignment |
| `simulate_exposure(users, config)` | Exposure | Simulate user behavior based on variant |
| `measure_metrics(users, events)` | Measurement | Compute metrics by variant |
| `analyze_results(users, events, metrics)` | Analysis | Run statistical tests |
| `make_decision(test_result)` | Decision | Generate recommendation |

### Preset Scenarios

```python
from simulation import scenario_clear_winner, scenario_no_effect, scenario_underpowered

# Large effect, adequate sample
results = scenario_clear_winner()  # 20% lift, 20k users

# No real effect
results = scenario_no_effect()  # 0% lift, 10k users

# Real effect, too few users
results = scenario_underpowered()  # 15% lift, 500 users
```

---

## analysis.py

Statistical tests and power analysis.

### Power Analysis

#### calculate_sample_size

Calculate required users per variant.

```python
from analysis import calculate_sample_size

n = calculate_sample_size(
    baseline_rate=0.10,           # Current conversion rate
    minimum_detectable_effect=0.10,  # Relative lift to detect
    alpha=0.05,                   # Significance level
    power=0.80                    # Statistical power
)
# → 14752
```

#### calculate_mde

Calculate minimum detectable effect for a given sample size.

```python
from analysis import calculate_mde

mde = calculate_mde(
    sample_size_per_variant=5000,
    baseline_rate=0.10,
    alpha=0.05,
    power=0.80
)
# → 0.175 (17.5% relative lift)
```

#### calculate_experiment_duration

Estimate how long to run the experiment.

```python
from analysis import calculate_experiment_duration

days = calculate_experiment_duration(
    sample_size_per_variant=15000,
    daily_traffic=5000,
    num_variants=2,
    traffic_fraction=1.0
)
# → 6 days
```

### Statistical Tests

#### two_proportion_z_test

Compare conversion rates between variants.

```python
from analysis import two_proportion_z_test

result = two_proportion_z_test(
    control_conversions=500,
    control_total=5000,
    treatment_conversions=550,
    treatment_total=5000,
    alpha=0.05
)

print(result.p_value)           # 0.0456
print(result.is_significant)    # True
print(result.relative_effect)   # 0.10 (10% lift)
print(result.confidence_interval)  # (0.001, 0.199)
```

#### two_sample_t_test

Compare continuous metrics (revenue, time, etc).

```python
from analysis import two_sample_t_test
import numpy as np

control = np.array([10, 20, 15, 25, 30])
treatment = np.array([12, 22, 18, 28, 35])

result = two_sample_t_test(control, treatment, alpha=0.05)
```

### Multiple Comparisons

#### bonferroni_correction

Conservative correction for multiple tests.

```python
from analysis import bonferroni_correction

p_values = [0.02, 0.04, 0.15, 0.01, 0.08]
significant = bonferroni_correction(p_values, alpha=0.05)
# → [False, False, False, True, False]
# Only p=0.01 passes with adjusted α=0.01
```

#### benjamini_hochberg_correction

Less conservative FDR control.

```python
from analysis import benjamini_hochberg_correction

p_values = [0.02, 0.04, 0.15, 0.01, 0.08]
significant = benjamini_hochberg_correction(p_values, alpha=0.05)
# → [True, True, False, True, False]
```

---

## assignment.py

Deterministic hash-based user assignment.

### Classes

#### Variant

```python
from assignment import Variant

control = Variant(name="control", weight=50)
treatment = Variant(name="treatment", weight=50)
```

#### Experiment

```python
from assignment import Experiment, Variant

experiment = Experiment(
    id="exp_checkout_v2",
    name="Single-Page Checkout",
    variants=[
        Variant("control", 50),
        Variant("treatment", 50)
    ]
)
# Weights must sum to 100
```

### Functions

#### assign_variant

Assign a user to a variant deterministically.

```python
from assignment import assign_variant

variant = assign_variant("user_123", experiment)
# → Variant(name="control", weight=50)

# Always returns the same result for the same user
variant2 = assign_variant("user_123", experiment)
assert variant.name == variant2.name  # True
```

#### get_assignment_bucket

Get the raw bucket (0-99) for a user.

```python
from assignment import get_assignment_bucket

bucket = get_assignment_bucket("user_123", "exp_checkout_v2")
# → 42
```

#### simple_ab_assignment

Quick 50/50 assignment without defining an Experiment.

```python
from assignment import simple_ab_assignment

variant = simple_ab_assignment("user_123", "exp_checkout_v2")
# → "control" or "treatment"
```

---

## metrics.py

Aggregate raw events into per-user metrics.

### Functions

#### compute_metric_by_variant

Compute metric statistics grouped by variant.

```python
from metrics import compute_metric_by_variant
import pandas as pd

users_df = pd.DataFrame({
    'user_id': ['u1', 'u2', 'u3', 'u4'],
    'variant': ['control', 'control', 'treatment', 'treatment']
})

# Metric values indexed by user_id
revenue = pd.Series({'u1': 50, 'u2': 0, 'u3': 75, 'u4': 25})

results = compute_metric_by_variant(users_df, revenue)
# → {
#     'control': MetricResult(mean=25.0, se=25.0, n=2),
#     'treatment': MetricResult(mean=50.0, se=25.0, n=2)
# }
```

#### Aggregation Helpers

```python
from metrics import conversion_rate, mean_metric, sum_metric

# Binary: 1 if event occurred
conversion = conversion_rate(events_df, 'purchased')

# Average per user
avg_value = mean_metric(events_df, 'order_value')

# Total per user
total_value = sum_metric(events_df, 'order_value')
```

---

## Using Your Own Data

### Required Data Format

**Assignments DataFrame** (`users_df`):
| Column | Type | Description |
|--------|------|-------------|
| `user_id` | str | Unique user identifier |
| `variant` | str | "control" or "treatment" |

**Events DataFrame** (`events_df`):
| Column | Type | Description |
|--------|------|-------------|
| `user_id` | str | User who triggered event |
| `converted` | int | 1 if conversion, 0 otherwise |
| `order_value` | float | Revenue amount (optional) |

### Analyze Custom Data

```python
import pandas as pd
from simulation import ExperimentReporter

# Load your data
users_df = pd.read_csv('assignments.csv')
events_df = pd.read_csv('events.csv')

# Use the notebook function
results = analyze_custom_data(users_df, events_df, expected_lift=0.10)
ExperimentReporter(results).print_full_report()
```

### Interactive Notebook

```bash
jupyter notebook notebooks/custom_experiment.ipynb
```

The notebook provides:
- Custom scenario configuration
- Data loading from CSV
- Direct statistical test access
- Power analysis calculators
