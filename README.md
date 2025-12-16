# A/B Experimentation: From Theory to Practice

A hands-on guide for understanding experimentation systems by building one.

![experimentation image](experimentation-poster.png "Poster represents null hypothesis rejection")

## Getting Started

```bash
git clone git@github.com:vepr-ua/ab-experimentation-guide.git
cd ab-experimentation-guide

# Start virtual environment
uv venv
source .venv/bin/activate
uv pip install -e .

# Run the simulation
python src/simulation.py

# Interactive notebook
uv pip install jupyter
jupyter notebook notebooks/custom_experiment.ipynb
```

## Documentation

| Document | Description |
|----------|-------------|
| [Key Concepts](docs/concepts.md) | Hypothesis, metrics, statistics, power analysis, assignment |
| [Practical Guide](docs/guide.md) | How to run experiments, interpret results, worked examples |
| [Common Pitfalls](docs/pitfalls.md) | Peeking, underpowered tests, multiple comparisons, and more |
| [API Reference](docs/api.md) | Complete function reference for all modules |

## The Experiment Lifecycle

Every A/B test follows this workflow:

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXPERIMENT LIFECYCLE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. HYPOTHESIS          "Changing X will improve Y by Z%"       │
│         │                                                       │
│         ▼                                                       │
│  2. DESIGN              Sample size, duration, metrics          │
│         │                                                       │
│         ▼                                                       │
│  3. ASSIGNMENT          Hash-based randomization → variants     │
│         │                                                       │
│         ▼                                                       │
│  4. EXPOSURE            Users experience control or treatment   │
│         │                                                       │
│         ▼                                                       │
│  5. MEASUREMENT         Collect events, compute metrics         │
│         │                                                       │
│         ▼                                                       │
│  6. ANALYSIS            Statistical tests, confidence intervals │
│         │                                                       │
│         ▼                                                       │
│  7. DECISION            Ship, iterate, or kill                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Example

```python
from simulation import run_experiment, ExperimentConfig, ExperimentReporter

# Configure your experiment
config = ExperimentConfig(
    num_users=20000,
    control_conversion_rate=0.10,
    treatment_lift=0.15,
)

# Run and analyze
results = run_experiment(config)
ExperimentReporter(results).print_full_report()
```

Output:
```
======================================================================
                        A/B EXPERIMENT REPORT
======================================================================

1. HYPOTHESIS
----------------------------------------------------------------------
   Single-page checkout will increase conversion rate
   Baseline: 10.0% → Target: 11.5%
   Expected lift: 15.0%

2. DESIGN (Power Analysis)
----------------------------------------------------------------------
   Sample size:  10,000/variant (20,000 total)
   Required:     6,693/variant for 15.0% MDE
   Status:       ✓ Adequately powered

...

7. DECISION
----------------------------------------------------------------------
   SHIP: Treatment shows +16.8% lift (p=0.0001)
```

## Project Structure

```
ab-experimentation-guide/
├── README.md
├── docs/
│   ├── concepts.md        # Statistical foundations
│   ├── guide.md           # Practical how-to guide
│   ├── pitfalls.md        # Common mistakes to avoid
│   └── api.md             # API reference
├── src/
│   ├── assignment.py      # User → variant assignment
│   ├── metrics.py         # Metric computation
│   ├── analysis.py        # Statistical tests + power analysis
│   └── simulation.py      # End-to-end experiment runner
└── notebooks/
    └── custom_experiment.ipynb  # Analyze your own data
```

## Module Overview

### [simulation.py](docs/api.md#simulationpy)
End-to-end experiment runner with lifecycle functions.

```python
from simulation import run_experiment, scenario_clear_winner
results = run_experiment()  # or scenario_clear_winner(), scenario_no_effect()
```

### [analysis.py](docs/api.md#analysispy)
Power analysis and statistical tests.

```python
from analysis import calculate_sample_size, calculate_mde, two_proportion_z_test

# How many users do I need?
n = calculate_sample_size(baseline_rate=0.10, minimum_detectable_effect=0.10)

# What can I detect with N users?
mde = calculate_mde(sample_size_per_variant=5000, baseline_rate=0.10)

# Is my result significant?
result = two_proportion_z_test(control_conversions=500, control_total=5000,
                                treatment_conversions=550, treatment_total=5000)
```

### [assignment.py](docs/api.md#assignmentpy)
Deterministic hash-based assignment.

```python
from assignment import Experiment, Variant, assign_variant

experiment = Experiment(id="exp_1", name="Test", variants=[
    Variant("control", 50), Variant("treatment", 50)
])
variant = assign_variant("user_123", experiment)  # Always same result
```

### [metrics.py](docs/api.md#metricspy)
Aggregate events into metrics.

```python
from metrics import compute_metric_by_variant

results = compute_metric_by_variant(users_df, revenue_per_user)
```

## Using Your Own Data

See the [interactive notebook](notebooks/custom_experiment.ipynb) or [API docs](docs/api.md#using-your-own-data).

```python
# Your data format:
# users_df:  user_id, variant
# events_df: user_id, converted, order_value

results = analyze_custom_data(users_df, events_df)
ExperimentReporter(results).print_full_report()
```

## Learn More

- [Key Concepts](docs/concepts.md) - Start here for statistical foundations
- [Practical Guide](docs/guide.md) - How to run experiments end-to-end
- [Common Pitfalls](docs/pitfalls.md) - Mistakes that invalidate experiments
- [API Reference](docs/api.md) - Detailed function documentation
