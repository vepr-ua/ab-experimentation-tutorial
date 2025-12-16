"""A/B Experimentation Tutorial Package."""

from .assignment import (
    Experiment,
    Variant,
    assign_variant,
    get_assignment_bucket,
    simple_ab_assignment,
)

from .analysis import (
    TestResult,
    calculate_sample_size,
    calculate_experiment_duration,
    two_proportion_z_test,
    two_sample_t_test,
    bonferroni_correction,
    benjamini_hochberg_correction,
)

from .simulation import (
    SimulationConfig,
    SimulatedExperiment,
    simulate_experiment,
    print_experiment_summary,
    create_clear_winner_scenario,
    create_no_effect_scenario,
    create_small_effect_scenario,
    create_underpowered_scenario,
)

__all__ = [
    # Assignment
    "Experiment",
    "Variant", 
    "assign_variant",
    "get_assignment_bucket",
    "simple_ab_assignment",
    # Analysis
    "TestResult",
    "calculate_sample_size",
    "calculate_experiment_duration",
    "two_proportion_z_test",
    "two_sample_t_test",
    "bonferroni_correction",
    "benjamini_hochberg_correction",
    # Simulation
    "SimulationConfig",
    "SimulatedExperiment",
    "simulate_experiment",
    "print_experiment_summary",
    "create_clear_winner_scenario",
    "create_no_effect_scenario",
    "create_small_effect_scenario",
    "create_underpowered_scenario",
]
