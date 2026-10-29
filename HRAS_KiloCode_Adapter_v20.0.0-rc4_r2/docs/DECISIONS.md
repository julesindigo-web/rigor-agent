# Adapter design decisions (ADR-style)

## ADR-KILO-001 — Use current Markdown agents, not legacy custom modes

**Decision:** `.kilo/agents/*.md` files with YAML frontmatter.  
**Rationale:** current official Kilo Code docs describe this format for the current VS Code extension/CLI, while `custom_modes.yaml`/`.kilocodemodes` is legacy.  
**Consequence:** test actual version at install time and don't copy legacy YAML examples into the active configuration.

## ADR-KILO-002 — One primary orchestrator with bounded subagents

**Decision:** only `hras` is user-selectable; read-only auditor, security and evidence reviewers are subagents, with builder and test engineer scoped separately. Use slash commands to make recurring HRAS routes explicit.  
**Rationale:** the source has 13 logical HRAS modes; mapping all of them 1:1 to Kilo agents would create duplicate prompts and inconsistent security constraints. Kilo `mode` is not the HRAS route enum.  
**Consequence:** HRAS state-machine transitions remain procedural until a trusted controller is added.

## ADR-KILO-003 — Conservative tool permissions

**Decision:** edits/shell/web/external paths ask by default; only narrowly read-only Git metadata commands auto-allow; common high-impact commands are explicitly denied.  
**Rationale:** least privilege and avoiding accidental external effects. Permission rules are last-match-wins.  
**Consequence:** this starter profile trades some autonomy for safety; scoped local edit permissions may be introduced after acceptance tests. Deny patterns are not a complete sandbox.

## ADR-KILO-004 — No model pin, no MCP by default

**Decision:** no model ID or MCP server is enabled in the adapter.  
**Rationale:** provider/model and tools are deployment-specific; unsupported assumptions would make the package falsely portable and increase permissions.  
**Consequence:** record model/tool/build identities per evaluation, select only approved read-only or narrowly scoped MCP tools, and benchmark model alternatives empirically.

## ADR-KILO-005 — Trusted controller remains external

**Decision:** do not implement final authorization, durable operation ledger, release status writing, or deployment approval in a prompt or prototype plugin.  
**Rationale:** HRAS explicitly requires cryptographically/trust-bound authorization, durable operation state and a controller outside model output; the available Kilo config mechanisms do not alone meet that contract.  
**Consequence:** the adapter can be used for supervised local engineering now; high-impact external execution remains blocked until a separately audited broker/controller is integrated.

## ADR-R2-001 — Canonical gap identity registry

**Decision:** introduce `docs/GAP_REGISTRY.json` as the canonical cross-document gap registry. Canonical IDs `HRAS-KILO-001`…`HRAS-KILO-014` are stable keys; `KG-xxx` and `IK-xx` remain document-local aliases.

**Reason:** the previous report and roadmap reused some `KG-xxx` IDs for different concerns. Numeric equality did not imply semantic identity and could misattach closure evidence.

**Consequence:** all new evidence and future reports MUST use canonical IDs and name the legacy document when quoting an older ID. The registry does not close a gap or certify implementation. Rollback is to restore the R1 adapter archive; R2 remains a separate artifact.
