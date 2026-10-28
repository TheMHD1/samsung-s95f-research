"""Build the data-only second DH extension from pinned authored outcomes."""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from validate_graph import validate


def build():
    proof = json.loads((HERE / 'dh-onset-02-source-proof.json').read_text())
    raw = (HERE / 'graph-with-dh-onset-01.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != proof['base_graph_sha256']:
        raise ValueError('first extension hash drift')
    graph = json.loads(raw)
    source = {}
    for ref in proof['sources']:
        f = (ROOT / ref['path']).resolve()
        if ROOT not in f.parents or f.stat().st_size > 8_000_000:
            raise ValueError('authored source containment/size')
        raw = f.read_bytes()
        if hashlib.sha256(raw).hexdigest() != ref['sha256']:
            raise ValueError('frozen DH source drift')
        source[f.name] = raw
    outcome = json.loads(source['phase-outcomes.json'])
    if outcome['apps_control'] != {'bulk_transfers': 960, 'clean_cycles': 80,
                                   'read_requests': 480, 'terminal': 'TimeLimit'}:
        raise ValueError('unexpected Apps control outcome')
    second = outcome['onset02']
    if not all(second[k] is True for k in ('capture_qualified', 'parent_workflow_accepted',
                                          'recovery_cleanup_confirmed', 'recovery_request_accepted')):
        raise ValueError('second workflow not accepted')
    if (second['bracket_width_us'], second['bulk_transfers'], second['read_requests'],
            second['clean_cycles']) != (250334, 80, 40, 4):
        raise ValueError('second capture counters changed')
    if (outcome['onset01_parent_workflow_accepted'] is not False or
            outcome['physical_state'] != 'unobserved' or
            outcome['stock_mode2_requests_total'] != 3 or
            outcome['volatile_threshold_writes'] != 0):
        raise ValueError('layered result or intervention scope changed')
    report = HERE / 'dh-onset-02.md'
    ref = {'path': str(report.relative_to(ROOT)),
           'sha256': hashlib.sha256(report.read_bytes()).hexdigest()}
    records = [
        ('dh.control01', 'Accepted no-key Apps80-cycle clean control on USB57',
         {'cycles': 80, 'headers': 480, 'bulk': 960, 'terminal': 'TimeLimit'}),
        ('dh.onset02', 'Second accepted DH controller onset after same-instance control',
         {'clean_cycles': 4, 'fault_cycle': 5, 'headers': 40, 'bulk': 80,
          'bracket_start_us': 174596221111, 'bracket_end_us': 174596471445}),
        ('dh.workflow02', 'Second parent workflow accepted; first remains rejected',
         {'accepted': True, 'first_workflow_accepted': False}),
        ('dh.recovery02', 'Separate second-trial stockMODE2 native completion and cleanup',
         {'accepted': True, 'physical_state': 'unobserved'})]
    for identity, label, attrs in records:
        graph['nodes'].append({'id': identity, 'kind': 'observation', 'label': label,
                               'source_refs': [ref], 'observation_class': 'native_capture',
                               'attributes': attrs,
                               'limitations': ['Finite software observation; emitted light unobserved.']})
    records = [
        ('dh.e21', 'dh.control01', 'state.clean', 'observes_finite_clean_control', 'observed'),
        ('dh.e22', 'dh.control01', 'dh.onset02', 'same_USB_instance_without_intervening_reset', 'observed'),
        ('dh.e23', 'dh.onset02', 'state.fault', 'observes_software_transition', 'observed'),
        ('dh.e24', 'dh.onset02', 'dh.workflow02', 'has_accepted_enclosing_workflow', 'observed'),
        ('dh.e25', 'dh.workflow02', 'dh.recovery02', 'records_separate_native_recovery', 'observed'),
        ('dh.e26', 'dh.recovery02', 'gap.electrical', 'does_not_prove_emitted_light', 'unknown')]
    for identity, a, b, relation, kind in records:
        edge = {'id': identity, 'from': a, 'to': b, 'relation': relation,
                'evidence_type': kind, 'evidence_refs': [dict(ref, locator='Frozen layered DH outcomes')],
                'limitations': []}
        if kind == 'observed':
            edge['observation_class'] = 'native_capture'
        graph['edges'].append(edge)
    graph['extension']['second_trial_proof'] = 'dh-onset-02-source-proof.json'
    graph['extension']['source_snapshots_unchanged'] = True
    validate(graph, ROOT)
    return graph


if __name__ == '__main__':
    graph = build()
    (HERE / 'graph-with-dh-onset-02.json').write_text(json.dumps(graph, indent=2) + '\n')
    print(json.dumps({'nodes': len(graph['nodes']), 'edges': len(graph['edges']),
                      'target_operations': 0}))
