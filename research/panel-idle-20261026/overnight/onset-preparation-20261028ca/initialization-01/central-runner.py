from pathlib import Path
import importlib.util,hashlib,json
B=Path('${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight');O=B/'onset-preparation-20261028ca/initialization-01'
O.mkdir(mode=0o700)
def load(name,p,d):
 if hashlib.sha256(p.read_bytes()).hexdigest()!=d:raise ValueError('source pin')
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
n=load('nav_ca',B/'ui-navigation-20261027br/navigate.py','74b60a9611f35a76d272b33677f773cc955838c2c6dda2c3565c371cc9d4d530')
r=load('root_ca',B/'managed-ui-tab-launch/root-with-margin.py','bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a')
q=load('constituents_ca',B/'recovery-quickpath-20261027bv/recover.py','4fddc3f6e933a19b15ba208e1ffc029ccd7df323c66cdb7ae24157f374e64a0f')
intent={'scope':'one explicitly recorded Apps-selected experimental stock initialization for USB lifecycle qualification; not invocation of black-only recovery quickpath','ownerBaseline':'Populated Apps page physically visible, owner reply immediately before preparation','maxMode2':1,'vendorBulkTransfers':0,'firmwareChanges':0,'noAutomaticRetry':True,'queueProof':False}
(O/'intent.json').write_text(json.dumps(intent,indent=2)+'\n');(O/'central-runner.py').write_bytes(Path(__file__).read_bytes())
def apps(s):
 if s['cached_current_tab']!='d/apps.tab' or s['screensaver_windows_present'] or not s['csfs_window_present']:raise ValueError('not Apps')
apps(n.command_snapshot(r,O,'before'))
for j in range(2):
 n.one_key('up','local',O,r,f'header-{j+1}')
 apps(n.command_snapshot(r,O,f'after-up-{j+1}'))
q.public_gate(O,r)
rec={'scope':'ordinary cached USB lifecycle logs around separately recorded stock initialization','calls':[]}
cmd='''set -eu
test "$(cat /proc/sys/kernel/random/boot_id)" = 00000000-0000-4000-8000-000000000000
cat /proc/uptime
printf 'DEVNUM='
cat /sys/bus/usb/devices/7-1/devnum
printf 'CONFIG='
cat /sys/bus/usb/devices/7-1/bConfigurationValue
printf 'USB_KERNEL_ROWS_BEGIN\n'
dmesg | sed -n '/usb 7-1/p' | tail -40
printf 'USB_KERNEL_ROWS_END\n'
cat /proc/uptime
'''
text=r.root(cmd,rec,O/'lifecycle-before.json');(O/'lifecycle-before.txt').write_text(text)
result=q.mode2(O)
text=r.root(cmd,rec,O/'lifecycle-after.json');(O/'lifecycle-after.txt').write_text(text)
summary={'mode2Accepted':result.get('accepted'),'mode2Cleanup':result.get('cleanup_confirmed'),'vendorBulkTransfers':0,'physicalPictureObservedAfter':False,'rawLifecycleSaved':True,'usbPhaseQualificationPending':True}
(O/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
