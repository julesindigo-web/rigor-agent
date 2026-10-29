#!/usr/bin/env python3
"""HRAS v20 static artifact validator. Does not test an LLM runtime."""
from pathlib import Path
from copy import deepcopy
import json, re, hashlib, sys, argparse, os, platform, shlex, tempfile, shutil
from datetime import datetime, timezone
from jsonschema import Draft202012Validator
import HRAS_v20_package_tool as package_tool
from HRAS_v20_reference_controller import strict_json_loads, jcs_canonical, case_hash, validate_contract, validate_bidirectional_trace, validate_trial_policy, validate_exception_independence, operation_may_submit, transition_allowed, validate_observation_provenance, current_spec_version, artifact_lifecycle_transition_allowed, validate_conformance_run_report, validate_performance_report_semantics, validate_intent_record_artifact, normalize_subroute_token, validate_workflow_transition_registry, retry_transition_allowed, load_workflow_transition_registry, exception_is_valid_for_use, validate_lifecycle_operability_spec, validate_security_posture_report, repair_loop_disposition
ROOT=Path(__file__).resolve().parent
VERSION_RECORD=strict_json_loads((ROOT/'HRAS_v20_Version.json').read_text(encoding='utf-8'))
SPEC_VERSION=current_spec_version()
checks=[]
def check(name, ok, details=''):
    checks.append({'check':name,'status':'PASS' if bool(ok) else 'FAIL','details':str(details)})
def load(name): return strict_json_loads((ROOT/name).read_text(encoding='utf-8'))
def local_ref_errors(schema):
    errors=[]
    def visit(node,path='$'):
        if isinstance(node,dict):
            ref=node.get('$ref')
            if isinstance(ref,str) and ref.startswith('#/'):
                cur=schema
                try:
                    for part in ref[2:].split('/'):
                        cur=cur[part.replace('~1','/').replace('~0','~')]
                except Exception: errors.append(f'{path}: unresolved {ref}')
            for k,v in node.items(): visit(v,path+'/'+str(k))
        elif isinstance(node,list):
            for i,v in enumerate(node): visit(v,path+f'/{i}')
    visit(schema); return errors
def route_enum_negative(s):
    obj={'decision_id':'x','primary_mode':'NOT_A_MODE','subroutes':[],'product_classes':[],'risk_class':'R1','scale_class':'S1','reason':'x','applicable_module_ids':[],'required_gate_ids':[],'spec_version':SPEC_VERSION,'spec_hash':'sha256:'+'0'*64,'created_at':'2026-10-27T00:00:00Z'}
    return bool(validate_contract(s,'RouteDecision',obj))
def auth_negative(s):
    obj={'decision_id':'d','decision':'ALLOW','principal_id':'p','issuer_id':'i','action':'deploy','resource':'prod','environment':'prod','audience':'prod-api','scope':['deploy'],'issued_at':'2026-10-27T00:00:00Z','expires_at':'2026-10-27T01:00:00Z','token_id':'t','nonce':'n','policy_version':'1','signature_verified':False,'revocation_checked':True,'replay_checked':True,'atomicity_strategy':'controller-check-use','audit_ref':'audit','reason_codes':[],'resource_limits':{'max_cost_minor':None,'max_records':None,'max_duration_ms':None,'allowed_target_hashes':[]},'signature_evidence_ref':'sig','signature_algorithm':'EdDSA','key_id':'k','signed_payload_hash':'sha256:'+'0'*64,'verification_timestamp':'2026-10-27T00:00:00Z','verifier_id':'trusted-verifier','grant_id':'grant'}
    return bool(validate_contract(s,'AuthorizationDecision',obj))
def duplicate_key_test():
    try: strict_json_loads('{"a":1,"a":2}')
    except Exception: return True
    return False
def trace_mutation_tests(trace,cases):
    requirements=trace['requirements']
    a=deepcopy(trace); a['requirements'][0]['test_ids'].append('UNKNOWN-TEST')
    unknown_edge_rejected=bool(validate_bidirectional_trace(a,cases,a['requirements']))
    b=deepcopy(trace); c=deepcopy(cases)
    rid=b['requirements'][0]['requirement_id']; tid=b['requirements'][0]['test_ids'][0]
    b['requirements'][0]['test_ids'].remove(tid)
    one_sided_req_rejected=bool(validate_bidirectional_trace(b,c,b['requirements']))
    c2=deepcopy(cases); next(x for x in c2 if x['test_id']==tid)['requirement_refs'].remove(rid)
    one_sided_case_rejected=bool(validate_bidirectional_trace(trace,c2,trace['requirements']))
    empty=deepcopy(trace); empty['edges']=[]
    empty_edges_rejected=bool(validate_bidirectional_trace(empty,cases,requirements))
    truncated=deepcopy(trace); truncated['edges'].pop()
    truncated_edges_rejected=bool(validate_bidirectional_trace(truncated,cases,requirements))
    duplicate=deepcopy(trace); duplicate['edges'].append(deepcopy(duplicate['edges'][0]))
    duplicate_edges_rejected=bool(validate_bidirectional_trace(duplicate,cases,requirements))
    reversed_edge=deepcopy(trace); e=deepcopy(reversed_edge['edges'][0]); e['requirement_id'],e['test_id']=e['test_id'],e['requirement_id']; reversed_edge['edges'][0]=e
    reversed_edges_rejected=bool(validate_bidirectional_trace(reversed_edge,cases,requirements))
    forged=deepcopy(trace); forged['edges'].append({'requirement_id':requirements[0]['requirement_id'],'test_id':'FORGED-TEST'})
    forged_edges_rejected=bool(validate_bidirectional_trace(forged,cases,requirements))
    return all((unknown_edge_rejected,one_sided_req_rejected,one_sided_case_rejected,empty_edges_rejected,truncated_edges_rejected,duplicate_edges_rejected,reversed_edges_rejected,forged_edges_rejected))

def oracle_mutation_test(s,c):
    x=deepcopy(c); x.pop('oracle_assertions',None)
    return bool(validate_contract(s,'TestCaseSpec',x))


def _case_pass_mutation_rejected(schemas, case):
    x=deepcopy(case)
    x['status']='PASS'; x['oracle_frozen']=True
    x['frozen_at']='2026-10-27T00:00:00Z'
    x['threshold_approved_at']='2026-10-27T00:00:00Z'; x['threshold_approved_by']='independent-owner'
    return bool(validate_contract(schemas,'TestCaseSpec',x))

def _sample_run_manifest(case, tests):
    return {
      'run_id':'sample-run-not-executed', 'spec_id':tests['spec_id'], 'spec_version':tests['spec_version'],
      'spec_hash':'sha256:'+'a'*64, 'schema_registry_hash':'sha256:'+'e'*64,
      'validator_version':f'HRAS-STATIC-VALIDATOR/{SPEC_VERSION}', 'validator_hash':'sha256:'+'f'*64,
      'test_suite_version':tests['suite_version'], 'test_suite_hash':'sha256:'+'1'*64,
      'runtime_build_id':'reference-runtime-build', 'model_id':'reference-model', 'model_version':'pinned-model-version',
      'config_hash':'sha256:'+'2'*64, 'tool_schema_hash':'sha256:'+'3'*64,
      'threshold_version':case['threshold_version'], 'threshold_set_hash':'sha256:'+'4'*64
    }

def _observation_sample(case, tests, run_manifest=None):
    run_manifest=run_manifest or _sample_run_manifest(case, tests)
    return {
      'provenance':{
        'test_id':case['test_id'],'case_hash':case['case_hash'],'spec_id':tests['spec_id'],'spec_version':tests['spec_version'],
        'spec_hash':run_manifest['spec_hash'],'schema_registry_hash':run_manifest['schema_registry_hash'],
        'validator_version':run_manifest['validator_version'],'validator_hash':run_manifest['validator_hash'],
        'test_suite_version':run_manifest['test_suite_version'],'test_suite_hash':run_manifest['test_suite_hash'],
        'fixture_ref':case['fixture_ref'],'fixture_declaration_hash':case['fixture_declaration_hash'],
        'fixture_hash':None,'environment_profile_ref':case['environment_profile_ref'],'environment_id':None,
        'runtime_build_id':run_manifest['runtime_build_id'],'model_id':run_manifest['model_id'],'model_version':run_manifest['model_version'],
        'tool_schema_hash':run_manifest['tool_schema_hash'],'config_hash':run_manifest['config_hash'],
        'threshold_version':run_manifest['threshold_version'],'threshold_set_hash':run_manifest['threshold_set_hash'],
        'trial_id':case['trial_policy']['seeds_or_run_ids'][0],'run_id':run_manifest['run_id'],'observed_at':'2026-10-27T00:00:00Z'
      },
      'actual':{},'checks':{},'effects':[],'artifacts':[],'execution_status':'COMPLETE','assertion_results':[]
    }

def _observation_schema_errors(schemas,case,tests):
    return validate_contract(schemas,'TestObservationEnvelope',_observation_sample(case,tests))

def _observation_missing_provenance_rejected(schemas,case,tests):
    x=_observation_sample(case,tests); del x['provenance']['fixture_declaration_hash']
    return bool(validate_contract(schemas,'TestObservationEnvelope',x))

def _materialized_case_and_observation(case, tests):
    c=deepcopy(case)
    c['fixture_binding_status']='MATERIALIZED_AND_HASHED'
    c['environment_id']='isolated-runtime-instance-001'
    c['fixture_hash']='sha256:'+'b'*64
    c['status']='PASS'; c['oracle_frozen']=True
    c['frozen_at']='2026-10-27T00:00:00Z'
    c['threshold_approved_at']='2026-10-27T00:00:00Z'; c['threshold_approved_by']='independent-owner'
    c['case_hash']=case_hash(c)
    run=_sample_run_manifest(c,tests)
    o=_observation_sample(case,tests,run)
    p=o['provenance']
    p.update({'test_id':c['test_id'],'case_hash':c['case_hash'],'spec_version':tests['spec_version'],'fixture_ref':c['fixture_ref'],
       'fixture_declaration_hash':c['fixture_declaration_hash'],'fixture_hash':c['fixture_hash'],
       'environment_profile_ref':c['environment_profile_ref'],'environment_id':c['environment_id']})
    return c,o,run

def _materialized_provenance_positive(case,tests):
    c,o,run=_materialized_case_and_observation(case,tests)
    return not validate_observation_provenance(c,o,run)

def _materialized_provenance_mismatch_rejected(case,tests):
    c,o,run=_materialized_case_and_observation(case,tests)
    o['provenance']['fixture_hash']='sha256:'+'c'*64
    return bool(validate_observation_provenance(c,o,run))

def _run_manifest_mismatch_rejected(case,tests):
    c,o,run=_materialized_case_and_observation(case,tests)
    o['provenance']['config_hash']='sha256:'+'9'*64
    return bool(validate_observation_provenance(c,o,run))

def _restricted_actions_complete(policy):
    text=json.dumps(policy.get('restricted_actions_policy',{}),ensure_ascii=False).lower()
    needles=['force-push','rewrite shared git history','sudo','global/package-manager install','upload source code','user data to a third party','disable scanners','branch protection','audit logs','sandbox','security controls','expand credential scope']
    return all(x in text for x in needles)

def artifact_lifecycle_mutation_tests(schemas):
    enum=schemas['$defs']['ArtifactLifecycleStatus']['enum']
    good={'artifact_id':'a1','schema_version':'1.0.0','spec_version':SPEC_VERSION,'status':'REVIEW_READY','created_at':'2026-10-28T00:00:00Z','owner':'test-owner','evidence_refs':[],'assumption_refs':[],'issue_refs':[],'payload':{},'content_hash':'sha256:'+'a'*64}
    valid=not validate_contract(schemas,'CommonArtifact',good)
    bad=deepcopy(good); bad['status']='PRODUCTION_READY'
    invalid_rejected=bool(validate_contract(schemas,'CommonArtifact',bad))
    return valid and invalid_rejected and set(enum)==set(schemas['$defs']['ArtifactLifecycleStatus']['x-hras-use-rules']) and all(status in schemas['$defs']['ArtifactLifecycleStatus']['x-hras-allowed-transitions'] for status in enum)

def inconclusive_aggregation_mutation_test():
    from HRAS_v20_reference_controller import aggregate_test_case_results
    rows=[{'test_id':'A','status':'PASS'},{'test_id':'B','status':'INCONCLUSIVE'}]
    counts=aggregate_test_case_results(rows)
    report={'selected_test_ids':['A','B'],'case_results':rows,'missing_results':[],'summary_counts':dict(counts),'overall_status':'PASS','release_blocking_failures':[]}
    errors=validate_conformance_run_report(report)
    report['overall_status']='INCONCLUSIVE'
    should_be_valid=not validate_conformance_run_report(report)
    report['summary_counts']['INCONCLUSIVE']=0
    mutation_rejected=bool(validate_conformance_run_report(report))
    return counts['PASS']==1 and counts['INCONCLUSIVE']==1 and bool(errors) and should_be_valid and mutation_rejected

def performance_metric_mutation_test():
    report={'payload':{'metrics':[{'metric_id':'p95','unit':'ms','method':'histogram'}], 'measurements':[{'metric_id':'p95','unit':'ms','method':'histogram','value':12,'observed_at':'2026-10-28T00:00:00Z','evidence_ref':'ev-1'}]}}
    good=not validate_performance_report_semantics(report)
    bad=deepcopy(report); bad['payload']['measurements'][0]['metric_id']='unknown'
    unknown_rejected=bool(validate_performance_report_semantics(bad))
    bad2=deepcopy(report); bad2['payload']['measurements'][0]['unit']='s'
    unit_rejected=bool(validate_performance_report_semantics(bad2))
    bad3=deepcopy(report); bad3['payload']['measurements'][0]['method']='manual'
    method_rejected=bool(validate_performance_report_semantics(bad3))
    return good and unknown_rejected and unit_rejected and method_rejected

def source_reference_semantics_valid(cases, req_ids, source_spec_version):
    qualified=re.compile(r'^[^@\s]+@[^:]+::[A-Za-z0-9_.:-]+$')
    for case in cases:
        refs=case.get('requirement_refs',[]); sources=case.get('source_requirement_refs',[])
        if not refs or not sources or not set(refs)<=req_ids: return False
        if any(not (src in req_ids or qualified.fullmatch(src)) for src in sources): return False
        if set(refs)==set(sources) and source_spec_version!=SPEC_VERSION:
            # Equality to active canonical IDs may represent active-spec provenance only.
            return False
    return True

def yaml_examples_disclosed_as_non_normative(spec):
    for match in re.finditer(r'```yaml',spec):
        preceding=spec[max(0,match.start()-220):match.start()]
        if 'intentionally incomplete and non-normative' not in preceding:
            return False
    return spec.count('```yaml')==3

def performance_semantics_schema_test(schemas):
    m=schemas['$defs']['PerformanceReport']['properties']['payload']['properties']['measurements']['items']
    return set(['metric_id','unit','method','value','observed_at','evidence_ref'])<=set(m.get('required',[])) and not {'metric_id','unit','method'}-set(m.get('properties',{}))

def resolve_report_root(report_dir: Path|None=None) -> Path:
    """Use an isolated temporary directory unless the caller explicitly chooses an output path."""
    if report_dir is not None:
        return Path(report_dir)
    candidate=Path(tempfile.mkdtemp(prefix='hras-v20-static-validation-'))
    try:
        candidate.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return candidate
    shutil.rmtree(candidate,ignore_errors=True)
    return Path(tempfile.mkdtemp(prefix='hras-v20-static-validation-',dir=str(ROOT.parent)))


def main(report_dir: Path|None=None):
    spec=(ROOT/'HRAS_v20_Canonical_Autonomous_Production_Grade_Spec.md').read_text(encoding='utf-8')
    schemas=load('HRAS_v20_Contract_Schemas.json'); tests=load('HRAS_v20_Test_Cases.json'); trace=load('HRAS_v20_Requirement_Traceability.json'); policy=load('HRAS_v20_Policy_Registry.json'); module_io=load('HRAS_v20_Module_IO_Registry.json')
    Draft202012Validator.check_schema(schemas)
    check('schema-meta-schema-valid',True,'JSON Schema Draft 2020-12')
    ref_errors=local_ref_errors(schemas); check('all-local-refs-resolve',not ref_errors,ref_errors[:10])
    module_contract_names={'IdeaExpansion','BrandContentSpec','EvidenceLedger','LifecycleAndOperabilitySpec','SecurityPostureReport'}
    check('module-output-contracts-present',module_contract_names <= set(schemas.get('$defs',{})),sorted(module_contract_names-set(schemas.get('$defs',{}))))
    module_schema_errors=validate_contract(schemas,'ModuleIOContractRegistry',module_io)
    missing_module_refs=[f"{m.get('module_id')}: missing {sid}" for m in module_io.get('modules',[]) for sid in [m.get('input_schema_id'),m.get('output_schema_id')] if sid not in schemas.get('$defs',{})]
    module_ids=[m.get('module_id') for m in module_io.get('modules',[])]
    check('module-io-registry-valid',not module_schema_errors and not missing_module_refs and len(module_ids)==len(set(module_ids)),module_schema_errors[:5]+missing_module_refs[:5])
    reqs=trace['requirements']; cases=tests['cases']; req_ids={x['requirement_id'] for x in reqs}; case_ids={x['test_id'] for x in cases}
    # MR-08: artifact lifecycle is a closed, distinct taxonomy with explicit transitions/use rules.
    lifecycle_names={'AccessibilityReport','ArchitecturePlan','ChangeSet','CommonArtifact','DesignSpec','EvaluationReport','ExecutionPlan','IntentRecordArtifact','OperationsReadiness','PerformanceReport','ProductSpec','SecurityAssessment','SourceSet','TestReport'}
    lifecycle_refs=all(schemas['$defs'][name]['properties']['status'].get('$ref')=='#/$defs/ArtifactLifecycleStatus' for name in lifecycle_names)
    lifecycle_data=schemas['$defs']['ArtifactLifecycleStatus']
    lifecycle_rules=set(lifecycle_data.get('enum',[]))==set(lifecycle_data.get('x-hras-use-rules',{})) and set(lifecycle_data.get('enum',[]))==set(lifecycle_data.get('x-hras-allowed-transitions',{}))
    lifecycle_transitions=artifact_lifecycle_transition_allowed('DRAFT','IN_PROGRESS') and not artifact_lifecycle_transition_allowed('DRAFT','VALIDATED') and not artifact_lifecycle_transition_allowed('SUPERSEDED','IN_PROGRESS') and not artifact_lifecycle_transition_allowed('IN_PROGRESS','IN_PROGRESS')
    check('artifact-status-enums-explicit-and-separated',lifecycle_refs and lifecycle_rules and lifecycle_transitions and artifact_lifecycle_mutation_tests(schemas))
    # MR-09: INCONCLUSIVE is explicit and totals derive from per-case outcomes.
    check('inconclusive-result-aggregation-fail-closed','INCONCLUSIVE' in schemas['$defs']['TestCaseResult']['properties']['status']['enum'] and 'INCONCLUSIVE' in schemas['$defs']['ConformanceRunReport']['properties']['summary_counts']['required'] and inconclusive_aggregation_mutation_test())
    # MR-11: measurements link back to a declared metric and method/unit.
    check('performance-metric-referential-integrity',performance_semantics_schema_test(schemas) and performance_metric_mutation_test())
    # MR-12: all YAML examples are deliberately marked shorthand, not valid executable instances.
    check('yaml-examples-explicitly-non-normative',yaml_examples_disclosed_as_non_normative(spec))
    # MR-16: internal record, persisted envelope, producer mapping and namespace rules.
    intent_modules=[m for m in module_io.get('modules',[]) if m.get('module_id')=='INTENT']
    intent_binding= len(intent_modules)==1 and intent_modules[0].get('input_schema_id')=='IntentCaptureRequest' and intent_modules[0].get('output_schema_id')=='IntentRecord'
    check('intent-record-and-source-reference-contracts-defined',intent_binding and schemas['$defs']['IntentRecordArtifact']['properties']['payload'].get('$ref')=='#/$defs/IntentRecord' and source_reference_semantics_valid(cases,req_ids,tests.get('source_spec_version',SPEC_VERSION)))
    route_subroutes=schemas['$defs']['RouteDecision']['properties']['subroutes']['items']['enum']
    alias_ok=policy.get('subroute_aliases',{}).get('RESEARCH')=='EVIDENCE_RESEARCH' and normalize_subroute_token('RESEARCH',policy,schemas)=='EVIDENCE_RESEARCH' and normalize_subroute_token('EVIDENCE_RESEARCH',policy,schemas)=='EVIDENCE_RESEARCH'
    try: normalize_subroute_token('UNKNOWN_SUBROUTE',policy,schemas); unknown_rejects=False
    except Exception: unknown_rejects=True
    prompt_text=(ROOT/'HRAS_v20_Compiled_Core_Prompt.md').read_text(encoding='utf-8')
    alias_trace_ok=trace.get('routing_alias_policy_ref')==policy.get('subroute_alias_policy',{}).get('id') and trace.get('routing_alias_policy',{}).get('canonical_value')=='EVIDENCE_RESEARCH'
    alias_docs_ok='legacy input token `RESEARCH` is normalized to `EVIDENCE_RESEARCH`' in spec and 'legacy subroute input token `RESEARCH` MUST be normalized to `EVIDENCE_RESEARCH`' in prompt_text
    check('canonical-evidence-research-subroute', 'EVIDENCE_RESEARCH' in route_subroutes and 'RESEARCH' not in route_subroutes and alias_ok and unknown_rejects and alias_trace_ok and alias_docs_ok,route_subroutes)
    reqs=trace['requirements']; cases=tests['cases']; req_ids={x['requirement_id'] for x in reqs}; case_ids={x['test_id'] for x in cases}
    version_identity_errors=package_tool.verify_version_identity(ROOT)
    check('version-identity-consistent',tests['spec_version']==SPEC_VERSION and trace['spec_version']==SPEC_VERSION and f'v{SPEC_VERSION}' in spec and schemas.get('$id')==f'urn:hras:schemas:{SPEC_VERSION}' and VERSION_RECORD.get('spec_version')==SPEC_VERSION and module_io.get('spec_version')==SPEC_VERSION and not version_identity_errors,version_identity_errors[:8])
    manifest_status=load('HRAS_v20_Package_Manifest.json').get('schema_registry_status')
    check('schema-registry-freeze-status-is-explicit-and-bound', VERSION_RECORD.get('schema_registry_status') in {'OPEN_NOT_FROZEN','FROZEN'} and manifest_status==VERSION_RECORD.get('schema_registry_status'), f"version={VERSION_RECORD.get('schema_registry_status')}; manifest={manifest_status}")
    check('test-count-derived',tests['case_count']==len(cases),f"declared={tests['case_count']} actual={len(cases)}")
    rendered_req_ids=set(re.findall(r'^\| (HRAS-R\d{3}) \|',spec,re.M))
    check('requirement-count-derived',len(req_ids)==len(reqs) and rendered_req_ids==req_ids,f'registry_count={len(reqs)} rendered_count={len(rendered_req_ids)}')
    check('test-IDs-unique',len(case_ids)==len(cases),f'count={len(cases)}')
    check('all-requirements-rendered',set(re.findall(r'^\| (HRAS-R\d{3}) \|',spec,re.M))==req_ids)
    check('all-requirements-have-test-or-disposition',all(r.get('test_ids') for r in reqs))
    trace_errors=validate_bidirectional_trace(trace,cases,reqs)
    check('bidirectional-trace-valid',not trace_errors,trace_errors[:15])
    check('bidirectional-trace-mutations-detected',trace_mutation_tests(trace,cases))
    check('all-case-refs-known',all(set(c.get('requirement_refs',[]))<=req_ids and bool(c.get('requirement_refs')) for c in cases))
    check('canonical-policy-IDs',set(x['id'] for x in [policy['non_waivable_policy'],policy['restricted_actions_policy'],policy['release_gate_policy'],policy['case_hash_policy']])=={'HRAS-POL-NW-001','HRAS-POL-ACTION-001','HRAS-POL-GATE-001','HRAS-POL-HASH-001'})
    check('case-hashes-recomputed',all(c.get('case_hash')==case_hash(c) for c in cases))
    package_integrity_errors=package_tool.verify_manifest_inventory(ROOT) + package_tool.verify_checksum_file(ROOT)
    check('package-file-hashes-sizes-and-checksum-coverage',not package_integrity_errors,package_integrity_errors[:20])
    check('all-cases-have-typed-oracle',all(c.get('oracle_assertions') and all(a.get('target') and a.get('evidence_path') and a.get('source_ref') for a in c['oracle_assertions']) for c in cases))
    check('oracle-required-field-mutation-detected',oracle_mutation_test(schemas,cases[0]))
    check('pass-criteria-distinct-from-description',all(c.get('pass_criteria')!=[c.get('expected_behavior')] for c in cases))
    # Check that every typed oracle is represented in both positive and negative criteria.
    criteria_complete=all(
      all(a['assertion_id'] in '\n'.join(c.get('pass_criteria',[])) for a in c.get('oracle_assertions',[])) and
      all(a['assertion_id'] in '\n'.join(c.get('failure_condition',[])) for a in c.get('oracle_assertions',[]))
      for c in cases)
    check('oracle-assertions-linked-to-pass-and-fail-criteria',criteria_complete)
    check('case-specific-failure-conditions',len({c['failure_condition'][0] for c in cases})==len(cases) and all(c['test_id'] in ' '.join(c['failure_condition']) for c in cases))
    check('observation-envelope-provenance-assertions',all(len(c['oracle_assertions'])>=5 and {a['target'] for a in c['oracle_assertions']} >= {'$.provenance.test_id','$.provenance.spec_version','$.provenance.fixture_declaration_hash','$.provenance.environment_profile_ref'} for c in cases))
    check('fixture-hash-semantics-explicit',all(c['fixture_binding_status']=='UNMATERIALIZED' and c['fixture_hash'] is None and c['environment_id'] is None and bool(re.fullmatch(r'sha256:[0-9a-f]{64}',c.get('fixture_declaration_hash',''))) for c in cases))
    check('environment-profiles-declared',all(c.get('environment_profile_ref') in schemas['$defs']['TestCaseSpec']['properties']['environment_profile_ref']['enum'] for c in cases))
    check('adversarial-trials-bounded-and-repeated',all(c['trial_policy']['minimum_trials']>=3 and c['trial_policy']['maximum_trials']>=3 and c['trial_policy']['stochasticity_class']=='ADVERSARIAL' for c in cases if c['test_level']=='SECURITY' or c['test_id'].startswith('SEC-')))
    check('source-and-case-trace-projections-equal',source_reference_semantics_valid(cases,req_ids,tests.get('source_spec_version',SPEC_VERSION)))
    check('pass-for-unmaterialized-fixture-rejected',_case_pass_mutation_rejected(schemas,cases[0]))
    check('observation-envelope-validates',not _observation_schema_errors(schemas,cases[0],tests))
    check('observation-envelope-missing-provenance-rejected',_observation_missing_provenance_rejected(schemas,cases[0],tests))
    check('unmaterialized-observation-cannot-pass-provenance-controller',bool(validate_observation_provenance(cases[0],_observation_sample(cases[0],tests),None)))
    check('materialized-matching-observation-provenance-accepted',_materialized_provenance_positive(cases[0],tests))
    check('materialized-mismatched-fixture-hash-rejected',_materialized_provenance_mismatch_rejected(cases[0],tests))
    check('run-manifest-config-mismatch-rejected',_run_manifest_mismatch_rejected(cases[0],tests))
    check('restricted-actions-present',_restricted_actions_complete(policy))
    check('policy-hash-contract-explicit',policy['case_hash_policy']['canonicalization']=='RFC 8785 JSON Canonicalization Scheme (JCS)' and any('Reject duplicate JSON object names' in x for x in policy['case_hash_policy']['rules']))
    check('all-trial-policies-bounded',all(not validate_trial_policy(c['trial_policy']) for c in cases))
    check('no-test-claims-execution',tests['status']=='PROPOSED_NOT_EXECUTED' and all(c['status']=='NOT_RUN' for c in cases))
    check('fixtures-not-pretended-materialized',all(c['fixture_binding_status']=='UNMATERIALIZED' for c in cases))
    check('main-workflow-failure-blocks',next(c for c in cases if c['test_id']=='PQ-003')['release_blocking'] is True)
    check('all-BLOCKER-cases-block',all(c['release_blocking'] for c in cases if c['failure_severity']=='BLOCKER'))
    check('nonblocking-HIGH-documented',all(c.get('release_impact_policy_ref') and len(c.get('release_blocking_rationale',''))>=12 for c in cases if c['failure_severity']=='HIGH' and not c['release_blocking']))
    check('general-and-incident-modes',{'GENERAL_ASSISTANCE','INCIDENT_RESPONSE'}<=set(schemas['$defs']['RouteDecision']['properties']['primary_mode']['enum']))
    check('tool-action-states-present',{'PREPARING_ACTION','AUTHORIZED_ACTION','EXECUTING_ACTION','RECONCILING_ACTION'}<=set(schemas['$defs']['StateTransition']['properties']['from_state']['enum']))
    check('new-statuses-present',{'LOCAL_VERIFIED','STAGING_READY','DEPLOYED_UNVERIFIED','ACTION_EXECUTED_UNVERIFIED','ACTION_VERIFIED','RECONCILIATION_REQUIRED'}<=set(schemas['$defs']['DeliveryManifest']['properties']['delivery_status']['enum']))
    check('validation-status-has-UNKNOWN','UNKNOWN' in schemas['$defs']['ValidationResult']['properties']['status']['enum'])
    check('schema-conditionals-present',sum(len(s.get('allOf',[])) for s in schemas['$defs'].values())>=10)
    check('authorization-crypto-evidence-required-for-allow',all(k in next(x['then'] for x in schemas['$defs']['AuthorizationDecision']['allOf'] if x.get('if',{}).get('properties',{}).get('decision',{}).get('const')=='ALLOW')['required'] for k in ['signature_evidence_ref','signature_algorithm','key_id','signed_payload_hash','verification_timestamp','verifier_id','grant_id']))
    check('exception-independent-approval-enforced',all(k in next(x['then']['required'] for x in schemas['$defs']['ExceptionRecord']['allOf'] if x.get('if',{}).get('properties',{}).get('status',{}).get('const')=='APPROVED') for k in ['proposer_id','approver_id','approver_authority','approver_independence_evidence_ref','approver_policy_version','approved_at','expires_at','review_at','evidence_refs']))
    check('non-waivable-condition-registry-explicit',len(policy['non_waivable_policy'].get('condition_registry',[]))==len(policy['non_waivable_policy'].get('conditions',[])) and all(x.get('non_waivable') is True and x.get('condition_id') for x in policy['non_waivable_policy']['condition_registry']))
    check('unknown-outcome-cannot-submit',not operation_may_submit({'state':'OUTCOME_UNKNOWN','must_not_resubmit':True,'submit_count':1}))
    check('tool-action-skip-is-rejected',not transition_allowed('TOOL_ACTION','PREPARING_ACTION','DELIVERED'))
    workflow=load('HRAS_v20_Workflow_Transitions.json')
    workflow_errors=validate_workflow_transition_registry(workflow,schemas)
    check('canonical-workflow-registry-valid',not workflow_errors,workflow_errors[:12])
    check('canonical-workflow-covers-all-modes',workflow.get('mode_count')==len(schemas['$defs']['RouteDecision']['properties']['primary_mode']['enum'])==len(workflow.get('modes',[])))
    check('workflow-retry-bounded-and-strategy-pivoted',retry_transition_allowed('IDEA_TO_PRODUCTION','VERIFYING','IMPLEMENTING',2,False) and not retry_transition_allowed('IDEA_TO_PRODUCTION','VERIFYING','IMPLEMENTING',3,False) and retry_transition_allowed('IDEA_TO_PRODUCTION','VERIFYING','IMPLEMENTING',3,True) and not retry_transition_allowed('IDEA_TO_PRODUCTION','VERIFYING','IMPLEMENTING',4,True) and retry_transition_allowed('IDEA_TO_PRODUCTION','VERIFYING','BLOCKED',4,False))
    retry_policy=workflow.get('repair_loop_policy',{})
    check('retry-policy-explicitly-enforces-no-progress-and-repeated-failure',retry_policy.get('no_progress_change_approach_at_occurrences')==2 and retry_policy.get('same_failure_change_approach_at_occurrences')==3 and repair_loop_disposition(1,2,False,True)=='CHANGE_APPROACH' and repair_loop_disposition(3,0,False,True)=='CHANGE_APPROACH' and repair_loop_disposition(3,0,True,True)=='RETRY_ALLOWED' and repair_loop_disposition(4,0,True,True)=='BLOCKED' and repair_loop_disposition(1,0,False,False)=='EXHAUSTED')
    north=load('HRAS_v20_North_Star_Subrequirement_Map.json')
    north_errors=validate_contract(schemas,'NorthStarSubrequirementMap',north)
    check('north-star-subrequirement-map-valid-and-canonical',not north_errors and north.get('core_north_stars')==[f'HRAS-NS-{i:03d}' for i in range(1,6)] and north.get('no_new_top_level_north_star') is True and north.get('independent_review_status')=='PENDING',north_errors[:8])
    check('north-star-map-references-existing-requirements-and-tests',all(set(m.get('requirement_refs',[]))<=req_ids and set(m.get('test_ids',[]))<=case_ids for m in north.get('concept_mappings',[])))
    coverage=load('HRAS_v20_Workflow_Coverage_Report.json')
    coverage_errors=validate_contract(schemas,'WorkflowCoverageReport',coverage)
    check('workflow-coverage-report-valid-and-current',not coverage_errors and coverage==package_tool.generate_workflow_coverage_report(ROOT),coverage_errors[:8])
    check('workflow-retry-edges-fail-closed-on-cycle-mutation',any('unbounded cycle remains' in e for e in validate_workflow_transition_registry({**deepcopy(workflow),'retry_edges':[x for x in deepcopy(workflow.get('retry_edges',[])) if not (x.get('primary_mode')=='IDEA_TO_PRODUCTION' and x.get('from_state')=='VERIFYING' and x.get('to_state')=='IMPLEMENTING')]},schemas)))
    check('annex-b-policy-registry-hash-bound',f"**Registry SHA-256 (generated):** `sha256:{hashlib.sha256((ROOT/'HRAS_v20_Policy_Registry.json').read_bytes()).hexdigest()}`" in spec)
    check('new-modules-registered',{'LIFECYCLE','SECURITY_POSTURE'} <= {m.get('module_id') for m in module_io.get('modules',[])})
    check('release-schema-requires-evidence',all(k in schemas['$defs']['ValidationResult']['properties'] for k in ['artifact_identity_verified','quality_profile_frozen','evidence_freshness_status','applicable_gates_passed','independent_review_passed','masterpiece_evidence_complete','user_outcome_validation_status','exception_refs']))
    lifecycle_rule_ids={r.get('x-hras-id') for r in schemas['$defs']['LifecycleAndOperabilitySpec'].get('allOf',[]) if isinstance(r,dict)}
    check('lifecycle-operability-crossfield-invariants',{'life-backup-required','life-migration-required','life-rollback-required','life-recovery-required','life-cost-estimate','life-not-applicable'} <= lifecycle_rule_ids)
    check('security-posture-pass-requires-independent-review',any(r.get('x-hras-id')=='security-pass-requires-review' for r in schemas['$defs']['SecurityPostureReport'].get('allOf',[]) if isinstance(r,dict)))
    check('lifecycle-security-semantic-validators-wired',callable(validate_lifecycle_operability_spec) and callable(validate_security_posture_report))

    check('invalid-route-enum-rejected',route_enum_negative(schemas))
    check('ALLOW-without-verified-signature-rejected',auth_negative(schemas))
    check('duplicate-json-keys-rejected',duplicate_key_test())
    check('self-approved-exception-rejected',not validate_exception_independence({'proposer_id':'x','approver_id':'x','approver_independence_evidence_ref':'e','approver_policy_version':'1'}))
    case_errors=[]
    for c in cases: case_errors.extend(f"{c['test_id']}: {e}" for e in validate_contract(schemas,'TestCaseSpec',c))
    check('all-test-cases-schema-valid',not case_errors,case_errors[:12])
    try:
        a=spec.index('## Annex A — Machine-readable control-plane schemas'); fs=spec.index('```json\n',a)+len('```json\n'); fe=spec.index('\n```',fs)
        embedded=strict_json_loads(spec[fs:fe]); check('embedded-schema-equals-companion',embedded==schemas)
    except Exception as e: check('embedded-schema-equals-companion',False,repr(e))
    check('annex-order',spec.index('## 28. Final canonical directive')<spec.index('## Annex A — Machine-readable control-plane schemas')<spec.index('## Annex B — Policy registry reference (generated, explanatory only)')<spec.index('## Annex C — v20 implementation'))
    check('INP-threshold-corrected','INP ≤ 200 milliseconds' in spec)
    check('obsolete-T-011-not-used',not re.search(r'(?<!AC-)\bT-011\b',(ROOT/'HRAS_v20_Change_Log_and_Traceability_Matrix.md').read_text(encoding='utf-8')))
    check('no-stale-v19-test-count-claims',not re.search(r'\b119 of 122\b|\b72/72\b',spec))
    # Validate duplicated claim scores use exactly 100 total weight in the human-readable quality report.
    score=(ROOT/'HRAS_v20_Final_Quality_Assessment.md').read_text(encoding='utf-8')
    weights=[int(x) for x in re.findall(r'^\| [^|]+ \| (\d+) \| [0-5](?:\.\d)? \|',score,re.M)]
    check('quality-score-weights-sum-100',sum(weights)==100,f'weights={weights}; total={sum(weights)}')
    failed=[x for x in checks if x['status']!='PASS']
    report_root=resolve_report_root(report_dir)
    report_root.mkdir(parents=True,exist_ok=True)
    tracked_inputs=['HRAS_v20_Workflow_Transitions.json','HRAS_v20_Governance_Decisions.json','HRAS_v20_Version.json','HRAS_v20_Canonical_Autonomous_Production_Grade_Spec.md','HRAS_v20_Compiled_Core_Prompt.md','HRAS_v20_Contract_Schemas.json','HRAS_v20_Policy_Registry.json','HRAS_v20_Module_IO_Registry.json','HRAS_v20_Requirement_Traceability.json','HRAS_v20_Test_Cases.json','HRAS_v20_Conformance_and_Adversarial_Test_Suite.md','HRAS_v20_Requirements_and_Design_Decisions.md','HRAS_v20_reference_controller.py','HRAS_v20_static_validator.py','HRAS_v20_package_tool.py','README_HRAS_v20_Package.md','HRAS_v20_Workflow_Transitions.json','HRAS_v20_Governance_Decisions.json','HRAS_v20_North_Star_Subrequirement_Map.json','HRAS_v20_Workflow_Coverage_Report.json','Visi HRAS.md','HRAS_v20_Vision_Provenance.json','HRAS_v20_Vision_Clause_Inventory.csv','.python-version','requirements-lock.txt']
    input_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in tracked_inputs}
    result={'report_version':SPEC_VERSION,'spec_id':VERSION_RECORD.get('spec_id'),'scope':'static artifacts, schemas, module I/O contracts, policy references, and traceability; no target LLM runtime exercised','status':'PASS' if not failed else 'FAIL','assertion_count':len(checks),'passed':len(checks)-len(failed),'failed':len(failed),'observed_at':datetime.now(timezone.utc).isoformat(),'command':shlex.join([sys.executable, *sys.argv]),'exit_code':0 if not failed else 1,'environment':{'python_executable':sys.executable,'python_version':sys.version.split()[0],'platform':platform.platform(),'working_directory':os.getcwd()},'input_sha256':input_hashes,'test_registry_counts':{'cases':len(cases),'typed_assertions':sum(len(c.get('oracle_assertions',[])) for c in cases),'not_run':sum(c.get('status')=='NOT_RUN' for c in cases),'fixtures_unmaterialized':sum(c.get('fixture_binding_status')=='UNMATERIALIZED' for c in cases)},'checks':checks}
    (report_root/'HRAS_v20_Static_Validation_Report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# HRAS v20 Static Validation Report','','**Version:** `'+SPEC_VERSION+'`','**Status:** `'+result['status']+'`',f"**Assertions:** {result['passed']}/{result['assertion_count']} passed; {result['failed']} failed.",f"**Observed at (UTC):** {result['observed_at']}",'','**Scope limit:** this validates static artifact structure, schemas, module I/O contracts, policy references and traceability. It does not execute the target LLM, production authorization broker, durable operation store, real tool adapters, isolated domain oracle, or deployment target. Runtime test cases retain their actual source statuses.','', '| Assertion | Status | Details |','|---|---|---|']
    for x in checks: lines.append(f"| {x['check']} | {x['status']} | {x['details'].replace('|','\\|').replace(chr(10),' ')[:220]} |")
    (report_root/'HRAS_v20_Static_Validation_Report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'assertion_count':len(checks),'passed':len(checks)-len(failed),'failed':len(failed),'report_dir':str(report_root)},indent=2))
    if failed: print(json.dumps(failed,ensure_ascii=False,indent=2)); return 1
    return 0
if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Validate HRAS static package artifacts without running the target runtime.')
    parser.add_argument('--report-dir',type=Path,default=None,help='explicitly choose a report output directory; default is a new temporary directory outside the package')
    args=parser.parse_args()
    raise SystemExit(main(args.report_dir))
