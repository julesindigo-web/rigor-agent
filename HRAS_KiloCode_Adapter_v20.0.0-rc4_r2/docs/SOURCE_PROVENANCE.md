# Upstream source provenance

This adapter copies the complete file inventory from `HRAS_v20.0.0-rc4-candidate-remediated-2026-10-29-r1.zip` into `.hras/source/` without editing those files. The source candidate ZIP's SHA-256 in the handoff context is:

`1c48c7dc3e4a127e8512f9e376f02f2893886f14ca4016aacd4edb5c40be002b`

The adapter's `scripts/validate_adapter.py` rechecks each entry against `HRAS_v20_Package_Manifest.json`. The upstream package validator can verify package identity, generated artifacts, vision provenance and checksums. The source package is evidence of a **candidate** spec only; it does not certify the target Kilo runtime.

Source identity recorded in `.hras/source/HRAS_v20_Version.json`: spec ID `HRAS-AUTO-ENG`, version `20.0.0-rc4`, candidate status `CANDIDATE_NOT_PRODUCTION_READY`, schema registry `OPEN_NOT_FROZEN`. The canonical spec says the parent baseline is `HRAS v18.0.0-rc1`, while the version record says `baseline_version` is `20.0.0-rc3`; the adapter preserves both source claims and flags the semantic relationship for owner clarification rather than editing the upstream artifact.
