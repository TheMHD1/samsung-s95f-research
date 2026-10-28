#!/usr/bin/env python3
"""Host-only exact DV delta / EZ pure model / cached builder proof."""
from pathlib import Path
import hashlib,json,re,struct,types
D=Path(__file__).resolve().parent;B=D.parent;V=B/'volatile-limit-dynamic-profile-20261028dv';E=B/'selective-endpoint-limit-design-20261028ez';checks=0
def check(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
lineage=json.loads((D/'source-lineage.json').read_bytes())
for n,d in lineage['parent_files'].items():check(sha((V/n).read_bytes())==d,'frozenDV '+n)
for n,d in lineage['modelPins'].items():check(sha((E/n).read_bytes())==d,'frozenEZ '+n)
a=(V/'Program.cs').read_text();z=(D/'Program.cs').read_text().replace('fa-','dv-')
oldModel=a[a.index('    static void GuardModel('):a.index('    static void GuardPair(')]
newPrefix=z[:z.index('    sealed class FakeClock')];i=newPrefix.index('    // Fixed exact image');j=newPrefix.index('    static void GuardPair(',i)
check(a[:a.index('    sealed class FakeClock')]==newPrefix[:i]+oldModel+newPrefix[j:],'entireproduction prefix differs only fixedtable/GuardModel')
start='    [DllImport("libc.so.6",EntryPoint="open",SetLastError=true)] static extern int ReceiptOpen'
check(a[a.index(start):]==z[z.index(start):],'entireReceipt/Main unchanged except fa prefix')
model=(E/'profile_model.py').read_text();model=model[model.index('STATIC='):];parser=(D/'parse-result.py').read_text();oldparser=(V/'parse-result.py').read_text()
check(model in parser,'exact frozenEZ model embedded')
for start,end in [('def binding_checks(','def parse_native('),('def parse_native(',"if __name__=='__main__':")]:
 check(oldparser[oldparser.index(start):oldparser.index(end)]==parser[parser.index(start):parser.index(end)].replace('fa-','dv-'),'unchanged parser '+start)
# Existing wrapper is byte-identical after schema/prefix/pin/selftest substitutions.
def normalized(s):
 s=s.replace('fa-','dv-').replace('205631','135901')
 for key in ['CHECKPOINT_SHA','PARSER_SHA']:s=re.sub(key+r" = '[^']+'",key+" = '<PIN>'",s)
 return s
check(normalized((V/'run-once.py').read_text())==normalized((D/'run-once.py').read_text()),'entirewrapperonlyschema/prefix/pins/testcount')
parentBuilder=B/'volatile-limit-trial-20261028dk/prepare-current-readiness.py';old=parentBuilder.read_text();new=(D/'prepare-readiness.py').read_text()
check(old[old.index('def sha('):]==new[new.index('def sha('):].replace('FA_CURRENT_READY','DK_CURRENT_READY').replace('fa-fresh-cached','dk-fresh-cached'),'cached builder body exactDK derivative')
check("WRAPPERS = {'fa': ('selective-endpoint-limit-writer-20261028fa/run-once.py', 'fa-fixed-limit-readiness-decision-v1')}"in new,'onlyfixedFAreadinessfamily')
m=types.ModuleType('pureEZ');exec(compile(model,'pureEZ','exec'),m.__dict__)
values=sorted(m.ALTERNATE_ENDPOINT_IMAGE);packed=b''.join(struct.pack('<H',x)for x in values);check(len(values)==72,'72finitevalues')
table=re.search(r'AlternateEndpointImage=\{([^}]+)\}',z);check(table is not None and list(map(int,table[1].split(',')))==values,'nativeexact72table')
check('Sha(imageBytes)=="'+sha(packed)+'"'in z,'nativefiniteimageSHA')
vectors=b''.join(struct.pack('<H',m.endpoint(2075,24,t,15,195,3000,3800)['endpoint'])for t in range(4096));check('Sha(vectors)=="'+sha(vectors)+'"'in z,'all4096arithmeticvectorcrosslanguage')
print(json.dumps(dict(sourceChecksPassed=checks,targetOperations=0,alternateImageSha256=sha(packed),nativeVectorSha256=sha(vectors)),sort_keys=True))
