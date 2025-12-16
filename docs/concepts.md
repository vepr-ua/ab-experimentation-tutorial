# Key Concepts

Core concepts you need to understand before running A/B experiments.

## 1. The Hypothesis

A good hypothesis is specific and measurable:
- **Bad**: "The new checkout will be better"
- **Good**: "Reducing checkout steps from 3 to 1 will increase conversion rate by 5%"

A hypothesis should specify:
- What you're changing
- What metric will improve
- By how much (your minimum detectable effect)

## 2. Metrics

| Type | Purpose | Example |
|------|---------|---------|
| **Primary** | What you're optimizing for | Conversion rate |
| **Secondary** | Related outcomes you care about | Revenue per user |
| **Guardrail** | Things that shouldn't get worse | Page load time, error rate |

**Choose your primary metric before starting.** This prevents cherry-picking "significant" results after the fact.

### Common Metric Types

- **Conversion rate**: Binary outcome (did user do X? yes/no)
- **Mean**: Average value per user (revenue, time on site)
- **Ratio**: Aggregate ratio (total revenue / total users)

## 3. Statistical Foundation

When we run an experiment, we're trying to answer: "Is the difference we observed real, or just noise?"

### Frequentist Approach

- **Null hypothesis (H₀)**: There's no difference between variants
- **Alternative hypothesis (H₁)**: There is a difference
- **p-value**: Probability of seeing this result if H₀ is true
- **Significance level (α)**: Threshold for rejecting H₀ (typically 0.05)

### The Math for Conversion Rates

For binary outcomes (converted/didn't convert), we use a two-proportion z-test:

```
        p̂₁ - p̂₂
z = ─────────────────
    √(p̂(1-p̂)(1/n₁ + 1/n₂))

where p̂ = (x₁ + x₂)/(n₁ + n₂)  (pooled proportion)
```

### For Continuous Metrics

For metrics like revenue or time on page, we use Welch's t-test, which compares means while accounting for potentially different variances between groups.

## 4. Sample Size & Power

Before running an experiment, you need to know how many users you need. This depends on:

- **Baseline conversion rate**: Your current metric value
- **Minimum Detectable Effect (MDE)**: Smallest improvement worth detecting
- **Statistical power (1-β)**: Probability of detecting a real effect (typically 0.8)
- **Significance level (α)**: False positive rate (typically 0.05)

### Sample Size Formula

```
         2(Z_α/2 + Z_β)² × p(1-p)
n ≈ ─────────────────────────────────
              (MDE)²
```

### The Power Tradeoff

| Want to detect | Users needed | Time to run |
|----------------|--------------|-------------|
| 20% lift | ~3,700/variant | Short |
| 10% lift | ~15,000/variant | Medium |
| 5% lift | ~60,000/variant | Long |

Smaller effects require exponentially more users to detect reliably.

## 5. Assignment

Users must be randomly assigned to variants in a way that's:
- **Deterministic**: Same user always sees same variant
- **Uniform**: ~50/50 split (for two variants)
- **Independent**: Assignment to one experiment doesn't affect another

### Hash-Based Assignment

We use hashing to achieve deterministic randomness:

```
hash(user_id + experiment_id) % 100 < 50 → control
```

This ensures:
- Same user always gets the same variant
- Different experiments get independent assignments
- No need to store assignments in a database

## 6. Confidence Intervals

A 95% confidence interval tells you the range of plausible effect sizes.

```
Result: +15% lift, 95% CI: [+5%, +25%]
```

This means:
- Our best estimate is +15% lift
- We're 95% confident the true effect is between +5% and +25%
- The effect is definitely positive (CI doesn't include 0)

### Reading Confidence Intervals

| CI | Interpretation |
|----|----------------|
| [+5%, +25%] | Significant positive effect |
| [-2%, +12%] | Inconclusive (CI includes 0) |
| [-15%, -3%] | Significant negative effect |

**Why CI matters more than p-value**: A p-value tells you "is there an effect?" A CI tells you "how big is the effect?" The latter is usually more useful for decisions.
