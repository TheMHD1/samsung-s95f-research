"""Fresh-clone pure controller models; no private acquisition or target adapter."""
from pathlib import Path
import json,subprocess,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/panel-idle-20261026/overnight'

class RefreshModels(unittest.TestCase):
    def run_model(self,phase,script,*,unit=False):
        results=[]
        for optimized in (False,True):
            argv=[sys.executable,'-B']+(['-O']if optimized else[])+(['-m','unittest','-v',script]if unit else[script])
            result=subprocess.run(argv,cwd=BASE/phase,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            if result.stdout.strip():results.append(json.loads(result.stdout))
            else:self.assertIn('OK',result.stderr)
        if results:self.assertEqual(results[0],results[1])
        return results[0]if results else{}

    def test_reference_seed_counts_events_not_distinct_buffers(self):
        self.run_model('reference-refresh-control-20261028eg','test_refresh_model',unit=True)

    def test_lane_width_wrap_sticky_flags_and_local_permission(self):
        r=self.run_model('rtp-lane-table-writers-20261028ec','test_lane_model.py')
        self.assertTrue(r['accepted']);self.assertEqual(r['targetOperations'],0)

    def test_selector_full_byte_and_distinct_mirror_models(self):
        r=self.run_model('selector-origin-20261028ej','test_model.py')
        self.assertTrue(r['accepted']);self.assertEqual((r['targetCalls'],r['networkCalls']),(0,0))

    def test_coordinator_is_pure_mock_with_no_target_binding(self):
        r=self.run_model('rtp-cold-control-design-20261028ef','test_coordinator.py')
        self.assertEqual((r['liveCalls'],r['networkCalls'],r['targetBindingsPresent']),(0,0,False))

if __name__=='__main__':unittest.main()
