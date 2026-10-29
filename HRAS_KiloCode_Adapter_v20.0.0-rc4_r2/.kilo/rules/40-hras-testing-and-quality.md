# HRAS testing, regression, and product quality

1. Discover the repository's actual test/lint/typecheck/build commands before inventing commands or dependencies.
2. Bug fix = regression test first. Prove it fails for the bug, then passes after the correction. Test changes require justification; no deleting/skipping/weakening/xfailing/hard-coding to create green.
3. Use risk-based test depth: affected tests first; full suite and smoke for standard changes; integration/e2e/failure injection plus independent re-check for critical-risk changes. Include the touched surface's null/edge/error/timeout/concurrency/backward-compatibility cases.
4. Record exact commands, environment, exit code, output, test count, skipped/xfail counts and artifact location. Missing tools/fixture means `BLOCKED` or `NOT_RUN`, never pass.
5. Product quality goes beyond compiling: validate user intent, acceptance criteria, complete workflows, API/data contracts, accessibility/responsiveness, error/loading/empty states, security/privacy, performance against measured goals, operability, documentation, licensing, and maintainability where applicable.
6. Do not over-engineer. State the quality profile, trade-offs, costs, assumptions, and acceptance threshold; add complexity only when it is justified by evidence and requirements.
