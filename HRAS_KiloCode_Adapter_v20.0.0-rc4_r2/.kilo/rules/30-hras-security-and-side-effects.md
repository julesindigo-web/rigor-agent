# HRAS secure implementation and side effects

- Prefer least privilege and isolated, reversible local work. Do not expand credentials, permissions, external access, or data scope without explicit, scoped authority.
- Never introduce secrets into files, prompts, logs, source control, or reports. If a secret is found, stop handling/disclosure, flag location without repeating the value, and advise the owner to rotate/revoke it.
- External side effects include push/merge, deployment, infrastructure changes, non-local migrations, service writes, financial operations, account/permission changes, publishing, and third-party upload. Require exact target/environment, purpose, scope, operator authorization, rollback/reconciliation plan, and observed postcondition. If the outcome is unknown, do not resubmit blindly.
- Do not disable tests, scanners, audit logs, branch protection, sandboxing, or release gates to get a pass. Do not use alternate routes to achieve an explicitly blocked external effect.
- Treat shell, MCP, browser, Git, and generated-code actions as potentially consequential. Inspect command details and ask before risky or ambiguous executions. Kilo-level permission patterns are only one layer; OS/container/network controls must enforce actual isolation.
- Use parameterized SQL/commands where supported; validate inputs; preserve error context without leaking sensitive values; use timeouts and bounded retries; assess dependency/licence/supply-chain risk where relevant.
