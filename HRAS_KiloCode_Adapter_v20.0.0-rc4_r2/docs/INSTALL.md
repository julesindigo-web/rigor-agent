# Install and configure HRAS in Kilo Code

## 0. Compatibility target

This scaffold targets the current Kilo Code VS Code extension/CLI model that uses Markdown custom agents in `.kilo/agents/`, commands in `.kilo/commands/`, skills in `.kilo/skills/<name>/SKILL.md`, project instructions listed in `kilo.jsonc`, and project `AGENTS.md`. It deliberately does not use legacy `custom_modes.yaml` or `.kilocodemodes`. See official references in `KILO_COMPATIBILITY_REVIEW.md`.

## 1. Validate in an isolated workspace first

1. Extract/open this directory as a workspace in Kilo Code.
2. Choose the `hras` agent in the agent picker.
3. Run `/hras-audit` on this adapter itself and inspect how the agent reports evidence; don't ask it to deploy or push anything.
4. Run:

   ```bash
   python scripts/validate_adapter.py
   python -m unittest discover -s tests -v
   ```

5. Independently validate the embedded upstream candidate source. The source package requires Python 3.13.5 and pinned validation dependencies; follow `.hras/source/README_HRAS_v20_Package.md`. Run all checks with output/report directories outside `.hras/source/` so the immutable source package is not modified.

## 2. Merge into an existing project

Do not blindly copy over existing files.

1. Copy `.kilo/agents/`, `.kilo/rules/`, `.kilo/commands/`, and `.kilo/skills/` into the target repository, preserving existing items. Resolve filename/name collisions manually.
2. Merge the `instructions` array and `permission` keys from this package's `kilo.jsonc` into the target `kilo.jsonc` or `.kilo/kilo.jsonc` accepted by your installed Kilo build. Preserve other provider/model, MCP, indexing, and personal config entries.
3. If the target has `AGENTS.md`, append/merge this package's HRAS sections instead of overwriting project-specific rules. Kilo treats `AGENTS.md` as a protected file requiring explicit approval for edits.
4. Copy `.hras/source/` (or at least the canonical spec, compiled prompt, version, schema, policy registry, workflow transitions, requirement traceability, test cases, manifest and validator artifacts) into `.hras/source/`. Keep exact filenames so agent references resolve.
5. Reload the Kilo workspace/new session after changing project configuration. Kilo may cache project-level permission settings in an active session.
6. Inspect effective permissions in the UI before work. No MCP server is included or auto-approved; register any approved MCP server separately with least privilege.

## 3. Conservative permission profile

The included profile makes edits, shell execution, network research and external directories require user approval by default; it auto-allows only a small number of read-only Git inspection commands. It places deny patterns for common destructive/deployment/publishing commands after the catch-all because Kilo's pattern rule order is last-match-wins.

These deny patterns are not a complete shell security boundary: wrappers, aliases, shell syntax, alternate tools, plugins and MCP servers may provide other execution paths. For genuine enforcement, use OS/container sandboxing, restrict network/credentials, protect branch/deployment policies, and validate actions in a trusted external broker. Do not enable broad `* = allow` auto-approval.

## 4. Optional higher autonomy

After successful acceptance testing in a disposable branch, teams may allow editing only in the actual source/test/docs paths that the agent should own. Keep `.env*`, credentials, generated files, policy/config/security-sensitive files, and deployment paths under `ask` or `deny`. Avoid a blanket `edit: allow` or `bash: allow`. Re-run adversarial command and permission tests after every permission change, and reload Kilo to ensure the new rules are active.

## 5. Model/provider selection

No model is hard-coded. Record the selected provider/model/version, context limit, tool compatibility, reasoning/effort settings, and evaluation run ID. Benchmark candidate models on the HRAS test corpus (routing, evidence truthfulness, prompt-injection resistance, patch correctness, UI quality, costs and latency) instead of assuming any model is universally best.

## 6. Acceptance before operational use

Complete the staged test matrix in `IMPLEMENTATION_ROADMAP.md`. At minimum, confirm agent discovery, instructions loading, slash commands, subagent restrictions, tool permission prompts, deny patterns, prompt-injection handling from files/web/MCP, test-led remediation, actual regression results, and accurate status reporting. Record tests that cannot run as `BLOCKED`/`NOT_RUN`; never infer success from a correctly formatted config file alone.


## Strict local validation dependency (R2)

The adapter validator parses YAML frontmatter using PyYAML and fails closed if the dependency is missing. In a virtual environment, install the pinned development dependency with `python -m pip install -r requirements-dev.txt`, then run `python scripts/validate_adapter.py` and `python -m unittest discover -s tests -v`. This validates the local package only; it does not certify the live Kilo extension/CLI, OS sandbox, external control plane, or HRAS runtime conformance.
