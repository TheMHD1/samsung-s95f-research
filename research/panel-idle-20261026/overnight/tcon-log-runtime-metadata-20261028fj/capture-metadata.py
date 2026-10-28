#!/usr/bin/env python3
"""One fixed cached metadata request; never read debugfs contents or special devices."""
from pathlib import Path
import importlib.util,hashlib,json,os
os.umask(0o077)
p=Path(__file__).resolve().parent
a=p.parent/'managed-ui-tab-launch/root-with-margin.py'
if hashlib.sha256(a.read_bytes()).hexdigest()!='bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a':raise ValueError('root adapter identity')
s=importlib.util.spec_from_file_location('fj_pinned_root',a);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
command="""set -eu
printf 'BOOT\n'
cat /proc/sys/kernel/random/boot_id
printf 'KERNEL\n'
uname -r
printf 'MOUNTS\n'
cat /proc/mounts
printf 'MODULES\n'
cat /proc/modules
printf 'DEBUGFS_METADATA\n'
for p in /sys/kernel/debug /sys/kernel/debug/tcon /sys/kernel/debug/tcon/tcon_micom_log; do
 if test -e "$p"; then stat -c '%F %a %s %n' "$p"; else printf 'ABSENT %s\n' "$p"; fi
done
printf 'MODULE_FILE\n'
p=/lib/modules/5.4.261/kernel/soc/sdp_tcon.ko
if test -f "$p"; then stat -c '%F %a %s %n' "$p"; sha256sum "$p"; else printf 'ABSENT %s\n' "$p"; fi
"""
record={'schema':'fj-fixed-cached-runtime-metadata-v1','calls':[]}
text=m.root(command,record,p/'metadata-root.json')
(p/'metadata.txt').write_text(text)
(p/'record.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'completed':True,'rootCalls':len(record['calls']),'vendorTransfers':0,'debugfsContentReads':0,'writes':0,'metadataFile':str(p/'metadata.txt')}))
