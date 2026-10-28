"""Small source block models. No execution, scheduling or physical-state model."""
def unsigned(value,bits):
    if type(value)is not int or not 0<=value<2**bits:
        raise ValueError('unsigned width')
    return value

def refresh(provider_byte):
    """3934/39fc: full byte copy, then zero-extended root24ca halfword mirror."""
    v=unsigned(provider_byte,8)
    return {'selectorC7':v,'root24ca':v}

def reference_edge(selector,mirror,counter):
    """c250: seed only when byte value differs from the halfword mirror."""
    v=unsigned(selector,8);old=unsigned(mirror,16);count=unsigned(counter,16)
    return {'mirror4c2':v if v!=old else old,
            'counter4c4':(1 if v else 0)if v!=old else count}

def auxiliary_edge(selector,mirror):
    """197a2: separate byte45d mirror; changed-to-nonzero flag in r7."""
    v=unsigned(selector,8);old=unsigned(mirror,8)
    return {'mirror45d':v,'changedToNonzero':v!=old and v!=0}

def dispatch(index,callback,active_after_callback,index_after_callback=None):
    """19574 abstract control path. Does not invoke callback or infer timer units.

    active and the index are sampled AFTER callback, which may change state.
    Omitted index_after_callback explicitly assumes a stable index. The next slot's
    delay value is not modeled: its word starts at the byte-index location.
    """
    i=unsigned(index,8);ptr=unsigned(callback,32);active=unsigned(active_after_callback,8)
    after=i if index_after_callback is None else unsigned(index_after_callback,8)
    if i>=1:
        return {'callbackSelected':None,'index':0,'active':0,'nextSlotOffset':None}
    selected=ptr or None
    if not active:
        return {'callbackSelected':selected,'index':0,'active':0,'nextSlotOffset':None}
    after=(after+1)&255
    return {'callbackSelected':selected,'index':after,'active':active,'nextSlotOffset':after*8}
