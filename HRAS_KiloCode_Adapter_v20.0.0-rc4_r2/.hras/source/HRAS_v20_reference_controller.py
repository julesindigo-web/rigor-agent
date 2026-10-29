#!/usr/bin/env python3
"""HRAS v20 reference controller primitives. Not a production security boundary by itself."""
from __future__ import annotations
import json, hashlib, re
from datetime import datetime, timezone
from pathlib import Path
from functools import lru_cache
from typing import Any
from jsonschema import Draft202012Validator

class ContractError(ValueError): pass

def strict_json_loads(text: str) -> Any:
    def object_pairs(pairs):
        out={}
        for k,v in pairs:
            if k in out: raise ContractError(f"duplicate JSON member: {k}")
            out[k]=v
        return out
    def bad_constant(x): raise ContractError(f"non-finite JSON constant: {x}")
    return json.loads(text, object_pairs_hook=object_pairs, parse_constant=bad_constant)

def _utf16_sort_key(s: str) -> bytes: return s.encode('utf-16-be','surrogatepass')
def jcs_canonical(value: Any) -> str:
    """Canonicalize HRAS test-case corpus domain. Reject floats; current frozen corpus uses integer JSON numbers only.

    Production implementations that permit fractional values MUST use an RFC 8785 implementation
    verified against the published RFC test vectors; this intentionally fails closed for floats.
    """
    if value is None: return 'null'
    if value is True: return 'true'
    if value is False: return 'false'
    if isinstance(value,int) and not isinstance(value,bool):
        if abs(value)>9007199254740991: raise ContractError('integer outside interoperable I-JSON range')
        return str(value)
    if isinstance(value,float): raise ContractError('floating-point value rejected by corpus-bounded canonicalizer')
    if isinstance(value,str): return json.dumps(value,ensure_ascii=False,separators=(',',':'))
    if isinstance(value,list): return '['+','.join(jcs_canonical(x) for x in value)+']'
    if isinstance(value,dict):
        if any(not isinstance(k,str) for k in value): raise ContractError('object keys must be strings')
        keys=sorted(value.keys(),key=_utf16_sort_key)
        return '{'+','.join(jcs_canonical(k)+':'+jcs_canonical(value[k]) for k in keys)+'}'
    raise ContractError(f'unsupported JSON type: {type(value).__name__}')

def case_hash(case: dict) -> str:
    body=dict(case); body.pop('case_hash',None)
    return 'sha256:'+hashlib.sha256(jcs_canonical(body).encode('utf-8')).hexdigest()

def current_spec_version() -> str:
    """Load active version identity from the single package source; fail closed if missing."""
    path=Path(__file__).with_name('HRAS_v20_Version.json')
    try:
        record=strict_json_loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        raise ContractError(f'active version record unavailable: {exc}') from exc
    version=record.get('spec_version') if isinstance(record,dict) else None
    if not isinstance(version,str) or not re.fullmatch(r'20\.0\.0-rc[0-9]+',version):
        raise ContractError('active version record has invalid spec_version')
    if record.get('spec_id')!='HRAS-AUTO-ENG':
        raise ContractError('active version record has mismatched spec_id')
    return version


def validate_observation_provenance(case: dict, observation: dict, expected_run_manifest: dict|None=None) -> list[str]:
    """Validate observation identity against a frozen materialized case and run manifest.

    This helper is a reference invariant checker only; signature verification of the manifest,
    trusted storage, runtime attestation, and provider evidence authenticity remain deployment controls.
    """
    errors=[]
    prov=observation.get('provenance') if isinstance(observation,dict) else None
    if not isinstance(prov,dict): return ['observation.provenance missing or not an object']
    if not isinstance(expected_run_manifest,dict):
        errors.append('signed/approved ConformanceRunReport manifest is required')
    try:
        recomputed=case_hash(case)
    except Exception as exc:
        return errors+[f'case hash could not be recomputed: {exc}']
    stored=case.get('case_hash')
    if stored!=recomputed: errors.append('case.case_hash does not match recomputed frozen case')
    try:
        active_version=current_spec_version()
    except Exception as exc:
        return errors+[f'active version identity unavailable: {exc}']
    case_checks={
      'test_id':case.get('test_id'),
      'case_hash':stored,
      'spec_id':'HRAS-AUTO-ENG',
      'spec_version':active_version,
      'fixture_ref':case.get('fixture_ref'),
      'fixture_declaration_hash':case.get('fixture_declaration_hash'),
      'environment_profile_ref':case.get('environment_profile_ref'),
    }
    for key,expected in case_checks.items():
        if prov.get(key)!=expected: errors.append(f'provenance.{key} mismatch')
    if case.get('fixture_binding_status')!='MATERIALIZED_AND_HASHED':
        errors.append('case fixture is not MATERIALIZED_AND_HASHED')
    if not case.get('environment_id'):
        errors.append('case environment_id is not bound to a real environment')
    if not case.get('fixture_hash') or prov.get('fixture_hash')!=case.get('fixture_hash'):
        errors.append('actual fixture_hash missing or mismatched')
    if prov.get('environment_id')!=case.get('environment_id'):
        errors.append('provenance.environment_id mismatch')
    if expected_run_manifest is not None:
        run_map={
          'run_id':'run_id','spec_id':'spec_id','spec_version':'spec_version','spec_hash':'spec_hash',
          'schema_registry_hash':'schema_registry_hash','validator_version':'validator_version','validator_hash':'validator_hash',
          'test_suite_version':'test_suite_version','test_suite_hash':'test_suite_hash','runtime_build_id':'runtime_build_id',
          'model_id':'model_id','model_version':'model_version','config_hash':'config_hash',
          'tool_schema_hash':'tool_schema_hash','threshold_version':'threshold_version','threshold_set_hash':'threshold_set_hash'
        }
        for prov_key,run_key in run_map.items():
            expected=expected_run_manifest.get(run_key)
            if not expected:
                errors.append(f'run manifest missing {run_key}')
            elif prov.get(prov_key)!=expected:
                errors.append(f'provenance.{prov_key} mismatches run manifest {run_key}')
        if case.get('threshold_version')!=expected_run_manifest.get('threshold_version'):
            errors.append('case threshold_version mismatches run manifest')
    if case.get('status')=='PASS':
        if case.get('oracle_frozen') is not True or not case.get('frozen_at'):
            errors.append('passing case lacks frozen oracle/time')
        if not case.get('threshold_approved_by') or not case.get('threshold_approved_at'):
            errors.append('passing case lacks independently approved threshold metadata')
    if observation.get('execution_status')!='COMPLETE':
        errors.append('observation execution_status is not COMPLETE')
    return errors

def load_registry(path: str|Path) -> dict:
    registry=strict_json_loads(Path(path).read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(registry)
    return registry

def validate_contract(registry: dict, def_name: str, value: Any) -> list[str]:
    if def_name not in registry.get('$defs',{}): return [f'missing schema: {def_name}']
    v=Draft202012Validator({'$schema':registry['$schema'],'$ref':'#/$defs/'+def_name,'$defs':registry['$defs']})
    return [f'{e.json_path}: {e.message}' for e in sorted(v.iter_errors(value),key=lambda e:list(map(str,e.absolute_path)))]

def validate_bidirectional_trace(trace: dict, cases: list[dict], requirements: list[dict]) -> list[str]:
    """Validate both projections and require the explicit edge list to match them exactly."""
    if not isinstance(trace, dict):
        return ['trace is not an object']
    errors=[]
    if not isinstance(cases, list) or not isinstance(requirements, list):
        return ['cases and requirements must be lists']
    case_ids=[c.get('test_id') for c in cases if isinstance(c,dict)]
    requirement_ids=[r.get('requirement_id') for r in requirements if isinstance(r,dict)]
    valid_case_ids=[x for x in case_ids if isinstance(x,str) and x]
    valid_requirement_ids=[x for x in requirement_ids if isinstance(x,str) and x]
    tids=set(valid_case_ids); rids=set(valid_requirement_ids)
    if len(case_ids)!=len(cases) or len(valid_case_ids)!=len(case_ids):
        errors.append('cases contain a malformed record or test_id')
    if len(valid_case_ids)!=len(tids): errors.append('duplicate test_id in cases')
    if len(requirement_ids)!=len(requirements) or len(valid_requirement_ids)!=len(requirement_ids):
        errors.append('requirements contain a malformed record or requirement_id')
    if len(valid_requirement_ids)!=len(rids): errors.append('duplicate requirement_id in requirements')

    case_by={}
    for c in cases:
        if not isinstance(c,dict) or not isinstance(c.get('test_id'),str) or not c['test_id']: continue
        refs=c.get('requirement_refs',[])
        case_by[c['test_id']]={x for x in refs if isinstance(x,str) and x} if isinstance(refs,list) else set()
    req_by={}
    for r in requirements:
        if not isinstance(r,dict) or not isinstance(r.get('requirement_id'),str) or not r['requirement_id']: continue
        refs=r.get('test_ids',[])
        req_by[r['requirement_id']]={x for x in refs if isinstance(x,str) and x} if isinstance(refs,list) else set()
    expected_edges=set()
    for c in cases:
        if not isinstance(c,dict): continue
        tid=c.get('test_id')
        refs=c.get('requirement_refs')
        if not isinstance(refs,list) or not refs:
            errors.append(f"{tid}: no requirement refs")
            continue
        if any(not isinstance(x,str) or not x for x in refs):
            errors.append(f"{tid}: malformed requirement ref")
        elif len(refs)!=len(set(refs)):
            errors.append(f"{tid}: duplicate requirement ref")
        for rid in refs:
            if not isinstance(rid,str) or rid not in rids:
                errors.append(f"{tid}: unknown requirement {rid}")
                continue
            expected_edges.add((rid,tid))
            if tid not in req_by.get(rid,set()):
                errors.append(f"edge missing from requirement projection: {rid}->{tid}")

    for r in requirements:
        if not isinstance(r,dict): continue
        rid=r.get('requirement_id')
        refs=r.get('test_ids')
        if not isinstance(refs,list) or not refs:
            errors.append(f"{rid}: no tests or signed N/A")
            continue
        if any(not isinstance(x,str) or not x for x in refs):
            errors.append(f"{rid}: malformed test_id in requirement projection")
        elif len(refs)!=len(set(refs)):
            errors.append(f"{rid}: duplicate test_id in requirement projection")
        for tid in refs:
            if not isinstance(tid,str) or tid not in tids:
                errors.append(f"{rid}: unknown test {tid}")
            elif rid not in case_by.get(tid,set()):
                errors.append(f"edge missing from case projection: {rid}->{tid}")

    explicit=trace.get('edges')
    if not isinstance(explicit,list):
        errors.append('trace.edges must be an explicit list')
        explicit=[]
    explicit_edges=[]
    for index,e in enumerate(explicit):
        if not isinstance(e,dict):
            errors.append(f'trace.edges[{index}] is not an object')
            continue
        rid=e.get('requirement_id'); tid=e.get('test_id')
        if not isinstance(rid,str) or not isinstance(tid,str):
            errors.append(f'trace.edges[{index}] has malformed endpoints')
            continue
        pair=(rid,tid)
        explicit_edges.append(pair)
        if rid not in rids or tid not in tids:
            errors.append(f"unknown edge {e}")
    explicit_set=set(explicit_edges)
    if len(explicit_edges)!=len(explicit_set):
        errors.append('trace.edges contains duplicate requirement/test pairs')
    missing=expected_edges-explicit_set
    extra=explicit_set-expected_edges
    if missing:
        errors.append(f'explicit edge list omits {len(missing)} expected pair(s): {sorted(missing)[:8]}')
    if extra:
        errors.append(f'explicit edge list contains {len(extra)} unexpected pair(s): {sorted(extra)[:8]}')
    return errors

def validate_trial_policy(policy: dict) -> list[str]:
    errors=[]
    if policy.get('minimum_trials',0)>policy.get('maximum_trials',0): errors.append('minimum_trials exceeds maximum_trials')
    if policy.get('stopping_rule')=='FIXED_N' and policy.get('minimum_trials')!=policy.get('maximum_trials'): errors.append('FIXED_N requires minimum_trials == maximum_trials')
    if policy.get('maximum_trials',0)!=len(policy.get('seeds_or_run_ids',[])): errors.append('every bounded trial must have an explicit seed/run ID')
    if policy.get('pass_rule')=='APPROVED_RATE_THRESHOLD' and policy.get('approved_rate_minimum') is None: errors.append('rate threshold missing')
    return errors

@lru_cache(maxsize=4)
def _active_schema_registry(schema_path: str, modified_ns: int) -> dict:
    # Cache key includes mtime so local schema edits invalidate the in-process copy.
    del modified_ns
    return load_registry(schema_path)

def _schema_for_controller() -> dict:
    path=Path(__file__).with_name('HRAS_v20_Contract_Schemas.json')
    return _active_schema_registry(str(path),path.stat().st_mtime_ns)

def authorize_decision(decision: dict, trusted_verify_callback) -> str:
    """Fail closed on malformed decision envelopes and on non-boolean verification.

    DENY is returned only for a schema-valid, reason-coded denial. INDETERMINATE
    covers malformed decisions and missing/unavailable verification. ALLOW requires
    a schema-valid signed grant plus a trusted verifier that returns literal True.
    This reference primitive is not itself a cryptographic trust boundary.
    """
    if not isinstance(decision, dict):
        return 'INDETERMINATE'
    try:
        schema=_schema_for_controller()
        if validate_contract(schema,'AuthorizationDecision',decision):
            return 'INDETERMINATE'
    except Exception:
        return 'INDETERMINATE'
    outcome=decision.get('decision')
    if outcome=='DENY': return 'DENY'
    if outcome=='INDETERMINATE': return 'INDETERMINATE'
    if outcome!='ALLOW' or not callable(trusted_verify_callback): return 'INDETERMINATE'
    try:
        verification_result=trusted_verify_callback(decision)
    except Exception:
        return 'INDETERMINATE'
    # Never coerce a result with bool(...): a truthy string such as "DENY" is not proof.
    if verification_result is not True: return 'INDETERMINATE'
    required_nonempty=(
        'decision_id','principal_id','issuer_id','action','resource','environment','audience',
        'issued_at','expires_at','token_id','nonce','policy_version','atomicity_strategy',
        'audit_ref','signature_evidence_ref','signature_algorithm','key_id','signed_payload_hash',
        'verification_timestamp','verifier_id','grant_id','decided_at')
    if any(not isinstance(decision.get(k),str) or not decision[k].strip() for k in required_nonempty):
        return 'INDETERMINATE'
    scope=decision.get('scope')
    if not isinstance(scope,list) or not scope or any(not isinstance(x,str) or not x.strip() for x in scope):
        return 'INDETERMINATE'
    try:
        issued_at=datetime.fromisoformat(decision['issued_at'].replace('Z','+00:00'))
        expires_at=datetime.fromisoformat(decision['expires_at'].replace('Z','+00:00'))
        decided_at=datetime.fromisoformat(decision['decided_at'].replace('Z','+00:00'))
        verified_at=datetime.fromisoformat(decision['verification_timestamp'].replace('Z','+00:00'))
        now=datetime.now(timezone.utc)
        if any(x.tzinfo is None for x in (issued_at,expires_at,decided_at,verified_at)): return 'INDETERMINATE'
        if issued_at > now or expires_at <= now or expires_at <= issued_at or decided_at > now or verified_at > now: return 'INDETERMINATE'
    except (TypeError,ValueError,KeyError): return 'INDETERMINATE'
    if not isinstance(decision.get('resource_limits'),dict): return 'INDETERMINATE'
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',decision['signed_payload_hash']): return 'INDETERMINATE'
    if not all(decision.get(k) is True for k in ('signature_verified','revocation_checked','replay_checked')): return 'INDETERMINATE'
    return 'ALLOW'

def validate_exception_independence(record: dict) -> bool:
    return bool(isinstance(record,dict) and record.get('proposer_id') and record.get('approver_id') and record['proposer_id']!=record['approver_id'] and record.get('approver_independence_evidence_ref') and record.get('approver_policy_version') and record.get('approver_authority'))

def exception_is_valid_for_use(record: dict, policy_registry: dict, now: datetime|None=None) -> bool:
    """Return True only for a schema-valid, independent, current, policy-waivable approval.

    This is a contract/invariant check, not an identity provider or policy signer. Unknown
    gates and any reference to a known non-waivable condition fail closed.
    """
    if not isinstance(record,dict) or not isinstance(policy_registry,dict): return False
    try:
        schema=_schema_for_controller()
        if validate_contract(schema,'ExceptionRecord',record): return False
    except Exception: return False
    if record.get('status')!='APPROVED' or record.get('waivable') is not True: return False
    if not validate_exception_independence(record): return False
    if not record.get('evidence_refs') or not record.get('compensating_controls'): return False
    nw=policy_registry.get('non_waivable_policy',{})
    condition_ids={x.get('condition_id') for x in nw.get('condition_registry',[]) if isinstance(x,dict) and x.get('non_waivable') is True}
    if record.get('gate_id') in condition_ids or record.get('gate_id')==nw.get('id') or record.get('policy_basis')==nw.get('id'):
        return False
    if any(cid and cid in record.get('policy_basis','') for cid in condition_ids): return False
    try:
        approved=datetime.fromisoformat(record['approved_at'].replace('Z','+00:00'))
        expires=datetime.fromisoformat(record['expires_at'].replace('Z','+00:00'))
        now=now or datetime.now(timezone.utc)
        if approved.tzinfo is None or expires.tzinfo is None or now.tzinfo is None: return False
        if approved>now or expires<=now or expires<=approved: return False
    except (KeyError,TypeError,ValueError): return False
    # No signature/identity source exists in this reference package. The independent approval
    # evidence reference must be checked by the real trusted broker before any side effect.
    if policy_registry.get('status') not in {'APPROVED','CANDIDATE_DECISIONS_RECORDED_CHAT_AUTHORIZATION_CRYPTOGRAPHIC_IDENTITY_UNVERIFIED'}:
        return False
    return True


def _workflow_cycle_after_retry_edges(mode: str, edges: set[tuple[str,str]], retry_edges: set[tuple[str,str]]) -> bool:
    """Return true if any directed cycle remains after guarded retry edges are removed."""
    graph: dict[str,list[str]] = {}
    for source,target in edges-retry_edges:
        graph.setdefault(source,[]).append(target)
    visiting:set[str]=set(); visited:set[str]=set()
    def visit(node: str) -> bool:
        if node in visiting: return True
        if node in visited: return False
        visiting.add(node)
        for nxt in graph.get(node,[]):
            if visit(nxt): return True
        visiting.remove(node); visited.add(node); return False
    return any(visit(node) for node in list(graph) if node not in visited)

@lru_cache(maxsize=4)
def _load_workflow_transition_registry_cached(schema_path: str, schema_mtime_ns: int, registry_path: str, registry_mtime_ns: int) -> tuple[dict, dict[str,set[tuple[str,str]]]]:
    del schema_mtime_ns, registry_mtime_ns
    schema=load_registry(schema_path)
    registry=strict_json_loads(Path(registry_path).read_text(encoding='utf-8'))
    errors=validate_contract(schema,'WorkflowTransitionRegistry',registry)
    if errors: raise ContractError('workflow transition registry invalid: '+'; '.join(errors[:8]))
    active=current_spec_version()
    if registry.get('spec_version')!=active: raise ContractError('workflow transition registry version does not match active version')
    modes=registry.get('modes',[])
    mode_enum=set(schema['$defs']['RouteDecision']['properties']['primary_mode']['enum'])
    mode_names=[m.get('primary_mode') for m in modes]
    if registry.get('mode_count')!=len(modes) or len(modes)!=len(mode_enum) or set(mode_names)!=mode_enum or len(mode_names)!=len(set(mode_names)):
        raise ContractError('workflow transition registry must cover each canonical primary mode exactly once')
    terminal=set(registry.get('terminal_states',[]))
    transition_map={}
    for item in modes:
        mode=item['primary_mode']; edges=[]
        for edge in item.get('transitions',[]):
            pair=(edge['from_state'],edge['to_state'])
            if pair[0]==pair[1]: raise ContractError(f'{mode}: self-transition forbidden: {pair}')
            if pair[0] in terminal: raise ContractError(f'{mode}: terminal-state re-entry forbidden: {pair}')
            edges.append(pair)
        if len(edges)!=len(set(edges)): raise ContractError(f'{mode}: duplicate transition edge')
        transition_map[mode]=set(edges)
    retry_items=registry.get('retry_edges',[])
    retry_keys=[(x.get('primary_mode'),x.get('from_state'),x.get('to_state')) for x in retry_items]
    if len(retry_keys)!=len(set(retry_keys)): raise ContractError('duplicate guarded retry edge')
    retry_by_mode:dict[str,set[tuple[str,str]]]={m:set() for m in transition_map}
    for mode,source,target in retry_keys:
        if (source,target) not in transition_map.get(mode,set()): raise ContractError(f'guarded retry edge is not a declared transition: {(mode,source,target)}')
        retry_by_mode[mode].add((source,target))
    for mode,edges in transition_map.items():
        if _workflow_cycle_after_retry_edges(mode,edges,retry_by_mode.get(mode,set())):
            raise ContractError(f'{mode}: unbounded workflow cycle remains after guarded retry edges are removed')
    for forbidden in registry.get('prohibited_shortcuts',[]):
        pair=(forbidden.get('from_state'),forbidden.get('to_state'))
        if pair in transition_map.get(forbidden.get('primary_mode'),set()):
            raise ContractError(f'prohibited shortcut is also permitted: {forbidden}')
    return registry,transition_map

def load_workflow_transition_registry() -> tuple[dict, dict[str,set[tuple[str,str]]]]:
    base=Path(__file__).resolve().parent
    schema_path=base/'HRAS_v20_Contract_Schemas.json'
    registry_path=base/'HRAS_v20_Workflow_Transitions.json'
    if not schema_path.is_file() or not registry_path.is_file(): raise ContractError('canonical schema/transition registry missing')
    return _load_workflow_transition_registry_cached(str(schema_path),schema_path.stat().st_mtime_ns,str(registry_path),registry_path.stat().st_mtime_ns)

def validate_workflow_transition_registry(registry: dict, schema: dict|None=None) -> list[str]:
    errors=[]
    try:
        schema=schema or _schema_for_controller()
        errors.extend(validate_contract(schema,'WorkflowTransitionRegistry',registry))
        if errors: return errors
        mode_enum=set(schema['$defs']['RouteDecision']['properties']['primary_mode']['enum'])
        modes=registry.get('modes',[]); names=[m.get('primary_mode') for m in modes]
        if registry.get('mode_count')!=len(modes) or set(names)!=mode_enum or len(names)!=len(set(names)):
            errors.append('transition registry does not cover the canonical mode enum exactly once')
        terminal=set(registry.get('terminal_states',[]))
        lookup={m['primary_mode']:set() for m in modes}
        for item in modes:
            for edge in item.get('transitions',[]):
                pair=(edge['from_state'],edge['to_state'])
                if pair[0]==pair[1] or pair[0] in terminal: errors.append(f"{item['primary_mode']}: illegal transition {pair}")
                if pair in lookup[item['primary_mode']]: errors.append(f"{item['primary_mode']}: duplicate transition {pair}")
                lookup[item['primary_mode']].add(pair)
        retry_items=registry.get('retry_edges',[])
        retry_keys=[(x.get('primary_mode'),x.get('from_state'),x.get('to_state')) for x in retry_items]
        if len(retry_keys)!=len(set(retry_keys)): errors.append('retry_edges contains duplicate edges')
        retry_by_mode={m:set() for m in names}
        for mode,source,target in retry_keys:
            if (source,target) not in lookup.get(mode,set()): errors.append(f'guarded retry edge is not a declared transition: {(mode,source,target)}')
            else: retry_by_mode[mode].add((source,target))
        for mode,edges in lookup.items():
            if _workflow_cycle_after_retry_edges(mode,edges,retry_by_mode.get(mode,set())):
                errors.append(f'{mode}: unbounded cycle remains when guarded retry edges are removed')
        for forbidden in registry.get('prohibited_shortcuts',[]):
            pair=(forbidden.get('from_state'),forbidden.get('to_state'))
            if pair in lookup.get(forbidden.get('primary_mode'),set()): errors.append(f'prohibited shortcut is allowed: {forbidden}')
    except Exception as exc: errors.append(f'workflow registry validation unavailable: {type(exc).__name__}: {exc}')
    return errors

def transition_allowed(mode: str, from_state: str, to_state: str) -> bool:
    """Consult the canonical versioned transition registry and fail closed on drift."""
    if from_state==to_state: return False
    try:
        registry, transitions=load_workflow_transition_registry()
        if any(x.get('primary_mode')==mode and x.get('from_state')==from_state and x.get('to_state')==to_state for x in registry.get('prohibited_shortcuts',[])):
            return False
        if any(x.get('primary_mode')==mode and x.get('from_state')==from_state and x.get('to_state')==to_state for x in registry.get('retry_edges',[])):
            return False
        return (from_state,to_state) in transitions.get(mode,set())
    except Exception:
        return False

def repair_loop_disposition(failure_signature_occurrences: int, no_progress_occurrences: int=0, material_strategy_or_root_cause_change: bool=False, budget_remaining: bool=True) -> str:
    """Return the plan-defined retry disposition; counts must come from trusted durable observations."""
    if (isinstance(failure_signature_occurrences, bool) or not isinstance(failure_signature_occurrences, int) or failure_signature_occurrences < 0
        or isinstance(no_progress_occurrences, bool) or not isinstance(no_progress_occurrences, int) or no_progress_occurrences < 0
        or material_strategy_or_root_cause_change not in (True, False) or budget_remaining not in (True, False)):
        return 'BLOCKED'
    if failure_signature_occurrences >= 4:
        return 'BLOCKED'
    if not budget_remaining:
        return 'EXHAUSTED'
    try:
        registry, _ = load_workflow_transition_registry()
        policy = registry['repair_loop_policy']
        same_failure_trigger = int(policy['same_failure_change_approach_at_occurrences'])
        no_progress_trigger = int(policy['no_progress_change_approach_at_occurrences'])
    except Exception:
        return 'BLOCKED'
    if not material_strategy_or_root_cause_change and (failure_signature_occurrences >= same_failure_trigger or no_progress_occurrences >= no_progress_trigger):
        return 'CHANGE_APPROACH'
    return 'RETRY_ALLOWED'


def retry_transition_allowed(mode: str, from_state: str, to_state: str, failure_signature_occurrences: int, material_strategy_or_root_cause_change: bool, budget_remaining: bool=True, no_progress_occurrences: int=0) -> bool:
    """Gate repair edges on canonical policy thresholds, strategy pivots, and remaining budget.

    The caller must persist and supply trusted counters. False on a repair edge may mean
    CHANGE_APPROACH; consult repair_loop_disposition for the explicit disposition.
    """
    try:
        registry, transitions = load_workflow_transition_registry()
        edge = (from_state, to_state)
        if edge not in transitions.get(mode, set()): return False
        if any(x.get('primary_mode')==mode and x.get('from_state')==from_state and x.get('to_state')==to_state for x in registry.get('prohibited_shortcuts', [])): return False
        guarded = {(x.get('from_state'), x.get('to_state')) for x in registry.get('retry_edges', []) if x.get('primary_mode')==mode}
    except Exception:
        return False
    disposition = repair_loop_disposition(failure_signature_occurrences, no_progress_occurrences, material_strategy_or_root_cause_change, budget_remaining)
    if disposition in {'BLOCKED', 'EXHAUSTED'}:
        return to_state in {'BLOCKED', 'EXHAUSTED'}
    if edge in guarded:
        return disposition == 'RETRY_ALLOWED'
    return transition_allowed(mode, from_state, to_state)

def normalize_subroute_token(value: str, policy_registry: dict, schema_registry: dict) -> str:
    """Normalize declared legacy aliases before schema validation; reject unknown tokens fail-closed."""
    aliases=policy_registry.get('subroute_aliases',{})
    canonical=schema_registry.get('$defs',{}).get('RouteDecision',{}).get('properties',{}).get('subroutes',{}).get('items',{}).get('enum',[])
    normalized=aliases.get(value,value)
    if normalized not in canonical:
        raise ContractError(f'unknown subroute token: {value!r}')
    return normalized

ARTIFACT_LIFECYCLE_TRANSITIONS={
    'DRAFT': {'IN_PROGRESS','CANCELLED'},
    'IN_PROGRESS': {'REVIEW_READY','CANCELLED'},
    'REVIEW_READY': {'IN_PROGRESS','VALIDATED','CANCELLED'},
    'VALIDATED': {'SUPERSEDED'},
    'SUPERSEDED': set(),
    'CANCELLED': set(),
}
TEST_RESULT_STATUSES=('PASS','FAIL','BLOCKED','NOT_RUN','NOT_APPLICABLE','INCONCLUSIVE')

def artifact_lifecycle_transition_allowed(from_status: str, to_status: str) -> bool:
    """Enforce artifact lifecycle only; never use this for workflow or delivery status."""
    if from_status not in ARTIFACT_LIFECYCLE_TRANSITIONS or to_status not in ARTIFACT_LIFECYCLE_TRANSITIONS:
        return False
    return to_status in ARTIFACT_LIFECYCLE_TRANSITIONS[from_status]

def aggregate_test_case_results(results: list[dict]) -> dict[str,int]:
    """Recompute per-case totals; unknown statuses fail closed rather than being ignored."""
    counts={status:0 for status in TEST_RESULT_STATUSES}
    for result in results:
        status=result.get('status')
        if status not in counts:
            raise ContractError(f'unknown test result status: {status!r}')
        counts[status]+=1
    return counts

def validate_conformance_run_report(report: dict) -> list[str]:
    """Semantic checks beyond schema: totals reconcile; INCONCLUSIVE/non-PASS cannot pass."""
    errors=[]
    results=report.get('case_results',[])
    selected=report.get('selected_test_ids',[])
    ids=[x.get('test_id') for x in results]
    if len(ids)!=len(set(ids)): errors.append('duplicate test_id in case_results')
    if len(selected)!=len(set(selected)): errors.append('duplicate selected_test_ids')
    if not set(ids)<=set(selected): errors.append('case_results contains unselected test ID')
    missing=set(selected)-set(ids)
    declared_missing=set(report.get('missing_results',[]))
    if missing!=declared_missing: errors.append('missing_results does not equal selected cases without results')
    try: actual=aggregate_test_case_results(results)
    except ContractError as exc:
        errors.append(str(exc)); actual={status:0 for status in TEST_RESULT_STATUSES}
    declared=report.get('summary_counts',{})
    for status in TEST_RESULT_STATUSES:
        if declared.get(status)!=actual[status]:
            errors.append(f'summary_counts.{status} mismatch: declared={declared.get(status)!r}, actual={actual[status]}')
    if report.get('overall_status')=='PASS':
        if missing: errors.append('overall PASS has missing selected test results')
        if report.get('release_blocking_failures'): errors.append('overall PASS has release-blocking failures')
        nonpass={k:v for k,v in actual.items() if k!='PASS' and v}
        if nonpass: errors.append(f'overall PASS includes non-PASS case results: {nonpass}')
        for result in results:
            if result.get('status')!='PASS':
                errors.append(f"overall PASS requires PASS for each selected result; {result.get('test_id')} is {result.get('status')}")
    if report.get('overall_status')=='INCONCLUSIVE' and not (actual.get('INCONCLUSIVE',0) or missing or declared_missing):
        errors.append('INCONCLUSIVE run has no inconclusive or missing result explaining status')
    return errors

def validate_performance_report_semantics(report: dict) -> list[str]:
    """Check measurement-to-metric integrity and matching units/methods."""
    errors=[]
    payload=report.get('payload',{}) if isinstance(report,dict) else {}
    metrics=payload.get('metrics',[]); measurements=payload.get('measurements',[])
    by_id={}
    for metric in metrics:
        mid=metric.get('metric_id')
        if not mid: errors.append('metric missing metric_id'); continue
        if mid in by_id: errors.append(f'duplicate metric_id: {mid}')
        by_id[mid]=metric
    for idx,measurement in enumerate(measurements):
        mid=measurement.get('metric_id')
        metric=by_id.get(mid)
        if metric is None:
            errors.append(f'measurements[{idx}] references undeclared metric_id {mid!r}'); continue
        if measurement.get('unit')!=metric.get('unit'):
            errors.append(f'measurements[{idx}] unit does not match metric {mid}')
        if measurement.get('method')!=metric.get('method'):
            errors.append(f'measurements[{idx}] method does not match metric {mid}')
    return errors

def validate_intent_record_artifact(registry: dict, artifact: dict) -> list[str]:
    """Validate the persisted wrapper and enforce same logical identity/version as its typed payload."""
    errors=validate_contract(registry,'IntentRecordArtifact',artifact)
    payload=artifact.get('payload',{}) if isinstance(artifact,dict) else {}
    for field in ('artifact_id','schema_version','spec_version'):
        if artifact.get(field)!=payload.get(field):
            errors.append(f'IntentRecordArtifact envelope/payload {field} mismatch')
    return errors

def validate_lifecycle_operability_spec(report: dict, schema_registry: dict|None=None) -> list[str]:
    """Validate lifecycle semantics beyond JSON shape; NOT_RUN remains non-passing evidence."""
    errors=[]
    try:
        schema_registry=schema_registry or _schema_for_controller()
        errors.extend(f'lifecycle spec: {e}' for e in validate_contract(schema_registry,'LifecycleAndOperabilitySpec',report))
        if errors: return errors
    except Exception as exc:
        return [f'lifecycle schema unavailable: {type(exc).__name__}: {exc}']
    applicability=report.get('applicability',{}); status=applicability.get('status')
    if status=='NOT_APPLICABLE':
        for key in ('rationale','approved_by','review_ref'):
            if not isinstance(applicability.get(key),str) or not applicability[key].strip():
                errors.append(f'NOT_APPLICABLE requires non-empty applicability.{key}')
        na_paths={
          'health_checks':('liveness','readiness','dependency_health'),
          'observability':('structured_logs','metrics','traces','correlation_ids','redaction'),
          'backup_restore':('restore_test_status',),
          'migrations':('up_migration_status','down_migration_status'),
          'rollback':('rollback_test_status',),
          'recovery_drills':('status',),
        }
        for section,fields in na_paths.items():
            for field in fields:
                if report.get(section,{}).get(field)!='NOT_APPLICABLE':
                    errors.append(f'NOT_APPLICABLE profile requires {section}.{field}=NOT_APPLICABLE')
        false_required=[('backup_restore','backup_required'),('migrations','migration_required'),('rollback','rollback_available'),('recovery_drills','required')]
        for section,key in false_required:
            if report.get(section,{}).get(key) is not False:
                errors.append(f'NOT_APPLICABLE profile requires {section}.{key}=false')
    elif status not in {'APPLICABLE','PARTIALLY_APPLICABLE'}:
        errors.append('applicability status is unknown')
    backup=report.get('backup_restore',{})
    if backup.get('backup_required') is True and backup.get('restore_test_status')=='NOT_APPLICABLE':
        errors.append('required backup/restore cannot be marked NOT_APPLICABLE')
    if backup.get('restore_test_status')=='PASS':
        if not backup.get('last_restore_drill_at') or not backup.get('evidence_refs'):
            errors.append('restore PASS requires drill timestamp and evidence references')
    migrations=report.get('migrations',{})
    if migrations.get('migration_required') is True:
        if 'NOT_APPLICABLE' in {migrations.get('up_migration_status'),migrations.get('down_migration_status')}:
            errors.append('required migrations need both up/down status applicable')
        if migrations.get('backup_before_migration') is not True:
            errors.append('required migrations need backup_before_migration=true')
    rollback=report.get('rollback',{})
    if rollback.get('rollback_available') is True:
        if rollback.get('rollback_test_status')=='NOT_APPLICABLE' or not rollback.get('rollback_runbook_ref'):
            errors.append('available rollback requires applicable test and runbook')
    if rollback.get('rollback_test_status')=='PASS' and not rollback.get('evidence_refs'):
        errors.append('rollback PASS requires evidence references')
    recovery=report.get('recovery_drills',{})
    if recovery.get('required') is True and recovery.get('status')=='NOT_APPLICABLE':
        errors.append('required recovery drills cannot be NOT_APPLICABLE')
    if recovery.get('status')=='PASS' and (not recovery.get('last_drill_at') or not recovery.get('evidence_refs')):
        errors.append('recovery PASS requires a drill timestamp and evidence references')
    tco=report.get('tco',{})
    if tco.get('estimate_status')=='ESTIMATED' and (not tco.get('evidence_refs') or not tco.get('assumptions')):
        errors.append('estimated TCO requires assumptions and evidence references')
    return errors


def validate_security_posture_report(report: dict, schema_registry: dict|None=None) -> list[str]:
    """Recompute finding counts and reject unsupported security PASS summaries."""
    errors=[]
    try:
        schema_registry=schema_registry or _schema_for_controller()
        errors.extend(f'security report: {e}' for e in validate_contract(schema_registry,'SecurityPostureReport',report))
        if errors: return errors
    except Exception as exc:
        return [f'security schema unavailable: {type(exc).__name__}: {exc}']
    findings=report.get('findings',[])
    active=[f for f in findings if f.get('status') in {'OPEN','INCONCLUSIVE'}]
    expected={
      'critical_open':sum(f.get('severity')=='CRITICAL' for f in active),
      'high_open':sum(f.get('severity')=='HIGH' for f in active),
      'medium_open':sum(f.get('severity')=='MEDIUM' for f in active),
      'low_open':sum(f.get('severity')=='LOW' for f in active),
      'release_blocking_open':sum(f.get('release_blocking') is True for f in active),
    }
    if report.get('counts')!=expected:
        errors.append(f'finding counts do not reconcile: expected {expected}')
    for finding in findings:
        if finding.get('status')=='ACCEPTED_RESIDUAL_RISK' and finding.get('release_blocking') is True:
            errors.append(f"release-blocking finding {finding.get('finding_id')} cannot be accepted as residual risk")
    if report.get('summary_status')=='PASS':
        checks=[('threat_model','status',{'PASS'}),('authn_authz','status',{'PASS','NOT_APPLICABLE'}),
                ('input_validation','status',{'PASS'}),('secret_handling','status',{'PASS'}),
                ('data_minimization_retention','status',{'PASS','NOT_APPLICABLE'})]
        for section,key,allowed in checks:
            value=report.get(section,{}).get(key)
            if value not in allowed: errors.append(f'PASS summary unsupported by {section}.{key}={value!r}')
        required_subchecks=[('input_validation',('injection_tests','boundary_tests','schema_enforcement')),
                            ('secret_handling',('redaction','leak_scan_status')),
                            ('dependency_security',('sast_status','sca_status','license_review_status','known_exploited_review_status'))]
        for section,fields in required_subchecks:
            for field in fields:
                if report.get(section,{}).get(field)!='PASS':
                    errors.append(f'PASS summary unsupported by {section}.{field}={report.get(section,{}).get(field)!r}')
        for i,control in enumerate(report.get('privacy_controls',[])):
            if control.get('status') not in {'PASS','NOT_APPLICABLE'}:
                errors.append(f'PASS summary unsupported by privacy_controls[{i}]')
        for finding in active:
            if finding.get('severity') in {'CRITICAL','HIGH'} and finding.get('release_blocking') is True:
                errors.append(f"PASS summary has open release-blocking {finding.get('severity')} finding {finding.get('finding_id')}")
        if report.get('review',{}).get('decision')!='APPROVE':
            errors.append('PASS summary requires an approved independent review decision')
    return errors

def operation_may_submit(
    record: dict,
    *,
    expected_request_hash: str | None = None,
    trusted_authorization_verify_callback=None,
) -> bool:
    """Fail-closed submit preflight, not an authorization or idempotency service.

    A submission is never permitted from a bare status label. The caller must supply
    the intended request hash and a trusted callback that verifies the referenced
    authorization is current and bound to the persisted operation, request payload,
    target, tool, side-effect class, idempotency key, expiry/revocation state, and
    durable submit/read-back state. The callback must return literal ``True``.
    If the trusted integration is unavailable, this primitive denies submission.
    """
    if not isinstance(record, dict):
        return False
    try:
        schema=_schema_for_controller()
        if validate_contract(schema, 'OperationRecord', record):
            return False
    except Exception:
        return False
    if record.get('state') != 'AUTHORIZED':
        return False
    if record.get('must_not_resubmit') is not False:
        return False
    submit_count=record.get('submit_count')
    if isinstance(submit_count, bool) or not isinstance(submit_count, int) or submit_count != 0:
        return False
    if not isinstance(expected_request_hash, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', expected_request_hash):
        return False
    if record.get('request_hash') != expected_request_hash:
        return False
    for key in ('operation_id','task_id','tool_id','target_resource','authorization_ref','idempotency_key'):
        value=record.get(key)
        if not isinstance(value, str) or not value.strip():
            return False
    if not callable(trusted_authorization_verify_callback):
        return False
    try:
        return trusted_authorization_verify_callback(record) is True
    except Exception:
        return False

def allowed_delivery_status(
    mode: str,
    status: str,
    validation: dict,
    operation_records: list[dict],
    policy_registry: dict,
    deployment_observed: bool=False,
    action_observed: bool=False,
    deployment_evidence: dict|None=None,
    trusted_deployment_verify_callback=None,
) -> bool:
    """Fail closed on statuses whose names imply observed external effects.

    For DEPLOYED_AND_VERIFIED, the caller must provide evidence derived from a
    trusted deployment observer. The provisional helper input requires a deployment
    ID, target identity, artifact/environment identity, authorization evidence,
    observer identity and passing post-deployment health/smoke checks. The callback
    must verify authenticity, authority, freshness, target and environment binding.
    This evidence shape is NOT yet a canonical machine-readable contract: MR-06 is
    blocked on D-05/D-06 and its schema/report integration. This reference helper
    does not implement the external trust provider.
    """
    if not isinstance(policy_registry,dict) or not isinstance(validation,dict) or not isinstance(operation_records,list): return False
    if status not in policy_registry.get('delivery_status_enum',[]): return False
    if mode in {'PLAN_ONLY','DESIGN_ONLY','RESEARCH_ONLY','ARTIFACT_AUDIT','PROTOTYPE'} and status in {'MASTERPIECE_VERIFIED','PRODUCTION_READY','DEPLOYED_UNVERIFIED','DEPLOYED_AND_VERIFIED'}: return False
    unresolved=any(isinstance(r,dict) and r.get('state') in {'OUTCOME_UNKNOWN','RECONCILING'} for r in operation_records)
    if unresolved and status!='RECONCILIATION_REQUIRED': return False
    if status=='RECONCILIATION_REQUIRED' and not unresolved:return False
    release_statuses={'PRODUCTION_READY','DEPLOYED_AND_VERIFIED','MASTERPIECE_VERIFIED'}
    if status=='DONE_WITH_GAPS':
        return bool(validation.get('failed_hard_gates') or validation.get('unknown_hard_gates') or validation.get('unresolved_blockers') or validation.get('unverified_items') or validation.get('active_exceptions') or validation.get('exception_refs') or validation.get('stale_evidence') or validation.get('evidence_defects'))
    # Any active approved exception can be described only as residual risk; it does not
    # create a PASS and only DONE_WITH_GAPS may carry exception-based release disposition.
    active_exception_refs=validation.get('active_exceptions',[])
    exception_refs=validation.get('exception_refs',[])
    if (active_exception_refs or exception_refs) and status!='DONE_WITH_GAPS': return False
    if status=='DEPLOYED_UNVERIFIED':
        return deployment_observed is True and bool(validation.get('unknown_hard_gates') or validation.get('stale_evidence') or validation.get('unverified_items'))
    if status in release_statuses or status=='ACTION_VERIFIED':
        if validation.get('status')!='PASS': return False
        forbidden=['failed_hard_gates','unknown_hard_gates','authorization_violations','evidence_defects','stale_evidence','operations_needing_reconciliation','budget_violations','unresolved_blockers','active_exceptions','exception_refs']
        if any(validation.get(k) for k in forbidden): return False
    if status in release_statuses:
        # These are proof inputs, not model-controlled labels; missing means not verified.
        if validation.get('artifact_identity_verified') is not True: return False
        if validation.get('quality_profile_frozen') is not True: return False
        if validation.get('evidence_freshness_status')!='PASS': return False
        if validation.get('applicable_gates_passed') is not True: return False
    if status=='PRODUCTION_READY':
        return True
    if status=='DEPLOYED_AND_VERIFIED':
        if deployment_observed is not True or not isinstance(deployment_evidence,dict): return False
        if not callable(trusted_deployment_verify_callback): return False
        try:
            schema=_schema_for_controller()
            if validate_contract(schema,'DeploymentVerificationEvidence',deployment_evidence): return False
        except Exception: return False
        identity_pairs=(('expected_artifact_hash','artifact_hash'),('expected_environment_id','environment_id'),('expected_target_identity','target_identity'),('expected_signed_manifest_hash','signed_manifest_hash'))
        if any(not validation.get(expected) or validation.get(expected)!=deployment_evidence.get(observed) for expected,observed in identity_pairs): return False
        try:
            observed_at=datetime.fromisoformat(deployment_evidence['observed_at'].replace('Z','+00:00'))
            valid_until=datetime.fromisoformat(deployment_evidence['valid_until'].replace('Z','+00:00'))
            now=datetime.now(timezone.utc)
            if observed_at.tzinfo is None or valid_until.tzinfo is None or observed_at>now or valid_until<=now or valid_until<=observed_at: return False
        except (TypeError,ValueError,KeyError): return False
        try:
            if trusted_deployment_verify_callback(deployment_evidence,validation) is not True: return False
        except Exception: return False
        return True
    if status=='MASTERPIECE_VERIFIED':
        return validation.get('independent_review_passed') is True and validation.get('masterpiece_evidence_complete') is True and validation.get('user_outcome_validation_status') in {'PASS','PROXY_ACCEPTED'}
    if status=='ACTION_EXECUTED_UNVERIFIED': return action_observed is True and bool(validation.get('unverified_items'))
    if status=='ACTION_VERIFIED': return action_observed is True and validation.get('status')=='PASS'
    return True
