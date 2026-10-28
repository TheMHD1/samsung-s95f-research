"""Pure design model. No target binding, I/O, helper, packets or automatic recovery."""
from dataclasses import dataclass

def uint(v,bits):
    if type(v)is not int or not 0<=v<(1<<bits):raise ValueError('unsigned width')
    return v

def set_low_bit(word):return uint(word,16)|1

def clear_low_bit(word):return uint(word,16)&0xfffe

@dataclass(frozen=True)
class Context:
    instance: str='synthetic-same-instance'
    root: int=0x20010000
    rows: int=2160
    lanes: int=1920
    packed_bytes: int=2880
    x_base: int=0
    aa: int=0
    ac: int=2
    operating_mode: int=4
    trainer: int=0
    writer_2460: int=0
    publisher_246e: int=0
    refresh_counter: int=0
    selector: int=0
    selector_mirror: int=0
    rt: tuple=(0,0,1)
    secondary: int=0
    primary: int=0
    other_primary_words: tuple=(0,)*67
    other_secondary_bytes: tuple=(0,)*67
    phase: str='ReadyForHeader'
    fingerprints_verified: bool=False

def invariant(c):
    if type(c)is not Context:raise ValueError('context')
    for x in (c.rows,c.lanes,c.packed_bytes,c.x_base,c.aa,c.ac,c.operating_mode,c.trainer,c.writer_2460,c.publisher_246e,c.refresh_counter,c.selector_mirror,c.primary):uint(x,16)
    uint(c.root,32);uint(c.selector,8);uint(c.secondary,8)
    if type(c.instance)is not str or not c.instance or c.root!=0x20010000 or (c.rows,c.lanes,c.packed_bytes,c.x_base)!=(2160,1920,2880,0):raise ValueError('root/geometry')
    if(c.aa,c.ac,c.operating_mode)!=(0,2,4):raise ValueError('source dispatch context')
    if(c.trainer,c.writer_2460,c.publisher_246e,c.refresh_counter)!=(0,0,0,0):raise ValueError('known writer/refresh controls')
    if c.selector not in(0,1)or c.selector_mirror!=c.selector:raise ValueError('settled sampled selector')
    if c.phase!='ReadyForHeader'or c.fingerprints_verified is not True:raise ValueError('source/protocol proof')
    if type(c.other_primary_words)is not tuple or len(c.other_primary_words)!=67 or type(c.other_secondary_bytes)is not tuple or len(c.other_secondary_bytes)!=67:raise ValueError('full window extent')
    for word in c.other_primary_words:
        if uint(word,16)!=0:raise ValueError('other primary lane changed; never overwrite')
    for byte in c.other_secondary_bytes:
        if uint(byte,8)!=0:raise ValueError('other secondary lane changed; never clear')
    if c.secondary!=0:raise ValueError('secondary changed; never clear it')
    if type(c.rt)is not tuple or len(c.rt)!=3:raise ValueError('RT shape')
    for value in c.rt:uint(value,16)
    if c.rt not in ((0,0,1),(1,0x1001,0)):raise ValueError('hybrid RT')
    return(c.instance,c.root,c.rows,c.lanes,c.packed_bytes,c.x_base,c.aa,c.ac,c.operating_mode)

def fresh_pair(a,b,word,restore=False):
    if invariant(a)!=invariant(b):raise ValueError('identity/context drift')
    if a.selector!=b.selector or a.rt!=b.rt:raise ValueError('in-transaction exposure drift')
    if a.primary!=word or b.primary!=word:raise ValueError('whole word changed; no overwrite')
    if not restore and a.rt!=(0,0,1):raise ValueError('set requires clean baseline')
    return True

@dataclass(frozen=True)
class Ownership:
    identity: tuple
    original: int=0
    installed: int=1
    set_readback_verified: bool=False
    phase: str='ReadyForHeader'

def admit_set(a,b):
    fresh_pair(a,b,0)
    return Ownership(invariant(a))

def admit_restore(owner,a,b):
    if type(owner)is not Ownership or owner.original!=0 or owner.installed!=1 or owner.set_readback_verified is not True or owner.phase!='ReadyForHeader':raise ValueError('missing confirmed ownership receipt')
    fresh_pair(a,b,1,restore=True)
    if invariant(a)!=owner.identity:raise ValueError('ownership context drift')
    # Across the separately admitted exposure C7 and clean/fault may change;
    # both are required stable/coherent within this restore transaction.
    return 0

@dataclass
class Transfer:
    phase: str='ReadyForHeader'
    write_may_have_changed: bool=False
    payload_obligated: bool=False
    write_transport_complete: bool=False
    readback_verified: bool=False
    def header(self,count):
        if self.phase!='ReadyForHeader':raise ValueError('no new header after ambiguity')
        self.write_may_have_changed=True
        self.phase='Unknown'
        if type(count)is int and count==12:self.phase='ExpectingWritePayload';self.payload_obligated=True
    def payload(self,count):
        if self.phase!='ExpectingWritePayload'or not self.payload_obligated:raise ValueError('no payload without exact header')
        self.phase='Unknown';self.payload_obligated=False
        if type(count)is int and count==2:self.phase='ReadyForHeader';self.write_transport_complete=True
    def readback(self,word,expected):
        uint(word,16);uint(expected,16)
        if self.phase!='ReadyForHeader'or not self.write_transport_complete:raise ValueError('no readback after unknown phase')
        if word!=expected:raise ValueError('readback mismatch: ownership unresolved')
        self.readback_verified=True


def confirm_set(pending,transfer,post_a,post_b):
    if type(pending)is not Ownership or pending.set_readback_verified is not False:raise ValueError('pending set admission')
    if type(transfer)is not Transfer or transfer.phase!='ReadyForHeader' or not transfer.write_transport_complete or not transfer.readback_verified:raise ValueError('missing exact write and readback proof')
    fresh_pair(post_a,post_b,1)
    if invariant(post_a)!=pending.identity:raise ValueError('post-write context drift')
    return Ownership(pending.identity,set_readback_verified=True)
