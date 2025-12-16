# Common Pitfalls

Mistakes that invalidate experiments and how to avoid them.

## 1. Peeking (The #1 Mistake)

**The problem**: Checking results daily and stopping when you see p < 0.05.

```
Day 1:  p = 0.23  (not significant)
Day 2:  p = 0.08  (not significant)
Day 3:  p = 0.04  (significant!) → STOP ❌
```

**Why it's wrong**: Random fluctuations will temporarily show significance. By checking repeatedly, you dramatically increase false positives. With daily peeking, your actual false positive rate can exceed 30% even with α = 0.05.

**The fix**:
- Decide sample size upfront using power analysis
- Run until you reach it
- Analyze once at the end

**Alternative**: Use sequential testing methods (like SPRT) that are designed for continuous monitoring.

## 2. Underpowered Experiments

**The problem**: Running experiments with too few users to detect realistic effects.

```
You want to detect: 5% lift
You have: 1,000 users
You need: 60,000 users
Result: "No significant difference" (but you couldn't have detected one anyway)
```

**Why it's wrong**: An underpowered experiment that shows "no effect" tells you nothing. The effect might exist—you just couldn't detect it.

**The fix**:
- Always run power analysis before starting
- If you can't get enough users:
  - Accept you can only detect larger effects
  - Run the experiment longer
  - Don't run it at all

```python
from analysis import calculate_sample_size, calculate_mde

# What can I detect with the users I have?
mde = calculate_mde(sample_size_per_variant=1000, baseline_rate=0.10)
# → 0.40 (can only detect 40%+ lift)
```

## 3. Multiple Comparisons

**The problem**: Testing many metrics inflates false positive rate.

```
Testing 20 metrics at α = 0.05
Expected false positives by chance: 1 metric (5% × 20 = 1)
```

If you test enough metrics, something will be "significant" by chance.

**Why it's wrong**: You'll find "significant" results that are actually just noise, leading to wrong conclusions.

**The fix**:
- Define primary metric upfront (before seeing data)
- Use Bonferroni correction: α_adjusted = 0.05 / num_tests
- Or use Benjamini-Hochberg for less conservative FDR control
- Report all metrics tested, not just significant ones

```python
from analysis import bonferroni_correction

p_values = [0.02, 0.04, 0.15, 0.01, 0.08]
significant = bonferroni_correction(p_values, alpha=0.05)
# With 5 tests, need p < 0.01 to be significant
```

## 4. Simpson's Paradox

**The problem**: A trend in aggregated data reverses when you segment.

```
Overall:  Treatment wins (+5%)
Mobile:   Control wins (+2%)
Desktop:  Control wins (+3%)

How? Treatment got more mobile users, who convert less overall.
```

**Why it's wrong**: The "winning" variant might actually be worse for every user segment. The aggregate result is misleading.

**The fix**:
- Check that variant assignment is balanced across key segments
- Look at results by segment (device, country, new vs returning)
- If imbalanced, stratify your analysis

## 5. Survivorship Bias

**The problem**: Only analyzing users who completed part of the flow.

```
Checkout experiment:
- Control: 100 started → 80 reached payment → 40 converted
  (50% of those who reached payment)
- Treatment: 100 started → 40 reached payment → 30 converted
  (75% of those who reached payment)

Looking only at "conversion among those who reached payment": treatment wins!
But treatment lost more users earlier in the funnel.
```

**Why it's wrong**: You're excluding the users who were most negatively affected by the treatment.

**The fix**:
- Always analyze based on assignment (intent-to-treat)
- The denominator should be "all users assigned," not "users who reached step X"
- Track the full funnel, not just the final conversion

## 6. Novelty and Primacy Effects

**The problem**: Short-term behavior differs from long-term behavior.

**Novelty effect**: Users interact more with something new just because it's new. Effect fades over time.

**Primacy effect**: Users stick with what they're used to. New things seem worse initially.

```
Week 1: Treatment +20% (novelty)
Week 4: Treatment +5% (true effect)
```

**The fix**:
- Run experiments for at least 1-2 full business cycles
- Segment by new vs. returning users
- Be skeptical of very large effects in short experiments

## 7. Selection Bias in Assignment

**The problem**: Assignment isn't truly random.

Examples:
- Only users who click a button enter the experiment
- Assignment based on user ID that correlates with behavior
- Technical issues cause some users to fall out of treatment

**Why it's wrong**: If groups differ before treatment, you can't attribute differences to the treatment.

**The fix**:
- Use hash-based assignment on stable user IDs
- Verify balance: groups should be similar on pre-experiment metrics
- Check for differential attrition (more users leaving one variant)

## 8. Interference Between Users

**The problem**: One user's treatment affects another user's outcome.

Examples:
- Social features: User A sees new share button → shares with User B → User B converts
- Marketplace: Seller A gets new feature → takes sales from Seller B
- Limited inventory: Users compete for same items

**Why it's wrong**: The stable unit treatment value assumption (SUTVA) is violated. Standard statistical tests don't apply.

**The fix**:
- Use cluster randomization (randomize by group, not individual)
- For marketplaces, consider geo-based experiments
- Be aware this is an advanced problem with no easy solution

## 9. Not Accounting for Multiple Variants

**The problem**: Testing A vs B vs C vs D without adjusting for comparisons.

```
4 variants = 6 pairwise comparisons
False positive risk: 1 - (0.95)^6 = 26%
```

**The fix**:
- Adjust significance threshold for number of comparisons
- Or use ANOVA-style tests designed for multiple groups
- Better yet: test one thing at a time

## 10. HARKing (Hypothesizing After Results Known)

**The problem**: Finding a significant segment and pretending you predicted it.

```
Overall: No significant effect
But wait! Among left-handed users on Tuesdays: +50% lift!
"We hypothesized that left-handed users would benefit most..."
```

**Why it's wrong**: With enough segments, you'll always find something significant by chance.

**The fix**:
- Pre-register your hypothesis and analysis plan
- Exploratory analysis is fine, but label it as such
- Confirm surprising findings in a follow-up experiment
