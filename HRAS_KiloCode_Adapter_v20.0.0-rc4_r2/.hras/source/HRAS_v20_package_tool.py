#!/usr/bin/env python3
"""Deterministic HRAS candidate package identity, inventory and checksum tool.

This is a local packaging/validation helper. It does not deploy, publish, or authorize release.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re, sys
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator
from HRAS_v20_reference_controller import strict_json_loads, case_hash, validate_contract, validate_workflow_transition_registry, _workflow_cycle_after_retry_edges

ROOT = Path(__file__).resolve().parent
MANIFEST = 'HRAS_v20_Package_Manifest.json'
CHECKSUMS = 'HRAS_v20_CHECKSUMS.txt'
VERSION_FILE = 'HRAS_v20_Version.json'
EXCLUDED_FROM_MANIFEST = {MANIFEST, 'HRAS_v20_Package_Manifest.md', CHECKSUMS}
DEFAULT_ADDITIONS = ['HRAS_v20_Version.json', 'HRAS_v20_Module_IO_Registry.json', 'HRAS_v20_package_tool.py', 'tests/test_rc4_plan_closure.py', 'HRAS_v20_Workflow_Transitions.json', 'HRAS_v20_Governance_Decisions.json', 'HRAS_v20_North_Star_Subrequirement_Map.json', 'HRAS_v20_Workflow_Coverage_Report.json', 'Visi HRAS.md', 'HRAS_v20_Vision_Provenance.json', 'HRAS_v20_Vision_Clause_Inventory.csv', '.python-version', 'requirements-lock.txt']


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(root: Path, name: str) -> Any:
    return strict_json_loads((root / name).read_text(encoding='utf-8'))


def safe_relative_path(raw: str) -> bool:
    p = Path(raw)
    return bool(raw) and not p.is_absolute() and '..' not in p.parts and '\\' not in raw



def generate_workflow_coverage_report(root: Path) -> dict[str, Any]:
    """Derive a static reachability/cycle report from the canonical workflow registry."""
    workflow = load_json(root, 'HRAS_v20_Workflow_Transitions.json')
    schemas = load_json(root, 'HRAS_v20_Contract_Schemas.json')
    modes = []
    terminal = set(workflow.get('terminal_states', []))
    retry_by_mode: dict[str, set[tuple[str, str]]] = {}
    for item in workflow.get('retry_edges', []):
        retry_by_mode.setdefault(item.get('primary_mode'), set()).add((item.get('from_state'), item.get('to_state')))
    for entry in sorted(workflow.get('modes', []), key=lambda x: x.get('primary_mode', '')):
        mode = entry['primary_mode']
        edges = {(x['from_state'], x['to_state']) for x in entry.get('transitions', [])}
        nodes = {x for edge in edges for x in edge}
        starts = {'RECEIVED'} & nodes
        reachable = set(starts)
        changed = True
        while changed:
            changed = False
            for source, target in edges:
                if source in reachable and target not in reachable:
                    reachable.add(target); changed = True
        reachable_terminals = sorted(terminal & reachable)
        modes.append({
            'primary_mode': mode,
            'transition_count': len(edges),
            'retry_guarded_edge_count': len(retry_by_mode.get(mode, set())),
            'state_count': len(nodes),
            'reachable_state_count': len(reachable),
            'unreachable_states': sorted(nodes - reachable),
            'reachable_terminal_states': reachable_terminals,
        })
    cycle_free = all(
        not _workflow_cycle_after_retry_edges(
            item['primary_mode'],
            {(x['from_state'], x['to_state']) for x in item.get('transitions', [])},
            retry_by_mode.get(item['primary_mode'], set()),
        ) for item in workflow.get('modes', [])
    )
    all_modes = set(x['primary_mode'] for x in workflow.get('modes', [])) == set(schemas['$defs']['RouteDecision']['properties']['primary_mode']['enum'])
    all_attributed = all(isinstance(a, str) and a and isinstance(b, str) and b and a != b
                         for mode in workflow.get('modes', []) for t in mode.get('transitions', [])
                         for a, b in [(t.get('from_state'), t.get('to_state'))])
    raw_hash = sha256(root / 'HRAS_v20_Workflow_Transitions.json')
    return {
        'report_id': 'HRAS-WORKFLOW-COVERAGE-REPORT',
        'spec_id': workflow.get('spec_id'),
        'spec_version': workflow.get('spec_version'),
        'registry_sha256': 'sha256:' + raw_hash,
        'mode_count': len(modes),
        'transition_count': sum(x['transition_count'] for x in modes),
        'retry_guarded_edge_count': len(workflow.get('retry_edges', [])),
        'prohibited_shortcut_count': len(workflow.get('prohibited_shortcuts', [])),
        'modes': modes,
        'all_modes_covered': all_modes and all(not x['unreachable_states'] for x in modes),
        'all_transitions_attributed': all_attributed,
        'all_cycles_guarded': cycle_free,
        'analysis_scope': 'STATIC_GRAPH_ONLY',
        'limitations': [
            'Generated from the canonical transition registry; does not execute runtime paths or prove enforcement by an external production controller.',
            'Reachability starts at RECEIVED; unreachable states are surfaced explicitly.',
            'Retry edges are bounded only when callers use retry_transition_allowed with trusted durable counters; production integration remains external.'
        ],
    }


def refresh_generated_views(root: Path) -> None:
    """Regenerate schema/policy explanatory views and graph report from canonical sources."""
    schema = load_json(root, 'HRAS_v20_Contract_Schemas.json')
    spec_path = root / 'HRAS_v20_Canonical_Autonomous_Production_Grade_Spec.md'
    spec = spec_path.read_text(encoding='utf-8')
    heading = '## Annex A — Machine-readable control-plane schemas'
    next_heading = '## Annex B — Policy registry reference (generated, explanatory only)'
    if heading not in spec or next_heading not in spec:
        raise ValueError('canonical specification missing generated Annex A/B headings')
    a = spec.index(heading)
    b = spec.index(next_heading, a)
    annex = spec[a:b]
    marker = '```json\n'
    if marker not in annex:
        raise ValueError('Annex A has no JSON code fence')
    fs = a + spec[a:b].index(marker) + len(marker)
    fe = spec.index('\n```', fs)
    schema_text = json.dumps(schema, ensure_ascii=False, indent=2)
    spec = spec[:fs] + schema_text + spec[fe:]
    # Regenerate only a provenance marker in explanatory Annex B; executable policy remains the sole JSON source.
    policy_hash = sha256(root / 'HRAS_v20_Policy_Registry.json')
    b = spec.index(next_heading)
    c = spec.find('\n## Annex C', b)
    if c < 0: raise ValueError('Annex B end marker (Annex C) missing')
    annex_b = spec[b:c]
    source_line = f'**Registry SHA-256 (generated):** `sha256:{policy_hash}`'
    existing = re.search(r'^\*\*Registry SHA-256 \(generated\):\*\* `sha256:[0-9a-f]{64}`$', annex_b, re.M)
    if existing:
        annex_b = annex_b[:existing.start()] + source_line + annex_b[existing.end():]
    else:
        # Insert after the normative-status callout paragraph, before explanatory details.
        match = re.search(r'(> \*\*Normative status.*?\n\n)', annex_b, re.S)
        if not match: raise ValueError('Annex B normative status paragraph missing')
        annex_b = annex_b[:match.end()] + source_line + '\n\n' + annex_b[match.end():]
    spec = spec[:b] + annex_b + spec[c:]
    spec_path.write_text(spec, encoding='utf-8')
    report = generate_workflow_coverage_report(root)
    (root / 'HRAS_v20_Workflow_Coverage_Report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Render the registry-freeze state from the canonical version source.
    version = load_json(root, VERSION_FILE)
    status_line = f"**Schema registry status:** `{version.get('schema_registry_status', 'MISSING')}`  "
    readme_path = root / 'README_HRAS_v20_Package.md'
    readme = readme_path.read_text(encoding='utf-8')
    if re.search(r'^\*\*Schema registry status:\*\* `[^`]+`  $', readme, re.M):
        readme = re.sub(r'^\*\*Schema registry status:\*\* `[^`]+`  $', status_line, readme, count=1, flags=re.M)
    else:
        marker = '\n## Start here'
        if marker not in readme: raise ValueError('README Start here heading missing for registry-status rendering')
        readme = readme.replace(marker, '\n' + status_line + '\n' + marker, 1)
    readme_path.write_text(readme, encoding='utf-8')


def verify_canonical_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        schemas = load_json(root, 'HRAS_v20_Contract_Schemas.json')
        trace = load_json(root, 'HRAS_v20_Requirement_Traceability.json')
        tests = load_json(root, 'HRAS_v20_Test_Cases.json')
        workflow = load_json(root, 'HRAS_v20_Workflow_Transitions.json')
        north = load_json(root, 'HRAS_v20_North_Star_Subrequirement_Map.json')
        coverage = load_json(root, 'HRAS_v20_Workflow_Coverage_Report.json')
        for name, value in [('NorthStarSubrequirementMap', north), ('WorkflowCoverageReport', coverage)]:
            errors.extend(f'{name}: {e.json_path}: {e.message}' for e in validate_contract(schemas, name, value))
        req_ids = {x.get('requirement_id') for x in trace.get('requirements', [])}
        test_ids = {x.get('test_id') for x in tests.get('cases', [])}
        if any(not set(m.get('requirement_refs', [])) <= req_ids for m in north.get('concept_mappings', [])):
            errors.append('North Star map contains unknown requirement references')
        if any(not set(m.get('test_ids', [])) <= test_ids for m in north.get('concept_mappings', [])):
            errors.append('North Star map contains unknown test references')
        if north.get('core_north_stars') != [f'HRAS-NS-{i:03d}' for i in range(1, 6)]:
            errors.append('North Star map must retain exactly canonical NS-001 through NS-005 in order')
        spec = (root / 'HRAS_v20_Canonical_Autonomous_Production_Grade_Spec.md').read_text(encoding='utf-8')
        for ns in north.get('core_north_stars', []):
            if ns not in spec: errors.append(f'North Star map core ID absent from spec: {ns}')
        if north.get('independent_review_status') != 'PENDING':
            errors.append('North Star map must disclose independent semantic review remains pending')
        expected_coverage = generate_workflow_coverage_report(root)
        if coverage != expected_coverage: errors.append('workflow coverage report is stale or not exactly derived from canonical registry')
        workflow_errors = validate_workflow_transition_registry(workflow, schemas)
        errors.extend(f'workflow registry: {e}' for e in workflow_errors)
        # D-12 is package-bound: policy registry source hash in Annex B must be exact.
        annex_b = spec[spec.index('## Annex B — Policy registry reference (generated, explanatory only)'):spec.index('## Annex C — v20 implementation and verification invariants')]
        policy_hash = 'sha256:' + sha256(root / 'HRAS_v20_Policy_Registry.json')
        if f'**Registry SHA-256 (generated):** `{policy_hash}`' not in annex_b:
            errors.append('Annex B generated policy-registry source hash is stale')
        # Package canonical source set must include the derived map and coverage report.
        manifest = load_json(root, MANIFEST)
        paths = {x.get('path') for x in manifest.get('files', []) if isinstance(x, dict)}
        required = {'HRAS_v20_North_Star_Subrequirement_Map.json', 'HRAS_v20_Workflow_Coverage_Report.json'}
        if not required <= paths: errors.append(f'manifest omits canonical generated artifacts: {sorted(required-paths)}')
    except Exception as exc:
        errors.append(f'canonical artifact verification unavailable: {type(exc).__name__}: {exc}')
    return errors


def verify_version_identity(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        version = load_json(root, VERSION_FILE)
        active = version.get('spec_version')
        spec_id = version.get('spec_id')
        if not isinstance(active, str) or not re.fullmatch(r'20\.0\.0-rc[0-9]+', active):
            return ['version source has invalid spec_version']
        if spec_id != 'HRAS-AUTO-ENG': errors.append('version source spec_id must be HRAS-AUTO-ENG')
        schemas = load_json(root, 'HRAS_v20_Contract_Schemas.json')
        policy = load_json(root, 'HRAS_v20_Policy_Registry.json')
        trace = load_json(root, 'HRAS_v20_Requirement_Traceability.json')
        tests = load_json(root, 'HRAS_v20_Test_Cases.json')
        module_io = load_json(root, 'HRAS_v20_Module_IO_Registry.json')
        manifest = load_json(root, MANIFEST)
        schema_registry_status = version.get('schema_registry_status')
        if schema_registry_status not in {'OPEN_NOT_FROZEN', 'FROZEN'}:
            errors.append(f'invalid or missing schema_registry_status: {schema_registry_status!r}')
        if manifest.get('schema_registry_status') != schema_registry_status:
            errors.append('package manifest schema_registry_status does not match version source')
        spec_text = (root / 'HRAS_v20_Canonical_Autonomous_Production_Grade_Spec.md').read_text(encoding='utf-8')
        prompt_text = (root / 'HRAS_v20_Compiled_Core_Prompt.md').read_text(encoding='utf-8')
        readme_text = (root / 'README_HRAS_v20_Package.md').read_text(encoding='utf-8')
        manifest_text = (root / 'HRAS_v20_Package_Manifest.md').read_text(encoding='utf-8')
        expected = {
            'schema $id': (schemas.get('$id'), f'urn:hras:schemas:{active}'),
            'schema $comment': (schemas.get('$comment'), f'Normative control-plane schema registry for spec_id HRAS-AUTO-ENG, version {active}. The package validator must pin this artifact by SHA-256. Domain payload schemas may extend these contracts but cannot weaken them.'),
            'policy version': (policy.get('version'), active),
            'trace spec_version': (trace.get('spec_version'), active),
            'test registry spec_version': (tests.get('spec_version'), active),
            'module IO spec_version': (module_io.get('spec_version'), active),
            'package manifest version': (manifest.get('version'), active),
        }
        for label, (actual, want) in expected.items():
            if actual != want: errors.append(f'{label} mismatch: expected {want!r}, got {actual!r}')
        identity_texts=[('canonical spec',spec_text),('compiled prompt',prompt_text),('README',readme_text),('package manifest Markdown',manifest_text)]
        for label, text in identity_texts:
            if active not in text: errors.append(f'{label} does not identify active version {active}')
            # A correct active-version token elsewhere must not mask a stale release-state
            # sentence. This is the exact failure mode audited in F-06.
            for match in re.finditer(r'HRAS\s+v(?P<version>20\.0\.0-rc[0-9]+)\s+remains\s+`CANDIDATE`', text):
                declared=match.group('version')
                if declared != active:
                    errors.append(f'{label} contains stale release-state identity {declared}; active version is {active}')
        freeze_label=f"**Schema registry status:** `{schema_registry_status}`"
        if freeze_label not in readme_text: errors.append('README does not render canonical schema_registry_status')
        if freeze_label not in manifest_text: errors.append('package manifest Markdown does not render canonical schema_registry_status')
        # Current active identities must not retain a stale release reference in normative identity fields.
        if f'urn:hras:schemas:20.0.0-rc3' in schemas.get('$id',''):
            errors.append('schema id retains rc3 identity')
        # The source version record intentionally retains baseline_version as provenance; other current identity fields do not.
        for case in tests.get('cases',[]):
            if case.get('case_hash') != case_hash(case): errors.append(f"test case hash mismatch: {case.get('test_id')}")
            if case.get('spec_version') not in (None, active): errors.append(f"test case {case.get('test_id')} has mismatched spec_version")
        if tests.get('case_count') != len(tests.get('cases',[])):
            errors.append('test registry case_count is not derived from current cases')
        Draft202012Validator.check_schema(schemas)
        workflow=load_json(root,'HRAS_v20_Workflow_Transitions.json')
        errors.extend(f'workflow registry: {e.json_path}: {e.message}' for e in Draft202012Validator({'$schema':schemas['$schema'],'$ref':'#/$defs/WorkflowTransitionRegistry','$defs':schemas['$defs']}).iter_errors(workflow))
        if workflow.get('spec_version')!=active: errors.append('workflow transition registry version mismatch')
        if workflow.get('mode_count')!=len(schemas['$defs']['RouteDecision']['properties']['primary_mode']['enum']): errors.append('workflow mode_count mismatch')
        if set(m.get('primary_mode') for m in workflow.get('modes',[]))!=set(schemas['$defs']['RouteDecision']['properties']['primary_mode']['enum']): errors.append('workflow registry mode set mismatch')
        decisions=load_json(root,'HRAS_v20_Governance_Decisions.json')
        if decisions.get('candidate_version')!=active: errors.append('governance decision record version mismatch')
        if 'No cryptographic signature or external identity-provider verification was available' not in decisions.get('identity_and_signature_limit',''): errors.append('governance decision record must disclose unverified cryptographic identity')
        if not set(f'D-{i:02d}' for i in range(1,16)) <= set(d.get('id') for d in decisions.get('decisions',[])) or sum(1 for d in decisions.get('decisions',[]) if d.get('id','').startswith('D-'))!=15: errors.append('governance decision record must cover D-01 through D-15 exactly')
        if not any(d.get('id')=='MR-43' for d in decisions.get('decisions',[])): errors.append('governance decision record missing MR-43 disposition')
        if not all(isinstance(d.get('decision'),str) and d.get('basis') for d in decisions.get('decisions',[])): errors.append('governance decision record contains incomplete decision/basis fields')
    except Exception as exc:
        errors.append(f'identity check could not complete: {type(exc).__name__}: {exc}')
    return errors


def verify_manifest_inventory(root: Path, strict_root: bool = False) -> list[str]:
    errors: list[str] = []
    try:
        manifest = load_json(root, MANIFEST)
        entries = manifest.get('files')
        if not isinstance(entries, list): return ['manifest files must be an array']
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                errors.append('manifest entry is not an object'); continue
            name = entry.get('path')
            if not isinstance(name, str) or not safe_relative_path(name):
                errors.append(f'unsafe manifest path: {name!r}'); continue
            if name in seen: errors.append(f'duplicate manifest path: {name}')
            seen.add(name)
            path = root / name
            if not path.is_file():
                errors.append(f'manifest path missing: {name}'); continue
            if entry.get('size_bytes') != path.stat().st_size:
                errors.append(f'size mismatch: {name}; expected={entry.get("size_bytes")} actual={path.stat().st_size}')
            digest = sha256(path)
            if entry.get('sha256') != digest:
                errors.append(f'SHA-256 mismatch: {name}')
        required = {'HRAS_v20_Version.json','HRAS_v20_Module_IO_Registry.json','HRAS_v20_Canonical_Autonomous_Production_Grade_Spec.md','HRAS_v20_Contract_Schemas.json','HRAS_v20_Policy_Registry.json','HRAS_v20_Requirement_Traceability.json','HRAS_v20_Test_Cases.json','HRAS_v20_static_validator.py','HRAS_v20_reference_controller.py','HRAS_v20_package_tool.py','tests/test_rc4_plan_closure.py','HRAS_v20_Workflow_Transitions.json','HRAS_v20_Governance_Decisions.json','HRAS_v20_North_Star_Subrequirement_Map.json','HRAS_v20_Workflow_Coverage_Report.json'}
        required |= {'HRAS_v20_North_Star_Subrequirement_Map.json','HRAS_v20_Workflow_Coverage_Report.json','Visi HRAS.md','HRAS_v20_Vision_Provenance.json','HRAS_v20_Vision_Clause_Inventory.csv','.python-version','requirements-lock.txt'}
        missing_required = required - seen
        if missing_required: errors.append(f'manifest omits required package paths: {sorted(missing_required)}')
        if strict_root:
            allowed = seen | EXCLUDED_FROM_MANIFEST
            actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
            extras = actual - allowed
            if extras: errors.append(f'clean package contains unmanifested files: {sorted(extras)}')
            missing_meta = EXCLUDED_FROM_MANIFEST - actual
            if missing_meta: errors.append(f'clean package missing required metadata files: {sorted(missing_meta)}')
    except Exception as exc:
        errors.append(f'manifest inventory could not complete: {type(exc).__name__}: {exc}')
    return errors


def verify_checksum_file(root: Path) -> list[str]:
    errors=[]
    try:
        seen=set()
        for number,line in enumerate((root/CHECKSUMS).read_text(encoding='utf-8').splitlines(),1):
            if not line.strip(): continue
            m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line)
            if not m: errors.append(f'{CHECKSUMS}:{number}: malformed checksum line'); continue
            expected,name=m.groups()
            if not safe_relative_path(name): errors.append(f'{CHECKSUMS}:{number}: unsafe path {name}'); continue
            if name in seen: errors.append(f'{CHECKSUMS}:{number}: duplicate path {name}')
            seen.add(name)
            path=root/name
            if not path.is_file(): errors.append(f'{CHECKSUMS}:{number}: listed path missing: {name}'); continue
            if sha256(path)!=expected: errors.append(f'{CHECKSUMS}:{number}: SHA-256 mismatch: {name}')
        for mandatory in [MANIFEST,'HRAS_v20_Package_Manifest.md']:
            if mandatory not in seen: errors.append(f'{CHECKSUMS} omits {mandatory}')
        manifest=load_json(root,MANIFEST)
        manifest_paths={x.get('path') for x in manifest.get('files',[]) if isinstance(x,dict)}
        missing_coverage=manifest_paths-seen
        if missing_coverage: errors.append(f'{CHECKSUMS} omits manifest-listed package files: {sorted(missing_coverage)}')
        expected_paths=manifest_paths | {MANIFEST, 'HRAS_v20_Package_Manifest.md'}
        unexpected=seen-expected_paths
        if unexpected: errors.append(f'{CHECKSUMS} lists paths outside the manifest/checksum policy: {sorted(unexpected)}')
        uncovered=expected_paths-seen
        if uncovered: errors.append(f'{CHECKSUMS} does not exactly cover manifest plus metadata paths: {sorted(uncovered)}')
    except Exception as exc:
        errors.append(f'checksum validation could not complete: {type(exc).__name__}: {exc}')
    return errors


def verify_module_registry(root: Path) -> list[str]:
    errors=[]
    try:
        schemas=load_json(root,'HRAS_v20_Contract_Schemas.json')
        registry=load_json(root,'HRAS_v20_Module_IO_Registry.json')
        Draft202012Validator.check_schema(schemas)
        schema={'$schema':schemas['$schema'],'$ref':'#/$defs/ModuleIOContractRegistry','$defs':schemas['$defs']}
        validator=Draft202012Validator(schema)
        errors.extend(f'module IO registry: {e.json_path}: {e.message}' for e in validator.iter_errors(registry))
        ids=[]
        for module in registry.get('modules',[]):
            mid=module.get('module_id'); ids.append(mid)
            for field in ('input_schema_id','output_schema_id'):
                sid=module.get(field)
                if sid not in schemas.get('$defs',{}): errors.append(f'{mid}: {field} references missing schema {sid!r}')
        if len(ids)!=len(set(ids)): errors.append('module IDs are not unique')
        wanted={'IdeaExpansion','BrandContentSpec','EvidenceLedger','LifecycleAndOperabilitySpec','SecurityPostureReport'}
        missing=wanted-set(schemas.get('$defs',{}))
        if missing: errors.append(f'missing required module contracts {sorted(missing)}')
        outputs={m.get('output_schema_id') for m in registry.get('modules',[])}
        if not wanted <= outputs: errors.append(f'module registry omits output mapping for {sorted(wanted-outputs)}')
        if not {'LIFECYCLE','SECURITY_POSTURE'} <= set(ids): errors.append('module registry omits LIFECYCLE or SECURITY_POSTURE')
        if not any(m.get('module_id')=='INTENT' and m.get('input_schema_id')=='IntentCaptureRequest' and m.get('output_schema_id')=='IntentRecord' for m in registry.get('modules',[])):
            errors.append('module registry omits explicit INTENT input/output binding')
    except Exception as exc:
        errors.append(f'module registry verification could not complete: {type(exc).__name__}: {exc}')
    return errors


def verify_static_report_hashes(root: Path) -> list[str]:
    errors=[]
    try:
        report=load_json(root,'HRAS_v20_Static_Validation_Report.json')
        if report.get('status')!='PASS': errors.append('stored static validation report is not PASS')
        expected=report.get('input_sha256')
        if not isinstance(expected,dict) or not expected: return errors+['static validation report has no input_sha256 map']
        for name,digest in expected.items():
            path=root/name
            if not path.is_file(): errors.append(f'static report input is missing: {name}')
            elif sha256(path)!=digest: errors.append(f'static report is stale for source input: {name}')
        if report.get('report_version')!=load_json(root,VERSION_FILE).get('spec_version'):
            errors.append('static report version does not match active version source')
    except Exception as exc:
        errors.append(f'static report verification could not complete: {type(exc).__name__}: {exc}')
    return errors

def verify_vision_provenance(root: Path) -> list[str]:
    """Verify the pinned vision source and its line-preserving inventory, not semantic equivalence."""
    errors=[]
    try:
        source=root/'Visi HRAS.md'
        metadata=load_json(root,'HRAS_v20_Vision_Provenance.json')
        raw=source.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        text=raw.decode('utf-8')
        if metadata.get('source_path')!='Visi HRAS.md': errors.append('vision provenance source_path is not canonical')
        if metadata.get('source_sha256')!=digest: errors.append('vision source SHA-256 does not match provenance')
        if metadata.get('source_size_bytes')!=len(raw): errors.append('vision source byte size does not match provenance')
        if metadata.get('source_line_count')!=len(text.splitlines()): errors.append('vision source line count does not match provenance')
        if metadata.get('semantic_mapping_status')!='PARTIAL' or metadata.get('independent_review_status')!='PENDING':
            errors.append('vision provenance must retain PARTIAL mapping and PENDING independent review until reviewed')
        with (root/'HRAS_v20_Vision_Clause_Inventory.csv').open(encoding='utf-8',newline='') as f:
            rows=list(csv.DictReader(f))
        lines=text.splitlines()
        if len(rows)!=len(lines): errors.append('vision clause inventory line count does not match source')
        for index,(row,line) in enumerate(zip(rows,lines),1):
            if row.get('line_number')!=str(index) or row.get('source_text')!=line:
                errors.append(f'vision clause inventory does not match source line {index}')
                break
            if row.get('mapping_status')!='UNMAPPED_PENDING_INDEPENDENT_REVIEW':
                errors.append(f'vision inventory line {index} claims unreviewed semantic mapping')
                break
    except Exception as exc:
        errors.append(f'vision provenance verification unavailable: {type(exc).__name__}: {exc}')
    return errors


def verify_package(root: Path, strict_root: bool=False) -> dict[str, Any]:
    groups={
        'version_identity':verify_version_identity(root),
        'module_io_registry':verify_module_registry(root),
        'manifest_inventory':verify_manifest_inventory(root,strict_root=strict_root),
        'checksums':verify_checksum_file(root),
        'static_report_hashes':verify_static_report_hashes(root),
        'canonical_generated_artifacts':verify_canonical_artifacts(root),
        'vision_provenance':verify_vision_provenance(root),
    }
    failures=[f'{group}: {e}' for group,items in groups.items() for e in items]
    return {'status':'PASS' if not failures else 'FAIL','root':str(root),'checks':{k:{'status':'PASS' if not v else 'FAIL','errors':v} for k,v in groups.items()},'failures':failures}


def refresh_manifest(root: Path, report: dict[str, Any] | None=None) -> None:
    refresh_generated_views(root)
    manifest=load_json(root,MANIFEST)
    version=load_json(root,VERSION_FILE)
    report_path=root/'HRAS_v20_Static_Validation_Report.json'
    if report is None and report_path.is_file():
        try:
            candidate_report=load_json(root,'HRAS_v20_Static_Validation_Report.json')
            if candidate_report.get('report_version')==version.get('spec_version') and candidate_report.get('status') in {'PASS','FAIL'}:
                report=candidate_report
        except Exception:
            report=None
    schemas=load_json(root,'HRAS_v20_Contract_Schemas.json')
    trace=load_json(root,'HRAS_v20_Requirement_Traceability.json')
    tests=load_json(root,'HRAS_v20_Test_Cases.json')
    source_paths=[x['path'] for x in manifest.get('files',[]) if isinstance(x,dict) and isinstance(x.get('path'),str)]
    for path in DEFAULT_ADDITIONS:
        if path not in source_paths: source_paths.append(path)
    # Manifest never hashes itself, the Markdown rendering, or checksum file.
    source_paths=[p for p in source_paths if p not in EXCLUDED_FROM_MANIFEST]
    for name in source_paths:
        path=root/name
        if not path.is_file(): raise FileNotFoundError(f'manifest source not available: {name}')
    manifest['version']=version['spec_version']
    manifest['release_status']='CANDIDATE_NOT_PRODUCTION_READY'
    manifest['schema_registry_status']=version.get('schema_registry_status', 'MISSING')
    manifest['manifest_version']='1.1.0'
    manifest['counts']={
        'requirements':len(trace.get('requirements',[])),
        'schema_definitions':len(schemas.get('$defs',{})),
        'test_cases':len(tests.get('cases',[])),
        'typed_oracle_assertions':sum(len(c.get('oracle_assertions',[])) for c in tests.get('cases',[])),
        'tests_not_run':sum(c.get('status') in ('NOT_RUN','BLOCKED') for c in tests.get('cases',[])),
        'fixtures_unmaterialized':sum(c.get('fixture_binding_status')!='MATERIALIZED_AND_HASHED' for c in tests.get('cases',[])),
    }
    manifest['static_validation']={
        'status':report.get('status','NOT_RUN') if report else 'NOT_RUN',
        'assertions':report.get('assertion_count') if report else None,
        'passed':report.get('passed') if report else None,
        'failed':report.get('failed') if report else None,
        'scope':'Reproduced static package checks only; no target LLM runtime, production authorization, durable operation store, isolated domain oracle, live adapters, or deployment target exercised.',
        'evidence_report':'HRAS_v20_Static_Validation_Report.json' if report else None,
    }
    manifest['manifest_scope']='The files array is the complete hashed package source/test inventory; this JSON manifest, its Markdown rendering, and the checksum file are listed only in HRAS_v20_CHECKSUMS.txt to avoid self-referential hashes. Workspace-only plan/audit source inputs are excluded from the release package.'
    manifest['limitations']=[
        'Candidate only; no owner approval, promotion, deployment, or production readiness implied.',
        'Runtime test cases remain NOT_RUN until fixture/environment materialization and frozen oracle/threshold execution.',
        'Reference controller remains illustrative and is not a production security boundary.',
        'D-02, D-05 and D-12 recommendations are recorded for candidate execution by explicit chat authorization; cryptographic identity/signature is not verified and no production approval is inferred.',
        'Independent domain oracle, live tool adapters, durable operation store, production auth broker, and target evidence are not present in this package.'
    ]
    manifest['files']=[{'path':name,'size_bytes':(root/name).stat().st_size,'sha256':sha256(root/name)} for name in source_paths]
    (root/MANIFEST).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # The markdown manifest is generated from the JSON manifest's current content, without embedding its own hash.
    md=['# HRAS v20.0.0-rc4 Candidate Package Manifest','',f"**Package:** `{manifest.get('package_id')}`  ",f"**Version:** `{manifest['version']}`  ",f"**Release status:** `{manifest['release_status']}`  ",f"**Schema registry status:** `{manifest['schema_registry_status']}`  ",f"**Static validation:** `{manifest['static_validation']['status']}` (runtime conformance is separate)",'', '## Derived counts']
    md += [f"- {k.replace('_',' ')}: {v}" for k,v in manifest['counts'].items()]
    md += ['', '## Hashed package files','', '| Path | Bytes | SHA-256 |','|---|---:|---|']
    md += [f"| `{x['path']}` | {x['size_bytes']} | `{x['sha256']}` |" for x in manifest['files']]
    md += ['', '## Limitations'] + [f'- {x}' for x in manifest['limitations']]
    md += ['', 'The JSON manifest, this Markdown rendering and the checksum file are checksum-protected but excluded from the JSON manifest file list to avoid recursive hashing.','']
    (root/'HRAS_v20_Package_Manifest.md').write_text('\n'.join(md),encoding='utf-8')
    # Checksums protect manifest files as well as every listed package file.
    checksum_names=sorted(set(source_paths+[MANIFEST,'HRAS_v20_Package_Manifest.md']))
    (root/CHECKSUMS).write_text(''.join(f'{sha256(root/n)}  {n}\n' for n in checksum_names),encoding='utf-8')


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description='Verify or refresh HRAS package identity, inventory and hashes. No promotion or deployment.')
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--check',action='store_true',help='verify version identity, schema/module contracts, clean inventory and checksums')
    parser.add_argument('--strict-root',action='store_true',help='fail if the root contains files not listed in the package manifest or metadata set')
    parser.add_argument('--refresh-manifest',action='store_true',help='recompute dynamic counts, manifest SHA/size entries and checksums from current sources')
    parser.add_argument('--report',type=Path,help='write verification JSON report to this path')
    args=parser.parse_args(argv)
    if args.refresh_manifest:
        refresh_manifest(args.root)
    result=verify_package(args.root,strict_root=args.strict_root)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if args.report: args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__': raise SystemExit(main())
