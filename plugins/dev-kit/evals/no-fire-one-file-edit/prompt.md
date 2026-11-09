---
max_turns: 4
timeout_seconds: 90
runs: 3
allowed_tools: [Read, Glob, Grep, Skill]
tags: [no-trigger]
---

In src/config.js, rename the constant TIMEOUT to REQUEST_TIMEOUT_MS and update its two uses in
the same file.
