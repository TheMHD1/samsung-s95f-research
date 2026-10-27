#!/usr/bin/env python3
"""Host-only index of researcher inventories; no network or device access."""
import datetime
import json
from pathlib import Path
import re

PROJECT = Path(__file__).resolve().parents[1]


def generate():
    inventories = sorted(PROJECT.glob('sources/*/source-inventory.json'))
    inventories += sorted(PROJECT.glob('sources/video-measurement/inventory.json'))
    records = []
    for path in inventories:
        raw = json.loads(path.read_text())
        entries = (raw if isinstance(raw, list) else
                   raw.get('sources', raw.get('source_repositories', [])))
        if not isinstance(entries, list):
            raise ValueError('Expected source list: ' + str(path))
        for index, entry in enumerate(entries):
            url = (entry.get('url') or entry.get('repoURL') or entry.get('docURL') or
                   entry.get('URL'))
            if not isinstance(url, str) or not url.startswith(('https://', 'http://')):
                raise ValueError('Missing source URL: ' + str(path) + ':' + str(index))
            commit = entry.get('commit')
            if commit is not None and not re.fullmatch(r'[0-9a-f]{40}', commit):
                raise ValueError('Invalid immutable commit: ' + str(path))
            records.append({
                'url': url, 'commit': commit,
                'license': entry.get('license', 'not recorded in entry'),
                'inventory': str(path.relative_to(PROJECT)), 'entry_index': index,
                'evidence_level': 'source discovery/review; not independent target replication',
            })
    by_commit = {}
    for record in records:
        if record['commit']:
            by_commit.setdefault(record['commit'], set()).add(record['url'])
    shared = [{'commit': key, 'urls': sorted(value),
               'limit': 'Shared commit lineage is not independent hardware corroboration.'}
              for key, value in by_commit.items() if len(value) > 1]
    result = {
        'schema': 's95f-external-source-registry-v1',
        'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': 'Index into original inventories; retain their reviewed paths/hashes and limits.',
        'inventory_count': len(inventories), 'entries': records,
        'distinct_urls': len({r['url'] for r in records}),
        'shared_commit_lineages': shared,
        'limits': ['URL count is not audited implementation count.',
                   'Document URLs may have no commit; inspect acquisition hash in original inventory.',
                   'Private raw target responses are not a public handoff bundle.'],
    }
    (PROJECT / 'source-registry.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'inventories': len(inventories), 'entries': len(records),
                      'distinct_urls': result['distinct_urls'], 'shared_lineages': len(shared)}))


if __name__ == '__main__':
    generate()
