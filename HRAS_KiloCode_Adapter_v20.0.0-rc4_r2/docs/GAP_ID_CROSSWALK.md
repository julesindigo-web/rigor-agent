# HRAS Kilo Gap ID Crosswalk

**Authority:** [`GAP_REGISTRY.json`](GAP_REGISTRY.json), version 1.0.0, as-of 2026-10-29.

The same legacy `KG-xxx` token has different meanings in the earlier integration report and implementation roadmap. `IK-xx` labels in the embedded integration audit are also document-local. Do not treat legacy numbers as global identifiers. Use canonical IDs `HRAS-KILO-001` through `HRAS-KILO-014` for all new findings, dashboards, decisions, and closure evidence.

The registry retains every observed legacy reference with its source document and canonical mapping. One legacy issue may map to multiple canonical concerns when its scope crosses authorization, release control, sandbox, or evidence boundaries. No gap is closed by the act of mapping it.
