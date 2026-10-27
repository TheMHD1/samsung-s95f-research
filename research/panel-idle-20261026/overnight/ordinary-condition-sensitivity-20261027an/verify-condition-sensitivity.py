#!/usr/bin/env python3
"""Offline, explicitly conditional sensitivity of the retained ordinary state."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
BASE = HERE.parent

def need(ok, why):
    if not ok:
        raise ValueError(why)

def load(path, digest):
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == digest, 'SHA-256 ' + str(path))
    return raw

def main():
    af = BASE/'npc-ap-divisor-provenance-20261027af/verify-divisor-provenance.py'
    load(af, 'c7109a19a443788513d84289e1c707175cc2c3cfe54530b9820874133b5faffa')
    spec = importlib.util.spec_from_file_location('pinned_af_math', af)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ordinary = load(BASE/'npc-ap-divisor-snapshot-20261027ak/capture-ordinary-after/ordinary-ap-exco-prefix.bin',
        '0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271')
    package = load(BASE/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin',
        'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0')
    load(BASE/'ap-exco-input-snapshot-20261027w/verify-aggregates.py',
        'f7058a485fd7edde0ebda256d917013999ba37a65355342db782b7d936f4e6b7')
    image = package[0x200:0x40200]
    need(hashlib.sha256(image[0x2f5d8:0x2f970]).hexdigest() ==
        '428c93783eeb93bec0a363d29043bca4c8aecdbf5e7339542ccd5c70ba537b45', 'complete helper')
    u16 = lambda offset: struct.unpack_from('<H', ordinary, offset)[0]
    u32 = lambda offset: struct.unpack_from('<I', ordinary, offset)[0]
    thresholds = [u32(o) for o in (0xd0,0xd4,0xd8)]
    initial = [u32(o) for o in (0xf8,0xfc,0x100)]
    recomputed = [u32(o) for o in (0x10a,0x10e,0x112)]
    need(thresholds == [7464960]*3, 'P0..2')
    need(initial == [8252833,8248159,8248218], 'retained initial sums')
    need(recomputed == [8254590,8251261,8250967], 'retained recomputed sums')
    need([u16(o) for o in (0xea,0xec,0xee)] == [3]*3 and u16(0xe8) == 0,
        'initial tail12..14')
    need([u16(o) for o in (0xf2,0xf4,0xf6,0x104,0x106,0x108)] == [6]*6,
        'capped recomputed tail9..14')
    need([u16(o) for o in (0xca,0xcc,0xce,0xe0,0xe2,0xe6,0xf0,0x116)] ==
        [1,1,0,30,30,1,900,1], 'retained decision controls')
    # This enumerates only the nonzero, finite nonnegative upper-capped
    # writer domain. Zero, exceptional conversion and count0 are excluded.
    by_index = {}
    for divisor in range(1,1025):
        index = module.derived_index(3,900,divisor,6)
        by_index.setdefault(index,[]).append(divisor)
    bands = {str(index):[min(values),max(values)] for index,values in sorted(by_index.items())}
    need(bands == {'3':[772,1024],'4':[601,771],'5':[491,600],'6':[1,490]}, 'exact binary32 index bands')
    need(module.derived_index(3,900,118,6) == 6 and
         module.derived_index(3,900,1024,6) == 3, 'observed/default substitutions')
    need(all(value>threshold for value,threshold in zip(initial,thresholds)) and
         all(value>threshold for value,threshold in zip(recomputed,thresholds)), 'both retained tails qualify')
    def tail(words, index):
        return sum(words[15-index:15]) & 0xffffffff
    witnesses=[]
    for before,after,threshold in zip(initial,recomputed,thresholds):
        # Two no-overflow tables reproduce both endpoints, yet disagree for
        # a shorter tail. These are constructed witnesses, not live bins.
        left=[0]*16;left[12]=before;left[9]=after-before
        right=[0]*16;right[14]=before;right[11]=after-before
        # A wrapping table also reproduces both endpoints but makes index4
        # zero. It prevents silently applying integer monotonicity to u32.
        wrapping=[0]*16;wrapping[12]=before
        wrapping[11]=(1<<32)-before;wrapping[9]=after
        for words in (left,right,wrapping):
            need(all(0<=v<=0xffffffff for v in words), 'u32 witness words')
            need(tail(words,3)==before and tail(words,6)==after, 'endpoint witness equality')
        need(tail(left,1)==0 and tail(right,1)==before, 'unknown bins underdetermine shorter tail')
        need(tail(wrapping,4)==0 and tail(wrapping,3)>threshold and tail(wrapping,6)>threshold,
             'u32 wrap invalidates unconditional monotonicity')
        for words in (left,right):
            need(sum(words[9:15])<=0xffffffff and
                 all(tail(words,index)>=before>threshold for index in (3,4,5,6)),
                 'conditional no-overflow monotonicity examples')
        witnesses.append({'initial':before,'recomputed':after,'added_group_mod_u32':after-before,
            'initial_margin':before-threshold,'recomputed_margin':after-threshold,
            'no_overflow_witnesses_differ_at_index1':True,
            'wrapping_witness_fails_condition_at_index4':True})
    print(json.dumps({
        'target_operations':0,'positive_writer_domain':[1,1024],
        'fixed_numerator':2700,'fixed_cap':6,'divisor_bands_by_final_index':bands,
        'retained_endpoint_tails_both_qualify':True,
        'held_table_index3_default_substitution_clears_condition':False,
        'all_domain_divisors_preserve_condition_requires_fixed_table_and_no_overflow':True,
        'source_bins_identified':False,'live_intervention_performed':False,
        'actual_counterfactual_outcome_proven':False,'blackout_cause_proven':False,
        'constructed_witnesses':witnesses,
    },sort_keys=True,separators=(',',':')))

if __name__ == '__main__':
    main()
