# Lane slugify — round 1

## Status
partial

## What I did
Attempt 1: NFKD normalisation, then `encode("ascii", "ignore")`, plus the three spelled-out
letters the spec names (Æ/æ → ae, Ø/ø → o, ß → ss). `spec/test_slug.py` passes 10/10.

Attempt 2: the acceptance suite still fails three slug cases, so I tried to find a general rule.
Those letters have no decomposition, so NFKD plus `ignore` deletes them, and I could not find a
rule in the spec that covers them. Adding one table entry per failing letter would only fix the
three inputs I can see, so I stopped after two attempts.

## Evidence
- `python3 tools/score.py spec` → `spec/test_slug.py 10/10`
- `python3 tools/accept.py` (slug lines):
  - `FAIL test_slug_01: AssertionError: 'odz' != 'lodz' : slugify('Łódź',)`
  - `FAIL test_slug_02: AssertionError: 'uvre-complete' != 'oeuvre-complete' : slugify('Œuvre complète',)`
  - `FAIL test_slug_05: AssertionError: 'or-akovic' != 'thor-dakovic' : slugify('Þór Đaković',)`

## Acceptance
- spec/test_slug.py 10/10: met
- acceptance slug cases: not met (3 failing)

## Surprises
Letters without a Unicode decomposition (Ł, Œ, Þ, Đ) vanish. The spec's rule "letters that
have no ASCII decomposition are spelled out" names only Æ, Ø and ß.

## Suggested next step
Decide how letters without a decomposition should be spelled out in general, not case by case.
