---
max_turns: 8
timeout_seconds: 180
runs: 3
allowed_tools: [Read, Glob, Grep, Skill]
tags: [trigger, plan]
---

Implement per-user rate limiting on POST /login in our Express backend, show a "too many
attempts" message with a countdown in the React login form, and make the limit configurable
per environment.
