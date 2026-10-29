---
description: Convert a short idea into a scoped product specification, then build, test, harden, document, and hand off the actual product.
agent: hras
---

Use `IDEA_TO_PRODUCTION`. Understand intended user and outcome; infer reasonable defaults and label material assumptions; ask only for ambiguity that materially changes safety, cost, or product direction and cannot be safely bounded. Inspect the repository before choosing architecture. Define testable acceptance criteria and quality profile; plan a dependency graph; implement complete end-to-end flows rather than stopping at a plan or mockup. Consider security/privacy, accessibility, responsive UX, loading/empty/error states, observability, performance, reliability, migration/rollback, licensing, and maintenance as relevant. Test with the actual project commands and record proof. External effects stay gated. If runtime/environment is unavailable, deliver the usable local subset and clearly report what remains unverified. Use the final handoff template.
