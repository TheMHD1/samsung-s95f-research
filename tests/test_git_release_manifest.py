"""A clean worktree must not hide ignored release files or stale index bytes."""
import hashlib,importlib.util,json,os,shutil,subprocess,tempfile
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('git_public_verify',ROOT/'tools/verify_public.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

@unittest.skipUnless(shutil.which('git'),'Git is required for index regressions')
class GitReleaseChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.env=dict(os.environ,GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
        self.git('init','-q');(self.root/'.git/info/exclude').write_text('*.log\n')
        (self.root/'research').mkdir();(self.root/'manifests').mkdir()
        (self.root/'README.md').write_text('public archive\n');(self.root/'research/retained.log').write_text('sanitized scientific log\n')
        self.manifest();self.git('add','README.md','manifests/release-files.json');self.commit()

    def git(self,*args):
        return subprocess.run(['git','-C',str(self.root),*args],env=self.env,check=True,capture_output=True,timeout=30).stdout

    def commit(self):
        self.git('-c','user.name=Research Test','-c','user.email=research@example.invalid','-c','commit.gpgSign=false','-c','core.hooksPath='+os.devnull,'commit','-qm','fixture')

    def manifest(self):
        rows=[]
        for name in ['README.md','research/retained.log']:
            data=(self.root/name).read_bytes();rows.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        (self.root/'manifests/release-files.json').write_text(json.dumps({'files':rows}))

    def include_log(self):self.git('add','-f','research/retained.log')

    def test_ignored_log_refused_despite_clean_worktree(self):
        self.assertEqual(self.git('status','--porcelain=v1'),b'')
        self.assertIn({'kind':'missing-from-git-index','path':'research/retained.log'},m.verify_git_manifest(self.root)['errors'])

    def test_exact_manifest_and_index_pass(self):
        self.include_log();r=m.verify_git_manifest(self.root)
        self.assertEqual(r['errors'],[]);self.assertEqual(r['expected_files'],3);self.assertEqual(r['indexed_files'],3)

    def test_updated_manifest_cannot_hide_stale_index_blob(self):
        self.include_log();(self.root/'research/retained.log').write_text('different scientific log\n');self.manifest();self.git('add','manifests/release-files.json')
        self.assertIn({'kind':'git-index-bytes-mismatch','path':'research/retained.log'},m.verify_git_manifest(self.root)['errors'])

    def test_unmanifested_index_file_refused(self):
        self.include_log();(self.root/'extra.md').write_text('not in release\n');self.git('add','extra.md')
        self.assertIn({'kind':'unmanifested-git-index-file','path':'extra.md'},m.verify_git_manifest(self.root)['errors'])

if __name__=='__main__':unittest.main()
