from __future__ import annotations
import copy, json, shutil
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
import HRAS_v20_package_tool as package_tool
from HRAS_v20_reference_controller import strict_json_loads, validate_contract, case_hash, current_spec_version, artifact_lifecycle_transition_allowed, aggregate_test_case_results, validate_conformance_run_report, validate_performance_report_semantics, validate_intent_record_artifact, normalize_subroute_token, authorize_decision, allowed_delivery_status, load_workflow_transition_registry, validate_workflow_transition_registry, retry_transition_allowed, transition_allowed, exception_is_valid_for_use, validate_lifecycle_operability_spec, validate_security_posture_report, repair_loop_disposition

ROOT=Path(__file__).resolve().parents[1]

def load(name):
    return strict_json_loads((ROOT/name).read_text(encoding='utf-8'))


def test_schema_registry_freeze_status_is_explicit_and_manifest_bound():
    from HRAS_v20_package_tool import verify_version_identity
    version=load('HRAS_v20_Version.json')
    manifest=load('HRAS_v20_Package_Manifest.json')
    assert version['schema_registry_status']=='OPEN_NOT_FROZEN'
    assert manifest['schema_registry_status']==version['schema_registry_status']
    mutated=copy.deepcopy(manifest); mutated['schema_registry_status']='FROZEN'
    (ROOT/'HRAS_v20_Package_Manifest.json').write_text(json.dumps(mutated,indent=2)+'\n',encoding='utf-8')
    try:
        errors=verify_version_identity(ROOT)
        assert any('schema_registry_status' in e for e in errors)
    finally:
        (ROOT/'HRAS_v20_Package_Manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


def test_active_version_source_and_identity_are_consistent():
    assert current_spec_version() == '20.0.0-rc4'
    assert not package_tool.verify_version_identity(ROOT)


def test_version_identity_mutation_fails_closed(tmp_path):
    # Each independent identity surface is mutated in an isolated copy; candidate source stays unchanged.
    names=['HRAS_v20_Version.json','HRAS_v20_Contract_Schemas.json','HRAS_v20_Policy_Registry.json','HRAS_v20_Requirement_Traceability.json','HRAS_v20_Test_Cases.json','HRAS_v20_Module_IO_Registry.json','HRAS_v20_Package_Manifest.json','HRAS_v20_Canonical_Autonomous_Production_Grade_Spec.md','HRAS_v20_Compiled_Core_Prompt.md','README_HRAS_v20_Package.md','HRAS_v20_Package_Manifest.md']
    for name in names: (tmp_path/name).write_bytes((ROOT/name).read_bytes())
    mutations=[
      ('HRAS_v20_Version.json',lambda x: x.update(spec_version='20.0.0-rc3')),
      ('HRAS_v20_Contract_Schemas.json',lambda x: x.update(**{'$id':'urn:hras:schemas:20.0.0-rc3'})),
      ('HRAS_v20_Policy_Registry.json',lambda x: x.update(version='20.0.0-rc3')),
      ('HRAS_v20_Requirement_Traceability.json',lambda x: x.update(spec_version='20.0.0-rc3')),
      ('HRAS_v20_Test_Cases.json',lambda x: x.update(spec_version='20.0.0-rc3')),
      ('HRAS_v20_Module_IO_Registry.json',lambda x: x.update(spec_version='20.0.0-rc3')),
      ('HRAS_v20_Package_Manifest.json',lambda x: x.update(version='20.0.0-rc3')),
    ]
    for index,(name,mutate) in enumerate(mutations):
      scratch=tmp_path/f'mutation-{index}'; shutil.copytree(tmp_path,scratch,ignore=shutil.ignore_patterns('mutation-*'))
      path=scratch/name; obj=json.loads(path.read_text(encoding='utf-8')); mutate(obj); path.write_text(json.dumps(obj),encoding='utf-8')
      assert package_tool.verify_version_identity(scratch), f'identity mutation was not detected: {name}'


def test_release_state_identity_rejects_stale_version_reference(tmp_path):
    # Regression for audit finding F-06: an active rc4 identity must not coexist
    # with a release-state sentence that still names rc1.
    scratch=tmp_path/'pkg'
    shutil.copytree(ROOT,scratch,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git'))
    spec=scratch/'HRAS_v20_Canonical_Autonomous_Production_Grade_Spec.md'
    text=spec.read_text(encoding='utf-8')
    active='HRAS v20.0.0-rc4 remains `CANDIDATE`'
    stale='HRAS v20.0.0-rc1 remains `CANDIDATE`'
    assert text.count(active)==1, 'expected one active release-state identity sentence'
    spec.write_text(text.replace(active,stale,1),encoding='utf-8')
    errors=package_tool.verify_version_identity(scratch)
    assert any('stale release-state identity' in error and '20.0.0-rc1' in error for error in errors), errors


def test_manifest_missing_path_mutation_is_detected(tmp_path):
    # Exercise the actual production checker against a scratch copy; the source manifest stays untouched.
    scratch=tmp_path/'pkg'
    shutil.copytree(ROOT,scratch,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git'))
    manifest=package_tool.load_json(scratch,package_tool.MANIFEST)
    manifest['files'].append({'path':'missing/nonexistent.json','size_bytes':1,'sha256':'0'*64})
    (scratch/package_tool.MANIFEST).write_text(json.dumps(manifest),encoding='utf-8')
    errors=package_tool.verify_manifest_inventory(scratch)
    assert any('manifest path missing: missing/nonexistent.json' in e for e in errors)


def test_manifest_inventory_and_checksums_pass():
    assert not package_tool.verify_manifest_inventory(ROOT)
    assert not package_tool.verify_checksum_file(ROOT)


def test_trace_explicit_edges_must_equal_bidirectional_projections():
    from HRAS_v20_reference_controller import validate_bidirectional_trace
    trace=load('HRAS_v20_Requirement_Traceability.json')
    cases=load('HRAS_v20_Test_Cases.json')['cases']
    requirements=trace['requirements']
    assert not validate_bidirectional_trace(trace,cases,requirements)
    # The explicit edge list is an independent integrity surface, not a decorative cache.
    mutations=[]
    empty=copy.deepcopy(trace); empty['edges']=[]; mutations.append(empty)
    truncated=copy.deepcopy(trace); truncated['edges'].pop(); mutations.append(truncated)
    duplicate=copy.deepcopy(trace); duplicate['edges'].append(copy.deepcopy(duplicate['edges'][0])); mutations.append(duplicate)
    reversed_edge=copy.deepcopy(trace); edge=reversed_edge['edges'][0]; edge['requirement_id'],edge['test_id']=edge['test_id'],edge['requirement_id']; mutations.append(reversed_edge)
    forged=copy.deepcopy(trace); forged['edges'].append({'requirement_id':requirements[0]['requirement_id'],'test_id':'FORGED-TEST'}); mutations.append(forged)
    for mutation in mutations:
        assert validate_bidirectional_trace(mutation,cases,requirements), mutation.get('edges',[])[:1]
    # Malformed nested values must be reported, not raise TypeError from set construction.
    malformed=copy.deepcopy(trace); malformed['edges']=[]; malformed_cases=copy.deepcopy(cases); malformed_cases[0]['requirement_refs']=[{'not':'hashable'}]
    assert validate_bidirectional_trace(malformed,malformed_cases,requirements)
    malformed_requirements=copy.deepcopy(requirements); malformed_requirements[0]['test_ids']=[{'not':'hashable'}]
    assert validate_bidirectional_trace(trace,cases,malformed_requirements)


def test_operation_submit_preflight_requires_bound_record_and_trusted_current_authorization():
    from datetime import datetime, timezone
    from HRAS_v20_reference_controller import operation_may_submit
    now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    request_hash='sha256:'+'a'*64
    record={
      'operation_id':'op-1','task_id':'task-1','tool_id':'provider.submit','side_effect_class':'IDEMPOTENT_MUTATION',
      'idempotency_key':'idem-1','target_resource':'service:demo','request_hash':request_hash,
      'authorization_ref':'authorization:1','state':'AUTHORIZED','provider_operation_id':None,
      'submit_count':0,'reconciliation_refs':[],'result_ref':None,'created_at':now,'updated_at':now,
      'must_not_resubmit':False,
    }
    assert operation_may_submit(record,expected_request_hash=request_hash,trusted_authorization_verify_callback=lambda _r:True)
    # A status-only record must never authorize a consequential submission.
    assert not operation_may_submit({'state':'AUTHORIZED','submit_count':0})
    assert not operation_may_submit(record,expected_request_hash=request_hash)
    assert not operation_may_submit(record,expected_request_hash='sha256:'+'b'*64,trusted_authorization_verify_callback=lambda _r:True)
    for result in ('ALLOW',1,False,None,{}):
        assert not operation_may_submit(record,expected_request_hash=request_hash,trusted_authorization_verify_callback=lambda _r,result=result:result)
    assert not operation_may_submit(record,expected_request_hash=request_hash,trusted_authorization_verify_callback=lambda _r:False)  # stale/expired/revoked auth
    def unavailable(_r): raise RuntimeError('authorization service unavailable')
    assert not operation_may_submit(record,expected_request_hash=request_hash,trusted_authorization_verify_callback=unavailable)
    for field,value in [('authorization_ref',None),('idempotency_key',None),('must_not_resubmit',True),('submit_count',1),('state','OUTCOME_UNKNOWN')]:
        bad=copy.deepcopy(record); bad[field]=value
        assert not operation_may_submit(bad,expected_request_hash=request_hash,trusted_authorization_verify_callback=lambda _r:True), field


def test_schema_registry_and_module_io_contracts_are_complete():
    schemas=load('HRAS_v20_Contract_Schemas.json')
    module_io=load('HRAS_v20_Module_IO_Registry.json')
    Draft202012Validator.check_schema(schemas)
    assert {'IdeaExpansion','BrandContentSpec','EvidenceLedger'} <= set(schemas['$defs'])
    assert not validate_contract(schemas,'ModuleIOContractRegistry',module_io)
    refs={m['input_schema_id'] for m in module_io['modules']} | {m['output_schema_id'] for m in module_io['modules']}
    assert refs <= set(schemas['$defs'])
    assert {'IdeaExpansion','BrandContentSpec','EvidenceLedger'} <= {m['output_schema_id'] for m in module_io['modules']}


def test_idea_expansion_positive_and_negative_contract():
    schemas=load('HRAS_v20_Contract_Schemas.json')
    valid={'expansion_id':'idea-1','schema_version':'1.0.0','spec_version':'20.0.0-rc4','source_intent_ref':'intent-1','product_class':'generic','target_users':['operators'],'problem_statement':'A concrete problem','desired_outcome':'A validated outcome','core_value_proposition':'Useful value','primary_user_journeys':[{'journey_id':'j1','user_goal':'complete task','success_outcome':'task complete'}],'acceptance_outcomes':['outcome independently verified'],'explicit_constraints':[],'assumption_refs':[],'evidence_refs':[],'created_at':'2026-10-28T12:00:00Z'}
    assert not validate_contract(schemas,'IdeaExpansion',valid)
    bad=copy.deepcopy(valid); bad['target_users']=[]
    assert validate_contract(schemas,'IdeaExpansion',bad)


def test_brand_content_contract_tracks_claims_and_asset_rights():
    schemas=load('HRAS_v20_Contract_Schemas.json')
    valid={'brand_spec_id':'brand-1','schema_version':'1.0.0','spec_version':'20.0.0-rc4','product_ref':'product-1','applicability':'OPTIONAL','audience':['intended users'],'positioning':'clear product position','voice_guidelines':['plain and direct'],'message_hierarchy':[{'message':'core message','purpose':'explain value','evidence_refs':[]}],'claim_register':[{'claim_id':'c1','claim':'claim wording','status':'UNVERIFIED','evidence_refs':[],'limitations':['not independently verified']}],'asset_rights':[{'asset_ref':'asset-1','rights_status':'UNKNOWN','source_ref':'source-unknown'}],'limitations':['asset rights require review'],'created_at':'2026-10-28T12:00:00Z'}
    assert not validate_contract(schemas,'BrandContentSpec',valid)
    bad=copy.deepcopy(valid); bad['claim_register'][0]['status']='VERIFIED'
    assert validate_contract(schemas,'BrandContentSpec',bad)


def test_evidence_ledger_epistemic_stage_and_hash_semantics():
    schemas=load('HRAS_v20_Contract_Schemas.json')
    valid={'ledger_id':'ledger-1','schema_version':'1.0.0','spec_version':'20.0.0-rc4','entries':[{'entry_id':'e1','claim_id':'claim-1','claim':'static structure is valid','stage':'STATIC_ANALYZED','result':'VERIFIED','source':'validator output','method':'schema and invariant checks','artifact_hash':'sha256:'+'a'*64,'observed_at':'2026-10-28T12:00:00Z','scope':'candidate package static checks','limitations':['does not prove runtime behavior'],'producer_id':'static-validator','verification_method':'reproduced command'}],'created_at':'2026-10-28T12:00:00Z','scope':'static checks','limitations':['no runtime execution']}
    assert not validate_contract(schemas,'EvidenceLedger',valid)
    bad=copy.deepcopy(valid); bad['entries'][0]['stage']='PRODUCTION_READY'
    assert validate_contract(schemas,'EvidenceLedger',bad)


def test_canonical_research_subroute_accepts_only_registered_name():
    schemas=load('HRAS_v20_Contract_Schemas.json')
    base={'decision_id':'d1','primary_mode':'RESEARCH_ONLY','subroutes':['EVIDENCE_RESEARCH'],'product_classes':['general'],'risk_class':'R1','scale_class':'S1','reason':'research route','applicable_module_ids':[],'required_gate_ids':[],'spec_version':'20.0.0-rc4','spec_hash':'sha256:'+'a'*64,'created_at':'2026-10-28T12:00:00Z'}
    assert not validate_contract(schemas,'RouteDecision',base)
    bad=copy.deepcopy(base); bad['subroutes']=['RESEARCH']
    assert validate_contract(schemas,'RouteDecision',bad)


def test_test_case_hashes_recomputed_after_rc4_versioning():
    tests=load('HRAS_v20_Test_Cases.json')
    assert tests['case_count']==len(tests['cases'])
    assert all(c['case_hash']==case_hash(c) for c in tests['cases'])
    assert all(c.get('spec_version') in (None,'20.0.0-rc4') for c in tests['cases'])


def test_artifact_lifecycle_status_is_closed_and_transitions_are_enforced():
    schemas=load('HRAS_v20_Contract_Schemas.json')
    good={'artifact_id':'a1','schema_version':'1.0.0','spec_version':'20.0.0-rc4','status':'REVIEW_READY','created_at':'2026-10-28T00:00:00Z','owner':'test-owner','evidence_refs':[],'assumption_refs':[],'issue_refs':[],'payload':{},'content_hash':'sha256:'+'a'*64}
    assert not validate_contract(schemas,'CommonArtifact',good)
    bad=copy.deepcopy(good); bad['status']='PRODUCTION_READY'
    assert validate_contract(schemas,'CommonArtifact',bad)
    assert artifact_lifecycle_transition_allowed('DRAFT','IN_PROGRESS')
    assert artifact_lifecycle_transition_allowed('REVIEW_READY','VALIDATED')
    assert not artifact_lifecycle_transition_allowed('DRAFT','VALIDATED')
    assert not artifact_lifecycle_transition_allowed('SUPERSEDED','IN_PROGRESS')


def test_inconclusive_counts_reconcile_and_never_pass_release_gate():
    rows=[{'test_id':'A','status':'PASS'},{'test_id':'B','status':'INCONCLUSIVE'}]
    counts=aggregate_test_case_results(rows)
    report={'selected_test_ids':['A','B'],'case_results':rows,'missing_results':[],'summary_counts':dict(counts),'overall_status':'PASS','release_blocking_failures':[]}
    assert validate_conformance_run_report(report)
    report['overall_status']='INCONCLUSIVE'
    assert not validate_conformance_run_report(report)
    report['summary_counts']['INCONCLUSIVE']=0
    assert validate_conformance_run_report(report)


def test_performance_measurements_require_declared_matching_metric():
    report={'payload':{'metrics':[{'metric_id':'p95','unit':'ms','method':'histogram'}], 'measurements':[{'metric_id':'p95','unit':'ms','method':'histogram','value':12,'observed_at':'2026-10-28T00:00:00Z','evidence_ref':'ev-1'}]}}
    assert not validate_performance_report_semantics(report)
    bad=copy.deepcopy(report); bad['payload']['measurements'][0]['metric_id']='unknown'
    assert validate_performance_report_semantics(bad)
    bad=copy.deepcopy(report); bad['payload']['measurements'][0]['unit']='s'
    assert validate_performance_report_semantics(bad)
    bad=copy.deepcopy(report); bad['payload']['measurements'][0]['method']='manual'
    assert validate_performance_report_semantics(bad)
    bad=copy.deepcopy(report); bad['payload']['metrics'].append(copy.deepcopy(bad['payload']['metrics'][0]))
    assert validate_performance_report_semantics(bad)


def test_intent_record_internal_and_persisted_wrapper_are_distinct_and_typed():
    schemas=load('HRAS_v20_Contract_Schemas.json')
    payload={'artifact_id':'intent-1','schema_version':'1.0.0','spec_version':'20.0.0-rc4','original_request':'Build a useful app','desired_outcome':'A verified application','explicit_constraints':['local-only'],'inferred_requirements':['needs user auth review'],'assumption_refs':[],'requested_mode':'IDEA_TO_PRODUCTION','route_ref':'route-1','risk_class':'R1','scale_class':'S1','authorization_notes':['No external actions authorized'],'scope_hash':'sha256:'+'b'*64,'created_at':'2026-10-28T00:00:00Z'}
    artifact={'artifact_id':'intent-1','artifact_type':'IntentRecord','schema_version':'1.0.0','spec_version':'20.0.0-rc4','status':'REVIEW_READY','created_at':'2026-10-28T00:00:00Z','owner':'test-owner','evidence_refs':[],'assumption_refs':[],'issue_refs':[],'payload':payload,'content_hash':'sha256:'+'a'*64}
    assert not validate_intent_record_artifact(schemas,artifact)
    bad=copy.deepcopy(artifact); bad['payload']['scope_hash']='not-a-hash'
    assert validate_intent_record_artifact(schemas,bad)
    bad=copy.deepcopy(artifact); bad['payload']['artifact_id']='different-id'
    assert validate_intent_record_artifact(schemas,bad)


def test_yaml_examples_are_explicitly_non_normative():
    text=(ROOT/'HRAS_v20_Canonical_Autonomous_Production_Grade_Spec.md').read_text(encoding='utf-8')
    for pos in [i for i in range(len(text)) if text.startswith('```yaml',i)]:
        assert 'intentionally incomplete and non-normative' in text[max(0,pos-220):pos]


def test_legacy_research_subroute_normalizes_before_schema_validation():
    policy=load('HRAS_v20_Policy_Registry.json'); schemas=load('HRAS_v20_Contract_Schemas.json')
    assert normalize_subroute_token('EVIDENCE_RESEARCH',policy,schemas)=='EVIDENCE_RESEARCH'
    assert normalize_subroute_token('RESEARCH',policy,schemas)=='EVIDENCE_RESEARCH'
    with pytest.raises(Exception): normalize_subroute_token('RESEARCHISH',policy,schemas)


# P0 regression coverage: authorization must fail closed on non-boolean verifier output.
def valid_authorization_decision():
    return {
      'decision_id':'decision-1','decision':'ALLOW','principal_id':'principal-1','issuer_id':'issuer-1',
      'action':'deploy','resource':'service:demo','environment':'staging','audience':'hras-controller',
      'scope':['deploy:service:demo'],'issued_at':'2026-10-28T00:00:00Z','expires_at':'2026-10-30T00:00:00Z',
      'token_id':'token-1','nonce':'nonce-1','policy_version':'policy-v1','atomicity_strategy':'idempotent',
      'audit_ref':'audit-1','reason_codes':[],'resource_limits':{'max_cost_minor':None,'max_records':None,'max_duration_ms':None,'allowed_target_hashes':[]},
      'signature_evidence_ref':'evidence:signature-1','signature_algorithm':'ed25519','key_id':'key-1',
      'signed_payload_hash':'sha256:'+'a'*64,'verification_timestamp':'2026-10-28T00:00:00Z','decided_at':'2026-10-28T00:00:00Z','verification_outcome':'VERIFIED',
      'verifier_id':'trusted-verifier-1','grant_id':'grant-1','signature_verified':True,
      'revocation_checked':True,'replay_checked':True,
    }


def test_authorization_callback_requires_literal_boolean_true():
    decision=valid_authorization_decision()
    assert authorize_decision(decision,lambda _:True)=='ALLOW'
    # Regression: prior bool(callback(...)) accepted the truthy string "DENY".
    for result in ('DENY','ALLOW',1,{},[],None,False):
        assert authorize_decision(decision,lambda _, result=result:result)=='INDETERMINATE'
    assert authorize_decision(decision,None)=='INDETERMINATE'
    assert authorize_decision(None,lambda _:True)=='INDETERMINATE'


def test_authorization_allow_requires_complete_evidence_and_boolean_controls():
    decision=valid_authorization_decision()
    for field in ('decision_id','principal_id','action','resource','environment','audience','issued_at','expires_at','token_id','nonce','policy_version','atomicity_strategy','audit_ref','signature_evidence_ref','signature_algorithm','key_id','signed_payload_hash','verification_timestamp','verifier_id','grant_id','resource_limits','scope'):
        mutated=copy.deepcopy(decision)
        mutated.pop(field)
        assert authorize_decision(mutated,lambda _:True)=='INDETERMINATE', field
    for field in ('signature_verified','revocation_checked','replay_checked'):
        mutated=copy.deepcopy(decision)
        mutated[field]=1
        assert authorize_decision(mutated,lambda _:True)=='INDETERMINATE', field
    mutated=copy.deepcopy(decision); mutated['signed_payload_hash']='not-a-digest'
    assert authorize_decision(mutated,lambda _:True)=='INDETERMINATE'
    mutated=copy.deepcopy(decision); mutated['scope']=[]
    assert authorize_decision(mutated,lambda _:True)=='INDETERMINATE'
    mutated=copy.deepcopy(decision); mutated['expires_at']='2020-01-01T00:00:00Z'
    assert authorize_decision(mutated,lambda _:True)=='INDETERMINATE'
    mutated=copy.deepcopy(decision); mutated['issued_at']='2099-01-01T00:00:00Z'
    assert authorize_decision(mutated,lambda _:True)=='INDETERMINATE'
    mutated=copy.deepcopy(decision); mutated['issued_at']='2026-10-29T00:00:00'; mutated['expires_at']='2026-10-30T00:00:00'
    assert authorize_decision(mutated,lambda _:True)=='INDETERMINATE'


def test_denial_and_indeterminate_never_call_verifier_or_authorize():
    def must_not_run(_):
        raise AssertionError('non-ALLOW decision must not call authorization verifier')
    base=valid_authorization_decision()
    denied={k:v for k,v in base.items() if k not in {'issued_at','expires_at','token_id','nonce','atomicity_strategy','resource_limits','signature_verified','revocation_checked','replay_checked','signature_evidence_ref','signature_algorithm','key_id','signed_payload_hash','verification_timestamp','verifier_id','grant_id'}}
    denied.update({'decision':'DENY','reason_codes':['POLICY_DENIED'],'verification_outcome':'REJECTED'})
    indeterminate={k:v for k,v in base.items() if k not in {'issued_at','expires_at','token_id','nonce','atomicity_strategy','resource_limits','signature_verified','revocation_checked','replay_checked','signature_evidence_ref','signature_algorithm','key_id','signed_payload_hash','verification_timestamp','verifier_id','grant_id'}}
    indeterminate.update({'decision':'INDETERMINATE','reason_codes':['VERIFIER_UNAVAILABLE'],'verification_outcome':'UNAVAILABLE'})
    assert authorize_decision(denied,must_not_run)=='DENY'
    assert authorize_decision(indeterminate,must_not_run)=='INDETERMINATE'
    assert authorize_decision({'decision':'UNKNOWN'},must_not_run)=='INDETERMINATE'


def test_deployed_and_verified_requires_trusted_observed_deployment_evidence():
    validation={'status':'PASS','failed_hard_gates':[],'unknown_hard_gates':[],
      'authorization_violations':[],'evidence_defects':[],'stale_evidence':[],
      'operations_needing_reconciliation':[],'budget_violations':[],
      'unresolved_blockers':[],'active_exceptions':[],
      'expected_artifact_hash':'sha256:'+'a'*64,'expected_environment_id':'staging:1',
      'expected_target_identity':'service:demo','expected_signed_manifest_hash':'sha256:'+'b'*64,
      'artifact_identity_verified':True,'quality_profile_frozen':True,'evidence_freshness_status':'PASS','applicable_gates_passed':True,'exception_refs':[]}
    policy={'delivery_status_enum':['DEPLOYED_AND_VERIFIED','DEPLOYED_UNVERIFIED','PRODUCTION_READY']}
    evidence={'deployment_id':'deployment-1','target_identity':'service:demo',
      'artifact_hash':'sha256:'+'a'*64,'environment_id':'staging:1',
      'schema_version':'1.0.0','observed_at':'2026-10-28T00:00:00Z','valid_until':'2026-10-30T00:00:00Z','deployment_evidence_ref':'evidence:deployment-1',
      'authorization_evidence_ref':'evidence:authorization-1','observer_id':'trusted-observer-1',
      'deployment_observed':True,'deployment_authorized':True,
      'post_deploy_health_status':'PASS','post_deploy_smoke_status':'PASS','signed_manifest_hash':'sha256:'+'b'*64,'signature_evidence_ref':'evidence:signature-1','verification_method':'trusted-provider-signed-manifest','verification_key_id':'key-1','verification_signature_ref':'signature:deployment-1','provider_id':'deployment-provider-1'}
    trusted=lambda _e,_v: True
    assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',validation,[],policy,deployment_observed=False,deployment_evidence=evidence,trusted_deployment_verify_callback=trusted)
    assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',validation,[],policy,deployment_observed=True)
    assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',validation,[],policy,deployment_observed=True,deployment_evidence=evidence,trusted_deployment_verify_callback=lambda _e,_v:'ALLOW')
    assert allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',validation,[],policy,deployment_observed=True,deployment_evidence=evidence,trusted_deployment_verify_callback=trusted)
    # Production readiness is not the same claim as an observed deployment.
    assert allowed_delivery_status('IDEA_TO_PRODUCTION','PRODUCTION_READY',validation,[],policy,deployment_observed=False)
    with_exception=copy.deepcopy(validation); with_exception['exception_refs']=['exc-1']
    assert not allowed_delivery_status('IDEA_TO_PRODUCTION','PRODUCTION_READY',with_exception,[],policy,deployment_observed=False)
    for field,value in [('deployment_authorized',False),('post_deploy_health_status','FAIL'),('post_deploy_smoke_status','NOT_RUN')]:
        bad=copy.deepcopy(evidence); bad[field]=value
        assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',validation,[],policy,deployment_observed=True,deployment_evidence=bad,trusted_deployment_verify_callback=trusted), field
    for field,value in [('artifact_hash','sha256:'+'b'*64),('environment_id','production:wrong'),('target_identity','service:wrong')]:
        bad=copy.deepcopy(evidence); bad[field]=value
        assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',validation,[],policy,deployment_observed=True,deployment_evidence=bad,trusted_deployment_verify_callback=trusted), field
    for field in ('deployment_id','target_identity','artifact_hash','environment_id','observed_at','deployment_evidence_ref','authorization_evidence_ref','observer_id'):
        bad=copy.deepcopy(evidence); bad.pop(field)
        assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',validation,[],policy,deployment_observed=True,deployment_evidence=bad,trusted_deployment_verify_callback=trusted), field
    bad=copy.deepcopy(evidence); bad['observed_at']='2099-01-01T00:00:00Z'
    assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',validation,[],policy,deployment_observed=True,deployment_evidence=bad,trusted_deployment_verify_callback=trusted)
    assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',validation,[],policy,deployment_observed=True,deployment_evidence=evidence,trusted_deployment_verify_callback=lambda _e,_v:False)
    assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',validation,[],policy,deployment_observed=True,deployment_evidence=evidence,trusted_deployment_verify_callback=lambda _e,_v:'PASS')
    def broken_verifier(_e,_v): raise RuntimeError('verifier unavailable')
    assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',validation,[],policy,deployment_observed=True,deployment_evidence=evidence,trusted_deployment_verify_callback=broken_verifier)
    bad_validation=copy.deepcopy(validation); bad_validation['expected_environment_id']='production:wrong'
    assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',bad_validation,[],policy,deployment_observed=True,deployment_evidence=evidence,trusted_deployment_verify_callback=trusted)
    bad_validation=copy.deepcopy(validation); bad_validation['stale_evidence']=['deployment observation is stale']
    assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',bad_validation,[],policy,deployment_observed=True,deployment_evidence=evidence,trusted_deployment_verify_callback=trusted)

def test_deployment_observed_must_be_literal_true():
    validation={'status':'PASS','failed_hard_gates':[],'unknown_hard_gates':[],
      'authorization_violations':[],'evidence_defects':[],'stale_evidence':[],
      'operations_needing_reconciliation':[],'budget_violations':[],
      'unresolved_blockers':[],'active_exceptions':[],
      'expected_artifact_hash':'sha256:'+'a'*64,'expected_environment_id':'staging:1',
      'expected_target_identity':'service:demo','expected_signed_manifest_hash':'sha256:'+'b'*64,
      'artifact_identity_verified':True,'quality_profile_frozen':True,'evidence_freshness_status':'PASS','applicable_gates_passed':True,'exception_refs':[]}
    policy={'delivery_status_enum':['DEPLOYED_AND_VERIFIED']}
    evidence={'deployment_id':'deployment-1','target_identity':'service:demo',
      'artifact_hash':'sha256:'+'a'*64,'environment_id':'staging:1',
      'schema_version':'1.0.0','observed_at':'2026-10-28T00:00:00Z','valid_until':'2026-10-30T00:00:00Z','deployment_evidence_ref':'evidence:deployment-1',
      'authorization_evidence_ref':'evidence:authorization-1','observer_id':'trusted-observer-1',
      'deployment_observed':True,'deployment_authorized':True,
      'post_deploy_health_status':'PASS','post_deploy_smoke_status':'PASS','signed_manifest_hash':'sha256:'+'b'*64,'signature_evidence_ref':'evidence:signature-1','verification_method':'trusted-provider-signed-manifest','verification_key_id':'key-1','verification_signature_ref':'signature:deployment-1','provider_id':'deployment-provider-1'}
    trusted=lambda _e,_v: True
    for observation in (False,None,0,1,'true','yes',{}):
        assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DEPLOYED_AND_VERIFIED',validation,[],policy,deployment_observed=observation,deployment_evidence=evidence,trusted_deployment_verify_callback=trusted)


def test_canonical_workflow_registry_drives_all_modes_and_bounded_retry_policy():
    schemas=load('HRAS_v20_Contract_Schemas.json'); workflow=load('HRAS_v20_Workflow_Transitions.json')
    assert not validate_workflow_transition_registry(workflow,schemas)
    registry,transition_map=load_workflow_transition_registry()
    assert set(transition_map)==set(schemas['$defs']['RouteDecision']['properties']['primary_mode']['enum'])
    assert len(transition_map)==13
    assert not transition_allowed('IDEA_TO_PRODUCTION','RECEIVED','DELIVERED')
    assert not transition_allowed('TOOL_ACTION','PREPARING_ACTION','DELIVERED')
    # Repair loops are guarded edges: ordinary transition API must reject them.
    assert not transition_allowed('IDEA_TO_PRODUCTION','VERIFYING','IMPLEMENTING')
    assert retry_transition_allowed('IDEA_TO_PRODUCTION','VERIFYING','IMPLEMENTING',2,False)
    assert not retry_transition_allowed('IDEA_TO_PRODUCTION','VERIFYING','IMPLEMENTING',2,False,True,2)
    assert repair_loop_disposition(1,2,False,True)=='CHANGE_APPROACH'
    assert repair_loop_disposition(3,0,False,True)=='CHANGE_APPROACH'
    assert repair_loop_disposition(3,0,True,True)=='RETRY_ALLOWED'
    assert repair_loop_disposition(4,0,True,True)=='BLOCKED'
    assert repair_loop_disposition(1,0,False,False)=='EXHAUSTED'
    assert not retry_transition_allowed('IDEA_TO_PRODUCTION','VERIFYING','IMPLEMENTING',3,False)
    assert retry_transition_allowed('IDEA_TO_PRODUCTION','VERIFYING','IMPLEMENTING',3,True)
    assert not retry_transition_allowed('IDEA_TO_PRODUCTION','VERIFYING','IMPLEMENTING',4,True)
    assert retry_transition_allowed('IDEA_TO_PRODUCTION','VERIFYING','BLOCKED',4,False)
    bad=copy.deepcopy(workflow); bad['modes'][0]['transitions'].append({'from_state':'DELIVERED','to_state':'VERIFYING'})
    assert validate_workflow_transition_registry(bad,schemas)
    bad=copy.deepcopy(workflow); bad['modes'].pop()
    assert validate_workflow_transition_registry(bad,schemas)
    # Removing a cycle guard reintroduces an unbounded cycle and must fail closed.
    bad=copy.deepcopy(workflow); guarded=next(x for x in bad['retry_edges'] if x['primary_mode']=='IDEA_TO_PRODUCTION' and x['from_state']=='VERIFYING' and x['to_state']=='IMPLEMENTING'); bad['retry_edges'].remove(guarded)
    assert any('unbounded cycle remains' in e for e in validate_workflow_transition_registry(bad,schemas))

def test_exception_reliant_delivery_cannot_claim_release_readiness():
    validation={'status':'PASS','failed_hard_gates':[],'unknown_hard_gates':[],'authorization_violations':[],'evidence_defects':[],'stale_evidence':[], 'operations_needing_reconciliation':[],'budget_violations':[],'unresolved_blockers':[],'active_exceptions':[], 'exception_refs':['exc-1'], 'artifact_identity_verified':True,'quality_profile_frozen':True,'evidence_freshness_status':'PASS','applicable_gates_passed':True}
    policy={'delivery_status_enum':['DONE_WITH_GAPS','PRODUCTION_READY','MASTERPIECE_VERIFIED']}
    assert not allowed_delivery_status('IDEA_TO_PRODUCTION','PRODUCTION_READY',validation,[],policy)
    assert not allowed_delivery_status('IDEA_TO_PRODUCTION','MASTERPIECE_VERIFIED',validation,[],policy)
    assert allowed_delivery_status('IDEA_TO_PRODUCTION','DONE_WITH_GAPS',validation,[],policy)
    no_gaps=copy.deepcopy(validation); no_gaps['exception_refs']=[]
    assert not allowed_delivery_status('IDEA_TO_PRODUCTION','DONE_WITH_GAPS',no_gaps,[],policy)


def test_exception_policy_matrix_covers_every_delivery_status():
    policy=load('HRAS_v20_Policy_Registry.json')
    validation={'status':'PASS','failed_hard_gates':[],'unknown_hard_gates':[],
      'authorization_violations':[],'evidence_defects':[],'stale_evidence':[],
      'operations_needing_reconciliation':[],'budget_violations':[],
      'unresolved_blockers':[],'active_exceptions':[], 'exception_refs':['exc-approved-residual-risk'],
      'artifact_identity_verified':True,'quality_profile_frozen':True,
      'evidence_freshness_status':'PASS','applicable_gates_passed':True,
      'expected_artifact_hash':'sha256:'+'a'*64,'expected_environment_id':'staging:1',
      'expected_target_identity':'service:demo','expected_signed_manifest_hash':'sha256:'+'b'*64,
      'independent_review_passed':True,'masterpiece_evidence_complete':True,
      'user_outcome_validation_status':'PASS'}
    statuses=policy['delivery_status_enum']
    assert statuses and len(statuses)==len(set(statuses))
    for status in statuses:
        got=allowed_delivery_status('IDEA_TO_PRODUCTION',status,validation,[],policy)
        assert got is (status=='DONE_WITH_GAPS'), (status,got)
    # A reference to a non-waivable condition is never a valid exception.
    from datetime import datetime, timezone
    bad={'exception_id':'exc-nw','gate_id':policy['non_waivable_policy']['id'],
      'issue_ref':'issue-1','scope':'artifact:one','affected_asset_hashes':['sha256:'+'a'*64],
      'impact':'would bypass a hard gate','compensating_controls':['manual review'],
      'policy_basis':policy['non_waivable_policy']['id'],'revalidation_plan':'retest',
      'rollback_plan':'revert','status':'APPROVED','waivable':True,
      'proposer_id':'alice','approver_id':'bob','approver_authority':'QA_OWNER',
      'approver_independence_evidence_ref':'evidence:independence','approver_policy_version':'policy-v1',
      'approved_at':'2026-10-28T00:00:00Z','expires_at':'2026-10-30T00:00:00Z',
      'review_at':'2026-10-29T00:00:00Z','evidence_refs':['evidence:review']}
    assert not exception_is_valid_for_use(bad,policy,datetime.fromisoformat('2026-10-29T10:00:00+00:00'))


def test_approved_exception_requires_independence_freshness_and_waivable_gate():
    from datetime import datetime, timezone
    policy=load('HRAS_v20_Policy_Registry.json')
    now=datetime.fromisoformat('2026-10-29T10:00:00+00:00')
    good={'exception_id':'exc-1','gate_id':'PRODUCT-QUALITY-LOW-01','issue_ref':'issue-1','scope':'artifact:one','affected_asset_hashes':['sha256:'+'a'*64], 'impact':'limited non-critical defect','compensating_controls':['manual review'], 'policy_basis':'HRAS-POL-GATE-001; profile applies','revalidation_plan':'retest by expiry','rollback_plan':'revert local slice','status':'APPROVED','waivable':True,'proposer_id':'alice','approver_id':'bob','approver_authority':'QA_OWNER','approver_independence_evidence_ref':'evidence:independence','approver_policy_version':'policy-v1','approved_at':'2026-10-28T00:00:00Z','expires_at':'2026-10-30T00:00:00Z','review_at':'2026-10-29T00:00:00Z','evidence_refs':['evidence:review']}
    assert exception_is_valid_for_use(good,policy,now)
    for field,value in [('approver_id','alice'),('expires_at','2026-10-28T00:00:00Z'),('waivable',False),('evidence_refs',[]),('status','REVOKED'),('gate_id','HRAS-NW-001')]:
        bad=copy.deepcopy(good); bad[field]=value
        assert not exception_is_valid_for_use(bad,policy,now), (field,value)
    bad=copy.deepcopy(good); bad['approver_authority']=''
    assert not exception_is_valid_for_use(bad,policy,now)
    # Approval fields are conditional by lifecycle state; only APPROVED is eligible for use.
    proposed=copy.deepcopy(good); proposed['status']='PROPOSED'
    for field in ['approver_id','approver_authority','approver_independence_evidence_ref','approver_policy_version','approved_at','expires_at','review_at','evidence_refs']:
        proposed.pop(field,None)
    assert not validate_contract(load('HRAS_v20_Contract_Schemas.json'),'ExceptionRecord',proposed)
    assert not exception_is_valid_for_use(proposed,policy,now)
    rejected=copy.deepcopy(good); rejected.update(status='REJECTED',reviewer_id='qa-1',reviewed_at='2026-10-29T00:00:00Z',rejection_reason='residual risk unacceptable')
    assert not validate_contract(load('HRAS_v20_Contract_Schemas.json'),'ExceptionRecord',rejected)
    assert not exception_is_valid_for_use(rejected,policy,now)
    for status in ['EXPIRED','REVOKED']:
        inactive=copy.deepcopy(good); inactive.update(status=status,status_changed_at='2026-10-29T00:00:00Z',status_change_reason='lifecycle transition')
        assert not validate_contract(load('HRAS_v20_Contract_Schemas.json'),'ExceptionRecord',inactive)
        assert not exception_is_valid_for_use(inactive,policy,now)


def lifecycle_operability_sample():
    return {'spec_id':'HRAS-AUTO-ENG','schema_version':'1.0.0','spec_version':'20.0.0-rc4','artifact_id':'artifact-1','product_class':'web-service','profile_hash':'sha256:'+'a'*64,
      'applicability':{'status':'APPLICABLE','rationale':'Service has a maintained runtime','approved_by':'owner-1','review_ref':'review-1'},
      'environment_configuration':{'configuration_sources':['versioned-config'],'secrets_handling':'MANAGED_SECRET_STORE','drift_detection':'ENABLED','evidence_refs':['evidence:config']},
      'health_checks':{'liveness':'NOT_RUN','readiness':'NOT_RUN','dependency_health':'NOT_RUN','evidence_refs':[]},
      'observability':{'structured_logs':'NOT_RUN','metrics':'NOT_RUN','traces':'NOT_RUN','correlation_ids':'NOT_RUN','redaction':'NOT_RUN','retention_policy_ref':'policy:retention','evidence_refs':[]},
      'backup_restore':{'backup_required':True,'restore_test_status':'NOT_RUN','last_restore_drill_at':None,'evidence_refs':[]},
      'migrations':{'migration_required':True,'up_migration_status':'NOT_RUN','down_migration_status':'NOT_RUN','backup_before_migration':True,'evidence_refs':[]},
      'rollback':{'rollback_available':True,'rollback_test_status':'NOT_RUN','rollback_runbook_ref':'runbook:rollback','evidence_refs':[]},
      'recovery_drills':{'required':True,'status':'NOT_RUN','last_drill_at':None,'evidence_refs':[]},
      'dependency_support':[{'dependency':'db-driver','version':'1.x','support_status':'SUPPORTED','upgrade_policy_ref':'policy:upgrade','license_status':'COMPATIBLE','evidence_refs':[]}],
      'incident_runbook':{'runbook_ref':'runbook:incident','severity_model':'SEV1-SEV4','triage_steps':['triage','contain','recover'],'escalation_owner':'ops-owner','evidence_refs':[]},
      'ownership':{'service_owner':'team-a','support_contact':'oncall@example.invalid','review_cadence':'quarterly','ownership_limits':['no 24x7 SLA']},
      'tco':{'estimate_status':'UNKNOWN','currency':None,'horizon_months':None,'assumptions':['provider cost not measured'],'estimated_amount_minor':None,'evidence_refs':[]},
      'portability':{'portability_status':'UNKNOWN','vendor_lock_in_risks':['provider-specific runtime'],'mitigation':['adapter boundary'],'evidence_refs':[]},'evidence_refs':['evidence:lifecycle-contract'],'limitations':['Runtime operations have not been exercised.'],'created_at':'2026-10-29T00:00:00Z'}

def security_posture_sample():
    return {'report_id':'sec-1','schema_version':'1.0.0','spec_version':'20.0.0-rc4','artifact_hash':'sha256:'+'a'*64,'profile_hash':'sha256:'+'b'*64,'scope':'static contract review',
      'threat_model':{'status':'NOT_RUN','attacker_model':'untrusted user and repository content','assets':['credentials','source'],'trust_boundaries':['tool broker'],'excluded_scenarios':['physical access'],'evidence_refs':[]},
      'authn_authz':{'status':'NOT_RUN','authn_method':'not configured','authz_model':'deny by default','least_privilege_review':'NOT_RUN','evidence_refs':[]},
      'input_validation':{'status':'NOT_RUN','injection_tests':'NOT_RUN','boundary_tests':'NOT_RUN','schema_enforcement':'NOT_RUN','evidence_refs':[]},
      'secret_handling':{'status':'NOT_RUN','secret_store':'not configured','redaction':'NOT_RUN','rotation_procedure':'MISSING','leak_scan_status':'NOT_RUN','evidence_refs':[]},
      'data_minimization_retention':{'status':'NOT_RUN','minimization':'not yet assessed','retention_policy_ref':None,'deletion_test_status':'NOT_RUN','evidence_refs':[]},
      'dependency_security':{'sast_status':'NOT_RUN','sca_status':'NOT_RUN','license_review_status':'NOT_RUN','known_exploited_review_status':'NOT_RUN','findings_count':{'critical':0,'high':0,'medium':0,'low':0,'unknown':0},'evidence_refs':[]},
      'privacy_controls':[],'untrusted_input_surfaces':[{'surface':'REPOSITORY_FILE','treated_as_untrusted':True,'enforcement_boundary':'trusted adapter','test_evidence_ref':'test:untrusted-source'}],
      'findings':[],'summary_status':'NOT_RUN','counts':{'critical_open':0,'high_open':0,'medium_open':0,'low_open':0,'release_blocking_open':0},'residual_risk':['No runtime security testing has been performed.'],'evidence_refs':[],
      'review':{'reviewer_id':'reviewer-1','independence_evidence_ref':'independence:1','reviewed_at':'2026-10-29T00:00:00Z','decision':'NOT_REVIEWED'},'limitations':['This is a test fixture, not a real audit.'],'observed_at':'2026-10-29T00:00:00Z'}

def test_lifecycle_operability_contract_detects_cross_field_contradictions():
    schemas=load('HRAS_v20_Contract_Schemas.json'); good=lifecycle_operability_sample()
    assert not validate_contract(schemas,'LifecycleAndOperabilitySpec',good)
    assert not validate_lifecycle_operability_spec(good,schemas)
    # Explicitly require lifecycle evidence only when the profile says it applies.
    na=copy.deepcopy(good); na['applicability']={'status':'NOT_APPLICABLE','rationale':'Product profile has no maintained runtime','approved_by':'profile-owner','review_ref':'review:na'}
    na['health_checks'].update(liveness='NOT_APPLICABLE',readiness='NOT_APPLICABLE',dependency_health='NOT_APPLICABLE')
    na['observability'].update(structured_logs='NOT_APPLICABLE',metrics='NOT_APPLICABLE',traces='NOT_APPLICABLE',correlation_ids='NOT_APPLICABLE',redaction='NOT_APPLICABLE')
    na['backup_restore'].update(backup_required=False,restore_test_status='NOT_APPLICABLE')
    na['migrations'].update(migration_required=False,up_migration_status='NOT_APPLICABLE',down_migration_status='NOT_APPLICABLE')
    na['rollback'].update(rollback_available=False,rollback_test_status='NOT_APPLICABLE')
    na['recovery_drills'].update(required=False,status='NOT_APPLICABLE')
    assert not validate_lifecycle_operability_spec(na,schemas)
    # Claiming PASS on an unperformed restore test must fail semantically.
    bad=copy.deepcopy(good); bad['migrations']['down_migration_status']='NOT_APPLICABLE'
    assert validate_contract(schemas,'LifecycleAndOperabilitySpec',bad)
    bad=copy.deepcopy(good); bad['backup_restore']['restore_test_status']='PASS'
    assert validate_lifecycle_operability_spec(bad,schemas)
    na=copy.deepcopy(good); na['applicability']={'status':'NOT_APPLICABLE','rationale':'No maintained runtime','approved_by':None,'review_ref':None}
    assert validate_lifecycle_operability_spec(na,schemas)

def test_security_posture_contract_recomputes_counts_and_rejects_fake_pass():
    schemas=load('HRAS_v20_Contract_Schemas.json'); good=security_posture_sample()
    assert not validate_contract(schemas,'SecurityPostureReport',good)
    assert not validate_security_posture_report(good,schemas)
    bad=copy.deepcopy(good); bad['counts']['high_open']=1
    assert validate_security_posture_report(bad,schemas)
    fake=copy.deepcopy(good); fake['summary_status']='PASS'; fake['review']['decision']='APPROVE'
    assert validate_security_posture_report(fake,schemas)
    finding=copy.deepcopy(good); finding['findings']=[{'finding_id':'F-HIGH','severity':'HIGH','status':'OPEN','description':'authorization bypass','impact':'external action','mitigation':'implement broker','release_blocking':True,'evidence_refs':['evidence:1']}]
    finding['counts']={'critical_open':0,'high_open':1,'medium_open':0,'low_open':0,'release_blocking_open':1}
    finding['summary_status']='PASS'; finding['review']['decision']='APPROVE'
    assert validate_security_posture_report(finding,schemas)


def test_north_star_map_is_crosslinked_and_candidate_limited():
    schemas=load('HRAS_v20_Contract_Schemas.json')
    north=load('HRAS_v20_North_Star_Subrequirement_Map.json')
    trace=load('HRAS_v20_Requirement_Traceability.json')
    cases=load('HRAS_v20_Test_Cases.json')
    assert not validate_contract(schemas,'NorthStarSubrequirementMap',north)
    assert north['core_north_stars']==['HRAS-NS-001','HRAS-NS-002','HRAS-NS-003','HRAS-NS-004','HRAS-NS-005']
    assert north['no_new_top_level_north_star'] is True
    assert all(set(m['requirement_refs']) <= {x['requirement_id'] for x in trace['requirements']} for m in north['concept_mappings'])
    assert all(set(m['test_ids']) <= {x['test_id'] for x in cases['cases']} for m in north['concept_mappings'])
    assert north['independent_review_status']=='PENDING'
    bad=copy.deepcopy(north); bad['concept_mappings'][0]['test_ids'].append('UNKNOWN-TEST')
    assert not validate_contract(schemas,'NorthStarSubrequirementMap',bad)  # schema alone cannot prove registry referential integrity
    import HRAS_v20_package_tool as pt
    scratch=ROOT/'..'/'northstar-map-mutation-scratch'
    if scratch.exists(): shutil.rmtree(scratch)
    shutil.copytree(ROOT,scratch,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git','.pytest_cache'))
    (scratch/'HRAS_v20_North_Star_Subrequirement_Map.json').write_text(json.dumps(bad,indent=2)+'\n')
    errors=pt.verify_canonical_artifacts(scratch)
    assert any('unknown test references' in e for e in errors)
    shutil.rmtree(scratch)


def test_workflow_coverage_report_is_hash_bound_and_cycle_guard_mutation_fails(tmp_path):
    import HRAS_v20_package_tool as pt
    schemas=load('HRAS_v20_Contract_Schemas.json')
    report=load('HRAS_v20_Workflow_Coverage_Report.json')
    assert not validate_contract(schemas,'WorkflowCoverageReport',report)
    assert report==pt.generate_workflow_coverage_report(ROOT)
    assert report['all_modes_covered'] and report['all_transitions_attributed'] and report['all_cycles_guarded']
    scratch=tmp_path/'workflow-mutation'
    shutil.copytree(ROOT,scratch,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git','.pytest_cache'))
    workflow=json.loads((scratch/'HRAS_v20_Workflow_Transitions.json').read_text())
    edge=next(x for x in workflow['retry_edges'] if x['primary_mode']=='IDEA_TO_PRODUCTION' and x['from_state']=='VERIFYING' and x['to_state']=='IMPLEMENTING')
    workflow['retry_edges'].remove(edge)
    (scratch/'HRAS_v20_Workflow_Transitions.json').write_text(json.dumps(workflow,indent=2)+'\n')
    errors=pt.verify_canonical_artifacts(scratch)
    assert any('unbounded cycle remains' in e for e in errors)
    assert any('workflow coverage report is stale' in e for e in errors)


def test_policy_registry_missing_or_hash_mismatch_fails_closed(tmp_path):
    import HRAS_v20_package_tool as pt
    scratch=tmp_path/'policy-mutation'
    shutil.copytree(ROOT,scratch,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git','.pytest_cache'))
    policy=json.loads((scratch/'HRAS_v20_Policy_Registry.json').read_text())
    policy['version']='20.0.0-rc3'
    (scratch/'HRAS_v20_Policy_Registry.json').write_text(json.dumps(policy,indent=2)+'\n')
    errors=pt.verify_canonical_artifacts(scratch)
    assert any('Annex B generated policy-registry source hash is stale' in e for e in errors)
    assert pt.verify_version_identity(scratch)
    (scratch/'HRAS_v20_Policy_Registry.json').unlink()
    missing_errors=pt.verify_canonical_artifacts(scratch)
    assert any('could not complete' in e or 'No such file' in e for e in missing_errors)
    assert pt.verify_version_identity(scratch)


def test_static_validator_defaults_to_isolated_output_directory():
    import HRAS_v20_static_validator as static_validator
    out=static_validator.resolve_report_root(None)
    assert out.is_dir()
    assert out.resolve()!=ROOT.resolve()
    assert out.resolve() != (ROOT/'HRAS_v20_Static_Validation_Report.json').resolve().parent
    shutil.rmtree(out)


def test_checksum_manifest_rejects_unexpected_paths(tmp_path):
    import HRAS_v20_package_tool as pt
    scratch=tmp_path/'checksum-unexpected'
    shutil.copytree(ROOT,scratch,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git','.pytest_cache'))
    unexpected=scratch/'unexpected-evidence.txt'
    unexpected.write_text('not a manifest member\n',encoding='utf-8')
    with (scratch/'HRAS_v20_CHECKSUMS.txt').open('a',encoding='utf-8') as f:
        f.write(f'{pt.sha256(unexpected)}  unexpected-evidence.txt\n')
    errors=pt.verify_checksum_file(scratch)
    assert any('paths outside the manifest/checksum policy' in e for e in errors)


def test_vision_provenance_is_byte_and_line_bound(tmp_path):
    import HRAS_v20_package_tool as pt
    assert not pt.verify_vision_provenance(ROOT)
    scratch=tmp_path/'vision-mutation'
    shutil.copytree(ROOT,scratch,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git','.pytest_cache'))
    with (scratch/'Visi HRAS.md').open('a',encoding='utf-8') as f:
        f.write('\nTampered source line.\n')
    errors=pt.verify_vision_provenance(scratch)
    assert any('SHA-256' in e or 'line count' in e for e in errors)
