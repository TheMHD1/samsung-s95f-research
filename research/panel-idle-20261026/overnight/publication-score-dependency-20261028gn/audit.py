#!/usr/bin/env python3
"""Bounded host-only GN instruction and status-helper footprint audit; no transport."""
from pathlib import Path
import hashlib, json, struct, sys
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B = HERE.parent
checks = 0

def require(condition, message):
    global checks
    if not condition:
        raise ValueError(message)
    checks += 1

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    pins = json.loads((HERE / 'input-pins.json').read_text())
    for row in pins['files']:
        p = Path(row['path'])
        data = p.read_bytes()
        require(len(data) == row['bytes'] and sha(data) == row['sha256'], 'input pin: ' + str(p))
    sys.path.insert(0, str(B / 'predicate-binary-oracle-20261028gd/tools'))
    sys.path.insert(0, '/tmp/tcon-capstone')
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    import unicorn
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_CPU_ARM_CORTEX_M4, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_SP, UC_ARM_REG_LR
    report = json.loads((HERE / 'source-audit.json').read_text())
    raw = (B / 'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
    require(len(raw) == 0x500000 and sha(raw) == report['packageSha256'], 'selected package')
    image = raw[0x40200:0x60200]
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for span in report['spans']:
        lo, hi = int(span['vaStart'], 16), int(span['vaEndExclusive'], 16)
        require(0 <= lo < hi <= len(image), 'span domain')
        require(sha(image[lo:hi]) == span['sha256'], 'instruction/literal span ' + span['name'])
        require(span['fileStart'] == hex(lo + 0x40200), 'file-coordinate convention')
    for row in report['positiveInstructions']:
        va = int(row['va'], 16)
        decoded = list(md.disasm(image[va:va+4], va, count=1))
        require(len(decoded) == 1 and decoded[0].mnemonic == row['mnemonic'] and decoded[0].op_str == row['operands'], 'instruction ' + row['va'])
    for row in report['literalU32']:
        require(struct.unpack_from('<I', image, int(row['va'], 16))[0] == int(row['value'], 16), 'literal ' + row['va'])
    # Executed function closure is only the exact helper + real root getter.
    # No score, logger, busywait, reference producer, hardware or firmware-loop stubs.
    expected_calls = [0x38fc]
    helper = list(md.disasm(image[0x1c0c8:0x1c12c], 0x1c0c8))
    require([int(x.op_str[1:], 16) for x in helper if x.mnemonic == 'bl'] == expected_calls, 'helper direct-call closure')
    require(not any(x.mnemonic in ('blx', 'bx') for x in helper), 'helper has no indirect call/branch')
    require([(x.address, x.mnemonic) for x in helper if x.mnemonic.startswith('str')] == [(0x1c0f2,'strh'), (0x1c102,'strh'), (0x1c112,'strh'), (0x1c122,'strh')], 'helper explicit stores')
    for label, lo, hi, targets in [
        ('setter', 0xc1e0, 0xc214, [0x38fc, 0x1b8c8, 0x1b8c8]),
        ('normal T', 0xc8a0, 0xca06, [0x38fc] + [0x2740] * 9),
        ('alternate T', 0xca10, 0xca76, [0x38fc]),
        ('T contribution', 0x2740, 0x278a, [0x38fc]),
    ]:
        decoded = list(md.disasm(image[lo:hi], lo))
        require([int(x.op_str[1:],16) for x in decoded if x.mnemonic == 'bl'] == targets, label + ' direct callees')
        require(not any(x.mnemonic == 'blx' for x in decoded), label + ' has no indirect call in slice')
    cases = 0
    maximum_instructions = 0
    footprint_destinations = set()
    for root in [0x20008000, 0x20010000]:
        for mode in [0, 1, 2, 3, 4, 5, 6, 255]:
            for mask in [2, 4]:
                for initial in [0, 1, 2, 65535]:
                    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
                    uc.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M4)
                    uc.mem_map(0, 0x40000); uc.mem_write(0, image)
                    uc.mem_map(0x20000000, 0x40000)
                    uc.mem_write(0x200004e0, struct.pack('<I', root))
                    offsets = [0x2486, 0x2488, 0x248c]
                    for off in offsets:
                        uc.mem_write(root + off, struct.pack('<H', initial))
                    saved = [0x12340004, 0x12340005, 0x12340006]
                    for reg, value in zip([UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6], saved):
                        uc.reg_write(reg, value)
                    sp = 0x2003f000; sentinel = 0x30000
                    uc.reg_write(UC_ARM_REG_SP, sp); uc.reg_write(UC_ARM_REG_LR, sentinel | 1)
                    uc.reg_write(UC_ARM_REG_R0, mode); uc.reg_write(UC_ARM_REG_R1, mask)
                    state = {'returned': False, 'instructions': 0, 'calls': [], 'writes': []}
                    def code(u, address, size, user_data):
                        state['instructions'] += 1
                        if address == sentinel:
                            state['returned'] = True; u.emu_stop(); return
                        require((0x1c0c8 <= address and address + size <= 0x1c12c) or (0x38fc <= address and address + size <= 0x3902), 'execution escapes helper closure')
                        if address == 0x38fc:
                            state['calls'].append(address)
                    def write(u, access, address, size, value, user_data):
                        state['writes'].append((address, size, value))
                    uc.hook_add(UC_HOOK_CODE, code)
                    uc.hook_add(UC_HOOK_MEM_WRITE, write)
                    uc.emu_start(0x1c0c9, sentinel + 4, timeout=1000000, count=100)
                    require(state['returned'] and state['calls'] == expected_calls, 'bounded return/callee')
                    require(uc.reg_read(UC_ARM_REG_SP) == sp, 'SP restored')
                    require([uc.reg_read(r) for r in [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6]] == saved, 'callee-saved registers')
                    selected = {1:0x2486, 2:0x2488, 4:0x248c, 6:0x248c}.get(mode)
                    stack_writes = [w for w in state['writes'] if sp - 16 <= w[0] < sp]
                    other_writes = [w for w in state['writes'] if not sp - 16 <= w[0] < sp]
                    require(sorted((a,s) for a,s,v in stack_writes) == [(sp-16,4),(sp-12,4),(sp-8,4),(sp-4,4)], 'fixed prologue stack writes')
                    expected = [] if selected is None else [(root + selected, 2, initial | mask)]
                    require(other_writes == expected, 'only selected RAM status OR')
                    for off in offsets:
                        value = struct.unpack('<H', uc.mem_read(root + off, 2))[0]
                        require(value == (initial | mask if off == selected else initial), 'status field value')
                    footprint_destinations.update(hex(a-root) for a,s,v in other_writes)
                    maximum_instructions = max(maximum_instructions, state['instructions'])
                    cases += 1
    require(cases == 128, 'finite helper matrix')
    print(json.dumps({'schema':'gn-publication-score-dependency-validation-v1', 'status':'PASS_HOST_ONLY_BOUNDED_SOURCE_AUDIT', 'checks':checks, 'inputPins':len(pins['files']), 'instructionChecks':len(report['positiveInstructions']), 'literalChecks':len(report['literalU32']), 'sourceSpans':len(report['spans']), 'realHelperCases':cases, 'maximumInstructionsIncludingReturnSentinel':maximum_instructions, 'helperNonStackWriteRootOffsets':sorted(footprint_destinations), 'unicornVersion':unicorn.__version__, 'targetOperations':0, 'binaryModified':False, 'wholeFirmwareAliasClosureProven':False, 'publicationScoreIndependenceProven':False, 'physicalOrCausalClaim':False}, sort_keys=True, indent=2))

if __name__ == '__main__':
    main()
