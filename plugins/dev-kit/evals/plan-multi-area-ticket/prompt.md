---
max_turns: 8
timeout_seconds: 180
runs: 3
allowed_tools: [Read, Glob, Grep, Skill]
tags: [trigger, plan]
---

Plan this before anyone writes code: add per-user rate limiting to POST /login in our Express
backend, show a "too many attempts" message with a countdown in the React login form, and make
the limit configurable per environment. Break it into pieces we can build in parallel.
