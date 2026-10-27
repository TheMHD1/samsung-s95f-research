#!/usr/bin/env python3
"""Bounded TIFS diagnosis-backend pointer reads; dry by default. No calls/setters."""
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ACCESS = BASE.parent / 'root-access/s95f-access.py'
spec = importlib.util.spec_from_file_location('qd_observer_helpers', HERE / 'snapshot-qd-runtime.py')
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
require = helpers.require
SOURCES = {
    'tifs': ('/usr/bin/TIFSDaemon', 'TIFSDaemon', 'd2ebc1d11be46b4a189ec87666b68b73ae58d6f5a3c10da901c80e1125620c11'),
    'wrapper': ('/usr/lib/libvideo-misc.so.0.1.0', 'libvideo-misc.so.0.1.0', 'fcd5faa76492151512544fd29783d33b9f63c91a863909cc0c53ba598ff9e5dd'),
    'impl': ('/prd/usr/lib/libvideo-ft-control-impl-sec.so.0.1.0', 'libvideo-ft-control-impl-sec.so.0.1.0', '2a2d24ed21babd5a7f67e6bd7aa3447cb9a7316fb0234ae4e0e1a93e77650b8d'),
}


def static_contract():
    sys.path.insert(0, '/tmp/tcon-capstone')
    from elftools.elf.elffile import ELFFile
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB
    contract = {}
    for key, (_, name, sha) in SOURCES.items():
        path = BASE / 'binaries' / name
        require(hashlib.sha256(path.read_bytes()).hexdigest() == sha, 'Offline source hash: ' + name)
        with path.open('rb') as handle:
            elf = ELFFile(handle)
            require(elf.elfclass == 32 and elf['e_machine'] == 'EM_ARM', 'ELF ABI')
            loads = [s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD' and s['p_offset'] == 0]
            require(len(loads) == 1, 'ELF zero-offset load')
            contract[key + '_base'] = loads[0]['p_vaddr']
            text = elf.get_section_by_name('.text')
            raw, base = text.data(), text['sh_addr']
            if key == 'wrapper':
                start = 0x47590c04
                code = {i.address: (i.mnemonic, i.op_str) for i in
                        Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(raw[start-base:start-base+8], start)}
                require(code[start] == ('ldr', 'r0, [pc, #4]') and
                        code[start+2] == ('add', 'r0, pc'), 'Wrapper global address getter')
                literal = int.from_bytes(raw[0x47590c0c-base:0x47590c10-base], 'little')
                contract['wrapper_global'] = (0x47590c0a + literal) & 0xffffffff
                require(contract['wrapper_global'] == 0x475a3048, 'Wrapper global address')
            if key in ('tifs', 'impl'):
                rel = elf.get_section_by_name('.rel.plt')
                dyn = elf.get_section(rel['sh_link'])
                got = {dyn.get_symbol(r['r_info_sym']).name: r['r_offset'] for r in rel.iter_relocations()}
                if key == 'tifs':
                    contract['diagnosis_got'] = got['ppi_video_system_diagnosis_set_factory_item']
                    require(contract['diagnosis_got'] == 0x165924, 'TIFS GOT')
                else:
                    contract['method_got'] = got['_ZN27VideoSystemDiagnosisSecImpl14setFactoryItemEiiPb']
                    entries = list(rel.iter_relocations())
                    method_index = [index for index, r in enumerate(entries) if
                        dyn.get_symbol(r['r_info_sym']).name == '_ZN27VideoSystemDiagnosisSecImpl14setFactoryItemEiiPb']
                    require(method_index == [15] and elf.get_section_by_name('.plt')['sh_addr'] == 0x2740
                            and 0x2740 + 20 + 12 * method_index[0] == 0x2808
                            and contract['method_got'] == 0x1ee9c, 'Impl ARM PLT-to-method GOT binding')
                    a = 0xc0e4
                    code = {i.address: (i.mnemonic, i.op_str) for i in
                            Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(raw[a-base:a-base+0x90], a)}
                    require(code[0xc0ec] == ('ldr', 'r8, [pc, #0x80]') and
                            code[0xc0fc] == ('add', 'r8, pc, r8'), 'Impl instance address calculation')
                    literal = int.from_bytes(raw[0xc174-base:0xc178-base], 'little')
                    contract['instance_global'] = (0xc104 + literal) & 0xffffffff
                    require(code[0xc12c] == ('b', '#0x2808'), 'Impl method PLT edge')
    return contract


class Capture:
    def __init__(self, destination, contract):
        self.path, self.contract = destination, contract
        self.ident = self.mapping = self.biases = None
        self.record = {'accepted': False, 'physical_state': 'unobserved', 'atomic': False,
                       'source_hashes_are_live_text_hashes': False, 'contract': contract,
                       'actions': 'exact process/source-file memory reads only; no API calls or writes', 'stages': []}
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.record, indent=2) + '\n')

    def stage(self, name, requests):
        command = ['set -eu', 'tv_pid=$(pidof TIFSDaemon)',
                   'case "$tv_pid" in \'\'|*[!0-9]*) exit 31;; esac']
        if self.ident:
            command += [f'test "$tv_pid" = {self.ident["pid"]}',
                        f'test "$(cat /proc/sys/kernel/random/boot_id)" = {self.ident["boot"]}',
                        'test "$(awk \'{print $22}\' /proc/$tv_pid/stat)" = ' + str(self.ident['start'])]

        def metadata(suffix):
            parts = []
            for label, cmd in [('BOOT', 'cat /proc/sys/kernel/random/boot_id'),
                               ('PID', 'echo "$tv_pid"'), ('EXE', 'readlink /proc/$tv_pid/exe'),
                               ('STAT', 'cat /proc/$tv_pid/stat'), ('UPTIME', 'cat /proc/uptime'),
                               ('MAPS', 'cat /proc/$tv_pid/maps')]:
                parts += [f"echo '@@ {label}{suffix}'", cmd]
            for key, (remote, _, _) in SOURCES.items():
                parts += [f"echo '@@ HASH_{key}{suffix}'", 'sha256sum ' + remote]
            return parts
        command += ["echo '@@ UTC'", 'date -u'] + metadata('')
        for label, (address, words) in requests.items():
            require(self.mapping is not None, 'No mapping before memory read')
            helpers.check_range(self.mapping, address, words)
            command += [f"echo '@@ READ_{label}'",
                        f'dd if=/proc/$tv_pid/mem bs=4 skip={address//4} count={words} | base64']
        command += metadata('_END')
        text = '\n'.join(command) + '\n'
        require(len(text.encode()) < 7500, 'Command size')
        entry = {'name': name, 'command': text, 'requests': requests}
        self.record['stages'].append(entry)
        self.save()
        p = subprocess.run(['python3', str(ACCESS), 'root', '--persistent-only', '--timeout', '25',
                            '--command', text], text=True, capture_output=True, timeout=55)
        entry.update({'transport_exit': p.returncode, 'transport_stderr': p.stderr})
        try:
            d = json.loads(p.stdout)
            entry['response'] = d
        except ValueError:
            entry['unparsed_stdout'] = p.stdout
            raise
        finally:
            self.save()
        require(p.returncode == 0 and not p.stderr, 'Transport result')
        require(d.get('model') == 'QN77S95FAFXZC' and d.get('authenticated') is True
                and d.get('uid') == d.get('euid') == 0 and d.get('root_persistence') == 'host-assisted'
                and d.get('global_system_files_unchanged_at_acquisition') is True, 'Root identity')
        require(len(d['commands']) == 1, 'Command count')
        c = d['commands'][0]
        require(c['exit_code'] == 0 and not c['timed_out'], 'Remote result')
        helpers.check_dd_stderr(c['stderr'])
        fields = helpers.blocks(c['stdout'])
        expected = {'UTC'} | {x + s for x in ('BOOT', 'PID', 'EXE', 'STAT', 'UPTIME', 'MAPS',
                    'HASH_tifs', 'HASH_wrapper', 'HASH_impl') for s in ('', '_END')} | {'READ_' + x for x in requests}
        require(set(fields) == expected, 'Output framing')
        identities = []
        for suffix in ('', '_END'):
            require(fields['EXE'+suffix] == '/usr/bin/TIFSDaemon', 'Executable')
            pid = fields['PID'+suffix]
            require(pid.isdigit() and fields['STAT'+suffix].startswith(pid+' (TIFSDaemon) '), 'Process stat')
            identities.append({'pid': int(pid), 'boot': fields['BOOT'+suffix],
                               'start': int(fields['STAT'+suffix].rsplit(') ', 1)[1].split()[19])})
            for key, (remote, _, sha) in SOURCES.items():
                require(fields['HASH_'+key+suffix].split() == [sha, remote], 'Installed source hash: ' + key)
        require(identities[0] == identities[1] and (not self.ident or self.ident == identities[0]), 'Process lifetime')
        require(fields['MAPS'] == fields['MAPS_END'], 'Mappings changed during stage')
        mapping = helpers.maps(fields['MAPS'])
        biases = {}
        for key, (remote, _, _) in SOURCES.items():
            candidates = [start - self.contract[key+'_base'] for start, _, perms, offset, path in mapping
                          if path == remote and offset == 0 and 'x' in perms]
            require(len(candidates) == 1, 'Exact mapping: ' + key)
            biases[key] = candidates[0]
        require(not self.biases or biases == self.biases, 'Source load bias changed')
        decoded = {}
        for label, (address, count) in requests.items():
            helpers.check_range(mapping, address, count)
            decoded[label] = helpers.decode(fields['READ_'+label], count)
        self.ident, self.mapping, self.biases = identities[0], mapping, biases
        entry.update({'identity': self.ident, 'biases': biases, 'decoded': decoded})
        self.save()
        return decoded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    contract = static_contract()
    if not args.run:
        print(json.dumps({'dry_run': True, 'contract': contract,
                          'plan': 'metadata, global/GOT, backend+3c with repeated globals; 44 memory bytes',
                          'physical_state': 'unobserved', 'no_calls_or_writes': True}, indent=2))
        return
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = HERE / ('factory-backend-runtime-' + stamp + '.json')
    require(not destination.exists(), 'Existing snapshot refused')
    capture = Capture(destination, contract)
    try:
        capture.stage('identity', {})
        w = contract['wrapper_global'] + capture.biases['wrapper']
        t = contract['diagnosis_got'] + capture.biases['tifs']
        g = contract['instance_global'] + capture.biases['impl']
        m = contract['method_got'] + capture.biases['impl']
        first = capture.stage('globals', {'wrapper_global': (w, 2), 'diagnosis_got': (t, 1),
                                         'instance_global': (g, 1), 'method_got': (m, 1)})
        require(first['diagnosis_got'] == [0x47590fd9 + capture.biases['wrapper']], 'Unexpected wrapper target')
        require(first['wrapper_global'][0] != 0 and first['wrapper_global'][1] != 0, 'Backend not initialized')
        table = first['wrapper_global'][1]
        last = capture.stage('backend_target', {'wrapper_global': (w, 2), 'diagnosis_got': (t, 1),
                           'instance_global': (g, 1), 'method_got': (m, 1), 'slot': (table+0x3c, 1)})
        require(all(first[k] == last[k] for k in first), 'Repeated pointer values changed')
        expected_target = 0xc0e4 + capture.biases['impl']
        expected_method = 0xaa54 + capture.biases['impl']
        require(last['slot'] == [expected_target] and last['method_got'] == [expected_method], 'Unexpected implementation target')
        require(last['instance_global'][0] != 0, 'Instance not initialized')
        helpers.check_range(capture.mapping, last['instance_global'][0], 1)
        for address in (expected_target, expected_method):
            require(any(start <= address < end and 'x' in perms and path == SOURCES['impl'][0]
                        for start, end, perms, _, path in capture.mapping), 'Non-executable target')
        capture.record.update({'accepted': True, 'summary': {'identity': capture.ident,
            'wrapper_global': hex(w), 'table': hex(table), 'slot_address': hex(table+0x3c),
            'slot_target': hex(expected_target), 'method_target': hex(expected_method),
            'instance': hex(last['instance_global'][0]), 'physical_state': 'unobserved',
            'memory_bytes_read': 44, 'capture_invoked_factory_function': False,
            'concurrent_daemon_activity_excluded': False}})
    except Exception as error:
        capture.record['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        capture.save()
    print(json.dumps({'path': str(destination), 'accepted': True, 'summary': capture.record['summary']}))


if __name__ == '__main__':
    main()
