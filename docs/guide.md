# Practical Guide

How to plan, run, and interpret A/B experiments.

## Why A/B Test?

A/B testing removes guesswork from decision-making. Instead of debating whether a change is "better," you measure it.

**Without A/B testing:**
- "I think users prefer the blue button" → Ship it → Hope it works

**With A/B testing:**
- "Let's test blue vs green" → 50% see blue, 50% see green → Blue converts 12% better → Ship blue with confidence

### Impact at Scale

Small differences in conversion rates translate to large business impact at scale.

| Baseline | Lift | Monthly Users | Extra Conversions/Month |
|----------|------|---------------|------------------------|
| 10% | +5% | 100,000 | +500 |
| 10% | +10% | 100,000 | +1,000 |
| 10% | +5% | 1,000,000 | +5,000 |

## Interpreting Results

### Understanding p-values

The p-value answers: "If there's truly no difference, what's the probability of seeing results this extreme?"

| p-value | Interpretation |
|---------|----------------|
| p < 0.01 | Strong evidence against null hypothesis |
| p < 0.05 | Sufficient evidence (standard threshold) |
| p < 0.10 | Weak evidence |
| p > 0.10 | Insufficient evidence |

**Common misconception**: p=0.03 does NOT mean "3% chance the treatment doesn't work." It means "3% chance of seeing this result if the treatment truly has no effect."

### Making Decisions

| Outcome | CI | Action |
|---------|-----|--------|
| Significant positive | [+5%, +25%] | **Ship it** |
| Significant negative | [-20%, -5%] | **Kill it** |
| Inconclusive | [-3%, +8%] | **Iterate** - run longer or redesign |
| Significant but tiny | [+0.1%, +0.5%] | Consider if worth the complexity |

## A Worked Example

Let's walk through a complete experiment.

### Scenario

Your e-commerce site has a 3-step checkout. You want to test a 1-step checkout.

**Hypothesis**: "Reducing checkout from 3 steps to 1 will increase purchase conversion by at least 10%."

### Step 1: Power Analysis

```python
from analysis import calculate_sample_size

n = calculate_sample_size(
    baseline_rate=0.10,      # Current 10% conversion
    minimum_detectable_effect=0.10,  # Want to detect 10% relative lift
    alpha=0.05,              # 5% false positive rate
    power=0.80               # 80% chance to detect real effect
)
# → 14,752 users per variant
```

You need ~30,000 total users. With 5,000 daily visitors, that's 6 days.

### Step 2: Run the Experiment

Randomly assign users:
- Control (50%): 3-step checkout
- Treatment (50%): 1-step checkout

**Important**: Don't peek at results until you reach your sample size!

### Step 3: Analyze Results

After reaching sample size:

```
Control:   1,520 / 15,000 = 10.13% conversion
Treatment: 1,680 / 15,000 = 11.20% conversion

Relative lift: +10.6%
95% CI: [+3.2%, +18.0%]
p-value: 0.004
```

### Step 4: Decision

- p < 0.05 ✓
- CI doesn't include 0 ✓
- Effect size is meaningful ✓

**Decision: Ship the 1-step checkout.**

## When NOT to A/B Test

A/B testing isn't always the right approach:

| Situation | Why Not | Alternative |
|-----------|---------|-------------|
| Small user base | Can't reach statistical significance | Qualitative research, user interviews |
| Urgent fix | No time to wait | Just ship it, monitor metrics |
| Ethical concerns | Can't withhold beneficial treatment | Give everyone the better option |
| Major redesign | Too many variables changing | Phased rollout, qualitative testing |
| Low-traffic feature | Years to reach significance | Make a judgment call |

**Rule of thumb**: If you can't reach required sample size within 2-4 weeks, consider alternatives.

## Experiment Checklist

### Before Starting

- [ ] Define a clear, measurable hypothesis
- [ ] Choose primary metric (before seeing any data)
- [ ] Run power analysis to determine sample size
- [ ] Verify you have enough traffic
- [ ] Check for conflicting experiments
- [ ] Set up proper event tracking

### During the Experiment

- [ ] Verify assignment is balanced (~50/50)
- [ ] Check for data quality issues
- [ ] **Don't peek at results** (or use sequential testing)
- [ ] Monitor guardrail metrics

### After Reaching Sample Size

- [ ] Analyze primary metric first
- [ ] Check confidence intervals, not just p-values
- [ ] Look for segments where effect differs
- [ ] Document results for future reference
- [ ] Make a decision: ship, kill, or iterate
