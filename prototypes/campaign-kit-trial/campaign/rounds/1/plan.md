# Round 1 — textkit-spec

## Thought
Two actions fit a round, so round 1 takes the two lanes with the most failing spec tests:
durations (compound units, decimals, rounding) and slugify (accents and spelled-out letters).
cells follows in round 2. A lane that cannot pass its spec file in one action tells the judge
which cases remain.

## Actions
### durations
Make `parse_duration` and `format_duration` follow the rules in the docstring of
`spec/test_durations.py` so every test there passes.

### slugify
Make `slugify` follow the rules in the docstring of `spec/test_slug.py` so every test there
passes.

```json round-manifest
{
  "round": 1,
  "thought": "Two actions per round: start with durations and slugify, which fail the most spec tests; cells follows in round 2.",
  "actions": [
    {"lane": "durations", "task": "Make parse_duration and format_duration in textkit/durations.py follow the rules in the docstring of spec/test_durations.py so every test there passes. Do not edit spec/.",
     "owns": ["textkit/durations.py"], "effort": "high",
     "acceptance": ["python3 tools/score.py spec shows spec/test_durations.py 24/24", "python3 tools/score.py tests shows tests total 7/7"]},
    {"lane": "slugify", "task": "Make slugify in textkit/slug.py follow the rules in the docstring of spec/test_slug.py so every test there passes. Do not edit spec/.",
     "owns": ["textkit/slug.py"], "effort": "medium",
     "acceptance": ["python3 tools/score.py spec shows spec/test_slug.py 10/10", "python3 tools/score.py tests shows tests total 7/7"]}
  ],
  "approved": false
}
```
