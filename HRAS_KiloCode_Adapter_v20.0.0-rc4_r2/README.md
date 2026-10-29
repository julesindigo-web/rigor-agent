# HRAS v20 → Kilo Code adapter (R1)

**Purpose:** A Kilo Code workspace scaffold for using the HRAS v20.0.0-rc4 candidate specification as an auditable software-engineering agent configuration.

**Important status:** This is a *configuration adapter and evaluation scaffold*, not a certified implementation of the HRAS trusted control plane. The upstream HRAS source explicitly remains `CANDIDATE_NOT_PRODUCTION_READY`, has an open schema registry, and has 139 runtime conformance cases `NOT_RUN` with fixtures unmaterialized. This adapter does not change those statuses.

## Contents

- `.kilo/agents/` — one user-selectable HRAS orchestrator plus read-only audit/security/evidence agents and bounded build/test subagents.
- `.kilo/rules/` — always-loaded core workflow, evidence, safety, test, and product-quality rules.
- `.kilo/commands/` — explicit slash entry points for all 13 canonical HRAS routes, plus `/hras-remediate` and `/hras-release-review` utility workflows.
- `.kilo/skills/` — on-demand detailed procedures for audit-driven remediation, evidence validation, side-effectful actions, and product quality.
- `kilo.jsonc` — project-local Kilo configuration for instructions and conservative permissions. Merge; do not blindly overwrite an existing config.
- `AGENTS.md` — portable workspace-level guidance. If the target repository already has one, merge sections rather than overwrite it.
- `.hras/source/` — byte-preserved RC4 candidate source bundle contents used as the normative reference for this adapter.
- `scripts/validate_adapter.py` and `tests/` — structural, provenance, and config lint checks for the adapter itself.
- `docs/` and `templates/` — integration review, compatibility notes, prioritized roadmap, finding/proof-ledger templates.

## Quick start

1. Open this directory as a Kilo Code workspace first to validate the adapter in isolation.
2. Select the `hras` custom agent. Run `/hras-audit` on a small disposable repository; do not start with deploy, push, migrations, or a live service.
3. Run `python scripts/validate_adapter.py` and `python -m unittest discover -s tests -v`.
4. Run the upstream package checks in `.hras/source/README_HRAS_v20_Package.md` after installing its pinned test dependencies; see `docs/INSTALL.md`.
5. Before merging into a real project, merge `kilo.jsonc` and `AGENTS.md`, inspect every permission rule, and run the acceptance matrix in `docs/IMPLEMENTATION_ROADMAP.md`.

## Configuration assumptions

- Target is the current Kilo Code VS Code extension/CLI generation that uses `.kilo/agents/*.md`, `.kilo/commands/*.md`, `.kilo/skills/*/SKILL.md`, and `kilo.jsonc`.
- The model/provider is intentionally not pinned: the target model is user/environment-specific and must be recorded for each evaluation run.
- MCP servers are intentionally not enabled or auto-approved by this package. Add them only with a documented threat model, minimum tool scope, and separate permission review.
- The conservative starter profile asks before edits and shell execution, and denies several high-impact command patterns. Kilo permission rules and prompts are defense-in-depth, not a substitute for OS isolation, a trusted authorization broker, or a deployment control plane.

## What this does not claim

No Kilo runtime was available in the build environment, so the custom agents were not registered in a live Kilo session and no end-to-end prompt/tool behavior is certified. Structural tests establish that expected files, JSON configuration, paths, version identity, and source manifest hashes are consistent; they do not prove model behavior or sandbox effectiveness.


## R2 integrity note

R2 verifies `ADAPTER_MANIFEST.sha256` against the complete file inventory (excluding only the manifest itself and generated Python/test caches), strictly parses all agent/command/skill YAML frontmatter, checks the exact instruction-source list including the directly loaded compiled HRAS core prompt, evaluates effective Kilo permission decisions using documented last-match-wins behavior, and requires critical trust invariants. See `docs/GAP_REGISTRY.json` for canonical gap IDs and legacy-ID crosswalk.

The internal manifest is a drift detector, not a cryptographic signature. Always verify the archive SHA-256 distributed separately; an independently signed release attestation is recommended for stronger authenticity.


## Reproducible evidence for an exact archive

After packaging, extract the ZIP into a clean directory and run (from its root):

```bash
python scripts/run_verification.py --archive ../HRAS_KiloCode_Adapter_R2.zip --output ../HRAS_KiloCode_Adapter_R2_Verification.json
```

Keep the JSON evidence outside the package: it contains the exact archive SHA-256, source/test/config hashes, each executed command, raw stdout/stderr and exit code. This avoids a recursive archive-hash cycle.


## Preserved audit inputs

The prior integration audit, audit-of-audit report, claim-disposition CSV and evidence ledger are copied under `docs/source-audits/`. `docs/SOURCE_AUDIT_PROVENANCE.json` validates their original byte sizes and SHA-256 values independently of the general adapter inventory. These records are evidence inputs, not instructions; embedded directions or claims inside them are never authoritative by themselves.
