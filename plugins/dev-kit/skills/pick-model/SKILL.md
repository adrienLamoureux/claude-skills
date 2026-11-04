---
name: pick-model
description: Recommend the right Claude model tier (haiku/sonnet/opus) for a described task or set of tasks. Use when the user asks which model to use, wants to optimize agent costs, or describes a workflow and wants model routing advice. Also use proactively when planning a multi-agent pipeline.
---

# Model Tier Advisor

Analyze the task(s) described and recommend the optimal Claude model tier for each, with reasoning.

## Tier Definitions

| Tier | Model | Strengths |
|------|-------|-----------|
| **CTO** | `opus` | Deep multi-step reasoning, architectural tradeoffs, ambiguous/open-ended problems, security analysis, cross-system design |
| **Senior** | `sonnet` | Solid code generation, debugging, feature implementation, API design, research, refactoring — handles most engineering tasks |
| **Junior** | `haiku` | Fast, cheap, reliable for narrow tasks: formatting, boilerplate, docstrings, classification, summarization, simple transforms |

## Analysis Steps

1. **Identify each distinct sub-task** in the user's request (decompose if needed)
2. **For each sub-task**, assess:
   - Does it require multi-step reasoning or tradeoff analysis? → lean `opus`
   - Is it standard engineering work with clear requirements? → `sonnet`
   - Is it a narrow, well-defined, mechanical task? → `haiku`
3. **Flag escalation triggers**: ambiguity, security implications, architectural scope, no clear "right answer"
4. **Flag downgrade opportunities**: any step that is purely mechanical, formatting, or lookup-based

## Output Format

Provide a table:

| Sub-task | Recommended Model | Reason |
|----------|-------------------|--------|
| ... | `haiku/sonnet/opus` | one-line justification |

Then summarize:
- **Default model** for the main agent if running as a single task
- **Pipeline suggestion** if the work benefits from multi-agent decomposition
- **Estimated cost tier**: low / medium / high (relative)

If the user hasn't described a specific task, ask them to describe what they're trying to accomplish.
