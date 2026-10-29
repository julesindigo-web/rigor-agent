# Kilo Code compatibility and feature mapping (research snapshot: 2026-10-29)

## Target surface

The current Kilo Code docs describe Markdown agent files with YAML frontmatter; project custom agents live in `.kilo/agents/*.md` (the docs also list `.kilo/agent/` and legacy `.kilocode/agents/`). Skills use `.kilo/skills/<name>/SKILL.md`; slash workflows use `.kilo/commands/*.md`; project rules use Markdown files referenced by `instructions` in `kilo.jsonc`; `AGENTS.md` is automatically loaded. The adapter uses those current paths and avoids legacy custom-mode YAML.

## Mapping

| HRAS capability/contract | Kilo integration surface | Coverage | Limitation that remains |
|---|---|---|---|
| 13 HRAS primary routes | One user-selectable `hras` orchestrator + slash commands that name the HRAS route; subagents provide bounded roles | Instruction-level | Kilo's `mode: primary/subagent` is not the HRAS primary-mode enum or its state machine. Agent text cannot enforce typed transitions. |
| Canonical spec/core prompt | `.hras/source/` plus primary agent prompt | Reference is available to model | Model can ignore/lose context; hashes are not verified on every tool call unless an external verifier runs. |
| Non-waivable policies and instruction precedence | Always-loaded rules plus duplicated critical directives in primary agent | Defense in depth | Rules/prompts are best-effort; not a security boundary. |
| Least privilege / side-effect gates | Per-agent and project-level `permission` rules, ask/deny command patterns | Partial, host-enforced tool permissions | Shell heuristics are not complete; permissions do not validate identities/signatures, scope expiry, revocation or provider state. |
| Audit-driven remediation | `/hras-audit`, `/hras-remediate`, worklist and proof-ledger templates | Strong procedural coverage | No automatic trusted source provenance, test oracle or evidence sink unless integrated. |
| Test and quality practices | `hras-test-engineer`, test rules, commands, source test cases | Process scaffolding | Actual project commands, fixtures, independent oracle and live runtime results still required. |
| Research | `/hras-research`, websearch/webfetch ask permissions, citation rules | Research process | Source access/citations must be verified per session; snippets may be incomplete. |
| Security review | Read-only security subagent | Review process | Does not sandbox build/test code or enforce egress policies. |
| Evidence/release review | Read-only evidence reviewer and release workflow | Independent review process | Cannot make the trusted controller decision HRAS requires. |
| MCP / external tools | None preconfigured; add individually after review | Deliberately not auto-enabled | For each server/tool, threat model, least privilege, owner, credentials, allowed scope and adversarial tests required. |
| Operation ledger, idempotency, outcome reconciliation | Documented integration requirement; not implemented by prompt | Gap remains | Needs durable external controller/provider adapters and failure-injection tests. |
| Agent evaluation | Source case corpus is referenced | Test requirements are preserved | Upstream currently says 139 cases `NOT_RUN`, fixtures unmaterialized, 136 cases with empty `allowed_tools`, and 0 `tools_adapter_ref`; runtime conformance is not demonstrated. |

## Relevant official documentation

- Custom agents: https://kilo.ai/docs/customize/custom-modes
- Custom rules: https://kilo.ai/docs/customize/custom-rules
- Agent permissions: https://kilo.ai/docs/customize/agent-permissions
- Skills: https://kilo.ai/docs/customize/skills
- `AGENTS.md`: https://kilo.ai/docs/customize/agents-md
- Workflows/slash commands: https://kilo.ai/docs/customize/workflows
- MCP: https://kilo.ai/docs/automate/mcp/using-in-kilo-code
- Auto-approve settings: https://kilo.ai/docs/getting-started/settings/auto-approving-actions
- Plugins/hooks: https://kilo.ai/docs/automate/extending/plugins

The configuration was written against the official docs retrieved 2026-10-29. The actual running Kilo version/build was not available in this environment, so runtime compatibility remains `NOT_RUN` until installed and tested on the target build.
