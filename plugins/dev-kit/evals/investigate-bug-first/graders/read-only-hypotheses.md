---
type: llm
weight: 1
---

The response starts a read-only investigation. It aims to reproduce the failure, works towards
several ranked hypotheses (for example data-dependent input, permissions, a recent change on the
export path) backed by file or log evidence, and proposes the smallest experiment that would
tell them apart. It does not edit code or propose a fix as the first step.
