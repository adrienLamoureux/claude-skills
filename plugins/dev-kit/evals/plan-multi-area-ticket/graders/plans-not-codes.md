---
type: llm
weight: 1
---

The response treats the request as planning, not implementation. It names a kebab-case slug
and a size (S, M or L) with a reason, and describes or starts a flow in which the repository is
mapped first and a plan is then written with: a frozen contract between the backend and the
frontend (the 429 response shape or equivalent), slices owned by separate paths that can run in
parallel, quality gates per slice, and a merge order. It ends by asking the user to approve the
plan or answer open questions. It does not present finished implementation code.
