"""Offline mocks only. No source imports from any root/target adapter."""
import copy
import json
import unittest
from dataclasses import replace
from coordinator import Action as A, Coordinator, Receipt, digest, GAP_LIMIT_US

RUN = digest('synthetic-run'); SOURCES = digest('synthetic-source-set')
LEASE = digest('synthetic-exclusive-owner'); BOOT = digest('synthetic-boot')
OLD, NEW, RECOVERED = map(digest, ('old', 'new', 'recovered'))
PINS = {a: digest('mock-source:' + a.value) for a in A}


class Mock:
    instances = 0
    submissions = 0
    def __init__(self, fault=True):
        Mock.instances += 1
        self.calls, self.requests, self.overrides = [], [], {}
        self.fail = self.bad_lease_at = None
        self.fault = fault
        self.gap = 1_000_000

    def owner_lease(self):
        return digest('other-owner') if self.bad_lease_at == len(self.calls) else LEASE

    def perform(self, action, request):
        Mock.submissions += 1
        self.calls.append(action); self.requests.append(copy.deepcopy(request))
        if self.fail == action:
            raise TimeoutError('submission/result ambiguous; never replay')
        f = {'accepted': True, 'retries': 0, 'physicalObserved': False}
        identity = OLD if action in (A.APPS, A.PUBLIC_INIT, A.INIT) else NEW
        if action in (A.APPS, A.HEADER, A.RETURN):
            f.update(cachedTab='d/apps.tab', keysReaped=True, vendorHeaders=0,
                     boundedHeaderWorkflow=True, screensaverAbsent=True, boot=BOOT)
        elif action in (A.PUBLIC_INIT, A.PUBLIC_RECOVERY):
            f.update(upgrade=0, power='lcdon', screen=1, burnin=0, vendorHeaders=0)
        elif action in (A.INIT, A.RECOVER):
            f.update(requests=1, helperExit=0, cleanupConfirmed=True)
        elif action in (A.FRESH, A.RECOVER_FRESH):
            identity = NEW if action == A.FRESH else RECOVERED
            f.update(previousIdentity=request['identitySha256'], oldDisconnected=True,
                freshEnumerated=True, initializationEvidence=request['initializationEvidence'],
                unbound=True, noHolders=True, descriptorPolicyMatched=True, bus=7, devnum=61,
                boot=BOOT, disconnectUs=900_000 if action == A.FRESH else 29_000_000+self.gap,
                enumerationUs=1_000_000 if action == A.FRESH else 30_000_000+self.gap)
        elif action in (A.READY_BASE, A.READY_DP, A.READY_POST):
            f.update(schema=request['wrapper']+'-readiness', unbound=True, noHolders=True,
                endpointQueueProof=False, lineageAccepted=True,
                previousVendorEvidence=request['previousVendorEvidence'],
                readinessSha256=digest('synthetic-ready:' + action.value))
        elif action in (A.BASE, A.DP, A.POST):
            start, end = {A.BASE:(2_000_000,3_000_000), A.DP:(4_000_000,24_000_000),
                         A.POST:(24_000_000+self.gap,25_000_000+self.gap)}[action]
            f.update(strictParserAccepted=True, bindingQualified=True,
                readinessSha256=request['readinessSha256'], phase='ReadyForHeader',
                released=True, closed=True, cleanup='STAGE_ABSENT', writes=0,
                nativeInvocations=1, boot=BOOT, firstHeaderUs=start, lastDataUs=end,
                headers=16, bulks=32, packingAndGateContextQualified=True,
                allSampledRLimits40=True, rtStart='Clean', rtEnd='Clean')
            if action == A.DP:
                count = 55 if self.fault else 640
                f.update(headers=count, bulks=2*count, trialQualified=True, keysReaped=True,
                    workflowAttempts=1, oneLeftDownUp=True, maxCycles=80, durationUs=20_000_000,
                    terminal='TransitionCaptured' if self.fault else 'CycleLimit',
                    triggerCycleOneClean=True, rtEnd='Faulted' if self.fault else 'Clean')
            if action == A.POST and self.fault:
                f.update(rtStart='Faulted', rtEnd='Faulted')
        f.update(self.overrides.get(action, {}))
        identity = f.pop('_identity', identity)
        return Receipt(action, digest('synthetic-evidence:' + action.value), identity, f)


class Tests(unittest.TestCase):
    def setup_run(self, fault=True):
        m = Mock(fault); journal = []
        c = Coordinator(m, lambda row: journal.append(copy.deepcopy(row)), RUN, SOURCES, PINS)
        return m, c, journal

    def finish(self, c):
        return c.observe(c.initialize())

    def test_clean(self):
        m,c,j = self.setup_run(False); result=self.finish(c)
        self.assertEqual(m.calls, list(A)[:12])
        self.assertTrue(result['comparisonQualified']); self.assertFalse(result['stockRecoveryLifecycleAccepted'])
        self.assertFalse(result['physicalObserved']); self.assertEqual(c.state,'complete')
        self.assertEqual(len(m.calls),len(set(m.calls)))
        self.assertEqual(j[0]['events'][0]['status'],'intent')
        self.assertEqual(j[-1]['state'],'complete')

    def test_fault(self):
        m,c,_=self.setup_run(); result=self.finish(c)
        self.assertEqual(m.calls,list(A)); self.assertTrue(result['stockRecoveryLifecycleAccepted'])
        self.assertFalse(result['ramOrCodeRestorationProven'])
        last=None
        for a,request in zip(m.calls,m.requests):
            self.assertEqual(request['previousVendorEvidence'],last)
            self.assertEqual(request['limit'],40); self.assertIs(request['endpointQueueProof'],False)
            self.assertEqual(request['sourceSha256'],PINS[a])
            if a in (A.BASE,A.DP,A.POST): last=digest('synthetic-evidence:'+a.value)
            if a in (A.FRESH,A.RECOVER_FRESH): last=None

    def test_every_submission_failure_stops_without_cleanup_retry_or_new_action(self):
        for a in A:
            with self.subTest(action=a):
                m,c,_=self.setup_run(); m.fail=a
                with self.assertRaises(TimeoutError):self.finish(c)
                before=list(m.calls)
                self.assertEqual(before[-1],a); self.assertEqual(c.state,'halted')
                self.assertEqual(len(before),len(set(before)))
                with self.assertRaises(ValueError): c.initialize()
                with self.assertRaises(ValueError): c.observe(c.ticket)
                self.assertEqual(m.calls,before)

    def test_unknown_phase_incomplete_cleanup_and_pending_key_no_post_header(self):
        for action in (A.BASE,A.DP,A.POST):
            for key,value in [('phase','Unknown'),('released',False),('closed',False),
                              ('cleanup','retained'),('strictParserAccepted',False),
                              ('bindingQualified',False),('accepted',False),('writes',1),
                              ('allSampledRLimits40',False),('nativeInvocations',2)]:
                with self.subTest(action=action, key=key):
                    m,c,_=self.setup_run();m.overrides[action]={key:value}
                    with self.assertRaises(ValueError): self.finish(c)
                    self.assertEqual(m.calls[-1],action)
            if action==A.DP:
                for key,value in [('keysReaped',False),('trialQualified',False),
                       ('oneLeftDownUp',False),('workflowAttempts',2),('maxCycles',81),
                       ('durationUs',21_000_000),('headers',648),('bulks',109),
                       ('terminal','AlreadyFaulted'),('triggerCycleOneClean',False)]:
                    m,c,_=self.setup_run();m.overrides[action]={key:value}
                    with self.assertRaises(ValueError):self.finish(c)
                    self.assertEqual(m.calls[-1],A.DP)

    def test_no_blind_freshness(self):
        for key,value in [('oldDisconnected',False),('freshEnumerated',False),
                   ('initializationEvidence',digest('wrong')),('previousIdentity',NEW),
                   ('_identity',OLD),('boot',digest('different')),('bus',8),('devnum',128),
                   ('unbound',False),('noHolders',False),('descriptorPolicyMatched',False),
                   ('enumerationUs',900_000)]:
            m,c,_=self.setup_run();m.overrides[A.FRESH]={key:value}
            with self.subTest(key=key),self.assertRaises(ValueError):self.finish(c)
            self.assertEqual(m.calls[-1],A.FRESH)

    def test_readiness_lineage_and_same_instance(self):
        for a in (A.READY_BASE,A.READY_DP,A.READY_POST):
            for key,value in [('previousVendorEvidence',digest('stale')),('unbound',False),
                       ('noHolders',False),('endpointQueueProof',True),('lineageAccepted',False),
                       ('readinessSha256','unhashed'),('_identity',OLD)]:
                m,c,_=self.setup_run();m.overrides[a]={key:value}
                with self.subTest(a=a,key=key),self.assertRaises(ValueError):self.finish(c)
                self.assertEqual(m.calls[-1],a)

    def test_classification_and_profile_guard(self):
        mutations={A.BASE:[('rtStart','Faulted'),('rtEnd','Faulted'),('headers',15),('bulks',31),
                             ('packingAndGateContextQualified',False)],
                   A.DP:[('rtEnd','Clean')],A.POST:[('rtStart','Clean'),('rtEnd','Clean')]}
        for a,changes in mutations.items():
            for key,value in changes:
                m,c,_=self.setup_run();m.overrides[a]={key:value}
                with self.subTest(a=a,key=key),self.assertRaises(ValueError):self.finish(c)
                self.assertEqual(m.calls[-1],a)

    def test_budget_overrun_is_quality_failure_but_safe_fault_recovery_still_runs(self):
        m,c,_=self.setup_run();m.gap=GAP_LIMIT_US+1; r=self.finish(c)
        self.assertFalse(r['comparisonQualified']);self.assertTrue(r['stockRecoveryLifecycleAccepted'])
        self.assertEqual(m.calls,list(A)); self.assertEqual(r['qualityIssues'],['dpToPostUs:budget_exceeded'])

    def test_context_change_post_refuses_no_recovery(self):
        m,c,_=self.setup_run();m.overrides[A.POST]={'packingAndGateContextQualified':False}
        with self.assertRaises(ValueError):self.finish(c)
        self.assertEqual(m.calls[-1],A.POST);self.assertNotIn(A.RECOVER,m.calls)

    def test_stale_arrays_are_not_admission_facts(self):
        # No zeros, global epoch, inferred A branch or primary-mask equality is required.
        m,c,_=self.setup_run(False)
        m.overrides[A.BASE]={'ordinal':69,'bStale':True,'diffStale':True,'primaryNonzero':True}
        self.assertTrue(self.finish(c)['completed'])

    def test_lost_lease(self):
        m,c,_=self.setup_run();m.bad_lease_at=5
        with self.assertRaises(ValueError):self.finish(c)
        self.assertEqual(len(m.calls),5);self.assertEqual(c.state,'halted')

    def test_intent_journal_failure_does_not_submit(self):
        m=Mock()
        def broken(_):raise OSError('durability failed')
        c=Coordinator(m,broken,RUN,SOURCES,PINS)
        with self.assertRaises(OSError):c.initialize()
        self.assertEqual(m.calls,[]);self.assertIn(A.APPS,c.used);self.assertEqual(c.state,'halted')

    def test_receipt_persistence_failure_stops(self):
        m=Mock();calls=[]
        def broken(row):
            calls.append(row)
            if row['events'][-1]['status']=='receipt':raise OSError('receipt durability failed')
        c=Coordinator(m,broken,RUN,SOURCES,PINS)
        with self.assertRaises(OSError):c.initialize()
        self.assertEqual(m.calls,[A.APPS]);self.assertEqual(c.state,'halted')

    def test_ticket_tamper_and_reentry(self):
        m,c,_=self.setup_run();t=c.initialize()
        with self.assertRaises(ValueError):c.observe(replace(t,enumeration_us=t.enumeration_us+1))
        self.assertEqual(m.calls,list(A)[:4])
        m,c,_=self.setup_run();t=c.initialize();c.observe(t);before=list(m.calls)
        with self.assertRaises(ValueError):c.observe(t)
        self.assertEqual(m.calls,before)

    def test_persisted_intent_precedes_every_submission(self):
        m,c,j=self.setup_run(); original=m.perform
        def guarded(action, request):
            self.assertEqual(j[-1]['events'][-1]['action'],action.value)
            self.assertEqual(j[-1]['events'][-1]['status'],'intent')
            return original(action,request)
        m.perform=guarded;self.finish(c)

    def test_final_entry_boundary_journal_failure_halts(self):
        for badstate in ('initialized','complete'):
            m=Mock()
            def journal(row):
                if row['state']==badstate:raise OSError('boundary durability failure')
            c=Coordinator(m,journal,RUN,SOURCES,PINS)
            with self.subTest(state=badstate),self.assertRaises(OSError):self.finish(c)
            self.assertEqual(c.state,'halted')

    def test_size_clock_and_common_claims(self):
        for action,change in [(A.BASE,{'extra':'x'*32769}),
                (A.DP,{'firstHeaderUs':2_000_000}),
                (A.POST,{'firstHeaderUs':1_000_000}),
                (A.PUBLIC_INIT,{'physicalObserved':True}),
                (A.APPS,{'retries':1}),
                (A.RECOVER_FRESH,{'disconnectUs':1})]:
            m,c,_=self.setup_run();m.overrides[action]=change
            with self.subTest(action=action),self.assertRaises(ValueError):self.finish(c)
            self.assertEqual(m.calls[-1],action)

    def test_bool_counts_refused(self):
        for action,key in [(A.BASE,'writes'),(A.BASE,'nativeInvocations'),(A.DP,'headers'),
                           (A.DP,'workflowAttempts'),(A.INIT,'requests')]:
            m,c,_=self.setup_run();m.overrides[action]={key:True}
            with self.assertRaises(ValueError):self.finish(c)
            self.assertEqual(m.calls[-1],action)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise SystemExit(1)
    print(json.dumps({'schema':'ef-offline-mock-tests-v1','testMethods':result.testsRun,'mockScenarios':Mock.instances,'mockActionSubmissions':Mock.submissions,
                      'failures':0,'liveCalls':0,'networkCalls':0,'targetBindingsPresent':False},sort_keys=True))
