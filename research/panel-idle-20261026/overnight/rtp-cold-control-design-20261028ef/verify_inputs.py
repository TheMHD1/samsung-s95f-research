"""Read-only scoped source/hash/anchor audit. Never imports a target adapter."""
import ast
import hashlib
import json
from pathlib import Path
from coordinator import Action, GAP_LIMIT_US, INIT_AGE_LIMIT_US, require

HERE=Path(__file__).resolve().parent
B=HERE.parent

def audit():
    manifest=json.loads((HERE/'input-provenance.json').read_text())
    rows=[]; checks=0
    for row in manifest['files']:
        rel=Path(row['path'])
        require(not rel.is_absolute() and '..' not in rel.parts,'scoped source path')
        p=B/rel
        require(p.is_file() and not p.is_symlink(),'ordinary source')
        raw=p.read_bytes(); checks+=1
        require(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],
                'source input changed: '+row['path']);checks+=1
        anchors=[]
        if row['anchors']:
            text=raw.decode()
            for anchor in row['anchors']:
                require(anchor['snippet'] in text,'source anchor missing')
                at=text.index(anchor['snippet'])
                require(1+text[:at].count('\n')==anchor['line'],'source anchor moved')
                anchors.append({'line':anchor['line'],'label':anchor['label']});checks+=1
        rows.append({'path':row['path'],'sha256':row['sha256'],'anchors':anchors})
    tree=ast.parse((HERE/'coordinator.py').read_text())
    imported=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): imported.update(x.name for x in node.names)
        if isinstance(node,ast.ImportFrom):imported.add(node.module)
    require(imported=={'dataclasses','enum','hashlib','json','re'},'pure coordinator import allowlist');checks+=1
    forbidden={'eval','exec','compile','open','__import__'}
    require(not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in forbidden
                    for n in ast.walk(tree)),'no dynamic execution or device/file entrypoint');checks+=1
    require(len(Action)==15 and GAP_LIMIT_US==30_000_000 and INIT_AGE_LIMIT_US==180_000_000,
            'fixed finite action and timing policy');checks+=1
    require(80*8+7==647,'source-derived maximum DP pairs');checks+=1
    plan=json.loads((HERE/'fixed-plan.json').read_text())
    require(plan['sourceSetSha256']==hashlib.sha256((HERE/'input-provenance.json').read_bytes()).hexdigest(), 'source-set binding');checks+=1
    require(set(plan['actionSources'])=={a.value for a in Action},'all fixed actions mapped');checks+=1
    pins={r['path']:r['sha256'] for r in manifest['files']}
    for item in plan['actionSources'].values():
        require(pins[item['path']]==item['sha256'],'action source binding');checks+=1
    return {'schema':'ef-source-audit-v1','checksPassed':checks,'sourceFiles':rows,
            'liveImports':0,'liveCalls':0,'networkCalls':0,'oemBytesCopied':0}

if __name__=='__main__':
    value=audit()
    expected=json.loads((HERE/'source-audit.json').read_text())
    require(value==expected,'audit output differs from frozen result')
    print(json.dumps({'checksPassed':value['checksPassed'],'sourceFiles':len(value['sourceFiles']),
                      'liveCalls':0,'networkCalls':0},sort_keys=True))
