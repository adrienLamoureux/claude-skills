# Lane durations — round 1

## Status
done

## What I did
Rewrote `parse_duration` (compound units, spaces, decimals, bare seconds, each unit once) and
`format_duration` (round half up, zero parts dropped) in `textkit/durations.py`.

## Evidence
- `python3 tools/score.py spec` → `spec/test_durations.py 24/24`
- `python3 tools/score.py tests` → `tests total 7/7`

## Acceptance
- spec/test_durations.py 24/24: met
- tests total 7/7: met

## Surprises
None.

## Suggested next step
None for this lane.
