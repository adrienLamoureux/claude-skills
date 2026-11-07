# Check — round 1

Commands run from the repo root, one at a time.

- `python3 tools/score.py spec` → `spec/test_cells.py 8/14`, `spec/test_durations.py 24/24`,
  `spec/test_slug.py 10/10`, `spec total __SPEC__`
- `python3 tools/accept.py` → `acceptance total __ACCEPT__`; the slug failures are
  test_slug_01 (Łódź), test_slug_02 (Œuvre complète) and test_slug_05 (Þór Đaković); the rest
  are cells cases (not yet worked on).
- `python3 tools/score.py tests` → `tests total 7/7`
- `git status --short` → `textkit/durations.py`, `textkit/slug.py` modified; nothing outside
  the lanes.

Lanes: durations reproduced 24/24, pass. slugify reproduced 10/10 on the spec, but its three
acceptance cases fail as the report says, so partial.

```json check-manifest
{
  "round": 1,
  "lanes": [{"lane": "durations", "status": "pass"}, {"lane": "slugify", "status": "partial"}],
  "criteria": [{"id": "spec-pass", "value": "__SPEC__", "met": false},
               {"id": "acceptance-pass", "value": "__ACCEPT__", "met": false},
               {"id": "guard-tests", "value": "7/7", "met": true}],
  "regressions": []
}
```
