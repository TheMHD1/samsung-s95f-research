"""Host-only executable design. No live port, shell, network or device binding.

A future centrally owned adapter must verify original artifacts with frozen parsers
before constructing Receipt. This module cannot certify an arbitrary port's claims.
"""
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re


def require(ok, why):
    if not ok:
        raise ValueError(why)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def hashed(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def integer(value, lo=0, hi=2**63-1):
    return type(value) is int and lo <= value <= hi


class Action(str, Enum):
    APPS = 'apps_before_initialization'
    PUBLIC_INIT = 'public_reject_checks_before_initialization'
    INIT = 'one_stock_mode2_initialization'
    FRESH = 'fresh_identity_after_initialization'
    HEADER = 'bounded_apps_header_preparation'
    READY_BASE = 'fresh_eb_baseline_readiness'
    BASE = 'one_eb_baseline'
    READY_DP = 'fresh_dp_readiness'
    DP = 'one_dp_80cycle_max_left_workflow'
    READY_POST = 'fresh_eb_post_readiness'
    POST = 'one_eb_post'
    RETURN = 'one_apps_return'
    PUBLIC_RECOVERY = 'public_reject_checks_before_recovery'
    RECOVER = 'one_stock_mode2_recovery'
    RECOVER_FRESH = 'fresh_identity_after_recovery'


@dataclass(frozen=True)
class Receipt:
    action: Action
    evidence_sha256: str  # digest of retained original result/native/raw artifact index
    identity: str         # digest of full exact wrapper META_KEYS identity (not devnum alone)
    facts: dict


@dataclass(frozen=True)
class InitTicket:
    run: str
    source_set: str
    initialization: str
    fresh_evidence: str
    identity: str
    boot: str
    enumeration_us: int

    @property
    def sha256(self):
        return digest(self.__dict__)


# Policy bounds for this design, not measured guarantees of the frozen wrappers.
# A quality overrun does not override safe cleanup/recovery after accepted I/O.
GAP_LIMIT_US = 30_000_000
INIT_AGE_LIMIT_US = 180_000_000


class Coordinator:
    """Two explicit entry points; once-only fixed action graph under one owner lease.

    port.perform(action, request) -> Receipt, port.owner_lease() -> pinned digest.
    journal(snapshot) must persist before returning; failure means stop. The caller
    must retain the same object and lease across initialize/observe; restart does
    not replay intent or offer resume. No live adapter is supplied by EF.
    """
    def __init__(self, port, journal, run, source_set, action_pins):
        require(hashed(run) and hashed(source_set), 'run/source digest')
        require(set(action_pins) == set(Action) and all(hashed(v) for v in action_pins.values()),
                'complete fixed source pin map')
        self.port, self.journal = port, journal
        self.run, self.source_set, self.pins = run, source_set, dict(action_pins)
        self.lease = port.owner_lease()
        require(hashed(self.lease), 'sole owner lease')
        self.events, self.used, self.quality = [], set(), []
        self.state, self.identity, self.boot = 'new', None, None
        self.last_vendor = None
        self.last_data_us = None
        self.ticket = None

    def snapshot(self):
        # Copy through JSON: a port/journal cannot mutate the in-memory event list.
        return json.loads(json.dumps({'schema': 'ef-cold-control-journal-v1',
            'run': self.run, 'sourceSet': self.source_set, 'state': self.state,
            'events': self.events, 'qualityIssues': self.quality}, allow_nan=False))

    def _call(self, action, **requirements):
        require(self.state != 'halted', 'halted: central reconciliation only')
        require(action not in self.used, 'one-shot action already consumed')
        try:
            require(self.port.owner_lease() == self.lease, 'exclusive owner lost')
            self.used.add(action)  # consume BEFORE persistence, submission or receipt
            request = {'run': self.run, 'sourceSha256': self.pins[action],
                'identitySha256': self.identity, 'previousVendorEvidence': self.last_vendor,
                'endpointQueueProof': False, 'limit': 40, **requirements}
            event = {'action': action.value, 'status': 'intent', 'request': request}
            self.events.append(event)
            self.journal(self.snapshot())
            r = self.port.perform(action, json.loads(json.dumps(request)))
            require(type(r) is Receipt and r.action == action and hashed(r.evidence_sha256)
                    and hashed(r.identity) and type(r.facts) is dict, 'receipt shape')
            # Isolate from mutable mock/adapter data. Validation is not an upstream parser substitute.
            encoded = json.dumps(r.facts, allow_nan=False)
            require(len(encoded.encode()) <= 32768, 'bounded normalized metadata; raw remains separate')
            f = json.loads(encoded)
            require(f.get('accepted') is True and f.get('retries') == 0
                    and type(f.get('retries')) is int, 'accepted one-shot receipt')
            if self.identity is not None and action not in (Action.FRESH, Action.RECOVER_FRESH):
                require(r.identity == self.identity, 'same instance required')
            require(f.get('physicalObserved') is False, 'physical evidence remains unobserved')
            event.update(status='receipt', evidenceSha256=r.evidence_sha256,
                         identity=r.identity, facts=f)
            self.journal(self.snapshot())
            return r.identity, r.evidence_sha256, f
        except BaseException:
            self.state = 'halted'
            # Preserve original intent even when journaling itself fails. No cleanup/retry here.
            try:
                self.journal(self.snapshot())
            except BaseException:
                pass
            raise

    def _check(self, condition, why):
        if not condition:
            self.state = 'halted'
            try:
                self.journal(self.snapshot())
            finally:
                raise ValueError(why)

    def _apps(self, action, header=False):
        identity, proof, f = self._call(action)
        self._check(f.get('cachedTab') == 'd/apps.tab' and f.get('keysReaped') is True
                    and f.get('vendorHeaders') == 0 and type(f.get('vendorHeaders')) is int
                    and (not header or (f.get('boundedHeaderWorkflow') is True
                                        and f.get('screensaverAbsent') is True)), 'Apps/header workflow')
        return identity, proof, f

    def _public(self, action):
        _, _, f = self._call(action)
        self._check(f.get('upgrade') == 0 and type(f.get('upgrade')) is int
                    and f.get('power') == 'lcdon' and f.get('screen') == 1
                    and type(f.get('screen')) is int and f.get('burnin') == 0
                    and type(f.get('burnin')) is int and f.get('vendorHeaders') == 0
                    and type(f.get('vendorHeaders')) is int,
                    'public reject signals')

    def _mode2(self, action):
        _, proof, f = self._call(action, maximumRequests=1, nativeDeadlineSeconds=12)
        self._check(f.get('requests') == 1 and type(f.get('requests')) is int
                    and f.get('helperExit') == 0 and type(f.get('helperExit')) is int
                    and f.get('cleanupConfirmed') is True, 'stock MODE2 receipt/cleanup')
        # Do not clear prior protocol ambiguity: this method is unreachable after halted.
        return proof

    def _fresh(self, action, mode2_proof):
        identity, proof, f = self._call(action, initializationEvidence=mode2_proof)
        old = self.identity
        self._check(f.get('previousIdentity') == old and identity != old
                    and f.get('oldDisconnected') is True and f.get('freshEnumerated') is True
                    and f.get('initializationEvidence') == mode2_proof
                    and f.get('unbound') is True and f.get('noHolders') is True
                    and f.get('descriptorPolicyMatched') is True
                    and f.get('bus') == 7 and type(f.get('bus')) is int
                    and integer(f.get('devnum'), 1, 127) and hashed(f.get('boot'))
                    and integer(f.get('disconnectUs')) and integer(f.get('enumerationUs'))
                    and f['disconnectUs'] < f['enumerationUs'], 'positive fresh enumeration')
        if self.last_data_us is not None:
            self._check(f['disconnectUs'] >= self.last_data_us, 'lifecycle follows last completed data')
        if self.boot is not None:
            self._check(f['boot'] == self.boot, 'same boot required')
        self.identity, self.boot = identity, f['boot']
        self.last_vendor = None  # fresh instance only; lifecycle evidence bound to ticket
        return proof, f

    def initialize(self):
        self._check(self.state == 'new', 'initialize entry once')
        self.state = 'initializing'
        identity, _, apps = self._apps(Action.APPS)
        self._check(hashed(apps.get('boot')), 'initial boot digest')
        self.identity, self.boot = identity, apps['boot']
        self._public(Action.PUBLIC_INIT)
        init = self._mode2(Action.INIT)
        fresh, f = self._fresh(Action.FRESH, init)
        self.ticket = InitTicket(self.run, self.source_set, init, fresh, self.identity,
                                 self.boot, f['enumerationUs'])
        self.state = 'initialized'
        try:
            self.journal(self.snapshot())
        except BaseException:
            self.state = 'halted'
            raise
        return self.ticket

    def _ready(self, action, wrapper):
        _, _, f = self._call(action, wrapper=wrapper,
            freshInstanceEvidence=self.ticket.fresh_evidence)
        self._check(f.get('schema') == wrapper + '-readiness' and f.get('unbound') is True
                    and f.get('noHolders') is True and f.get('endpointQueueProof') is False
                    and f.get('lineageAccepted') is True
                    and f.get('previousVendorEvidence') == self.last_vendor
                    and hashed(f.get('readinessSha256')), 'current readiness/phase lineage')
        return f['readinessSha256']

    def _usb(self, action, readiness):
        _, proof, f = self._call(action, readinessSha256=readiness)
        self._check(f.get('strictParserAccepted') is True and f.get('bindingQualified') is True
                    and f.get('readinessSha256') == readiness
                    and f.get('phase') == 'ReadyForHeader' and f.get('released') is True
                    and f.get('closed') is True and f.get('cleanup') == 'STAGE_ABSENT'
                    and f.get('writes') == 0 and type(f.get('writes')) is int
                    and f.get('nativeInvocations') == 1 and type(f.get('nativeInvocations')) is int
                    and f.get('boot') == self.boot and integer(f.get('firstHeaderUs'))
                    and integer(f.get('lastDataUs')) and f['firstHeaderUs'] <= f['lastDataUs'],
                    'strict terminal, binding, artifact and cleanup contract')
        self._check(f['firstHeaderUs'] >= self.ticket.enumeration_us
                    and (self.last_data_us is None or f['firstHeaderUs'] >= self.last_data_us),
                    'same-boot read chronology before any next action')
        if action in (Action.BASE, Action.POST):
            self._check(f.get('headers') == 16 and type(f.get('headers')) is int
                        and f.get('bulks') == 32 and type(f.get('bulks')) is int
                        and f.get('packingAndGateContextQualified') is True,
                        'EB exact 16/32/source context')
        else:
            # 80 full cycles + at most seven postfault pairs; duplicate retained baseline is not I/O.
            self._check(integer(f.get('headers'), 1, 647) and integer(f.get('bulks'))
                        and f['bulks'] == 2*f['headers'] and f.get('trialQualified') is True
                        and f.get('keysReaped') is True and f.get('workflowAttempts') == 1
                        and type(f.get('workflowAttempts')) is int
                        and f.get('oneLeftDownUp') is True and f.get('maxCycles') == 80
                        and f.get('durationUs') == 20_000_000
                        and f.get('terminal') in ('TransitionCaptured', 'TimeLimit', 'CycleLimit'),
                        'DP finite synchronized workflow')
        self._check(f.get('allSampledRLimits40') is True, 'unchanged 40 in every retained/checkpoint R')
        self.last_vendor = proof
        self.last_data_us = f['lastDataUs']
        return proof, f

    def observe(self, ticket):
        self._check(self.state == 'initialized' and type(ticket) is InitTicket
                    and ticket == self.ticket and ticket.sha256 == self.ticket.sha256,
                    'exact initialization ticket and unused observation entry')
        self.state = 'observing'
        self._apps(Action.HEADER, header=True)  # normal bounded preparation, once, before baseline
        base_ready = self._ready(Action.READY_BASE, 'eb')
        _, base = self._usb(Action.BASE, base_ready)
        self._check(base.get('rtStart') == base.get('rtEnd') == 'Clean', 'clean baseline brackets')
        dp_ready = self._ready(Action.READY_DP, 'dp')
        _, dp = self._usb(Action.DP, dp_ready)
        self._check(dp.get('triggerCycleOneClean') is True and dp.get('rtEnd') in ('Clean', 'Faulted')
                    and ((dp['rtEnd'] == 'Faulted') == (dp['terminal'] == 'TransitionCaptured')),
                    'qualified initial clean/onset classification')
        post_ready = self._ready(Action.READY_POST, 'eb')
        _, post = self._usb(Action.POST, post_ready)
        self._check(post.get('rtStart') == post.get('rtEnd') == dp['rtEnd'],
                    'post-read expected stable fault/clean classification')
        spans = {'enumerationToBaselineUs': base['firstHeaderUs']-ticket.enumeration_us,
            'baselineToDpUs': dp['firstHeaderUs']-base['lastDataUs'],
            'dpToPostUs': post['firstHeaderUs']-dp['lastDataUs']}
        self._check(all(integer(v) for v in spans.values()), 'same-boot target time ordering')
        for name, value in spans.items():
            bound = INIT_AGE_LIMIT_US if name == 'enumerationToBaselineUs' else GAP_LIMIT_US
            if value > bound:
                self.quality.append(name + ':budget_exceeded')
        self._apps(Action.RETURN)
        recovery = False
        if dp['rtEnd'] == 'Faulted':
            self._public(Action.PUBLIC_RECOVERY)
            recovery_proof = self._mode2(Action.RECOVER)
            self._fresh(Action.RECOVER_FRESH, recovery_proof)
            recovery = True
        self.state = 'complete'
        try:
            self.journal(self.snapshot())
        except BaseException:
            self.state = 'halted'
            raise
        return {'schema': 'ef-cold-control-outcome-v1', 'completed': True,
            'comparisonQualified': not self.quality, 'qualityIssues': list(self.quality),
            'spansUs': spans, 'stockRecoveryLifecycleAccepted': recovery,
            'ramOrCodeRestorationProven': False, 'physicalObserved': False,
            'historicalLaneExecutionProven': False, 'rootCauseEstablished': False,
            'ticketSha256': ticket.sha256, 'journalSha256': digest(self.snapshot())}
