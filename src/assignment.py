"""
Assignment Module: Deterministic user → variant assignment

The key insight: we need assignment to be both random AND deterministic.
- Random: to ensure unbiased groups
- Deterministic: so users always see the same variant

We achieve this by hashing (user_id, experiment_id) to get a stable "random" number.
"""

import hashlib
from dataclasses import dataclass
from typing import Literal


@dataclass
class Variant:
    """Represents an experiment variant."""
    name: str
    weight: int  # Relative weight (e.g., 50 for 50%)


@dataclass
class Experiment:
    """Experiment configuration."""
    id: str
    name: str
    variants: list[Variant]
    
    def __post_init__(self):
        total_weight = sum(v.weight for v in self.variants)
        if total_weight != 100:
            raise ValueError(f"Variant weights must sum to 100, got {total_weight}")


def get_assignment_bucket(user_id: str, experiment_id: str, salt: str = "") -> int:
    """
    Generate a deterministic bucket (0-99) for a user in an experiment.
    
    The bucket is derived from a hash of (user_id, experiment_id, salt).
    This ensures:
    - Same user always gets same bucket for same experiment
    - Different experiments get independent assignments
    - Salt allows re-randomization if needed
    
    Args:
        user_id: Unique user identifier
        experiment_id: Unique experiment identifier
        salt: Optional salt for re-randomization
    
    Returns:
        Integer 0-99 representing the user's bucket
    """
    # Concatenate inputs with a delimiter that won't appear in IDs
    key = f"{user_id}|{experiment_id}|{salt}"
    
    # MD5 is fine here - we need speed, not cryptographic security
    hash_bytes = hashlib.md5(key.encode()).digest()
    
    # Use first 4 bytes as an integer, mod 100 for bucket
    hash_int = int.from_bytes(hash_bytes[:4], byteorder='big')
    return hash_int % 100


def assign_variant(user_id: str, experiment: Experiment) -> Variant:
    """
    Assign a user to a variant based on their bucket.
    
    Example with 50/50 split:
        - Buckets 0-49  → Control
        - Buckets 50-99 → Treatment
    
    Example with 80/10/10 split:
        - Buckets 0-79  → Control
        - Buckets 80-89 → Treatment A
        - Buckets 90-99 → Treatment B
    """
    bucket = get_assignment_bucket(user_id, experiment.id)
    
    cumulative = 0
    for variant in experiment.variants:
        cumulative += variant.weight
        if bucket < cumulative:
            return variant
    
    # Shouldn't reach here if weights sum to 100
    return experiment.variants[-1]


# Convenience function for simple A/B tests
def simple_ab_assignment(user_id: str, experiment_id: str) -> Literal["control", "treatment"]:
    """Quick assignment for simple 50/50 A/B tests."""
    bucket = get_assignment_bucket(user_id, experiment_id)
    return "control" if bucket < 50 else "treatment"


# --- Demonstration ---

if __name__ == "__main__":
    # Create an experiment
    checkout_experiment = Experiment(
        id="exp_checkout_v2",
        name="Single-Page Checkout",
        variants=[
            Variant("control", 50),
            Variant("treatment", 50),
        ]
    )
    
    # Show that assignment is deterministic
    print("=== Deterministic Assignment Demo ===\n")
    
    test_users = ["user_123", "user_456", "user_789"]
    
    for user_id in test_users:
        bucket = get_assignment_bucket(user_id, checkout_experiment.id)
        variant = assign_variant(user_id, checkout_experiment)
        print(f"{user_id}: bucket={bucket:2d} → {variant.name}")
    
    print("\n(Running again to show determinism...)\n")
    
    for user_id in test_users:
        bucket = get_assignment_bucket(user_id, checkout_experiment.id)
        variant = assign_variant(user_id, checkout_experiment)
        print(f"{user_id}: bucket={bucket:2d} → {variant.name}")
    
    # Verify distribution is roughly uniform
    print("\n=== Distribution Check (10,000 users) ===\n")
    
    assignments = {"control": 0, "treatment": 0}
    for i in range(10000):
        variant = assign_variant(f"user_{i}", checkout_experiment)
        assignments[variant.name] += 1
    
    for name, count in assignments.items():
        pct = count / 100
        print(f"{name}: {count} ({pct:.1f}%)")
