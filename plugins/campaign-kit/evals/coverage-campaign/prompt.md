---
max_turns: 8
timeout_seconds: 180
runs: 3
allowed_tools: [Read, Glob, Grep, Skill]
tags: [trigger, campaign]
---

Our monorepo's test coverage sits around 55%. I want it at 80% within the week without making
CI noticeably slower. Run this as a campaign: several workstreams in parallel, and keep
iterating until we hit it.
